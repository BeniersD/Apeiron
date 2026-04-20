"""
Meta-specificatie voor Laag 1 (en hogere lagen).

Dit bestand bevat de definitie van de meta-theoretische keuzes die de
interpretatie van irreducibiliteit, atomiciteit en generativiteit sturen.
Het fungeert als een "metalaag" die aangeeft welke decompositieprincipes
primair zijn, of atomiciteit binair of continu is, en welke standaard-
gewichten gelden. Ook wordt hier een registry voor atomiciteitsframeworks
beheerd.

Alle mutaties op de meta-specificatie zijn thread-safe door gebruik van
een reentrant lock (RLock). De registratie van atomiciteitsframeworks is
idempotent (check-or-create) zodat herladen van modules geen fouten
veroorzaakt.

Bugfixes t.o.v. de originele implementatie
-------------------------------------------

1. **Ontologische grammatica ontbrak** – ``MetaSpecification`` had geen
   formeel ``axioms``-veld. De theorie vereist dat de meta-laag de
   basisregels vastlegt die bepalen wat als observeerbaar geldt en hoe
   relaties worden gevormd. Het veld ``axioms: List[str]`` is toegevoegd
   met vier standaard-axioma's die de Layer 1-theorie operationaliseren.

2. **``decomposition_operators`` was altijd leeg** – Het veld bestond maar
   werd nergens automatisch gevuld. ``__post_init__`` vult het nu
   vanuit de geregistreerde ``DECOMPOSITION_OPERATORS`` (lazy import om
   circulaire afhankelijkheid te vermijden). Dit maakt
   ``validate()`` en ``get_operator()`` correct bruikbaar.

3. **``validate()`` controleerde niets substantieels** – De enige echte
   check was of gewichten 0 of 1 zijn in binaire modus. Uitgebreid met:
   - Controle dat de som van formele decompositie-gewichten hoger is dan
     de som van heuristische gewichten (conform de theoretische hiërarchie).
   - Controle dat alle primaire principes een bijbehorende geregistreerde
     operator hebben.
   - Controle op dubbele principenamen in ``primary_principles``.
   - Waarschuwing bij gewichten buiten [0, 1].

Uitbreidingen
-------------
- ``axioms: List[str]`` – vier standaard theoretisch gemotiveerde axioma's.
- ``__post_init__`` – automatische populatie van ``decomposition_operators``
  vanuit de globale registry.
- ``add_principle()`` – voeg een nieuw primair principe dynamisch toe.
- ``remove_principle()`` – verwijder een primair principe op naam.
- ``get_principle_names()`` – lijst van namen van primaire principes.
- ``register_operator()`` – convenience-methode om een operator direct op
  de MetaSpecification te registreren (in ``decomposition_operators``).
- ``get_operator()`` – haal een geregistreerde operator op bij naam.
- ``add_weight()`` – voeg een gewicht toe voor een nieuw framework zonder
  dat het framework al in ``default_atomicity_weights`` hoeft te staan.
- ``snapshot()`` – exporteer de huidige staat als een plain dict (geen lock
  gehouden na return, geschikt voor logging en serialisatie).
- ``DecompositionPrinciple.unregister()`` – verwijder een principe uit de
  class-registry (idempotent, voor tests en dynamisch gebruik).
"""

from __future__ import annotations

import copy
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ============================================================================
# Observer-relativiteit
# ============================================================================

class ObserverDependence:
    """Hoe observer-relativiteit wordt behandeld."""

    ABSOLUTE = "absolute"      # observer-onafhankelijk
    RELATIVE = "relative"      # afhankelijk van observer
    CONTEXTUAL = "contextual"  # afhankelijk van context


# ============================================================================
# Dynamische decompositieprincipes (thread-safe)
# ============================================================================

