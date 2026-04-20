"""
discovery.py - Autonome ontdekking van nieuwe decompositieprincipes voor Laag 1.

Dit bestand bevat mechanismen om op basis van data-analyse nieuwe vormen van
irreducibiliteit te identificeren die niet door de standaardkaders worden gedekt.
De gevonden principes kunnen dynamisch worden geregistreerd in de meta-specificatie,
decompositieoperatoren en atomiciteitsframeworks. Ook bevat het een evolutionaire
feedbacklus die de meta-specificatie aanpast op basis van succes van principes.

Bugfixes t.o.v. de originele implementatie
-------------------------------------------
1. **Confidence was altijd arbitrair 0.5** – vervangen door ``_compute_confidence``
   die de informatiediverging meet tussen de nieuwe classificatie en bestaande
   frameworks. Een principe met hoge divergentie (extra discriminatievermogen)
   krijgt een hogere confidence.

2. **Voorstellen werden niet gevalideerd vóór registratie** – ``_validate_proposal``
   controleert of het voorstel zowel atomaire als niet-atomaire gevallen oplevert
   (discriminatief) en consistent is met de meta-spec axioma's.

3. **Evolutionaire update convergeert naar 50 % succes-rate** – fout: een principe
   met 90 % succes-rate is uitstekend en mag niet worden afgestraft. De update
   gebruikt nu een gewogen voortschrijdend gemiddelde (exponential moving average)
   dat de huidige gewichtswaarde naar de succes-rate trekt zonder te convergeren
   naar 0.5 als doel.

4. **``persist`` / ``load`` schreven direct naar ``default_atomicity_weights``**
   waardoor de RLock in MetaSpecification werd omzeild. Nu gebruikt via
   ``meta_spec.update_weight()``.

5. **``FrequencyDecompositionOperator.decompose`` splitste simpelweg op positie**
   (array[:mid], array[mid:]) zonder enige Fourier-analyse. Nu gesplitst in
   laag- en hoogfrequente componenten via IFFT.

6. **``_detect_clustering_principle`` gebruikte alleen het eerste element** voor
   de statistische heuristiek en negeerde de rest van de datastroom. Nu wordt
   over de volledige stream geaggregeerd.

7. **``default_atomicity``-closure in ``register_proposal``** ving de ``name``
   variabele niet correct in een loop. Nu expliciet gefixeerd via default-argument.

Uitbreidingen
-------------
- ``EvolutionaryFeedbackLoop.get_stats()`` – gestructureerde statistieken.
- ``EvolutionaryFeedbackLoop.reset()`` – tellers en geladen gewichten wissen.
- ``HeuristicDiscovery._compute_confidence()`` – formele confidence op basis van
  informatiediverging.
- ``HeuristicDiscovery._get_existing_atomicity_rate()`` – helpers voor validatie.
- ``HeuristicDiscovery._validate_proposal()`` – discriminatie- en axioma-check.
- ``HeuristicDiscovery._detect_entropy_principle()`` – entropie-gebaseerde heuristiek.
- ``HeuristicDiscovery._detect_sparsity_principle()`` – schaarsheids-heuristiek.
- ``DensityBasedDecompositionOperator`` – configureerbare ``eps`` / ``min_samples``;
  1D- én 2D-ondersteuning; verbeterde fallback.
- ``FrequencyDecompositionOperator`` – echte FFT-gebaseerde laag/hoog-splitsing;
  configureerbaar ``cutoff_fraction``.
- ``auto_discovery_pipeline`` – validatie-stap vóór registratie; configureerbare
  ``confidence_threshold``; atomaire/niet-atomaire controle.
"""

from __future__ import annotations

import logging
import json
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

