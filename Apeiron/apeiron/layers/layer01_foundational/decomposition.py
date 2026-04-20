"""
decomposition.py - Formele decompositieoperatoren voor Laag 1.

Dit bestand definieert een raamwerk voor het ontbinden van observables in
delen, als basis voor een formele atomiciteitstest. Het biedt een abstracte
basisklasse `DecompositionOperator`, een registry voor concrete operatoren,
en een aantal generieke en domeinspecifieke implementaties.

Elke operator kan worden toegepast op een observable (een willekeurig object)
en retourneert een lijst van delen. Als de operator niet van toepassing is
(bijv. omdat de observable niet voldoet aan de vereiste structuur), wordt
een lege lijst geretourneerd. De atomiciteit van een observable voor een
bepaald kader kan worden afgeleid uit het feit of de operator een niet-triviale
decompositie oplevert.

Theoretische grondslag (Layer 1 proposities):
    - Proposition 1 (Boolean atomicity): element a ∈ B is een atoom als
      a ≠ 0 en er geen b ∈ B bestaat met 0 < b < a. Morfismen van Booleaanse
      algebra's beelden atomen af op atomen of nul.
    - Proposition 2 (Measure atomicity): meetbare set A is een atoom als
      μ(A) > 0 en elke meetbare B ⊆ A voldoet aan μ(B) = 0 of μ(B) = μ(A).
    - Proposition 3 (Categorical atomicity): zero-object is uniek tot op
      isomorfisme en heeft zowel initiale als terminale universele eigenschap.
    - Proposition 4 (Information atomicity): atomaire eenheid minimaliseert
      de afweging beschrijvingslengte vs. discrimineerbaarheid (Kolmogorov).
    - Proposition 5 (Inverse limit): Layer 1 als pro-object: stabiel onder
      verfijning van resolutie naar ε→0.

Operatoren zijn onderverdeeld in twee categorieën:
    FORMELE OPERATOREN  – direct theoretisch gemotiveerd (boolean, measure,
                          categorical, information, geometric, qualitative,
                          inverse_limit, palindrome/symmetry).
    UTILITY OPERATOREN  – praktische hulpmiddelen zonder directe theoretische
                          grondslag in Layer 1 (list_split, string_split,
                          dict_split, array_split). Enkel beschikbaar via
                          get_decomposition_operator(), niet als primaire
                          atomiciteitstest.
"""

from __future__ import annotations

import logging
import itertools
import threading
import zlib
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optionele bibliotheken – graceful degradation
# ---------------------------------------------------------------------------

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    KMeans = None  # type: ignore[assignment,misc]
    HAS_SKLEARN = False
    logger.warning("scikit-learn niet beschikbaar – geometrische clustering valt terug op mediaan-splitsing.")

try:
    import scipy.stats as _scipy_stats
    HAS_SCIPY = True
except ImportError:
    _scipy_stats = None  # type: ignore[assignment]
    HAS_SCIPY = False
    logger.warning("scipy niet beschikbaar – statistische maat-normalisatie uitgeschakeld.")


# ===========================================================================
# Basisklasse
# ===========================================================================

class DecompositionOperator(ABC):
    """
    Abstracte basisklasse voor een decompositieoperator.

    Een operator kan op een observable worden toegepast en levert een lijst
    van delen op. De operator kan optioneel een controle uitvoeren of hij
    van toepassing is op de gegeven observable via ``can_decompose``.

    Subklassen moeten ``decompose`` implementeren en kunnen ``can_decompose``
    overschrijven voor efficiënte type-controle.
    """

    # Naam voor logging en introspectie – subklassen kunnen overschrijven.
    operator_name: str = "base"

    @abstractmethod
    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        """
        Ontbind de observable in een lijst van delen.

        Args:
            obs:     De observable (willekeurig object).
            context: Optioneel woordenboek met extra parameters
                     (bijv. drempelwaarden, maatfuncties).

        Returns:
            Lijst van delen. Een lege lijst betekent dat er geen zinvolle
            decompositie mogelijk is (of dat de operator niet van toepassing
            is), wat impliceert dat de observable atomair is ten opzichte van
            dit kader.
        """

    def can_decompose(self, obs: Any) -> bool:
        """
        Controleert of de operator structureel van toepassing is op de observable.

        Standaardimplementatie retourneert True; subklassen kunnen dit
        overschrijven voor een efficiënte type-controle vóór ``decompose``.
        """
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# ===========================================================================
# Registry (thread-safe, check-or-create)
# ===========================================================================

DECOMPOSITION_OPERATORS: Dict[str, DecompositionOperator] = {}
_registry_lock = threading.Lock()


def register_decomposition_operator(name: str, operator: DecompositionOperator) -> None:
    """
    Registreer een decompositieoperator onder een gegeven naam.

    Als de naam al bestaat, wordt alleen een debug-melding gelogd en wordt de
    bestaande operator niet overschreven (check-or-create patroon). Dit
    voorkomt crashes bij herladen van modules (pytest, multiprocessing).

    Args:
        name:     Unieke sleutel voor de operator.
        operator: Instantie van een ``DecompositionOperator`` subklasse.
    """
    with _registry_lock:
        if name in DECOMPOSITION_OPERATORS:
            logger.debug(
                "Operator '%s' is al geregistreerd. Bestaande instantie blijft behouden.", name
            )
            return
        DECOMPOSITION_OPERATORS[name] = operator
        logger.debug("Geregistreerde decompositieoperator: %s", name)