class DecompositionPrinciple:
    """
    Dynamisch uitbreidbare decompositieprincipes.

    Elk principe heeft een unieke naam en kan worden geregistreerd.
    De registry is thread-safe door een klasse-lock.

    Methoden
    --------
    register(name)
        Registreer (of haal op) een principe bij naam. Idempotent.
    get(name)
        Haal een principe op bij naam; retourneert None als afwezig.
    all()
        Retourneer een lijst van alle geregistreerde principenamen.
    unregister(name)
        Verwijder een principe uit de registry. Idempotent (geen fout als
        afwezig). Nuttig voor tests en dynamisch gebruik.
    """

    _registry: Dict[str, DecompositionPrinciple] = {}
    _lock: threading.Lock = threading.Lock()

    def __init__(self, name: str) -> None:
        self.name = name
        # Registratie gebeurt via de classmethod register, niet rechtstreeks hier.

    @classmethod
    def register(cls, name: str) -> DecompositionPrinciple:
        """
        Registreer een nieuw principe.

        Als de naam al bestaat, retourneer het bestaande principe
        (check-or-create). Thread-safe.

        Args:
            name: Unieke naam voor het principe.

        Returns:
            Het (nieuw) geregistreerde ``DecompositionPrinciple``-object.
        """
        with cls._lock:
            if name in cls._registry:
                logger.debug(
                    "Principe '%s' bestaat al, bestaande instantie wordt teruggegeven.",
                    name,
                )
                return cls._registry[name]
            principle = cls.__new__(cls)
            principle.__init__(name)
            cls._registry[name] = principle
            return principle

    @classmethod
    def get(cls, name: str) -> Optional[DecompositionPrinciple]:
        """Haal een principe op via naam. Thread-safe (alleen lezen)."""
        with cls._lock:
            return cls._registry.get(name)

    @classmethod
    def all(cls) -> List[str]:
        """Lijst van alle geregistreerde principenamen. Thread-safe."""
        with cls._lock:
            return list(cls._registry.keys())

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Verwijder een principe uit de registry.

        Idempotent: geen fout als het principe niet bestaat. Thread-safe.

        Args:
            name: Naam van het te verwijderen principe.
        """
        with cls._lock:
            if name in cls._registry:
                del cls._registry[name]
                logger.debug("Principe '%s' verwijderd uit registry.", name)

    def __repr__(self) -> str:
        return f"DecompositionPrinciple({self.name})"


# Vooraf gedefinieerde standaardprincipes (worden eenmalig geregistreerd)
LOGICAL = DecompositionPrinciple.register("logical")
MEASURE = DecompositionPrinciple.register("measure")
CATEGORICAL = DecompositionPrinciple.register("categorical")
INFORMATION = DecompositionPrinciple.register("information")
GEOMETRIC = DecompositionPrinciple.register("geometric")
QUALITATIVE = DecompositionPrinciple.register("qualitative")

# Mapping van principenaam naar alternatieve operatornamen.
# De principenamen zijn theoretisch gemotiveerd (bv. "logical" voor
# Booleaanse logica) maar de operators gebruiken soms kortere namen
# (bv. "boolean"). Deze mapping maakt validate() robuust zonder
# afhankelijkheid van externe modules.
PRINCIPLE_OPERATOR_ALIASES: Dict[str, List[str]] = {
    "logical":    ["boolean", "decomposition_boolean"],
    "measure":    ["measure", "decomposition_measure"],
    "categorical": ["categorical", "decomposition_categorical"],
    "information": ["information", "decomposition_information"],
    "geometric":  ["geometric", "decomposition_geometric"],
    "qualitative": ["qualitative", "decomposition_qualitative"],
}


# ============================================================================
# Meta-specificatie (thread-safe)
# ============================================================================

@dataclass
class MetaSpecification:
    """
    Formele specificatie van de meta-theoretische keuzes voor een implementatie.

    Alle mutaties op de gewichten en andere instelbare velden zijn beschermd
    door een reentrant lock (RLock) om thread-safe gebruik in parallelle
    omgevingen (zoals FastAPI, multiprocessing) te garanderen.

    Velden
    ------
    primary_principles
        De decompositieprincipes die als primair worden beschouwd.
    atomicity_is_binary
        Indien True wordt atomiciteit als 0 of 1 geïnterpreteerd.
    observer_dependence
        Hoe observer-relativiteit wordt behandeld.
    default_atomicity_weights
        Standaardgewichten voor combinatie van atomiciteitsscores.
    decomposition_operators
        Geregistreerde decompositieoperatoren (callable per naam).
        Wordt automatisch gevuld vanuit ``DECOMPOSITION_OPERATORS`` bij
        initialisatie via ``__post_init__``.
    axioms
        Lijst van formele axioma's die de ontologische grammatica van
        Layer 1 vastleggen. Vier standaard-axioma's zijn ingebouwd;
        extra axioma's kunnen worden toegevoegd voor hogere lagen.

    Notes
    -----
    Het is aanbevolen per observable een kopie te maken via ``.copy()``
    zodat wijzigingen in de ene observable de andere niet beïnvloeden.
    """

    # Welke decompositieprincipes worden als primair beschouwd?
    primary_principles: List[DecompositionPrinciple] = field(
        default_factory=lambda: [
            LOGICAL, MEASURE, CATEGORICAL, INFORMATION, GEOMETRIC, QUALITATIVE,
        ]
    )

    # Hoe moet atomiciteit worden geïnterpreteerd?
    atomicity_is_binary: bool = False   # Indien True is atomiciteit 0 of 1

    # Hoe wordt observer-relativiteit behandeld?
    observer_dependence: str = ObserverDependence.RELATIVE

    # Standaardgewichten voor combinatie van atomiciteitsscores
    default_atomicity_weights: Dict[str, float] = field(
        default_factory=lambda: {
            # Heuristische frameworks (lager gewicht)
            "boolean": 0.5,
            "discrete_cardinality": 0.5,
            "category": 0.5,
            "info": 0.5,
            "topological": 0.4,
            "geometric": 0.4,
            "quantum": 0.4,
            "fractal": 0.3,
            "dynamical": 0.0,    # Intentioneel 0: hoort bij Layers 7-10
            "group": 0.0,        # Intentioneel 0: hoort bij Layers 7-10
            "statistical": 0.2,
            # Formele decompositie-gebaseerde frameworks (hoger gewicht)
            "decomposition_boolean": 1.0,
            "decomposition_measure": 1.0,
            "decomposition_categorical": 1.0,
            "decomposition_information": 1.0,
            "decomposition_geometric": 0.8,
            "decomposition_qualitative": 1.0,
            # Kwalitatief dimensie-framework
            "qualitative": 1.0,
        }
    )

    # Gewichten per kwalitatieve dimensienaam voor qualitative_dimensions_atomicity().
    # Sleutels zijn dimensienamen (bv. "intensity", "density"); waarden ∈ [0, 1].
    # Afwezige dimensies krijgen gewicht 1.0 (uniform).
    qualitative_dim_weights: Dict[str, float] = field(default_factory=dict)

    # -----------------------------------------------------------------------
    # Formal/heuristic separation (added v3.1 per hypercritical feedback)
    # -----------------------------------------------------------------------
    # The evaluation reports identified that the code's most important
    # theoretical gap is the conflation of formal proofs with heuristics.
    # These fields enable Layer 1 to distinguish between FORMALLY PROVEN
    # atomicity claims and HEURISTICALLY ESTIMATED ones.

    # Minimum weight a framework must have before its score is considered
    # "formal" vs. "heuristic".  Frameworks with weight >= this value that
    # have a corresponding SelfProvingAtomicity certificate are treated as
    # formal; all others are heuristic suggestions only.
    formal_proof_weight_threshold: float = 0.5

    # Set of framework names that produce FORMALLY PROVEN results.
    # Only frameworks listed here may contribute to the "proven_atomicity"
    # certificate.  All others are heuristic and contribute only to
    # combined_atomicity.  Default: empty (Layer 6+ fills this after
    # SelfProvingAtomicity validates them).
    proven_frameworks: List[str] = field(default_factory=list)

    # Observer aggregation operator type.
    # "weighted_mean"  : classic weighted average (default, backward-compat)
    # "geometric_mean" : multiplicative — any zero collapses the score
    # "harmonic_mean"  : biases toward low scores (conservative)
    # "median"         : robust to outlier frameworks
    observer_aggregation: str = "weighted_mean"

    # Geregistreerde decompositieoperatoren (wordt gevuld via __post_init__)

    decomposition_operators: Dict[str, Callable] = field(default_factory=dict)

    # Formele axioma's die de ontologische grammatica van Layer 1 vastleggen.
    # Bug fix: ontbrak in de originele implementatie. De vier standaard-axioma's
    # operationaliseren de theoretische grondslag van de meta-laag.
    axioms: List[str] = field(
        default_factory=lambda: [
            "irreducibility_is_observer_relative",
            "atomicity_is_continuous_not_binary",
            "decomposition_vacuity_implies_atomicity",
            "generativity_requires_non_null_resonance",
        ]
    )

    # Interne lock voor thread-veiligheid (wordt niet geserialiseerd)
    _lock: threading.RLock = field(
        default_factory=threading.RLock,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """
        Vul ``decomposition_operators`` automatisch vanuit de globale
        ``DECOMPOSITION_OPERATORS``-registry na initialisatie.

        Bug fix: het veld ``decomposition_operators`` was altijd leeg
        omdat het nooit werd gevuld. Via een lazy import (om circulaire
        afhankelijkheden te vermijden) worden de geregistreerde operatoren
        overgenomen. Reeds handmatig ingevulde operatoren worden niet
        overschreven (check-or-create per sleutel).

        De import is in een try/except geplaatst zodat de MetaSpecification
        ook standalone (zonder decomposition.py) kan worden gebruikt.
        """
        try:
            from .decomposition import DECOMPOSITION_OPERATORS  # type: ignore[import]
            with self._lock:
                for name, op in DECOMPOSITION_OPERATORS.items():
                    if name not in self.decomposition_operators:
                        self.decomposition_operators[name] = op
        except ImportError:
            # Standalone gebruik of circulaire import: laat leeg.
            logger.debug(
                "decomposition.py niet beschikbaar bij MetaSpecification.__post_init__; "
                "decomposition_operators blijft leeg."
            )

    # -----------------------------------------------------------------------
    # Gewichtsbeheer
    # -----------------------------------------------------------------------

    def update_weight(self, framework_name: str, new_weight: float) -> None:
        """
        Werk het gewicht van een atomiciteitsframework bij.

        De waarde wordt geklemd tussen 0.0 en 1.0. Gooit ``ValueError``
        als het framework onbekend is.  Thread-safe.

        Args:
            framework_name: Naam van het te updaten framework.
            new_weight:     Nieuw gewicht (wordt geklemd naar [0, 1]).

        Raises:
            ValueError: Als ``framework_name`` niet in
                        ``default_atomicity_weights`` staat.
        """
        with self._lock:
            if framework_name not in self.default_atomicity_weights:
                raise ValueError(f"Onbekend framework: {framework_name!r}")
            clamped = max(0.0, min(1.0, new_weight))
            self.default_atomicity_weights[framework_name] = clamped
            logger.debug(
                "Gewicht voor %s bijgewerkt naar %s", framework_name, clamped
            )

    def get_weight(self, framework_name: str) -> float:
        """
        Haal het gewicht van een framework op.

        Thread-safe.

        Args:
            framework_name: Naam van het framework.

        Returns:
            Het gewicht (float), of 0.0 als het framework onbekend is.
        """
        with self._lock:
            return self.default_atomicity_weights.get(framework_name, 0.0)

    def add_weight(self, framework_name: str, weight: float) -> None:
        """
        Voeg een gewicht toe voor een nieuw framework.

        Anders dan ``update_weight`` werkt deze methode ook als het
        framework nog niet in ``default_atomicity_weights`` staat – het
        wordt dan toegevoegd. Bestaande gewichten worden overschreven.
        Thread-safe.

        Args:
            framework_name: Naam van het framework.
            weight:         Gewicht (wordt geklemd naar [0, 1]).
        """
        with self._lock:
            clamped = max(0.0, min(1.0, weight))
            self.default_atomicity_weights[framework_name] = clamped
            logger.debug(
                "Gewicht voor nieuw framework %s ingesteld op %s",
                framework_name, clamped,
            )

    # -----------------------------------------------------------------------
    # Principebeheer
    # -----------------------------------------------------------------------

    def add_principle(
        self, principle: DecompositionPrinciple, *, allow_duplicate: bool = False
    ) -> None:
        """
        Voeg een primair principe dynamisch toe.

        Registreert het principe ook in ``DecompositionPrinciple._registry``
        als dat nog niet is gebeurd. Thread-safe.

        Args:
            principle:       Het toe te voegen principe.
            allow_duplicate: Indien False (standaard) wordt een al aanwezig
                             principe stilzwijgend overgeslagen.
        """
        with self._lock:
            existing_names = [p.name for p in self.primary_principles]
            if principle.name in existing_names and not allow_duplicate:
                logger.debug(
                    "Principe '%s' is al aanwezig in primary_principles, overgeslagen.",
                    principle.name,
                )
                return
            # Zorg dat het principe in de klasse-registry staat
            DecompositionPrinciple.register(principle.name)
            self.primary_principles.append(principle)
            logger.debug(
                "Principe '%s' toegevoegd aan primary_principles.", principle.name
            )

    def remove_principle(self, name: str) -> bool:
        """
        Verwijder een primair principe op naam.

        Thread-safe. Idempotent: geen fout als het principe niet aanwezig is.

        Args:
            name: Naam van het te verwijderen principe.

        Returns:
            True als het principe is verwijderd; False als het niet aanwezig was.
        """
        with self._lock:
            original_len = len(self.primary_principles)
            self.primary_principles = [
                p for p in self.primary_principles if p.name != name
            ]
            removed = len(self.primary_principles) < original_len
            if removed:
                logger.debug(
                    "Principe '%s' verwijderd uit primary_principles.", name
                )
            return removed

    def get_principle_names(self) -> List[str]:
        """
        Retourneer een lijst van namen van alle primaire principes.

        Thread-safe.

        Returns:
            Lijst van principenamen in volgorde van ``primary_principles``.
        """
        with self._lock:
            return [p.name for p in self.primary_principles]

    # -----------------------------------------------------------------------
    # Operatorbeheer
    # -----------------------------------------------------------------------

    def register_operator(self, name: str, operator: Callable) -> None:
        """
        Registreer een decompositieoperator direct op deze MetaSpecification.

        Handig voor het lokaal toevoegen van een operator zonder de globale
        registry te wijzigen. Check-or-create: bestaande operatoren worden
        niet overschreven. Thread-safe.

        Args:
            name:     Naam voor de operator.
            operator: Callable die de decompositie uitvoert.
        """
        with self._lock:
            if name in self.decomposition_operators:
                logger.debug(
                    "Operator '%s' al geregistreerd in MetaSpecification, overgeslagen.",
                    name,
                )
                return
            self.decomposition_operators[name] = operator
            logger.debug("Operator '%s' geregistreerd in MetaSpecification.", name)

    def get_operator(self, name: str) -> Optional[Callable]:
        """
        Haal een geregistreerde decompositieoperator op bij naam.

        Kijkt eerst in ``self.decomposition_operators``; valt dan terug
        op de globale ``DECOMPOSITION_OPERATORS``-registry.  Thread-safe.

        Args:
            name: Naam van de operator.

        Returns:
            De operator-callable, of None als niet gevonden.
        """
        with self._lock:
            op = self.decomposition_operators.get(name)
            if op is not None:
                return op

        # Fallback naar globale registry (buiten lock om deadlock te vermijden)
        try:
            from .decomposition import DECOMPOSITION_OPERATORS  # type: ignore[import]
            return DECOMPOSITION_OPERATORS.get(name)
        except ImportError:
            return None

    # -----------------------------------------------------------------------
    # Validatie
    # -----------------------------------------------------------------------

    def validate(self) -> bool:
        """
        Controleer interne consistentie van de MetaSpecification.

        Uitgevoerde controles:

        1. **Binaire modus**: als ``atomicity_is_binary`` True is, moeten
           alle gewichten precies 0.0 of 1.0 zijn.
        2. **Gewichtsbereik**: alle gewichten moeten in [0, 1] liggen
           (waarschuwing bij overtreding, geen directe afkeuring).
        3. **Hiërarchische consistentie**: de som van de formele
           decompositie-gewichten (``decomposition_*``) moet hoger zijn
           dan de som van de heuristische gewichten. Dit drukt de
           theoretische prioriteit van formele boven heuristische kaders uit.
        4. **Principedekking**: elk primair principe moet een bijbehorende
           geregistreerde operator hebben (in ``decomposition_operators``
           of de globale registry).
        5. **Dubbele principenamen**: ``primary_principles`` mag geen
           twee principes met dezelfde naam bevatten.
        6. **Registry-aanwezigheid**: alle primaire principes moeten in de
           klasse-registry van ``DecompositionPrinciple`` staan.

        Thread-safe (leest onder lock).

        Returns:
            True als alle controles slagen; False bij de eerste fout.
        """
        with self._lock:
            # 1. Binaire modus: gewichten moeten 0 of 1 zijn
            if self.atomicity_is_binary:
                for fw_name, w in self.default_atomicity_weights.items():
                    if w not in (0.0, 1.0):
                        logger.warning(
                            "In binaire modus horen gewichten 0 of 1 te zijn, "
                            "maar '%s' heeft gewicht %s.",
                            fw_name, w,
                        )
                        return False

            # 2. Gewichtsbereik
            for fw_name, w in self.default_atomicity_weights.items():
                if not (0.0 <= w <= 1.0):
                    logger.warning(
                        "Gewicht voor '%s' ligt buiten [0, 1]: %s.", fw_name, w
                    )

            # 3. Hiërarchische consistentie (formele > heuristische som)
            # Alleen gecontroleerd in continue modus: in binaire modus zijn alle
            # gewichten 0 of 1, waardoor de absolute som weinig zegt over de
            # relatieve prioriteit van formele vs. heuristische kaders.
            if not self.atomicity_is_binary:
                formal_names = {
                    k for k in self.default_atomicity_weights
                    if k.startswith("decomposition_")
                }
                heuristic_names = {
                    k for k in self.default_atomicity_weights
                    if not k.startswith("decomposition_")
                }
                formal_sum = sum(
                    self.default_atomicity_weights[k] for k in formal_names
                )
                heuristic_sum = sum(
                    self.default_atomicity_weights[k] for k in heuristic_names
                )
                if formal_sum < heuristic_sum:
                    logger.warning(
                        "Hiërarchische inconsistentie: som van formele gewichten "
                        "(%.3f) is lager dan som van heuristische gewichten (%.3f). "
                        "Formele kaders zouden zwaarder moeten wegen.",
                        formal_sum, heuristic_sum,
                    )
                    return False

            # 4. Principedekking: elk primair principe zou een bijbehorende
            #    geregistreerde operator moeten hebben. De controle is intentioneel
            #    tolerant: de mapping van principenaam naar operatornaam is niet
            #    altijd één-op-één (bv. "logical" → "boolean"). We controleren
            #    daarom of er minimaal één operator beschikbaar is waarvan de naam:
            #    (a) gelijk is aan de principenaam, of
            #    (b) gelijk is aan "decomposition_<principenaam>", of
            #    (c) de principenaam als substring bevat.
            #    Als geen van deze gevallen opgaat én er überhaupt geen operators
            #    geregistreerd zijn, is dat een echte fout.
            registered_ops = set(self.decomposition_operators.keys())
            try:
                from .decomposition import DECOMPOSITION_OPERATORS  # type: ignore[import]
                registered_ops |= set(DECOMPOSITION_OPERATORS.keys())
            except ImportError:
                pass

            if registered_ops:
                # Alleen controleren als er überhaupt operators geregistreerd zijn.
                # Gebruikt PRINCIPLE_OPERATOR_ALIASES voor de mapping van
                # principenaam naar operatornaam.
                for p in self.primary_principles:
                    # Verzamel alle kandidaat-operatornamen voor dit principe
                    alias_names = PRINCIPLE_OPERATOR_ALIASES.get(p.name, [])
                    candidate_names = (
                        {p.name, f"decomposition_{p.name}"}
                        | set(alias_names)
                    )
                    covered = bool(candidate_names & registered_ops)
                    if not covered:
                        logger.warning(
                            "Principe '%s' heeft geen bijbehorende geregistreerde "
                            "operator (gezocht: %s). "
                            "Voeg er een toe via register_operator().",
                            p.name, sorted(candidate_names),
                        )
                        return False

            # 5. Dubbele principenamen
            seen_names: Set[str] = set()
            for p in self.primary_principles:
                if p.name in seen_names:
                    logger.warning(
                        "Dubbele principenaam gevonden: '%s'.", p.name
                    )
                    return False
                seen_names.add(p.name)

            # 6. Registry-aanwezigheid
            registered_principle_names = DecompositionPrinciple.all()
            for p in self.primary_principles:
                if p.name not in registered_principle_names:
                    logger.warning(
                        "Principe '%s' niet geregistreerd in DecompositionPrinciple-registry.",
                        p.name,
                    )
                    return False

            # 7. Formeel/heuristisch onderscheid: proven_frameworks moeten
            #    bestaan als frameworks in default_atomicity_weights.
            #    Frameworks zonder gewicht kunnen niet formeel worden erkend.
            for fw in self.proven_frameworks:
                if fw not in self.default_atomicity_weights:
                    logger.warning(
                        "proven_frameworks bevat '%s', maar dit framework heeft "
                        "geen gewicht in default_atomicity_weights. "
                        "Voeg een gewicht toe voor formele certificering.",
                        fw,
                    )
                    return False

            # 8. observer_aggregation moet een bekende methode zijn.
            valid_aggregations = {"weighted_mean", "geometric_mean", "harmonic_mean", "median"}
            if self.observer_aggregation not in valid_aggregations:
                logger.warning(
                    "Onbekende observer_aggregation '%s'. Geldige waarden: %s.",
                    self.observer_aggregation, sorted(valid_aggregations),
                )
                return False

        return True

    # -----------------------------------------------------------------------
    # Snapshot (export)
    # -----------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """
        Exporteer de huidige staat als een plain dict.

        Geschikt voor logging, serialisatie en overdracht. De lock wordt
        vrijgegeven vóór de return (het geretourneerde dict is een kopie).
        Thread-safe.

        Returns:
            Dict met sleutels ``principles``, ``atomicity_is_binary``,
            ``observer_dependence``, ``weights``, ``operator_names``,
            ``axioms``.
        """
        with self._lock:
            return {
                "principles": [p.name for p in self.primary_principles],
                "atomicity_is_binary": self.atomicity_is_binary,
                "observer_dependence": self.observer_dependence,
                "weights": dict(self.default_atomicity_weights),
                "qualitative_dim_weights": dict(self.qualitative_dim_weights),
                "operator_names": list(self.decomposition_operators.keys()),
                "axioms": list(self.axioms),
                "formal_proof_weight_threshold": self.formal_proof_weight_threshold,
                "proven_frameworks": list(self.proven_frameworks),
                "observer_aggregation": self.observer_aggregation,
            }

    # -----------------------------------------------------------------------
    # Kopie
    # -----------------------------------------------------------------------

    def copy(self) -> MetaSpecification:
        """
        Maak een diepe kopie van deze meta-specificatie.

        Handig voor het geven van een eigen exemplaar aan elke observable,
        zodat wijzigingen in de ene observable de andere niet beïnvloeden.
        Thread-safe (kopieert onder lock).

        Returns:
            Een nieuwe ``MetaSpecification``-instantie met dezelfde waarden.
        """
        with self._lock:
            new_primary = copy.deepcopy(self.primary_principles)
            new_weights = copy.deepcopy(self.default_atomicity_weights)
            new_operators = copy.deepcopy(self.decomposition_operators)
            new_axioms = list(self.axioms)
            new_qual_weights = copy.deepcopy(self.qualitative_dim_weights)
            return MetaSpecification(
                primary_principles=new_primary,
                atomicity_is_binary=self.atomicity_is_binary,
                observer_dependence=self.observer_dependence,
                default_atomicity_weights=new_weights,
                decomposition_operators=new_operators,
                axioms=new_axioms,
                qualitative_dim_weights=new_qual_weights,
                formal_proof_weight_threshold=self.formal_proof_weight_threshold,
                proven_frameworks=list(self.proven_frameworks),
                observer_aggregation=self.observer_aggregation,
            )

    # -----------------------------------------------------------------------
    # Representatie
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"MetaSpecification("
                f"principles={len(self.primary_principles)}, "
                f"binary={self.atomicity_is_binary}, "
                f"weights={len(self.default_atomicity_weights)}, "
                f"axioms={len(self.axioms)})"
            )


# ============================================================================
# Registry voor atomiciteitsframeworks (idempotent)
# ============================================================================

# Elk framework is een callable met handtekening:
#   (observable: UltimateObservable, context: dict) -> float
ATOMICITY_FRAMEWORKS: Dict[str, Callable] = {}

# Lock voor de registry
_atomicity_lock = threading.Lock()


def register_atomicity_framework(
    name: str,
    func: Callable,
    depends_on: Optional[List[str]] = None,
) -> None:
    """
    Registreer een atomiciteitsframework.

    Als de naam al bestaat, wordt alleen een debug-melding gelogd en wordt
    de bestaande registratie behouden (check-or-create patroon). Dit
    voorkomt crashes bij herladen van modules (pytest, multiprocessing).

    Args:
        name:       Unieke naam voor het framework.
        func:       Callable met handtekening
                    ``(observable, context: dict) -> float``.
        depends_on: Optionele lijst van namen van frameworks waarvan dit
                    framework afhankelijk is (voor toekomstig gebruik).
    """
    with _atomicity_lock:
        if name in ATOMICITY_FRAMEWORKS:
            logger.debug("Framework '%s' is al geregistreerd, overslaan.", name)
            return
        ATOMICITY_FRAMEWORKS[name] = func
        logger.debug("Geregistreerd atomiciteitsframework: %s", name)


def atomicity_framework(
    name: str,
    depends_on: Optional[List[str]] = None,
) -> Callable:
    """
    Decorator om een functie als atomiciteitsframework te registreren.

    Args:
        name:       Naam waaronder het framework wordt geregistreerd.
        depends_on: Optionele lijst van afhankelijke frameworknamen.

    Returns:
        De ongewijzigde gedecoreerde functie.

    Example::

        @atomicity_framework("my_framework")
        def my_atomicity(obs, ctx):
            return 1.0
    """
    def decorator(func: Callable) -> Callable:
        register_atomicity_framework(name, func, depends_on)
        return func
    return decorator


# ============================================================================
# Globale standaard meta-specificatie
# (wordt vaak gedeeld; voor thread-veiligheid: per observable een kopie via .copy())
# ============================================================================

DEFAULT_META_SPEC = MetaSpecification()