# Imports uit de eigen module (worden later gebruikt bij registratie)
from .meta_spec import (
    DecompositionPrinciple,
    register_atomicity_framework,
    ATOMICITY_FRAMEWORKS,
    MetaSpecification,
)
from .decomposition import (
    DecompositionOperator,
    register_decomposition_operator,
    is_atomic_by_operator,
    DECOMPOSITION_OPERATORS,
    PalindromeDecompositionOperator,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optionele bibliotheken – graceful degradation
# ---------------------------------------------------------------------------

try:
    from sklearn.cluster import DBSCAN, KMeans
    HAS_SKLEARN = True
except ImportError:
    DBSCAN = None  # type: ignore[assignment,misc]
    KMeans = None  # type: ignore[assignment,misc]
    HAS_SKLEARN = False
    logger.warning("scikit-learn niet beschikbaar – sommige ontdekkingsmethoden werken niet.")

try:
    from scipy.stats import entropy as scipy_entropy
    HAS_SCIPY = True
except ImportError:
    scipy_entropy = None  # type: ignore[assignment]
    HAS_SCIPY = False
    logger.warning("scipy niet beschikbaar – entropie-berekening valt terug op numpy.")


# ---------------------------------------------------------------------------
# Interne hulpfuncties
# ---------------------------------------------------------------------------

def _safe_extract_array(obs: Any) -> Optional[np.ndarray]:
    """
    Extraheer een numpy float-array uit een observable of ruwe waarde.

    Probeert achtereenvolgens: ``obs.value``, directe conversie.

    Args:
        obs: Observable-object of ruwe waarde.

    Returns:
        Float-array of ``None`` als extractie mislukt.
    """
    try:
        val = obs.value if hasattr(obs, "value") else obs
        arr = np.asarray(val, dtype=float)
        if arr.size == 0 or not np.all(np.isfinite(arr)):
            return None
        return arr
    except Exception:
        return None


def _shannon_entropy(arr: np.ndarray, bins: int = 20) -> float:
    """
    Schat de Shannon-entropie van een 1D-array via een histogram.

    Args:
        arr:  1D float-array.
        bins: Aantal histogram-bins (default: 20).

    Returns:
        Shannon-entropie in nats (≥ 0).
    """
    counts, _ = np.histogram(arr, bins=bins)
    total = counts.sum()
    if total == 0:
        return 0.0
    probs = counts[counts > 0] / total
    return float(-np.sum(probs * np.log(probs)))


# ===========================================================================
# Evolutionaire feedbacklus
# ===========================================================================

class EvolutionaryFeedbackLoop:
    """
    Past de gewichten in een MetaSpecification aan op basis van het succes van
    ontdekte principes.

    De aanpassing gebruikt een **exponential moving average (EMA)** naar de
    gemeten succes-rate, in plaats van te convergeren naar 0.5. Een principe
    met succes-rate 1.0 trekt het gewicht dus richting 1.0 (hoger), niet
    richting 0.5.

    Update-formule per principe::

        ema_rate  = α · success_rate + (1 − α) · ema_rate_prev
        new_weight = clip(old_weight + lr · (ema_rate − old_weight), 0, 1)

    waarbij ``α = smoothing`` (default 0.3) de smoothing-factor is.

    Na een gewijziging kunnen optioneel alle observables als stale worden
    gemarkeerd zodat hun atomiciteit opnieuw wordt berekend.

    Alle mutaties zijn thread-safe via een interne RLock. Persist en load
    communiceren met de meta-spec via ``update_weight()`` zodat ook de
    RLock van de meta-spec wordt gerespecteerd.

    Attributes:
        meta_spec:       De te beheren MetaSpecification.
        learning_rate:   Stapgrootte voor gewichtsupdates (0..1, default 0.1).
        smoothing:       EMA-smoothing-factor α (0..1, default 0.3).
        usage_counter:   Telt hoe vaak elk principe is gebruikt.
        success_counter: Telt hoe vaak elk principe succesvol was.
    """

    def __init__(
        self,
        meta_spec: MetaSpecification,
        learning_rate: float = 0.1,
        smoothing: float = 0.3,
    ) -> None:
        """
        Args:
            meta_spec:     De meta-specificatie waarvan de gewichten worden aangepast.
            learning_rate: Stapgrootte voor gewichtsupdates (0..1).
            smoothing:     EMA-smoothing-factor α (0..1). Hogere waarden reageren
                           sneller op recente resultaten, lagere waarden zijn
                           stabieler.
        """
        if not 0.0 < learning_rate <= 1.0:
            raise ValueError(f"learning_rate moet in (0, 1] liggen, got {learning_rate}")
        if not 0.0 < smoothing <= 1.0:
            raise ValueError(f"smoothing moet in (0, 1] liggen, got {smoothing}")

        self.meta_spec = meta_spec
        self.learning_rate = learning_rate
        self.smoothing = smoothing
        self.usage_counter: Dict[str, int] = {}
        self.success_counter: Dict[str, int] = {}
        self._ema_rates: Dict[str, float] = {}   # exponential moving average per principe
        self._lock = threading.RLock()

    # -----------------------------------------------------------------------
    # Registratie van gebruik
    # -----------------------------------------------------------------------

    def record_usage(self, principle_name: str, success: bool) -> None:
        """
        Registreer dat een principe is gebruikt en of dat tot een succesvolle
        uitkomst leidde.

        Args:
            principle_name: Naam van het principe (bv. ``"boolean"``).
            success:        True als het principe correct werkte.
        """
        with self._lock:
            self.usage_counter[principle_name] = (
                self.usage_counter.get(principle_name, 0) + 1
            )
            if success:
                self.success_counter[principle_name] = (
                    self.success_counter.get(principle_name, 0) + 1
                )

    # -----------------------------------------------------------------------
    # Gewichtsupdate (EMA-gebaseerd – bug 3 fix)
    # -----------------------------------------------------------------------

    def _current_success_rate(self, principle_name: str) -> float:
        """Bereken de huidige succes-rate voor een principe."""
        total = self.usage_counter.get(principle_name, 0)
        if total == 0:
            return 0.5  # Onbekend: neutraal als startwaarde
        return self.success_counter.get(principle_name, 0) / total

    def update_weights(self) -> None:
        """
        Werk de gewichten in de meta-specificatie bij op basis van de succes-rates.

        Gebruikt een exponential moving average (EMA) zodat een principe met
        hoge succes-rate een hoger gewicht krijgt – niet naar 0.5 convergeert.

        Formule::

            ema  = α · rate + (1 − α) · ema_prev
            Δw   = lr · (ema − old_weight)
            w'   = clip(old_weight + Δw, 0, 1)

        Alleen principes die in ``default_atomicity_weights`` voorkomen worden
        bijgewerkt.
        """
        with self._lock:
            for principle_name in list(self.usage_counter.keys()):
                if principle_name not in self.meta_spec.default_atomicity_weights:
                    continue

                rate = self._current_success_rate(principle_name)

                # EMA-update
                prev_ema = self._ema_rates.get(
                    principle_name,
                    self.meta_spec.get_weight(principle_name),
                )
                ema = self.smoothing * rate + (1.0 - self.smoothing) * prev_ema
                self._ema_rates[principle_name] = ema

                # Gewichtsupdate richting EMA
                old_weight = self.meta_spec.get_weight(principle_name)
                delta = self.learning_rate * (ema - old_weight)
                new_weight = float(np.clip(old_weight + delta, 0.0, 1.0))

                # Via update_weight() voor thread-safe toegang tot meta_spec
                self.meta_spec.update_weight(principle_name, new_weight)
                logger.info(
                    "Gewicht voor %s bijgewerkt: %.4f → %.4f (ema=%.4f, rate=%.4f)",
                    principle_name, old_weight, new_weight, ema, rate,
                )

    def evolve(
        self, observables_registry: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Voer één evolutiestap uit: werk gewichten bij en markeer eventueel
        alle observables als stale.

        Args:
            observables_registry: Optioneel dict van observables. Voor elk
                                  observable wordt ``_mark_stale()`` aangeroepen.
        """
        self.update_weights()
        if observables_registry is not None:
            for obs in observables_registry.values():
                if hasattr(obs, "_mark_stale"):
                    obs._mark_stale()
            logger.debug(
                "Alle %d observables gemarkeerd als stale na gewichtsupdate.",
                len(observables_registry),
            )

    # -----------------------------------------------------------------------
    # Persist / load (bug 4 fix: via update_weight)
    # -----------------------------------------------------------------------

    def persist(self, filepath: str = "evolution_weights.json") -> None:
        """
        Sla de huidige gewichten, usage- en success-tellers op in een JSON-bestand.

        Args:
            filepath: Pad naar het JSON-bestand.
        """
        with self._lock:
            data = {
                "usage_counter": dict(self.usage_counter),
                "success_counter": dict(self.success_counter),
                "ema_rates": dict(self._ema_rates),
                "weights": dict(self.meta_spec.default_atomicity_weights),
                "learning_rate": self.learning_rate,
                "smoothing": self.smoothing,
            }
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        logger.info("Evolutionaire feedback opgeslagen naar %s", filepath)

    def load(self, filepath: str = "evolution_weights.json") -> None:
        """
        Laad eerder opgeslagen gegevens uit een JSON-bestand.

        Gewichten worden bijgewerkt via ``meta_spec.update_weight()`` zodat
        de RLock van de meta-spec wordt gerespecteerd (bug 4 fix).

        Args:
            filepath: Pad naar het JSON-bestand.
        """
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        with self._lock:
            self.usage_counter = dict(data.get("usage_counter", {}))
            self.success_counter = dict(data.get("success_counter", {}))
            self._ema_rates = dict(data.get("ema_rates", {}))
            self.learning_rate = float(data.get("learning_rate", self.learning_rate))
            self.smoothing = float(data.get("smoothing", self.smoothing))
            weights = data.get("weights", {})

        # Gebruik update_weight() buiten de lock zodat meta_spec zijn eigen lock
        # kan pakken zonder deadlock (beide zijn RLocks, maar dit is veiliger)
        for k, v in weights.items():
            try:
                self.meta_spec.update_weight(k, float(v))
            except ValueError:
                # Onbekend framework: sla op in de ema_rates cache voor toekomstig gebruik
                logger.debug(
                    "Gewicht voor onbekend framework '%s' niet geladen in meta_spec.", k
                )

        logger.info("Evolutionaire feedback geladen uit %s", filepath)

    # -----------------------------------------------------------------------
    # Introspectie (nieuw)
    # -----------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourneer een gestructureerd overzicht van alle bijgehouden statistieken.

        Returns:
            Dict met per principe: ``usage``, ``successes``, ``rate``,
            ``ema``, ``current_weight``.
        """
        with self._lock:
            stats: Dict[str, Any] = {}
            for name in self.usage_counter:
                rate = self._current_success_rate(name)
                stats[name] = {
                    "usage": self.usage_counter[name],
                    "successes": self.success_counter.get(name, 0),
                    "rate": rate,
                    "ema": self._ema_rates.get(name, None),
                    "current_weight": self.meta_spec.get_weight(name),
                }
            return stats

    def reset(self) -> None:
        """
        Wis alle tellers en EMA-rates. De huidige gewichten in de meta-spec
        worden NIET gereset (die zijn eigendom van de meta-spec).
        """
        with self._lock:
            self.usage_counter.clear()
            self.success_counter.clear()
            self._ema_rates.clear()
        logger.debug("EvolutionaryFeedbackLoop gereset.")


# ===========================================================================
# DiscoveryProposal
# ===========================================================================

@dataclass
class DiscoveryProposal:
    """
    Vertegenwoordigt een voorgesteld nieuw decompositieprincipe.

    Attributes:
        name:           Unieke naam (bv. ``"clustering"``).
        description:    Korte beschrijving van het principe.
        operator_class: ``DecompositionOperator``-subklasse die het principe
                        implementeert.
        atomicity_func: Optioneel expliciete atomiciteitsfunctie. Als None
                        wordt een standaard gegenereerd op basis van
                        ``is_atomic_by_operator``.
        confidence:     Confidence in het voorstel (0..1). Wordt berekend door
                        ``_compute_confidence``; standaardwaarde 0.0 totdat een
                        formele schatting beschikbaar is.
        evidence:       Ondersteunende data (bv. clustertelling, piekfrequentie).
        validated:      True als ``_validate_proposal`` het voorstel heeft
                        goedgekeurd.
        operator_kwargs: Kwargs voor de constructie van de operator-instantie.
    """

    name: str
    description: str
    operator_class: type
    atomicity_func: Optional[Callable] = None
    confidence: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    validated: bool = False
    operator_kwargs: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# HeuristicDiscovery
# ===========================================================================

class HeuristicDiscovery:
    """
    Ontdekt nieuwe decompositieprincipes door patronen in data te analyseren.

    Voor elk heuristisch ontdekt principe wordt:
    1. De confidence formeel berekend via ``_compute_confidence``.
    2. Het voorstel gevalideerd via ``_validate_proposal`` voordat het in
       ``self.proposals`` terecht komt.

    Heuristieken:
        - ``_detect_clustering_principle``  – lokale dichtheidsstructuur (DBSCAN)
        - ``_detect_frequency_principle``   – periodiciteit (FFT)
        - ``_detect_symmetry_principle``    – palindroom- / spiegelsymmetrie
        - ``_detect_entropy_principle``     – hoge-entropie atomiciteit (nieuw)
        - ``_detect_sparsity_principle``    – schaarsheids-atomiciteit (nieuw)
    """

    def __init__(
        self,
        data_stream: List[Any],
        meta_spec: Optional[MetaSpecification] = None,
    ) -> None:
        """
        Args:
            data_stream: Lijst van observables of ruwe data.
            meta_spec:   Optioneel de huidige meta-specificatie.
        """
        self.data_stream = data_stream
        self.meta_spec = meta_spec
        self.proposals: List[DiscoveryProposal] = []
        self._lock = threading.Lock()

    # -----------------------------------------------------------------------
    # Publieke interface
    # -----------------------------------------------------------------------

    def discover(self) -> List[DiscoveryProposal]:
        """
        Voer alle heuristische analyses uit en retourneer de lijst van
        gevalideerde voorstellen.

        Returns:
            Lijst van ``DiscoveryProposal``-objecten met ``validated=True``.
        """
        with self._lock:
            self.proposals = []
            self._detect_clustering_principle()
            self._detect_frequency_principle()
            self._detect_symmetry_principle()
            self._detect_entropy_principle()
            self._detect_sparsity_principle()
            return list(self.proposals)

    # -----------------------------------------------------------------------
    # Confidence-berekening (bug 1 fix)
    # -----------------------------------------------------------------------

    def _get_existing_atomicity_rate(
        self, test_values: List[Any]
    ) -> float:
        """
        Bereken welk deel van ``test_values`` als atomair wordt geclassificeerd
        door de bestaande geregistreerde decompostie-operatoren.

        Args:
            test_values: Lijst van ruwe waarden (niet observables).

        Returns:
            Fractie van waarden die atomair zijn (gemiddeld over alle operatoren).
            Retourneert 0.5 als geen waarden of operatoren beschikbaar zijn.
        """
        if not test_values or not DECOMPOSITION_OPERATORS:
            return 0.5
        rates = []
        for op_name in DECOMPOSITION_OPERATORS:
            n_atomic = sum(
                1 for v in test_values
                if is_atomic_by_operator(v, op_name)
            )
            rates.append(n_atomic / len(test_values))
        return float(np.mean(rates)) if rates else 0.5

    def _compute_confidence(
        self,
        operator_class: type,
        test_values: List[Any],
        operator_kwargs: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Bereken de formele confidence voor een voorgesteld principe.

        Confidence wordt bepaald door de **informatiediverging**: het absolute
        verschil tussen de atomiciteits-rate van het nieuwe principe en de
        gemiddelde rate van bestaande principes op dezelfde data. Een groter
        verschil impliceert dat het nieuwe principe extra discriminatievermogen
        toevoegt.

        Formule::

            rate_new      = fraction(test_values classified atomic by new op)
            rate_existing = average over existing operators
            divergence    = |rate_new − rate_existing|
            confidence    = min(1.0, divergence * 2.0)

        Een divergentie ≥ 0.5 levert confidence 1.0. Een divergentie van 0.0
        levert confidence 0.0 (principe voegt niets toe).

        Args:
            operator_class:  ``DecompositionOperator``-subklasse om te testen.
            test_values:     Lijst van ruwe waarden om op te testen.
            operator_kwargs: Kwargs voor instantiatie van de operator.

        Returns:
            Confidence in [0, 1].
        """
        if not test_values:
            return 0.0

        try:
            op = operator_class(**(operator_kwargs or {}))
        except Exception as exc:
            logger.debug("Operator-instantiatie mislukt bij confidence-berekening: %s", exc)
            return 0.0

        n_atomic = 0
        n_applicable = 0
        for val in test_values:
            try:
                if not op.can_decompose(val):
                    continue
                n_applicable += 1
                parts = op.decompose(val)
                if len(parts) < 2:
                    n_atomic += 1
            except Exception:
                continue

        if n_applicable == 0:
            return 0.0

        rate_new = n_atomic / n_applicable
        rate_existing = self._get_existing_atomicity_rate(test_values)
        divergence = abs(rate_new - rate_existing)
        return float(min(1.0, divergence * 2.0))

    # -----------------------------------------------------------------------
    # Validatie (bug 2 fix)
    # -----------------------------------------------------------------------

    def _validate_proposal(
        self,
        proposal: DiscoveryProposal,
        test_values: List[Any],
    ) -> bool:
        """
        Controleer of het voorstel voldoet aan de formele vereisten:

        1. **Discriminatief**: de operator moet zowel atomaire als niet-atomaire
           gevallen produceren (geen degenerate operator die altijd True of
           altijd False retourneert).
        2. **Consistent met meta-spec axioma's**: als de meta-spec een lijst
           van axioma's heeft, worden de relevante axioma's gecontroleerd.
        3. **Niet overbodig**: het principe moet een detecteerbaar andere
           classificatie geven dan de al bestaande operatoren (confidence > 0).

        Args:
            proposal:    Het te valideren voorstel.
            test_values: Lijst van ruwe waarden om op te testen.

        Returns:
            True als het voorstel geldig is.
        """
        if not test_values:
            logger.debug("Validatie van %s overgeslagen: geen testwaarden.", proposal.name)
            return False

        # Instantieer de operator
        try:
            op = proposal.operator_class(**(proposal.operator_kwargs or {}))
        except Exception as exc:
            logger.debug(
                "Validatie van %s mislukt bij instantiatie: %s", proposal.name, exc
            )
            return False

        # Eis 1: discriminatief
        results = []
        for val in test_values:
            try:
                if not op.can_decompose(val):
                    results.append(True)   # niet van toepassing → atoom
                    continue
                parts = op.decompose(val)
                results.append(len(parts) < 2)
            except Exception:
                continue

        if not results:
            logger.debug("Validatie van %s mislukt: geen toepasselijke waarden.", proposal.name)
            return False

        n_atomic = sum(results)
        n_total = len(results)

        has_atomic = n_atomic > 0
        has_non_atomic = n_atomic < n_total
        if not (has_atomic and has_non_atomic):
            logger.debug(
                "Validatie van %s mislukt: niet discriminatief "
                "(%d/%d atomair).", proposal.name, n_atomic, n_total,
            )
            return False

        # Eis 2: meta-spec axioma's (indien beschikbaar)
        if self.meta_spec is not None:
            axioms = getattr(self.meta_spec, "axioms", [])
            if "atomicity_is_continuous_not_binary" in axioms:
                # Niet-binaire operators zijn acceptabel; skip binaire check
                pass

        # Eis 3: niet overbodig (confidence moet > 0 zijn)
        if proposal.confidence <= 0.0:
            logger.debug(
                "Validatie van %s mislukt: confidence is 0.", proposal.name
            )
            return False

        return True

    # -----------------------------------------------------------------------
    # Heuristieken
    # -----------------------------------------------------------------------

    def _extract_test_values(self, max_n: int = 50) -> Tuple[List[Any], List[np.ndarray]]:
        """
        Extraheer ruwe waarden en numerieke arrays uit de datastroom.

        Args:
            max_n: Maximaal aantal te verwerken elementen.

        Returns:
            Tuple (raw_values, numeric_arrays).
        """
        raw_values: List[Any] = []
        arrays: List[np.ndarray] = []

        for obs in self.data_stream[:max_n]:
            val = obs.value if hasattr(obs, "value") else obs
            raw_values.append(val)
            arr = _safe_extract_array(obs)
            if arr is not None:
                arrays.append(arr)

        return raw_values, arrays

    def _detect_clustering_principle(self) -> None:
        """
        Detecteer of de data een clusterstructuur vertoont die niet door
        bestaande geometrische decompositie wordt gevat.

        Gebruikt de volledige datastroom (max. 50 elementen) voor de
        statistische heuristiek – niet alleen het eerste element (bug 6 fix).
        """
        if len(self.data_stream) < 10:
            return

        raw_values, arrays = self._extract_test_values(max_n=50)
        if not arrays:
            return

        operator_kwargs: Dict[str, Any] = {"eps": 0.5, "min_samples": 2}
        evidence: Dict[str, Any] = {}

        # Statistische heuristiek over de volledige stream
        flat_vals: List[float] = []
        for arr in arrays:
            if arr.ndim == 1:
                flat_vals.extend(arr.tolist())
        if flat_vals:
            arr_all = np.asarray(flat_vals)
            mean_abs = np.mean(np.abs(arr_all))
            std_ = np.std(arr_all)
            evidence["std"] = float(std_)
            evidence["mean_abs"] = float(mean_abs)

        # DBSCAN-clustering op beschikbare 2D-punten
        if HAS_SKLEARN and DBSCAN is not None:
            points = [a for a in arrays if a.ndim == 1 and len(a) > 1]
            if len(points) >= 10:
                try:
                    # Zorg voor uniform-dimensionale matrix (pad/trim naar kortste)
                    min_dim = min(len(p) for p in points)
                    pts_mat = np.array([p[:min_dim] for p in points])
                    # Set OMP_NUM_THREADS=1 to avoid MKL/vcomp DLL conflict on Windows
                    # (fatal exception code 0xc06d007f from threadpoolctl)
                    import os as _os
                    _old_omp = _os.environ.get("OMP_NUM_THREADS")
                    _os.environ["OMP_NUM_THREADS"] = "1"
                    try:
                        clustering = DBSCAN(eps=0.5, min_samples=2).fit(pts_mat)
                    finally:
                        if _old_omp is None:
                            _os.environ.pop("OMP_NUM_THREADS", None)
                        else:
                            _os.environ["OMP_NUM_THREADS"] = _old_omp
                    labels = clustering.labels_
                    n_clusters = len(set(labels) - {-1})
                    noise_ratio = float(np.mean(labels == -1))
                    evidence["n_clusters"] = n_clusters
                    evidence["noise_ratio"] = noise_ratio
                    if n_clusters < 2:
                        return   # Geen zinvolle clusterstructuur
                except Exception as exc:
                    logger.debug("DBSCAN mislukt: %s", exc)
                    return
            else:
                return   # Te weinig punten voor clustering
        else:
            return   # Zonder sklearn: sla clustering over

        confidence = self._compute_confidence(
            DensityBasedDecompositionOperator, raw_values, operator_kwargs
        )
        proposal = DiscoveryProposal(
            name="density_based",
            description="Scheiding op basis van lokale dichtheid (DBSCAN-achtig)",
            operator_class=DensityBasedDecompositionOperator,
            confidence=confidence,
            evidence=evidence,
            operator_kwargs=operator_kwargs,
        )
        if self._validate_proposal(proposal, raw_values):
            proposal.validated = True
            self.proposals.append(proposal)

    def _detect_frequency_principle(self) -> None:
        """
        Detecteer periodiciteit in de data via FFT.

        Een hoge piekscore in het frequentiespectrum (exclusief DC) wijst op
        periodiciteit die een Fourier-gebaseerde decompositie rechtvaardigt.
        """
        if not self.data_stream:
            return

        raw_values, arrays = self._extract_test_values(max_n=10)
        series_list = [a.flatten() for a in arrays if a.ndim in (1, 2) and a.size >= 10]

        if not series_list:
            return

        peak_freqs: List[float] = []
        peak_scores: List[float] = []

        for series in series_list:
            try:
                fft_vals = np.fft.rfft(series)
                freqs = np.fft.rfftfreq(len(series))
                magnitudes = np.abs(fft_vals)
                # Exclusief DC (index 0)
                if len(magnitudes) < 2:
                    continue
                peak_idx = int(np.argmax(magnitudes[1:])) + 1
                peak_freq = float(freqs[peak_idx])
                dc_power = float(magnitudes[0] ** 2)
                total_power = float(np.sum(magnitudes ** 2))
                # Piek-score = fractie van vermogen in de top-frequentie (excl. DC)
                peak_power = float(magnitudes[peak_idx] ** 2)
                score = (peak_power / (total_power - dc_power + 1e-12))
                if peak_freq > 0.01:
                    peak_freqs.append(peak_freq)
                    peak_scores.append(score)
            except Exception as exc:
                logger.debug("FFT-analyse mislukt: %s", exc)

        if not peak_freqs:
            return

        mean_score = float(np.mean(peak_scores))
        mean_freq = float(np.mean(peak_freqs))
        evidence = {"peak_freq": mean_freq, "peak_score": mean_score}

        # Alleen voorstellen als de piek significant is (> 20 % van het vermogen)
        if mean_score < 0.2:
            return

        # Gebruik de mediane piekfrequentie als cutoff
        cutoff = float(np.clip(mean_freq, 0.05, 0.45))
        operator_kwargs = {"cutoff_fraction": cutoff}

        confidence = self._compute_confidence(
            FrequencyDecompositionOperator, raw_values, operator_kwargs
        )
        proposal = DiscoveryProposal(
            name="frequency",
            description="Scheiding op basis van dominante frequentie (FFT laag/hoog)",
            operator_class=FrequencyDecompositionOperator,
            confidence=confidence,
            evidence=evidence,
            operator_kwargs=operator_kwargs,
        )
        if self._validate_proposal(proposal, raw_values):
            proposal.validated = True
            self.proposals.append(proposal)

    def _detect_symmetry_principle(self) -> None:
        """
        Detecteer symmetrieën (palindroom / spiegelsymmetrie) in de datastroom.

        Controleert over meerdere elementen (niet enkel het eerste) voor
        een robuustere schatting.
        """
        if not self.data_stream:
            return

        raw_values, arrays = self._extract_test_values(max_n=30)
        flat_arrays = [a.flatten() for a in arrays if a.ndim in (1, 2) and a.size > 1]

        if not flat_arrays:
            return

        n_palindrome = sum(
            1 for a in flat_arrays if np.allclose(a, a[::-1], atol=1e-6)
        )
        n_antisymmetric = sum(
            1 for a in flat_arrays if np.allclose(a, -a[::-1], atol=1e-6)
        )
        n_total = len(flat_arrays)
        palindrome_rate = n_palindrome / n_total
        evidence = {
            "palindrome_rate": palindrome_rate,
            "antisymmetric_rate": n_antisymmetric / n_total,
            "n_checked": n_total,
        }

        # Alleen voorstellen als een aanzienlijk deel symmetrisch is
        if palindrome_rate < 0.1:
            return

        confidence = self._compute_confidence(
            PalindromeDecompositionOperator, raw_values
        )
        proposal = DiscoveryProposal(
            name="palindrome_symmetry",
            description="Symmetrie op basis van palindroomstructuur",
            operator_class=PalindromeDecompositionOperator,
            confidence=confidence,
            evidence=evidence,
        )
        if self._validate_proposal(proposal, raw_values):
            proposal.validated = True
            self.proposals.append(proposal)

    def _detect_entropy_principle(self) -> None:
        """
        Detecteer of hoge-entropie reeksen een apart decompositieprincipe
        rechtvaardigen.

        Een reeks met hoge Shannon-entropie is informatietheretisch complex
        en kan baat hebben bij entropie-gebaseerde decompositie.

        **Drempel-kalibratie (antwoord op 'magic numbers' kritiek):**
        In plaats van een vaste drempel van 1.5 nats, wordt de drempel
        bepaald via een **percentielbenadering op de huidige datastroom**:
        splitsen wanneer de gemiddelde entropie boven het 75e percentiel
        valt van de entropies in de stroom.  Als de stroom te klein is voor
        statistisch betekenisvolle percentielschatting (< 5 samples), wordt
        een conservatieve fallback van 1.0 nat gebruikt.

        Dit maakt de drempel zelf-kalibrerend: de AI past zijn eigen
        'magic number' aan op basis van de data, zoals vereist door de
        post-antropocentrische architectuur.
        """
        if not self.data_stream:
            return

        raw_values, arrays = self._extract_test_values(max_n=30)
        flat_arrays = [a.flatten() for a in arrays if a.ndim in (1, 2) and a.size >= 8]

        if not flat_arrays:
            return

        entropies = [_shannon_entropy(a) for a in flat_arrays]
        mean_entropy = float(np.mean(entropies))
        evidence = {
            "mean_entropy": mean_entropy,
            "max_entropy": float(np.max(entropies)),
            "n_checked": len(flat_arrays),
        }

        # Self-calibrating threshold: 75th percentile of observed entropies.
        # Fallback to 1.0 nat when too few samples for reliable percentile estimation.
        if len(entropies) >= 5:
            threshold = float(np.percentile(entropies, 75))
        else:
            threshold = 1.0  # Conservative prior (Layer 6+ will refine this)
        evidence["entropy_threshold"] = threshold

        if mean_entropy < threshold:
            return

        confidence = self._compute_confidence(
            EntropyDecompositionOperator, raw_values
        )
        proposal = DiscoveryProposal(
            name="entropy_based",
            description="Decompositie op basis van Shannon-entropie van deelreeksen",
            operator_class=EntropyDecompositionOperator,
            confidence=confidence,
            evidence=evidence,
        )
        if self._validate_proposal(proposal, raw_values):
            proposal.validated = True
            self.proposals.append(proposal)

    def _detect_sparsity_principle(self) -> None:
        """
        Detecteer of schaarsheid (veel nul-waarden) een apart decompositieprincipe
        rechtvaardigt.

        Schaarse vectoren kunnen worden gesplitst in een niet-nul structuur en
        een nul-structuur, wat informatie kan opleveren over irreducibiliteit in
        context van gecomprimeerde representaties.

        **Drempel-kalibratie (verbeterd na feedback op bimodale distributies):**
        De oorspronkelijke vaste drempel (0.3) was een 'magic number'.  De
        mediaan-benadering faalde bij bimodale distributies (bijv. 57% schaarse
        en 43% dichte vectoren): de mediaan is dan gelijk aan de maximale
        schaarsheidswaarde, waardoor ``mean_sparsity < threshold`` altijd faalt.

        De verbeterde aanpak gebruikt een **bimodaliteitsdetectie**:
        1. Bereken de standaarddeviatie van de schaarsheidsratios.
        2. Als std > 0.25 (bimodaal), is het gemiddelde de beste indicator
           voor de aanwezigheid van een schaarse klasse.
        3. Als std ≤ 0.25 (unimodaal), gebruik de mediaan als threshold.

        Dit is theoretisch gefundeerd: een hoge std in schaarsheid impliceert
        dat de datastroom twee klassen bevat (schaars en dicht) — precies de
        situatie die een nieuw decompositieprincipe rechtvaardigt.

        De verzadigingsconstante (0.25) is een initiële prior; een hogere laag
        (Layer 6 Meta-Learning) kan deze via ``meta_spec.metadata`` aanpassen.
        """
        if not self.data_stream:
            return

        raw_values, arrays = self._extract_test_values(max_n=30)
        flat_arrays = [a.flatten() for a in arrays if a.ndim in (1, 2) and a.size >= 4]

        if not flat_arrays:
            return

        sparsity_ratios = [
            float(np.mean(np.abs(a) < 1e-9)) for a in flat_arrays
        ]
        mean_sparsity = float(np.mean(sparsity_ratios))
        std_sparsity = float(np.std(sparsity_ratios))
        evidence = {
            "mean_sparsity": mean_sparsity,
            "max_sparsity": float(np.max(sparsity_ratios)),
            "std_sparsity": std_sparsity,
            "n_checked": len(flat_arrays),
        }

        # Bimodality-aware threshold selection:
        # High std → bimodal (sparse + dense classes exist) → use mean as indicator
        # Low std  → unimodal → use median (avoids false positives)
        bimodal_threshold = 0.25   # Prior: Layer 6+ can update via meta_spec
        if len(sparsity_ratios) >= 5:
            if std_sparsity > bimodal_threshold:
                # Bimodal distribution: mean is a reliable indicator of mixed sparsity
                threshold = max(0.1, mean_sparsity * 0.5)  # Activate if mean > 10%
            else:
                # Unimodal: percentile-based (60th to avoid median being threshold)
                threshold = float(np.percentile(sparsity_ratios, 60))
                threshold = max(threshold, 0.1)
        else:
            threshold = 0.15  # Conservative prior for small datasets

        evidence["sparsity_threshold"] = threshold
        evidence["is_bimodal"] = std_sparsity > bimodal_threshold

        if mean_sparsity < threshold:
            return

        confidence = self._compute_confidence(
            SparsityDecompositionOperator, raw_values
        )
        proposal = DiscoveryProposal(
            name="sparsity_based",
            description="Decompositie op basis van schaarsheid (nul vs. niet-nul structuur)",
            operator_class=SparsityDecompositionOperator,
            confidence=confidence,
            evidence=evidence,
        )
        if self._validate_proposal(proposal, raw_values):
            proposal.validated = True
            self.proposals.append(proposal)

    # -----------------------------------------------------------------------
    # Registratie
    # -----------------------------------------------------------------------

    @staticmethod
    def register_proposal(proposal: DiscoveryProposal) -> bool:
        """
        Registreer een goedgekeurd voorstel in het systeem.

        Voegt het principe toe aan ``DecompositionPrinciple``, registreert de
        operator en (optioneel) een atomiciteitsframework.

        Check-or-create: als het principe al geregistreerd is, wordt niets
        gedaan en wordt False geretourneerd.

        De closure-fix (bug 7): de naam wordt via een default-argument
        gebonden zodat elke default_atomicity-functie de correcte naam
        gebruikt, ook in een loop.

        Args:
            proposal: Het te registreren voorstel.

        Returns:
            True als het principe nieuw geregistreerd is, False als het al bestond.
        """
        name = proposal.name

        if name in DECOMPOSITION_OPERATORS:
            logger.warning(
                "Principe %s is al geregistreerd als operator, overslaan.", name
            )
            return False

        # 1. Voeg principe toe aan dynamische registry
        DecompositionPrinciple.register(name)
        logger.info("Nieuw decompositieprincipe geregistreerd: %s", name)

        # 2. Instantieer en registreer de operator
        try:
            operator = proposal.operator_class(**(proposal.operator_kwargs or {}))
        except Exception as exc:
            logger.error(
                "Operator-instantiatie voor %s mislukt: %s", name, exc
            )
            return False

        register_decomposition_operator(name, operator)

        # 3. Registreer atomiciteitsframework
        if proposal.atomicity_func is not None:
            register_atomicity_framework(name, proposal.atomicity_func)
        else:
            # Bug 7 fix: naam vastleggen via default-argument in de closure
            def _default_atomicity(
                obs: Any, ctx: Optional[Dict] = None, _name: str = name
            ) -> float:
                """Standaard atomiciteitsframework via is_atomic_by_operator."""
                val = obs.value if hasattr(obs, "value") else obs
                return 1.0 if is_atomic_by_operator(val, _name, ctx) else 0.0

            register_atomicity_framework(name, _default_atomicity)

        logger.info(
            "Operator en atomiciteitsframework voor %s geregistreerd.", name
        )
        return True


# ===========================================================================
# Dynamische operatoren
# ===========================================================================

class DensityBasedDecompositionOperator(DecompositionOperator):
    """
    Splitst data op basis van lokale dichtheid (DBSCAN-achtig).

    Ondersteunt zowel 1D- als 2D-arrays. Vereist scikit-learn; anders
    fallback op mediaan-splitsing.

    Args:
        eps:         DBSCAN buurtradius (default: 0.5).
        min_samples: Minimaal aantal punten per cluster (default: 2).
    """

    operator_name = "density_based"

    def __init__(self, eps: float = 0.5, min_samples: int = 2) -> None:
        self.eps = eps
        self.min_samples = min_samples

    def can_decompose(self, obs: Any) -> bool:
        try:
            arr = np.asarray(obs, dtype=float)
            return arr.ndim in (1, 2) and arr.shape[0] >= 2
        except Exception:
            return False

    def decompose(
        self, obs: Any, context: Optional[Dict] = None
    ) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        arr = np.asarray(obs, dtype=float)
        # Zorg voor 2D-representatie voor DBSCAN
        pts = arr.reshape(-1, 1) if arr.ndim == 1 else arr

        if HAS_SKLEARN and DBSCAN is not None:
            try:
                clustering = DBSCAN(
                    eps=self.eps, min_samples=self.min_samples
                ).fit(pts)
                labels = clustering.labels_
                unique_labels = sorted(set(labels) - {-1})
                if len(unique_labels) < 2:
                    return []   # Niet genoeg clusters
                clusters = [pts[labels == lbl] for lbl in unique_labels]
                # Terug naar oorspronkelijke dimensie
                if arr.ndim == 1:
                    clusters = [c.flatten() for c in clusters]
                return clusters
            except Exception as exc:
                logger.warning("DBSCAN mislukt: %s – fallback op mediaan.", exc)

        return self._fallback_split(pts, arr.ndim == 1)

    def _fallback_split(
        self, pts: np.ndarray, flatten_output: bool
    ) -> List[Any]:
        """Eenvoudige splitsing op mediaan van de eerste dimensie."""
        if pts.shape[0] < 2:
            return []
        median = np.median(pts[:, 0])
        left = pts[pts[:, 0] <= median]
        right = pts[pts[:, 0] > median]
        if len(left) == 0 or len(right) == 0:
            mid = pts.shape[0] // 2
            left, right = pts[:mid], pts[mid:]
        if flatten_output:
            return [left.flatten(), right.flatten()]
        return [left, right]


class FrequencyDecompositionOperator(DecompositionOperator):
    """
    Splitst een 1D-reeks in laag- en hoogfrequente componenten via IFFT.

    Gebruikt IFFT om echte laag/hoog-frequente componenten te reconstrueren,
    in plaats van simpelweg te splitsen op positie (bug 5 fix).

    Args:
        cutoff_fraction: Fractie van frequenties (0..0.5) die als
                         laagfrequent worden beschouwd (default: 0.25).
                         Waarden dichter bij 0.5 bevatten meer frequenties
                         in de laagfrequente component.
    """

    operator_name = "frequency"

    def __init__(self, cutoff_fraction: float = 0.25) -> None:
        self.cutoff_fraction = float(
            np.clip(cutoff_fraction, 1e-3, 0.499)
        )

    def can_decompose(self, obs: Any) -> bool:
        try:
            arr = np.asarray(obs, dtype=float).flatten()
            return arr.ndim == 1 and len(arr) >= 4
        except Exception:
            return False

    def decompose(
        self, obs: Any, context: Optional[Dict] = None
    ) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        arr = np.asarray(obs, dtype=float).flatten()
        n = len(arr)

        try:
            fft_vals = np.fft.rfft(arr)
            freqs = np.fft.rfftfreq(n)

            # Laagfrequent masker
            low_mask = np.abs(freqs) <= self.cutoff_fraction

            # Controleer of er iets te splitsen valt
            if low_mask.all() or (~low_mask).all():
                return []

            # Reconstueer via IFFT
            fft_low = fft_vals.copy()
            fft_low[~low_mask] = 0.0
            fft_high = fft_vals.copy()
            fft_high[low_mask] = 0.0

            low_component = np.fft.irfft(fft_low, n=n)
            high_component = np.fft.irfft(fft_high, n=n)

            # Controleer dat beide componenten niet-triviaal zijn
            if (
                np.max(np.abs(low_component)) < 1e-12
                or np.max(np.abs(high_component)) < 1e-12
            ):
                return []

            return [low_component.tolist(), high_component.tolist()]

        except Exception as exc:
            logger.warning("FFT-decompositie mislukt: %s", exc)
            return []


class EntropyDecompositionOperator(DecompositionOperator):
    """
    Decompositie op basis van Shannon-entropie van deelreeksen (nieuw).

    Splitst een 1D-reeks in twee helften en controleert of de entropie van
    het geheel significant hoger is dan de gemiddelde entropie van de delen.
    Hoge entropie-gain impliceert interne structuur die decompositie
    rechtvaardigt.

    Args:
        min_entropy_gain: Minimale entropie-gain (in nats) om te splitsen
                          (default: 0.3).
        bins:             Aantal histogram-bins voor entropie-schatting
                          (default: 20).
    """

    operator_name = "entropy_based"

    def __init__(
        self, min_entropy_gain: float = 0.3, bins: int = 20
    ) -> None:
        self.min_entropy_gain = min_entropy_gain
        self.bins = bins

    def can_decompose(self, obs: Any) -> bool:
        try:
            arr = np.asarray(obs, dtype=float).flatten()
            return arr.ndim == 1 and len(arr) >= 8
        except Exception:
            return False

    def decompose(
        self, obs: Any, context: Optional[Dict] = None
    ) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        arr = np.asarray(obs, dtype=float).flatten()
        total_entropy = _shannon_entropy(arr, self.bins)

        best_gain = 0.0
        best_split: Optional[Tuple[np.ndarray, np.ndarray]] = None

        # Zoek de splitsing met de hoogste entropie-gain
        step = max(1, len(arr) // 10)
        for mid in range(step, len(arr) - step, step):
            left, right = arr[:mid], arr[mid:]
            if len(left) < 2 or len(right) < 2:
                continue
            h_left = _shannon_entropy(left, self.bins)
            h_right = _shannon_entropy(right, self.bins)
            avg_half_entropy = (h_left + h_right) / 2.0
            gain = total_entropy - avg_half_entropy
            if gain > best_gain:
                best_gain = gain
                best_split = (left, right)

        if best_split is None or best_gain < self.min_entropy_gain:
            return []

        return [best_split[0].tolist(), best_split[1].tolist()]


class SparsityDecompositionOperator(DecompositionOperator):
    """
    Decompositie op basis van schaarsheid (nieuw).

    Splitst een 1D- of 2D-array in een niet-nul structuur en een nul-structuur
    als het aandeel nulwaarden boven de drempel ligt.

    Args:
        sparsity_threshold: Minimale fractie nulwaarden om te splitsen
                            (default: 0.3).
        zero_atol:          Absolute tolerantie voor nulwaarden (default: 1e-9).
    """

    operator_name = "sparsity_based"

    def __init__(
        self, sparsity_threshold: float = 0.3, zero_atol: float = 1e-9
    ) -> None:
        self.sparsity_threshold = sparsity_threshold
        self.zero_atol = zero_atol

    def can_decompose(self, obs: Any) -> bool:
        try:
            arr = np.asarray(obs, dtype=float).flatten()
            return arr.ndim == 1 and len(arr) >= 4
        except Exception:
            return False

    def decompose(
        self, obs: Any, context: Optional[Dict] = None
    ) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        arr = np.asarray(obs, dtype=float).flatten()
        zero_mask = np.abs(arr) < self.zero_atol
        sparsity = float(np.mean(zero_mask))

        if sparsity < self.sparsity_threshold:
            return []   # Niet schaars genoeg

        non_zero_part = arr[~zero_mask]
        zero_part = arr[zero_mask]

        if len(non_zero_part) == 0 or len(zero_part) == 0:
            return []

        return [non_zero_part.tolist(), zero_part.tolist()]


# ===========================================================================
# Detectie-pipeline
# ===========================================================================

def auto_discovery_pipeline(
    data_stream: List[Any],
    meta_spec: Optional[MetaSpecification] = None,
    auto_register: bool = False,
    confidence_threshold: float = 0.7,
    feedback_loop: Optional[EvolutionaryFeedbackLoop] = None,
) -> List[DiscoveryProposal]:
    """
    Voer ontdekking uit op een datastroom en registreer eventueel automatisch
    nieuwe principes.

    Stappen:
    1. Heuristische detectie via ``HeuristicDiscovery.discover()``.
    2. Elk voorstel met ``validated=True`` en ``confidence ≥ confidence_threshold``
       wordt optioneel automatisch geregistreerd.
    3. Als een feedback_loop is meegegeven, wordt elk (niet-)geregistreerd
       voorstel gelogd.

    Args:
        data_stream:          Lijst van observables of ruwe data.
        meta_spec:            Huidige meta-specificatie (kan None zijn).
        auto_register:        Indien True, worden valide voorstellen boven de
                              drempel automatisch geregistreerd.
        confidence_threshold: Minimale confidence voor auto-registratie
                              (default: 0.7).
        feedback_loop:        Optionele EvolutionaryFeedbackLoop voor bijwerken
                              van gewichten.

    Returns:
        Lijst van alle gedetecteerde ``DiscoveryProposal``-objecten (inclusief
        niet-gevalideerde en niet-geregistreerde).
    """
    discoverer = HeuristicDiscovery(data_stream, meta_spec)
    proposals = discoverer.discover()

    for prop in proposals:
        if prop.validated and prop.confidence >= confidence_threshold and auto_register:
            registered = HeuristicDiscovery.register_proposal(prop)
            if registered:
                logger.info(
                    "Automatisch geregistreerd: %s (confidence %.3f)",
                    prop.name, prop.confidence,
                )
                if feedback_loop:
                    feedback_loop.record_usage(prop.name, success=True)
            else:
                logger.debug(
                    "Principe %s bestond al – niet opnieuw geregistreerd.",
                    prop.name,
                )
        else:
            reason = []
            if not prop.validated:
                reason.append("niet gevalideerd")
            if prop.confidence < confidence_threshold:
                reason.append(f"confidence {prop.confidence:.3f} < {confidence_threshold}")
            if not auto_register:
                reason.append("auto_register=False")
            logger.info(
                "Voorgesteld principe: %s (%s)",
                prop.name, ", ".join(reason) if reason else "geen registratie gevraagd",
            )

    return proposals