def get_decomposition_operator(name: str) -> Optional[DecompositionOperator]:
    """Haal een geregistreerde operator op. Retourneert None als niet gevonden."""
    return DECOMPOSITION_OPERATORS.get(name)


# ===========================================================================
# UTILITY OPERATOREN
# Praktische hulpmiddelen zonder directe theoretische grondslag in Layer 1.
# Beschikbaar via get_decomposition_operator() maar NIET geregistreerd als
# primaire atomiciteitstest voor de theoretische kaders.
# ===========================================================================

class ListSplitOperator(DecompositionOperator):
    """
    Splitst een lijst of tuple in twee ongeveer gelijke helften.

    Categorie: UTILITY – geen directe theoretische grondslag in Layer 1.
    Gebruik voor pre-processing of algemene structuuranalyse.
    """

    operator_name = "list_split"

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, (list, tuple))

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []
        n = len(obs)
        if n < 2:
            return []
        mid = n // 2
        return [obs[:mid], obs[mid:]]


class StringSplitOperator(DecompositionOperator):
    """
    Splitst een string in twee helften op basis van lengte.

    Categorie: UTILITY – geen directe theoretische grondslag in Layer 1.
    Voor informatietheorie op strings: gebruik InformationDecompositionOperator.
    """

    operator_name = "string_split"

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, str)

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []
        n = len(obs)
        if n < 2:
            return []
        mid = n // 2
        return [obs[:mid], obs[mid:]]


class DictSplitOperator(DecompositionOperator):
    """
    Splitst een dictionary in twee dictionaries met ongeveer de helft van de sleutels.

    Categorie: UTILITY – geen directe theoretische grondslag in Layer 1.
    """

    operator_name = "dict_split"

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, dict)

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []
        keys = list(obs.keys())
        n = len(keys)
        if n < 2:
            return []
        mid = n // 2
        return [{k: obs[k] for k in keys[:mid]}, {k: obs[k] for k in keys[mid:]}]


class ArraySplitOperator(DecompositionOperator):
    """
    Splitst een numpy-array in twee delen langs de eerste as.

    Categorie: UTILITY – geen directe theoretische grondslag in Layer 1.
    Voor geometrische atomiciteit: gebruik GeometricDecompositionOperator.
    """

    operator_name = "array_split"

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, np.ndarray)

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []
        if obs.shape[0] < 2:
            return []
        mid = obs.shape[0] // 2
        return [obs[:mid], obs[mid:]]


# ===========================================================================
# FORMELE OPERATOREN
# Direct gemotiveerd door de theoretische proposities van Layer 1.
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. Boolean atomicity  (Proposition 1)
# ---------------------------------------------------------------------------

class BooleanDecompositionOperator(DecompositionOperator):
    """
    Booleaanse decompositie op basis van Proposition 1.

    Formele definitie: element a ∈ B is een atoom als a ≠ 0 en er geen
    b ∈ B bestaat met 0 < b < a (d.w.z. er bestaat geen niet-triviale
    deelverzameling in de partiële orde).

    Implementatie:
        - ``frozenset`` / ``set``: de partiële orde is set-inclusie (⊆).
          Een atoom is een éénelementige niet-lege verzameling.
          Controleer: bestaat er een b met ∅ ⊂ b ⊂ obs?
        - ``int`` / ``float``: in de standaard orde op N zijn positieve
          gehele getallen atomen (niet verder splitsbaar zonder verlies
          van algebraïsche identiteit).
        - Alle andere typen: worden als atomair beschouwd voor dit kader
          (operatie niet van toepassing).

    Corrects Proposition 1 invariant: een morfisme van Booleaanse algebra's
    beeldt atomen af op atomen of op nul. De test valideert dit door te
    controleren of de kleinst mogelijke niet-triviale deelverzameling
    bestaat.
    """

    operator_name = "boolean"

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, (set, frozenset, int, float, bool))

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        # Getallen: atomen in de standaard partiële orde op N
        # (gehele getallen kunnen niet worden gesplitst zonder verlies
        # van algebraïsche identiteit; booleans zijn triviale atomen)
        if isinstance(obs, (int, float, bool)):
            return []  # atomair

        # Verzamelingen: partiële orde via inclusie
        if isinstance(obs, (set, frozenset)):
            if len(obs) < 2:
                # Lege verzameling = nul-element (niet atomair per definitie)
                # Éénelementige verzameling = atoom
                return []

            # Er bestaat een b met ∅ ⊂ b ⊂ obs: geef de minimale decompositie.
            # Per Proposition 1: geef het eerste element als éénelementig atoom
            # en de rest als complement, zodat de union de originele verzameling
            # reconstrueert en beide delen niet-leeg zijn.
            lst = sorted(obs, key=repr)  # deterministische volgorde
            atom = type(obs)([lst[0]])
            complement = type(obs)(lst[1:])
            return [atom, complement]

        return []

    def is_boolean_atom(self, obs: Any) -> bool:
        """
        Test direct of de observable een Booleaans atoom is.

        Returns:
            True als de observable een atoom is in de Booleaanse algebra
            geïnduceerd door zijn type.
        """
        return len(self.decompose(obs)) == 0 and self.can_decompose(obs)


# ---------------------------------------------------------------------------
# 2. Measure atomicity  (Proposition 2)
# ---------------------------------------------------------------------------

class MeasureDecompositionOperator(DecompositionOperator):
    """
    Maattheoretische decompositie op basis van Proposition 2.

    Formele definitie: een meetbare verzameling A is een atoom voor maat μ als
        μ(A) > 0  en  ∀ meetbare B ⊆ A: μ(B) = 0 of μ(B) = μ(A).

    De maat μ is configureerbaar via ``measure_fn``. Standaard wordt
    cardinaliteit (len) gebruikt als proxy voor discrete ruimten, wat correct
    is voor de uniforme telbare maat op eindige verzamelingen.

    Args:
        measure_fn: Callable (element) -> float die de maat van een element
                    retourneert. Standaard: cardinaliteit via len(), met
                    fallback naar 1.0 voor scalaire typen.
        max_subsets: Maximaal aantal te testen deelverzamelingen bij de
                     exhaustieve atomiciteitstest (default: 64). Hogere
                     waarden zijn nauwkeuriger maar duurder voor grote sets.
    """

    operator_name = "measure"

    def __init__(
        self,
        measure_fn: Optional[Callable[[Any], float]] = None,
        max_subsets: int = 64,
    ) -> None:
        self._measure_fn = measure_fn or self._default_measure
        self.max_subsets = max_subsets

    @staticmethod
    def _default_measure(element: Any) -> float:
        """
        Standaard maatfunctie: cardinaliteit voor collecties, 1.0 voor scalairs.

        Deze keuze implementeert de uniforme telbare maat op eindige
        discrete ruimten. Voor continue ruimten moet een domeinspecifieke
        maatfunctie worden meegegeven.
        """
        if isinstance(element, (set, frozenset, list, tuple)):
            return float(len(element))
        if isinstance(element, dict):
            return float(len(element))
        if isinstance(element, np.ndarray):
            return float(element.size)
        if isinstance(element, (int, float, complex)):
            return abs(float(element)) if isinstance(element, (int, float)) else 1.0
        if isinstance(element, str):
            return float(len(element))
        try:
            return float(len(element))
        except TypeError:
            return 1.0

    @property
    def measure_fn(self) -> Callable[[Any], float]:
        """Publieke toegang tot de maatfunctie (read-only)."""
        return self._measure_fn

    def can_decompose(self, obs: Any) -> bool:
        # Van toepassing op alles waarvoor de maatfunctie een positieve waarde geeft
        try:
            return self._measure_fn(obs) > 0
        except Exception:
            return False

    def is_measure_atom(self, obs: Any) -> bool:
        """
        Test Proposition 2 direct: controleer of elke deelverzameling
        maat 0 of volle maat heeft.

        Dit is de theoretisch correcte atomiciteitstest. ``decompose()``
        retourneert een lege lijst als en slechts als ``is_measure_atom``
        True is.

        Args:
            obs: De te testen observable.

        Returns:
            True als de observable een atoom is voor de ingestelde maat.
        """
        total = self._measure_fn(obs)
        if total <= 0:
            # Maat nul: per definitie geen atoom (nul-element)
            return False

        for sub in self._generate_subsets(obs):
            m = self._measure_fn(sub)
            if 0.0 < m < total:
                return False  # Niet-triviale deelverzameling gevonden → geen atoom
        return True

    def _generate_subsets(self, obs: Any) -> Iterator[Any]:
        """
        Generator die niet-triviale deelverzamelingen produceert.

        Beperkt tot ``self.max_subsets`` om combinatorische explosie te
        voorkomen bij grote collecties.  Voor collecties met meer dan 20
        elementen wordt random sampling gebruikt in plaats van exhaustieve
        iteratie, waardoor de tijdcomplexiteit O(max_subsets) blijft i.p.v.
        O(2^n).  De sampling is reproduceerbaar door de vaste seed per
        observable via het hash van de repr.
        """
        import random as _random

        if isinstance(obs, (set, frozenset)):
            items = list(obs)
        elif isinstance(obs, (list, tuple)):
            items = list(obs)
        elif isinstance(obs, np.ndarray) and obs.ndim == 1:
            items = list(range(obs.shape[0]))  # indices
        elif isinstance(obs, dict):
            items = list(obs.keys())
        else:
            return  # Scalaire typen — geen deelverzamelingen

        n = len(items)
        if n <= 1:
            return  # Geen niet-triviale deelverzamelingen mogelijk

        count = 0

        # Voor kleine collecties: exhaustieve iteratie
        if n <= 20:
            for size in range(1, n):
                for combo in itertools.combinations(range(n), size):
                    if count >= self.max_subsets:
                        return
                    yield self._items_to_subset(obs, items, combo)
                    count += 1

        else:
            # Voor grote collecties: random sampling om O(2^n) te vermijden.
            # Reproduceerbare seed gebaseerd op de hash van de observable.
            rng = _random.Random(hash(repr(obs)) & 0xFFFFFFFF)
            while count < self.max_subsets:
                size = rng.randint(1, n - 1)
                combo = tuple(sorted(rng.sample(range(n), size)))
                yield self._items_to_subset(obs, items, combo)
                count += 1

    @staticmethod
    def _items_to_subset(obs: Any, items: list, combo: tuple) -> Any:
        """Zet een tuple van indices om naar het juiste subset-type."""
        if isinstance(obs, (set, frozenset)):
            return type(obs)(items[i] for i in combo)
        if isinstance(obs, (list, tuple)):
            return type(obs)(items[i] for i in combo)
        if isinstance(obs, np.ndarray):
            return obs[list(combo)]
        if isinstance(obs, dict):
            return {items[i]: obs[items[i]] for i in combo}
        return [items[i] for i in combo]

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        """
        Retourneert een decompositie als en slechts als de observable GEEN
        maat-atoom is (Proposition 2). Gebruikt ``is_measure_atom`` als
        theoretische filter.

        Een decompositie wordt enkel teruggegeven als er een niet-triviale
        deelverzameling van positieve maat kleiner dan de volle maat bestaat.
        """
        if not self.can_decompose(obs):
            return []

        if self.is_measure_atom(obs):
            return []  # Atomair – geen decompositie

        # Geef de eerste niet-triviale decompositie terug
        total = self._measure_fn(obs)
        for sub in self._generate_subsets(obs):
            m = self._measure_fn(sub)
            if 0.0 < m < total:
                # Bouw complement
                complement = self._complement(obs, sub)
                if complement is not None and self._measure_fn(complement) > 0:
                    return [sub, complement]

        # Fallback: eenvoudige halvering (zou niet bereikt moeten worden
        # als is_measure_atom correct werkt)
        return self._fallback_split(obs)

    def _complement(self, whole: Any, part: Any) -> Optional[Any]:
        """Berekent het complement van ``part`` in ``whole``."""
        try:
            if isinstance(whole, (set, frozenset)):
                return type(whole)(x for x in whole if x not in part)
            if isinstance(whole, (list, tuple)):
                part_set = set(id(x) for x in part)
                result = [x for x in whole if id(x) not in part_set]
                # Veilige fallback: gebruik indices
                part_list = list(part)
                result2 = [x for x in whole if x not in part_list]
                return type(whole)(result2) if result2 else None
            if isinstance(whole, dict):
                return {k: v for k, v in whole.items() if k not in part}
            if isinstance(whole, np.ndarray):
                part_set = set(map(tuple, part)) if part.ndim > 1 else set(part.tolist())
                mask = np.array([
                    (tuple(x) if whole.ndim > 1 else x) not in part_set
                    for x in whole
                ])
                return whole[mask]
        except Exception as exc:
            logger.debug("Complement-berekening mislukt: %s", exc)
        return None

    def _fallback_split(self, obs: Any) -> List[Any]:
        """Nooddecompositie via halvering (theoretisch niet gemotiveerd)."""
        if isinstance(obs, (list, tuple)):
            items = list(obs)
            mid = len(items) // 2
            if mid == 0:
                return []
            return [type(obs)(items[:mid]), type(obs)(items[mid:])]
        if isinstance(obs, (set, frozenset)):
            items = sorted(obs, key=repr)
            mid = len(items) // 2
            if mid == 0:
                return []
            return [type(obs)(items[:mid]), type(obs)(items[mid:])]
        if isinstance(obs, np.ndarray) and obs.shape[0] >= 2:
            mid = obs.shape[0] // 2
            return [obs[:mid], obs[mid:]]
        return []


# ---------------------------------------------------------------------------
# 3. Categorical atomicity  (Proposition 3)
# ---------------------------------------------------------------------------

class CategoricalDecompositionOperator(DecompositionOperator):
    """
    Categorietheoretische decompositie op basis van Proposition 3.

    Formele definitie: een object is een zero-object (en dus atomair) als het
    tegelijk initieel en terminaal is. Een object heeft deelobjecten als het
    een niet-triviale factorisatie toelaat via subobjects.

    Implementatie:
        - Primair: gebruikt het ``subobjects``-attribuut als het aanwezig is.
          Dit is de formeel correcte indicator voor een categorie waarbij
          deelobjecten expliciet gedefinieerd zijn.
        - Secundair: als ``is_zero_object`` of ``is_initial``/``is_terminal``
          aanwezig zijn, wordt dit gebruikt om atomiciteit direct af te leiden.
        - Tertiair: als het object zelf een ``CategoricalStructure`` is (uit
          irreducible_unit.py), wordt gecontroleerd of het als zero-object
          geconfigureerd is.

    Expressly NIET van toepassing op lijsten, dicts of andere Python-typen
    zonder categoriestructuur (anders dan in de originele implementatie).
    """

    operator_name = "categorical"

    def can_decompose(self, obs: Any) -> bool:
        # Van toepassing als het object categorietheretische metadata heeft
        return (
            hasattr(obs, "subobjects")
            or hasattr(obs, "is_zero_object")
            or hasattr(obs, "initial_object")
            or hasattr(obs, "objects")  # CategoricalStructure
        )

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        # 1. Zero-object check: atomair per definitie (Proposition 3)
        if getattr(obs, "is_zero_object", False):
            return []

        # 2. Initieel EN terminaal: zero-object criterium
        is_initial = getattr(obs, "is_initial", None)
        is_terminal = getattr(obs, "is_terminal", None)
        if is_initial is True and is_terminal is True:
            return []

        # 3. CategoricalStructure met initial_object als zero-object
        if hasattr(obs, "initial_object") and hasattr(obs, "terminal_object"):
            if obs.initial_object is not None and obs.initial_object == obs.terminal_object:
                return []  # Zero-object aanwezig → het geheel is al minimaal

        # 4. Expliciete deelobjecten
        subs = getattr(obs, "subobjects", None)
        if subs is not None and len(subs) > 0:
            return list(subs)

        # 5. CategoricalStructure: controleer morfismen voor subobject-structuur
        if hasattr(obs, "objects") and hasattr(obs, "morphisms"):
            subobjects = self._extract_subobjects_from_category(obs)
            if subobjects:
                return subobjects

        return []

    def _extract_subobjects_from_category(self, cat: Any) -> List[Any]:
        """
        Extraheer subobjecten uit een CategoricalStructure door te zoeken
        naar objecten met uitsluitend uitgaande morfismen (kandidaat-subobjecten).

        Een object X is een subobject van Y als er een monomorfisme X → Y
        bestaat. In de vereenvoudigde implementatie kijken we naar objecten
        die enkel als bron van morfismen voorkomen.
        """
        if not hasattr(cat, "morphisms") or not hasattr(cat, "objects"):
            return []

        source_only: set = set()
        target_only: set = set()

        for (src, tgt) in cat.morphisms.keys():
            if src != tgt:  # Negeer identiteitsmorfismen
                source_only.add(src)
                target_only.add(tgt)

        # Echte subobjecten: objecten die enkel als bron voorkomen
        # (geen enkel morfisme eindigt in hen vanuit een ander object)
        candidates = source_only - target_only
        return list(candidates)


# ---------------------------------------------------------------------------
# 4. Information atomicity  (Proposition 4 / Kolmogorov)
# ---------------------------------------------------------------------------

class InformationDecompositionOperator(DecompositionOperator):
    """
    Informatietheoretische decompositie op basis van Kolmogorov-complexiteit.

    Formele definitie (Proposition 4): een observable is atomair als elke
    poging tot decompositie de totale beschrijvingslengte verhoogt of gelijk
    houdt zonder discriminatieve informatiewinst:
        gain = K(left) + K(right) - K(whole) ≥ 0  → atoom

    Negatieve gain (K(links) + K(rechts) < K(geheel)) impliceert dat de
    onderdelen samen compacter te beschrijven zijn dan het geheel, wat wijst
    op interne structuur die decompositie rechtvaardigt.

    Kolmogorov-complexiteit K wordt benaderd via zlib-compressie (level=9).

    Verbeteringen t.o.v. de originele implementatie:
        - Homogene-blokken-heuristiek behoudt zijn directe split.
        - Expliciete check op niet-informatieve decompositie (gain ≥ 0 → atoom).
        - Configureerbaar aantal scan-posities voor lange strings.
        - Ondersteuning voor bytes naast str.

    Args:
        max_scan_positions: Maximaal aantal splitsposities dat wordt onderzocht
                            (default: 20). Hogere waarden zijn nauwkeuriger
                            maar trager.
    """

    operator_name = "information"

    def __init__(self, max_scan_positions: int = 20) -> None:
        self.max_scan_positions = max_scan_positions

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, (str, bytes))

    def _to_bytes(self, obs: Any) -> bytes:
        if isinstance(obs, str):
            return obs.encode("utf-8")
        return obs

    def _complexity(self, data: bytes) -> int:
        """
        Geschatte Kolmogorov-complexiteit K(data) via zlib-compressie.

        Eigenschap: K(x) ≤ |zlib(x)| + O(1). Hoe lager de ratio
        |zlib(x)| / |x|, hoe meer interne structuur (regelmatiger) x is.
        """
        if len(data) == 0:
            return 0
        return len(zlib.compress(data, level=9))

    def _detect_homogeneous_blocks(self, s: str) -> Optional[int]:
        """
        Detecteert of de string bestaat uit precies twee homogene blokken
        (bijv. 'aaabbb'). Retourneert de splitspositie of None.

        Een homogeen blok is een maximale deelrij van identieke tekens.
        """
        if len(s) < 2:
            return None
        first_char = s[0]
        i = 1
        while i < len(s) and s[i] == first_char:
            i += 1
        if i == len(s):
            return None  # Slechts één blok
        second_char = s[i]
        for j in range(i + 1, len(s)):
            if s[j] != second_char:
                return None  # Meer dan twee blokken
        return i  # Splitspositie: einde eerste blok

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        data = self._to_bytes(obs)
        if len(data) < 2:
            return []  # Te kort om te splitsen

        # 1. Heuristiek: twee homogene blokken → directe split
        # Zowel str als bytes: converteer bytes tijdelijk naar str voor detectie
        if isinstance(obs, (str, bytes)):
            check_str = obs if isinstance(obs, str) else obs.decode("latin-1")
            split_pos = self._detect_homogeneous_blocks(check_str)
            if split_pos is not None and 0 < split_pos < len(obs):
                return [obs[:split_pos], obs[split_pos:]]

        # 2. Scan naar de beste splitsing op basis van Kolmogorov-gain
        total_complexity = self._complexity(data)
        best_split: Optional[Tuple[Any, Any]] = None
        best_gain = 0.0  # Drempel: gain MOET negatief zijn om decompositie te rechtvaardigen

        step = max(1, len(data) // self.max_scan_positions)
        for i in range(step, len(data), step):
            left = data[:i]
            right = data[i:]
            gain = self._complexity(left) + self._complexity(right) - total_complexity
            if gain < best_gain:  # Strikt negatief: onderdelen samen compacter
                best_gain = gain
                best_split = (left, right)

        if best_split is not None:
            # Negatieve gain gevonden: decompositie is informatief
            if isinstance(obs, str):
                try:
                    return [
                        best_split[0].decode("utf-8"),
                        best_split[1].decode("utf-8"),
                    ]
                except UnicodeDecodeError:
                    return [best_split[0], best_split[1]]
            return [best_split[0], best_split[1]]

        # Gain ≥ 0 voor alle splitsposities: de observable is informatietheretisch atomair
        return []


# ---------------------------------------------------------------------------
# 5. Geometric atomicity (puntenwolk)
# ---------------------------------------------------------------------------

class GeometricDecompositionOperator(DecompositionOperator):
    """
    Geometrische decompositie: splits een puntenwolk in twee clusters.

    Gebruikt k-means (k=2) via scikit-learn indien beschikbaar; valt terug
    op mediaan-splitsing langs de eerste hoofdcomponent als KMeans niet
    beschikbaar is of mislukt.

    Een puntenwolk is geometrisch atomair als alle punten identiek zijn
    (d.w.z. één punt in de meetkundige ruimte).

    Args:
        n_init:       Aantal willekeurige initialisaties voor KMeans (default: 10).
        random_state: Seed voor reproduceerbaarheid (default: 0).
    """

    operator_name = "geometric"

    def __init__(self, n_init: int = 10, random_state: int = 0) -> None:
        self.n_init = n_init
        self.random_state = random_state

    def can_decompose(self, obs: Any) -> bool:
        return (
            isinstance(obs, np.ndarray)
            and obs.ndim == 2
            and obs.shape[0] >= 2
        )

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        # Atomair als alle punten identiek zijn
        if np.all(obs == obs[0]):
            return []

        if HAS_SKLEARN and KMeans is not None:
            try:
                # Set n_jobs=1 to avoid MKL/vcomp DLL conflict on Windows (code 0xc06d007f).
                # threadpoolctl is called by sklearn internally; forcing single-threaded avoids
                # the crash when sklearn's MKL and conda's vcomp are incompatible.
                import os as _os
                _old_omp = _os.environ.get("OMP_NUM_THREADS")
                _os.environ["OMP_NUM_THREADS"] = "1"
                try:
                    kmeans = KMeans(
                        n_clusters=2,
                        random_state=self.random_state,
                        n_init=self.n_init,
                    ).fit(obs)
                finally:
                    if _old_omp is None:
                        _os.environ.pop("OMP_NUM_THREADS", None)
                    else:
                        _os.environ["OMP_NUM_THREADS"] = _old_omp
                labels = kmeans.labels_
                cluster1 = obs[labels == 0]
                cluster2 = obs[labels == 1]
                if len(cluster1) == 0 or len(cluster2) == 0:
                    return self._fallback_split(obs)
                return [cluster1, cluster2]
            except Exception as exc:
                logger.warning(
                    "KMeans-clustering mislukt (%s), valt terug op mediaan-splitsing.", exc
                )

        return self._fallback_split(obs)

    def _fallback_split(self, obs: np.ndarray) -> List[Any]:
        """Splits op mediaan van de eerste kolom (deterministisch)."""
        if obs.shape[0] < 2:
            return []
        median = np.median(obs[:, 0])
        left = obs[obs[:, 0] <= median]
        right = obs[obs[:, 0] > median]
        if len(left) == 0 or len(right) == 0:
            # Edge-case: alle waarden zijn gelijk aan de mediaan
            mid = obs.shape[0] // 2
            return [obs[:mid], obs[mid:]]
        return [left, right]


class GeometricPointOperator(DecompositionOperator):
    """
    Geometrische atomiciteit op puntniveau.

    Een puntenwolk is atomair als alle punten identiek zijn (één punt in de
    meetkundige ruimte). Anders wordt elk punt als apart deel beschouwd.

    Dit is de fijnste granulariteit van geometrische decompositie en
    correspondeert met de notion van een atoom als punt in de ruimte.
    """

    operator_name = "geometric_point"

    def can_decompose(self, obs: Any) -> bool:
        return (
            isinstance(obs, np.ndarray)
            and obs.ndim == 2
            and obs.shape[0] >= 1
        )

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []
        if np.all(obs == obs[0]):
            return []  # Atomair: één uniek punt
        return [obs[i : i + 1] for i in range(obs.shape[0])]


# ---------------------------------------------------------------------------
# 6. Qualitative atomicity
# ---------------------------------------------------------------------------

class QualitativeDecompositionOperator(DecompositionOperator):
    """
    Decompositie op basis van kwalitatieve dimensies.

    Gebruikt de ``is_atomic()``-methode van kwalitatieve dimensieobjecten
    (QualitativeDimension en subklassen uit qualitative_dimensions.py) als
    primaire atomiciteitstest.

    Als een dimensie niet atomair is, wordt een type-specifieke decompositie
    geprobeerd:
        - VectorDimension  → componenten als aparte ScalarDimension-objecten.
        - ColourDimension  → RGB-kanalen als IntensityDimension-objecten.
        - Overige typen    → geen verdere splitsing.
    """

    operator_name = "qualitative"

    def can_decompose(self, obs: Any) -> bool:
        # Circulaire import vermijden via lazy import
        try:
            from .qualitative_dimensions import QualitativeDimension
            return isinstance(obs, QualitativeDimension)
        except ImportError:
            return hasattr(obs, "is_atomic") and hasattr(obs, "value")

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        # Als de dimensie zichzelf als atomair beschouwt: stop
        if hasattr(obs, "is_atomic") and obs.is_atomic():
            return []

        # Type-specifieke decompositie
        try:
            from .qualitative_dimensions import (
                VectorDimension,
                ColourDimension,
                ColourSpace,
                ScalarDimension,
                IntensityDimension,
            )

            if isinstance(obs, VectorDimension):
                return [
                    ScalarDimension(name=f"{obs.name}_comp{i}", value=float(val), unit=obs.unit)
                    for i, val in enumerate(np.asarray(obs.value).flat)
                ]

            if isinstance(obs, ColourDimension):
                rgb = obs.convert_to(ColourSpace.RGB).value
                return [
                    IntensityDimension(value=float(rgb[0])),
                    IntensityDimension(value=float(rgb[1])),
                    IntensityDimension(value=float(rgb[2])),
                ]

        except ImportError as exc:
            logger.debug("Kwalitatieve decompositie: import mislukt (%s).", exc)
        except Exception as exc:
            logger.warning("Kwalitatieve decompositie mislukt: %s", exc)

        return []


# ---------------------------------------------------------------------------
# 7. Symmetry / Palindrome operator
# ---------------------------------------------------------------------------

class PalindromeDecompositionOperator(DecompositionOperator):
    """
    Symmetrie-gebaseerde decompositie.

    Een 1D-array (of lijst) is symmetrisch (palindroom) als arr ≈ arr[::-1]
    binnen de opgegeven tolerantie. Symmetrische arrays worden als atomair
    beschouwd in dit kader omdat ze geen informatief asymmetrisch complement
    hebben.

    Niet-symmetrische arrays worden gesplitst in twee helften, wat het
    beginpunt is voor verdere symmetrie-analyse in hogere lagen.

    Args:
        atol: Absolute tolerantie voor de symmetrie-check (default: 1e-9).
        rtol: Relatieve tolerantie (default: 0.0).
    """

    operator_name = "palindrome"

    def __init__(self, atol: float = 1e-9, rtol: float = 0.0) -> None:
        self.atol = atol
        self.rtol = rtol

    def can_decompose(self, obs: Any) -> bool:
        try:
            arr = np.asarray(obs)
            return arr.ndim == 1 and len(arr) > 1
        except Exception:
            return False

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []
        arr = np.asarray(obs)
        if np.allclose(arr, arr[::-1], atol=self.atol, rtol=self.rtol):
            return []  # Symmetrisch = atomair voor dit kader
        mid = len(arr) // 2
        return [arr[:mid].tolist(), arr[mid:].tolist()]


# ---------------------------------------------------------------------------
# 8. Inverse limit operator  (Proposition 5 – nieuw)
# ---------------------------------------------------------------------------

class InverseLimitOperator(DecompositionOperator):
    """
    Test convergentie onder verfijning van resolutie (Proposition 5).

    Formele grondslag: Layer 1 kan worden gerepresenteerd als pro-object
        lim← {S_ε}_{ε>0}
    Het inverse limiet bestaat als elke eindige benadering S_ε consistent
    is met alle fijnere benaderingen. Een observable is atomair in dit kader
    als zijn representatie stabiel blijft onder resolutieverfijning naar ε→0.

    Implementatie:
        Voor numpy-arrays: vergroott de resolutie door progressief meer
        elementen te gebruiken (subsampling). Als de genormaliseerde
        representatie convergeert (maximale absolute afwijking < atol),
        is de observable atomair.

        Voor scalaire waarden: altijd atomair (geen verfijning mogelijk).

    Args:
        scales:      Tuple van fractions (0, 1] die de resolutiestappen
                     aangeven (default: (1.0, 0.5, 0.25, 0.1)).
        atol:        Convergentie-drempel voor maximale absolute afwijking
                     (default: 1e-3).
        norm:        Genormaliseerde representatie gebruiken (default: True).
    """

    operator_name = "inverse_limit"

    def __init__(
        self,
        scales: Tuple[float, ...] = (1.0, 0.5, 0.25, 0.1),
        atol: float = 1e-3,
        norm: bool = True,
    ) -> None:
        self.scales = scales
        self.atol = atol
        self.norm = norm

    def can_decompose(self, obs: Any) -> bool:
        return isinstance(obs, (np.ndarray, int, float, complex))

    def _at_scale(self, obs: np.ndarray, scale: float) -> np.ndarray:
        """
        Geeft een genormaliseerde representatie van ``obs`` bij resolutie ``scale``.

        Subsampled versie: neem elke ceil(1/scale) elementen uit het array.

        Normalisatie: deelt door het absolute gemiddelde van het VOLLEDIGE array
        (schaal-invariant), zodat constante arrays bij alle resoluties dezelfde
        genormaliseerde waarde geven en dus als atomair worden herkend.
        Als het gemiddelde nul is, wordt de L2-norm van het volledige array gebruikt.
        """
        step = max(1, int(round(1.0 / scale)))
        sampled = obs[::step].astype(float)
        if self.norm:
            # Normaliseer door het absolute gemiddelde van het VOLLEDIGE array
            ref_norm = float(np.mean(np.abs(obs)))
            if ref_norm > 0:
                sampled = sampled / ref_norm
            else:
                l2 = float(np.linalg.norm(obs))
                if l2 > 0:
                    sampled = sampled / l2
        return sampled

    def _representations_converge(self, obs: np.ndarray) -> bool:
        """
        Test of de representaties bij alle schalen convergeren naar de
        representatie bij de volledige resolutie.
        """
        if obs.shape[0] < 2:
            return True  # Triviaal convergent

        ref = self._at_scale(obs, self.scales[0])  # Volledig resolutie
        for scale in self.scales[1:]:
            approx = self._at_scale(obs, scale)
            # Interpoleer approx terug naar de lengte van ref voor vergelijking
            if len(approx) < len(ref):
                indices = np.linspace(0, len(approx) - 1, len(ref))
                approx_interp = np.interp(indices, np.arange(len(approx)), approx)
            else:
                approx_interp = approx[: len(ref)]
            max_dev = np.max(np.abs(ref - approx_interp))
            if max_dev > self.atol:
                return False  # Divergentie gedetecteerd
        return True

    def decompose(self, obs: Any, context: Optional[Dict] = None) -> List[Any]:
        if not self.can_decompose(obs):
            return []

        # Scalaire waarden: geen verfijning mogelijk → atomair
        if isinstance(obs, (int, float, complex)):
            return []

        arr = np.asarray(obs).flatten()
        if arr.shape[0] < 2:
            return []

        if self._representations_converge(arr):
            return []  # Convergeert → atomair in de inverse limiet zin

        # Divergeert: geef de representaties bij de twee grofste schalen terug
        # als indicatie van de instabiele decompositie
        coarse1 = self._at_scale(arr, self.scales[-2] if len(self.scales) > 2 else self.scales[0])
        coarse2 = self._at_scale(arr, self.scales[-1])
        return [coarse1.tolist(), coarse2.tolist()]


# ===========================================================================
# Registratie
# ===========================================================================

# --- Formele operatoren (theoretisch gemotiveerd – primaire atomiciteitstest) ---

register_decomposition_operator("boolean",       BooleanDecompositionOperator())
register_decomposition_operator("measure",        MeasureDecompositionOperator())
register_decomposition_operator("categorical",    CategoricalDecompositionOperator())
register_decomposition_operator("information",    InformationDecompositionOperator())
register_decomposition_operator("geometric",      GeometricDecompositionOperator())
register_decomposition_operator("geometric_point", GeometricPointOperator())
register_decomposition_operator("qualitative",    QualitativeDecompositionOperator())
register_decomposition_operator("palindrome",     PalindromeDecompositionOperator())
register_decomposition_operator("inverse_limit",  InverseLimitOperator())

# --- Utility operatoren (praktisch hulpmiddel – geen primaire atomiciteitstest) ---

register_decomposition_operator("list_split",   ListSplitOperator())
register_decomposition_operator("string_split", StringSplitOperator())
register_decomposition_operator("dict_split",   DictSplitOperator())
register_decomposition_operator("array_split",  ArraySplitOperator())


# ===========================================================================
# Hulpfunctie
# ===========================================================================

def is_atomic_by_operator(
    obs: Any,
    operator_name: str,
    context: Optional[Dict] = None,
) -> bool:
    """
    Bepaal of een observable atomair is volgens een specifieke decompositieoperator.

    Een observable is atomair als de operator geen niet-triviale decompositie
    oplevert (lege lijst) of als de operator niet van toepassing is op het
    type van de observable (``can_decompose`` retourneert False).

    Ondersteunt het lazy ontology protocol: als ``obs`` een ``_is_lazy_observable``
    vlag heeft en nog niet gecollapsed is, wordt ``collapse(context)`` aangeroepen
    vóór de decompositietest.

    Args:
        obs:           De te testen observable (willekeurig object).
        operator_name: Naam van de geregistreerde operator.
        context:       Optioneel context-dict voor de operator en collapse.

    Returns:
        True als de observable atomair is voor het gegeven kader.

    Raises:
        ValueError: Als de operator niet geregistreerd is.
    """
    # Lazy ontology: collapse indien nodig
    if (
        getattr(obs, "_is_lazy_observable", False)
        and not getattr(obs, "collapsed", True)
        and callable(getattr(obs, "collapse", None))
    ):
        obs.collapse(context or {})

    operator = get_decomposition_operator(operator_name)
    if operator is None:
        raise ValueError(
            f"Onbekende decompositieoperator: '{operator_name}'. "
            f"Beschikbaar: {sorted(DECOMPOSITION_OPERATORS.keys())}"
        )

    if not operator.can_decompose(obs):
        # Operator niet van toepassing op dit type → beschouw als atomair
        # (geen zinvolle decompositie in dit kader)
        return True

    parts = operator.decompose(obs, context)

    if len(parts) < 2:
        return True  # Geen of onvoldoende delen → atomair

    # Saniteitscheck: geen enkel deel mag identiek zijn aan het origineel
    for part in parts:
        try:
            if part is obs:
                logger.warning(
                    "Operator '%s' retourneerde een deel dat identiek is aan het origineel (identity).",
                    operator_name,
                )
            elif part == obs:
                logger.warning(
                    "Operator '%s' retourneerde een deel gelijk aan het origineel (equality).",
                    operator_name,
                )
        except Exception:
            # Vergelijking mislukt voor complexe objecten: negeer
            pass

    return False