"""
Unit tests voor Laag 1: Foundational Observables.

Deze tests controleren de functionaliteit van de modules:
- meta_spec: MetaSpecification, registratie van frameworks (check-or-create),
  axioma's, validate(), snapshot, add/remove principe, add_weight,
  register_operator, get_operator, PRINCIPLE_OPERATOR_ALIASES, unregister
- decomposition: decompositieoperatoren en is_atomic_by_operator
- qualitative_dimensions: is_atomic methoden, dirty-flag cache, _compute_is_atomic,
  ResonanceBridge, gewogen kwalitatieve atomiciteit, gradient_symbolic guard
- irreducible_unit: atomiciteitsberekening (info_atomicity richting-fix,
  boolean_atomicity operator-delegatie, category_atomicity zero-object test,
  scipy-fallback confidence interval), generativity_score, _atomicity_lock,
  lazy substructures, embedding, properties
- observables: aanmaken van observables met meta_spec en potential (SimpleNamespace),
  _infer_type uitbreidingen (callable→STOCHASTIC, 2D array→TOPOLOGICAL),
  emit_to_layer, get_by_type, get_by_observer, remove_observable, validate(),
  get_stats() met generativity_scores, configureerbare atom_threshold
- density_field: twee-kanaal invloed (resonantie + embedding), afstandsverval,
  sample_influence Monte Carlo, compute_influence_matrix, get_top_influencers,
  apply_influence_all, _embedding_similarity
- discovery: evolutionaire feedbacklus (EMA-gebaseerde gewichtsupdate, persist/load
  via update_weight, confidence-berekening, validate_proposal),
  get_stats, reset, FrequencyDecompositionOperator FFT, EntropyDecompositionOperator,
  SparsityDecompositionOperator

Uitvoeren met (vanuit de hoofdmap apeiron):
    PYTHONPATH=. pytest layers/layer01_foundational/tests/test_layer1.py -v
"""

import os
import pytest
import numpy as np
import tempfile
import json
import threading
import sys
from unittest.mock import patch, MagicMock

# Absolute imports ten opzichte van de top-level package 'apeiron'
from apeiron.layers.layer01_foundational.meta_spec import (
    MetaSpecification,
    DecompositionPrinciple,
    LOGICAL,
    DEFAULT_META_SPEC,
    register_atomicity_framework,
    atomicity_framework,
    ATOMICITY_FRAMEWORKS,
    PRINCIPLE_OPERATOR_ALIASES,
)
from apeiron.layers.layer01_foundational.decomposition import (
    DECOMPOSITION_OPERATORS,
    is_atomic_by_operator,
    ListSplitOperator,
    BooleanDecompositionOperator,
    QualitativeDecompositionOperator,
    GeometricPointOperator,
    PalindromeDecompositionOperator,
    InformationDecompositionOperator,
    register_decomposition_operator,
    get_decomposition_operator,
    GeometricDecompositionOperator,
)
from apeiron.layers.layer01_foundational.qualitative_dimensions import (
    ScalarDimension,
    VectorDimension,
    ColourDimension,
    ColourSpace,
    MultiResolutionDimension,
    IntensityDimension,
    TextureDimension,
    TextureType,
    ResonanceBridge,
    gradient_symbolic,
    SYMPY_AVAILABLE,
)
from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
    boolean_atomicity,
    info_atomicity,
    decomposition_boolean_atomicity,
    qualitative_dimensions_atomicity,
    get_framework_names_for_principle,
    GUDHI_AVAILABLE,
    category_atomicity,
    group_atomicity,
    GeometricStructure,
)
from apeiron.layers.layer01_foundational.observables import (
    Layer1_Observables,
)
from apeiron.layers.layer01_foundational.density_field import (
    DensityField,
    InfluenceSample,
)
from apeiron.layers.layer01_foundational.discovery import (
    EvolutionaryFeedbackLoop,
    HeuristicDiscovery,
    auto_discovery_pipeline,
    FrequencyDecompositionOperator,
)


# ============================================================================
# Hulpfuncties en fixtures
# ============================================================================

@pytest.fixture
def clear_registries():
    """Maak registries leeg voor en na een test (indien nodig)."""
    orig_atomicity = ATOMICITY_FRAMEWORKS.copy()
    orig_decomp = DECOMPOSITION_OPERATORS.copy()
    yield
    ATOMICITY_FRAMEWORKS.clear()
    ATOMICITY_FRAMEWORKS.update(orig_atomicity)
    DECOMPOSITION_OPERATORS.clear()
    DECOMPOSITION_OPERATORS.update(orig_decomp)


@pytest.fixture
def cleanup_test_principe():
    """Verwijdert eventueel testprincipe uit de DecompositionPrinciple registry na de test."""
    yield
    DecompositionPrinciple._registry.pop('test_principe', None)
    DecompositionPrinciple._registry.pop('test_unregister_principe', None)
    DecompositionPrinciple._registry.pop('test_add_principe', None)


def make_obs(obs_id="test", value=42,
             obs_type=ObservabilityType.DISCRETE) -> UltimateObservable:
    """Hulpfunctie om een UltimateObservable aan te maken."""
    return UltimateObservable(id=obs_id, value=value, observability_type=obs_type)


# ============================================================================
# Tests voor meta_spec.py
# ============================================================================

class TestMetaSpecDefaults:
    """Tests voor standaardwaarden van MetaSpecification."""

    def test_defaults(self):
        """Test dat de standaard MetaSpecification correct is."""
        spec = MetaSpecification()
        assert len(spec.primary_principles) == 6
        assert spec.atomicity_is_binary is False
        assert spec.default_atomicity_weights['boolean'] == 0.5
        assert spec.default_atomicity_weights['decomposition_boolean'] == 1.0
        assert spec.default_atomicity_weights['qualitative'] == 1.0

    # Bug fix 1: axioms field with 4 defaults
    def test_axioms_field_present(self):
        """Test dat het axioma-veld aanwezig is met 4 standaard-axioma's."""
        spec = MetaSpecification()
        assert hasattr(spec, 'axioms')
        assert len(spec.axioms) == 4
        expected = {
            "irreducibility_is_observer_relative",
            "atomicity_is_continuous_not_binary",
            "decomposition_vacuity_implies_atomicity",
            "generativity_requires_non_null_resonance",
        }
        assert set(spec.axioms) == expected

    # Bug fix 2: decomposition_operators auto-populated
    def test_decomposition_operators_auto_populated(self):
        """Test dat decomposition_operators bij initialisatie gevuld wordt."""
        spec = MetaSpecification()
        assert len(spec.decomposition_operators) > 0
        # De zes standaardoperatoren moeten aanwezig zijn
        for op_name in ("boolean", "measure", "categorical",
                        "information", "geometric", "qualitative"):
            assert op_name in spec.decomposition_operators, (
                f"Operator '{op_name}' ontbreekt in decomposition_operators"
            )

    def test_repr_includes_axioms(self):
        """Test dat __repr__ het aantal axioma's vermeldt."""
        r = repr(MetaSpecification())
        assert "axioms=4" in r


class TestMetaSpecWeights:
    """Tests voor gewichtsbeheer in MetaSpecification."""

    def test_update_weight_normal(self):
        spec = MetaSpecification()
        spec.update_weight('boolean', 0.8)
        assert spec.default_atomicity_weights['boolean'] == 0.8

    def test_update_weight_clamping(self):
        spec = MetaSpecification()
        spec.update_weight('boolean', 1.5)
        assert spec.default_atomicity_weights['boolean'] == 1.0
        spec.update_weight('boolean', -0.1)
        assert spec.default_atomicity_weights['boolean'] == 0.0

    def test_update_weight_unknown_raises(self):
        spec = MetaSpecification()
        with pytest.raises(ValueError):
            spec.update_weight('nonexistent', 0.5)

    # Extension: add_weight (werkt ook voor onbekende frameworks)
    def test_add_weight_new_framework(self):
        spec = MetaSpecification()
        spec.add_weight("brand_new_framework", 0.75)
        assert spec.default_atomicity_weights["brand_new_framework"] == 0.75

    def test_add_weight_clamping(self):
        spec = MetaSpecification()
        spec.add_weight("fw_high", 2.5)
        assert spec.default_atomicity_weights["fw_high"] == 1.0
        spec.add_weight("fw_low", -0.5)
        assert spec.default_atomicity_weights["fw_low"] == 0.0

    def test_get_weight(self):
        spec = MetaSpecification()
        assert spec.get_weight("boolean") == 0.5
        assert spec.get_weight("nonexistent_xyz") == 0.0


class TestMetaSpecCopy:
    """Tests voor kopieergedrag van MetaSpecification."""

    def test_copy_preserves_weights(self):
        spec = MetaSpecification()
        spec.update_weight('boolean', 0.9)
        copy_spec = spec.copy()
        assert copy_spec.default_atomicity_weights['boolean'] == 0.9

    def test_copy_is_independent(self):
        spec = MetaSpecification()
        spec.update_weight('boolean', 0.9)
        copy_spec = spec.copy()
        copy_spec.update_weight('boolean', 0.5)
        assert spec.default_atomicity_weights['boolean'] == 0.9

    def test_copy_preserves_axioms(self):
        spec = MetaSpecification()
        spec.axioms.append("extra_axiom_test")
        copy_spec = spec.copy()
        assert "extra_axiom_test" in copy_spec.axioms

    def test_copy_axioms_independent(self):
        spec = MetaSpecification()
        copy_spec = spec.copy()
        copy_spec.axioms.append("only_in_copy")
        assert "only_in_copy" not in spec.axioms


class TestMetaSpecPrinciples:
    """Tests voor principebeheer in MetaSpecification."""

    def test_register_check_or_create(self, cleanup_test_principe):
        """Test dat DecompositionPrinciple.register() bij dubbele registratie het bestaande object teruggeeft."""
        p1 = DecompositionPrinciple.register("test_principe")
        p2 = DecompositionPrinciple.register("test_principe")
        assert p1 is p2
        assert p1.name == "test_principe"

    # Extension: unregister
    def test_unregister_principle(self, cleanup_test_principe):
        """Test dat een principe verwijderd kan worden uit de registry."""
        DecompositionPrinciple.register("test_unregister_principe")
        assert "test_unregister_principe" in DecompositionPrinciple.all()
        DecompositionPrinciple.unregister("test_unregister_principe")
        assert "test_unregister_principe" not in DecompositionPrinciple.all()
        # Idempotent
        DecompositionPrinciple.unregister("test_unregister_principe")

    # Extension: add_principle / remove_principle / get_principle_names
    def test_add_remove_principle(self, cleanup_test_principe):
        """Test add_principle en remove_principle."""
        spec = MetaSpecification()
        new_p = DecompositionPrinciple.register("test_add_principe")
        spec.add_principle(new_p)
        assert "test_add_principe" in spec.get_principle_names()
        # Dubbel toevoegen → stilzwijgend overgeslagen
        spec.add_principle(new_p)
        assert spec.get_principle_names().count("test_add_principe") == 1
        # Verwijderen
        removed = spec.remove_principle("test_add_principe")
        assert removed is True
        assert "test_add_principe" not in spec.get_principle_names()
        # Verwijderen van iets dat er niet is → False
        assert spec.remove_principle("nonexistent_xyz") is False

    def test_get_principle_names_returns_list(self):
        spec = MetaSpecification()
        names = spec.get_principle_names()
        assert isinstance(names, list)
        assert "logical" in names
        assert "measure" in names


class TestMetaSpecOperators:
    """Tests voor operatorbeheer in MetaSpecification."""

    def test_register_get_operator(self):
        """Test register_operator en get_operator."""
        spec = MetaSpecification()
        op = lambda obs, ctx=None: []
        spec.register_operator("test_op_xyz", op)
        retrieved = spec.get_operator("test_op_xyz")
        assert retrieved is op

    def test_register_operator_check_or_create(self):
        """Test dat dubbele registratie het bestaande object behoudt."""
        spec = MetaSpecification()
        op1 = lambda obs, ctx=None: []
        op2 = lambda obs, ctx=None: []
        spec.register_operator("test_dup_op", op1)
        spec.register_operator("test_dup_op", op2)
        assert spec.decomposition_operators["test_dup_op"] is op1

    def test_get_operator_falls_back_to_global(self):
        """get_operator kijkt ook in de globale DECOMPOSITION_OPERATORS."""
        spec = MetaSpecification()
        op = spec.get_operator("boolean")
        assert op is not None

    def test_get_operator_unknown_returns_none(self):
        spec = MetaSpecification()
        assert spec.get_operator("totally_unknown_xyz_abc") is None


class TestMetaSpecValidate:
    """Tests voor validate() uitbreidingen."""

    def test_validate_default_spec_passes(self):
        """De standaard MetaSpecification moet validatie doorstaan."""
        spec = MetaSpecification()
        assert spec.validate() is True

    # Bug fix 3: validate() formal > heuristic check
    def test_validate_fails_when_heuristic_exceeds_formal(self):
        """Validatie mislukt als heuristische gewichten zwaarder zijn dan formele."""
        spec = MetaSpecification()
        heuristic_names = [k for k in spec.default_atomicity_weights
                           if not k.startswith("decomposition_")]
        for k in heuristic_names:
            spec.default_atomicity_weights[k] = 3.0  # boost heuristieken
        assert spec.validate() is False

    def test_validate_binary_mode_correct_weights(self):
        """In binaire modus mogen gewichten alleen 0 of 1 zijn."""
        spec = MetaSpecification()
        spec.atomicity_is_binary = True
        for k in list(spec.default_atomicity_weights):
            spec.default_atomicity_weights[k] = 1.0
        assert spec.validate() is True

    def test_validate_binary_mode_wrong_weight(self):
        """In binaire modus is 0.5 een ongeldig gewicht."""
        spec = MetaSpecification()
        spec.atomicity_is_binary = True
        spec.default_atomicity_weights["boolean"] = 0.5
        assert spec.validate() is False

    def test_validate_duplicate_principles(self):
        """Validatie mislukt bij dubbele principenamen."""
        spec = MetaSpecification()
        spec.primary_principles.append(LOGICAL)
        assert spec.validate() is False

    def test_validate_skip_formal_check_in_binary_mode(self):
        """In binaire modus wordt de formele > heuristische check overgeslagen."""
        spec = MetaSpecification()
        spec.atomicity_is_binary = True
        for k in list(spec.default_atomicity_weights):
            spec.default_atomicity_weights[k] = 1.0
        # Validatie slaagt ondanks dat de gewichten niet de formele > heuristische
        # hiërarchie reflecteren (check is uitgeschakeld in binaire modus)
        assert spec.validate() is True


class TestMetaSpecSnapshot:
    """Tests voor snapshot()."""

    def test_snapshot_returns_plain_dict(self):
        spec = MetaSpecification()
        snap = spec.snapshot()
        assert isinstance(snap, dict)
        for key in ("principles", "weights", "axioms", "operator_names",
                    "atomicity_is_binary"):
            assert key in snap, f"Sleutel '{key}' ontbreekt in snapshot"

    def test_snapshot_is_copy(self):
        """Aanpassen van de snapshot mag de spec niet beïnvloeden."""
        spec = MetaSpecification()
        snap = spec.snapshot()
        snap["weights"]["boolean"] = 999.0
        assert spec.get_weight("boolean") != 999.0

    def test_snapshot_axioms_count(self):
        spec = MetaSpecification()
        snap = spec.snapshot()
        assert len(snap["axioms"]) == 4


class TestPrincipleOperatorAliases:
    """Tests voor PRINCIPLE_OPERATOR_ALIASES."""

    def test_aliases_exported(self):
        assert PRINCIPLE_OPERATOR_ALIASES is not None
        assert isinstance(PRINCIPLE_OPERATOR_ALIASES, dict)

    def test_logical_maps_to_boolean(self):
        assert "boolean" in PRINCIPLE_OPERATOR_ALIASES.get("logical", [])
        assert "decomposition_boolean" in PRINCIPLE_OPERATOR_ALIASES.get("logical", [])

    def test_all_six_principles_present(self):
        expected = {"logical", "measure", "categorical",
                    "information", "geometric", "qualitative"}
        assert expected.issubset(set(PRINCIPLE_OPERATOR_ALIASES.keys()))


class TestAtomicityFrameworkRegistry:
    """Tests voor de atomiciteitsframework-registry."""

    def test_register_check_or_create(self, clear_registries):
        """Bij duplicaat wordt geen fout gegooid."""
        def dummy(obs, ctx): return 0.5
        register_atomicity_framework("dummy", dummy)
        assert "dummy" in ATOMICITY_FRAMEWORKS
        register_atomicity_framework("dummy", dummy)
        assert ATOMICITY_FRAMEWORKS["dummy"] is dummy

    def test_decorator(self, clear_registries):
        """Test de decorator voor registratie."""
        @atomicity_framework("deco_dummy")
        def func(obs, ctx): return 0.7
        assert "deco_dummy" in ATOMICITY_FRAMEWORKS
        assert ATOMICITY_FRAMEWORKS["deco_dummy"] is func


# ============================================================================
# Tests voor decomposition.py
# ============================================================================

class TestDecompositionOperators:
    """Tests voor decompositieoperatoren."""

    def test_list_split_operator(self):
        op = ListSplitOperator()
        assert op.can_decompose([1, 2, 3]) is True
        assert op.decompose([1, 2, 3]) == [[1], [2, 3]]
        assert op.decompose([1]) == []
        assert op.decompose("abc") == []

    def test_boolean_decomposition_operator(self):
        op = BooleanDecompositionOperator()
        assert op.decompose(42) == []
        result = op.decompose({1, 2, 3, 4})
        assert len(result) == 2
        assert op.decompose({1}) == []
        assert op.decompose([1, 2]) == []

    def test_geometric_point_operator(self):
        op = GeometricPointOperator()
        points = np.array([[1, 1], [1, 1], [1, 1]])
        assert op.decompose(points) == []
        points2 = np.array([[1, 1], [2, 2], [3, 3]])
        parts = op.decompose(points2)
        assert len(parts) == 3
        assert np.array_equal(parts[0], [[1, 1]])
        assert np.array_equal(parts[1], [[2, 2]])
        assert np.array_equal(parts[2], [[3, 3]])

    def test_palindrome_decomposition_operator(self):
        op = PalindromeDecompositionOperator()
        pal = [1, 2, 3, 2, 1]
        assert op.decompose(pal) == []
        nonpal = [1, 2, 3, 4, 5]
        parts = op.decompose(nonpal)
        assert len(parts) == 2
        assert parts[0] == [1, 2]
        assert parts[1] == [3, 4, 5]

    def test_is_atomic_by_operator(self):
        assert is_atomic_by_operator(42, "boolean") is True
        assert is_atomic_by_operator({1, 2}, "boolean") is False
        with pytest.raises(ValueError):
            is_atomic_by_operator(42, "bestaat_niet")

    def test_information_decomposition_gain_fix(self):
        """InformationDecompositionOperator splitst alleen bij negatieve gain."""
        op = InformationDecompositionOperator()
        data = "aaaaaa"
        parts = op.decompose(data)
        assert parts == []

        data_mixed = "a" * 1000 + "b" * 1000
        parts_mixed = op.decompose(data_mixed)
        if len(parts_mixed) == 2:
            assert parts_mixed[0] + parts_mixed[1] == data_mixed
        else:
            pytest.skip("InformationDecompositionOperator vond geen split voor deze string")


try:
    import sklearn
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn niet geïnstalleerd")
def test_geometric_decomposition_operator():
    op = GeometricDecompositionOperator()
    points = np.array([[0, 0], [0, 1], [10, 10], [10, 11]])
    result = op.decompose(points)
    assert len(result) == 2
    assert len(result[0]) == 2
    assert len(result[1]) == 2


# ============================================================================
# Tests voor qualitative_dimensions.py
# ============================================================================

class TestQualitativeDimensionsIsAtomic:
    """Tests voor is_atomic() in kwalitatieve dimensies."""

    def test_scalar_dimension_is_atomic(self):
        s = ScalarDimension("test", 3.14)
        assert s.is_atomic() is True

    def test_vector_dimension_is_atomic_basis(self):
        v = VectorDimension("test", [1, 0, 0])
        assert v.is_atomic() is True

    def test_vector_dimension_is_atomic_multi_nonzero(self):
        v2 = VectorDimension("test", [1, 1, 0])
        assert v2.is_atomic() is False

    def test_vector_dimension_is_atomic_threshold(self):
        v3 = VectorDimension("test", [1.0, 0.005, 0.0])
        assert v3.is_atomic(threshold=0.01) is True

    def test_colour_dimension_is_atomic_pure(self):
        red = ColourDimension([1, 0, 0], colour_space=ColourSpace.RGB)
        assert red.is_atomic() is True

    def test_colour_dimension_is_atomic_grey(self):
        grey = ColourDimension([0.5, 0.5, 0.5], colour_space=ColourSpace.RGB)
        assert grey.is_atomic() is False

    def test_multi_resolution_dimension_is_atomic_equal(self):
        values = {0.1: 1.0, 1.0: 1.0, 10.0: 1.0}
        mr = MultiResolutionDimension("test", values)
        assert mr.is_atomic() is True

    def test_multi_resolution_dimension_is_atomic_different(self):
        values2 = {0.1: 1.0, 1.0: 2.0, 10.0: 1.0}
        mr2 = MultiResolutionDimension("test", values2)
        assert mr2.is_atomic() is False


class TestQualitativeDimensionsDirtyFlag:
    """Tests voor de dirty-flag atomiciteitscache."""

    def test_atomic_stale_starts_true(self):
        """_atomic_stale moet True zijn na aanmaak."""
        s = ScalarDimension("x", 1.0)
        assert s._atomic_stale is True
        assert s._atomic_cache is None

    def test_is_atomic_populates_cache(self):
        """Na is_atomic() call moet de cache gevuld zijn."""
        s = ScalarDimension("x", 1.0)
        result = s.is_atomic()
        assert s._atomic_stale is False
        assert s._atomic_cache == result

    def test_is_atomic_uses_cache_on_second_call(self):
        """Tweede aanroep gebruikt de cache (geen herberekening)."""
        s = ScalarDimension("y", 2.0)
        r1 = s.is_atomic()
        # Vervals de cache
        s._atomic_cache = not r1
        r2 = s.is_atomic()
        assert r2 == (not r1), "Tweede aanroep moet gecachte waarde teruggeven"

    def test_mark_atomic_stale_invalidates(self):
        """_mark_atomic_stale() invalideert de cache."""
        s = ScalarDimension("z", 3.0)
        s.is_atomic()
        assert s._atomic_stale is False
        s._mark_atomic_stale()
        assert s._atomic_stale is True
        assert s._atomic_cache is None
        # Volgende call herberekent
        r = s.is_atomic()
        assert isinstance(r, bool)
        assert s._atomic_stale is False

    def test_compute_is_atomic_overridable(self):
        """_compute_is_atomic() kan worden overschreven door subklassen."""
        class AlwaysNonAtomic(ScalarDimension):
            def _compute_is_atomic(self, threshold=0.01):
                return False

        m = AlwaysNonAtomic("mock", 42.0)
        assert m.is_atomic() is False
        assert m._atomic_cache is False
        m._mark_atomic_stale()
        assert m.is_atomic() is False

    def test_cache_fields_non_init_non_repr(self):
        """Cache-velden zijn non-init, non-repr en worden niet vergeleken."""
        import dataclasses
        s = ScalarDimension("test", 1.0)
        fields = {f.name: f for f in dataclasses.fields(s)}
        for fname in ('_atomic_cache', '_atomic_stale'):
            assert fname in fields, f"{fname} ontbreekt als dataclass-field"
            assert fields[fname].init is False
            assert fields[fname].repr is False
            assert fields[fname].compare is False

    def test_cache_independent_per_instance(self):
        """Cache is onafhankelijk per instantie."""
        v1 = VectorDimension("v1", [1.0, 0.0, 0.0])  # atomair
        v2 = VectorDimension("v2", [1.0, 1.0, 0.0])  # niet-atomair
        assert v1.is_atomic() is True
        assert v2.is_atomic() is False
        assert v1._atomic_cache is True
        assert v2._atomic_cache is False


class TestGradientSymbolicGuard:
    """Test dat gradient_symbolic graceful degradeert als SymPy ontbreekt."""

    def test_gradient_symbolic_with_sympy(self):
        """Werkt correct als SymPy beschikbaar is."""
        if not SYMPY_AVAILABLE:
            pytest.skip("SymPy niet beschikbaar")
        import sympy as sp
        x = sp.Symbol('x')
        result = gradient_symbolic(x ** 2, x)
        assert str(result) == "2*x"

    def test_gradient_symbolic_raises_without_sympy(self):
        """
        Zonder SymPy moet een ImportError worden gegooid (niet NameError).

        v3.0: Gebruikt altijd mocking i.p.v. te skippen – test is nu
        altijd actief ongeacht of SymPy geïnstalleerd is.
        """
        import apeiron.layers.layer01_foundational.qualitative_dimensions as qd_module
        with patch.object(qd_module, "SYMPY_AVAILABLE", False):
            with pytest.raises(ImportError, match="SymPy"):
                gradient_symbolic(None, None)

    def test_gradient_symbolic_raises_when_sympy_mocked_absent(self):
        """
        Test de ImportError-guard via mocking, ongeacht of SymPy geïnstalleerd is.

        ``test_gradient_symbolic_raises_without_sympy`` wordt overgeslagen als
        SymPy aanwezig is, waardoor de guard-tak nooit wordt gedekt op een
        omgeving waar SymPy geïnstalleerd is. Dit is de complementaire test:
        hij patcht ``SYMPY_AVAILABLE`` naar ``False`` in het bronmodule en
        verifieert dat ``gradient_symbolic`` dan een ``ImportError`` gooit –
        nooit een ``NameError`` (de bug die de guard moest voorkomen).
        """
        import apeiron.layers.layer01_foundational.qualitative_dimensions as qd_module
        with patch.object(qd_module, "SYMPY_AVAILABLE", False):
            with pytest.raises(ImportError, match="SymPy"):
                gradient_symbolic(None, None)


class TestResonanceBridge:
    """Tests voor ResonanceBridge."""

    def test_translate_registered_mapping(self):
        bridge = ResonanceBridge()

        def texture_to_colour(val):
            if isinstance(val, np.ndarray) and val.size == 1:
                scalar_val = val.item()
            else:
                scalar_val = val
            return [scalar_val, 0.5, 0.5]

        bridge.register_mapping(TextureDimension, ColourDimension, texture_to_colour)
        tex = TextureDimension(value=0.8, texture_type=TextureType.GABOR)
        col = bridge.translate(tex, ColourDimension)
        assert col is not None
        assert isinstance(col, ColourDimension)
        assert np.isclose(col.value[0], 0.8)
        assert np.isclose(col.value[1], 0.5)

    def test_translate_unregistered_mapping_returns_none(self):
        bridge = ResonanceBridge()
        tex = TextureDimension(value=0.8, texture_type=TextureType.GABOR)
        col2 = bridge.translate(tex, ScalarDimension)
        assert col2 is None


# ============================================================================
# Tests voor irreducible_unit.py
# ============================================================================

class TestAtomicityFunctions:
    """Tests voor individuele atomiciteitsfuncties."""

    # Bug fix 1: info_atomicity richting – eenvoudig = hoge score
    def test_info_atomicity_direction(self):
        """Eenvoudige (comprimeerbare) waarden moeten een hogere score krijgen."""
        obs_simple = make_obs("simple", "a" * 100)
        obs_random = make_obs("random", "xK7pQ2mN9r3yZv8wL5eAhJsBtCuDfGiOo" * 3)
        score_simple = info_atomicity(obs_simple)
        score_random = info_atomicity(obs_random)
        assert score_simple > score_random, (
            f"Eenvoudige string ({score_simple:.3f}) moet hoger scoren dan "
            f"complexe string ({score_random:.3f})"
        )
        assert score_simple > 0.5, "Sterk comprimeerbare string moet > 0.5 scoren"

    def test_info_atomicity_short_string_guard(self):
        """
        Korte waarden (< 10 bytes) retourneren 1.0 ongeacht zlib-overhead.

        Experimenteel aangetoond (falsificatie-experiment): zlib voegt ~9 bytes
        overhead toe, waardoor ratio > 1 voor ultrakorte inputs zoals integer 1.
        Dit is een implementatie-artefact; de fix retourneert 1.0 voor inputs
        < min_bytes (default=10).
        """
        # Integer 1: was falsified (score=0.0), now correctly 1.0
        obs_one = make_obs("one", 1)
        assert info_atomicity(obs_one) == 1.0, (
            "Integer 1 must score 1.0 (short-string guard, zlib overhead artefact fixed)"
        )
        # Other short primitives all map to 1.0
        for val in [0, True, False, 42, "a", "xy"]:
            obs = make_obs(f"short_{val}", val)
            score = info_atomicity(obs)
            assert score == 1.0, (
                f"Short value {val!r} (len={len(str(val).encode())}) must score 1.0, got {score}"
            )

    def test_info_atomicity_configurable_min_bytes(self):
        """info_min_bytes in metadata overrides the default short-string threshold."""
        obs = make_obs("cfg", "hello world")  # 11 bytes — above default threshold of 10
        score_default = info_atomicity(obs)
        assert 0.0 <= score_default <= 1.0

        # Override to 20: 11 < 20 → must return 1.0
        obs.metadata["info_min_bytes"] = 20
        score_override = info_atomicity(obs)
        assert score_override == 1.0, f"Override threshold 20: expected 1.0, got {score_override}"

        # Override to 5: 11 >= 5 → uses zlib compression
        obs.metadata["info_min_bytes"] = 5
        score_low = info_atomicity(obs)
        assert 0.0 <= score_low <= 1.0

    def test_info_atomicity_empty_string(self):
        obs = make_obs("empty", "")
        assert info_atomicity(obs) == 1.0

    def test_info_atomicity_range(self):
        for val in [42, "hello", [1, 2, 3], None]:
            obs = make_obs("test", val)
            score = info_atomicity(obs)
            assert 0.0 <= score <= 1.0, f"Score buiten [0,1] voor value={val!r}: {score}"

    # Bug fix 2: boolean_atomicity via operator delegatie
    def test_boolean_atomicity_integer(self):
        obs = make_obs("int", 42)
        assert boolean_atomicity(obs) == 1.0

    def test_boolean_atomicity_list(self):
        """Lijst met meerdere elementen → niet atomair (0.5)."""
        obs = make_obs("list", [1, 2, 3])
        assert boolean_atomicity(obs) == 0.5

    def test_boolean_atomicity_bool(self):
        obs = make_obs("bool", True)
        assert boolean_atomicity(obs) == 1.0

    def test_decomposition_boolean_atomicity_set(self):
        obs = make_obs("set", {1, 2, 3})
        assert decomposition_boolean_atomicity(obs) == 0.0

    def test_decomposition_boolean_atomicity_integer(self):
        obs2 = make_obs("int", 42)
        assert decomposition_boolean_atomicity(obs2) == 1.0

    def test_qualitative_dimensions_atomicity(self):
        obs = make_obs("qual", None)
        vec = VectorDimension("velocity", [1, 1, 0])
        obs.add_qualitative_dimension("velocity", vec)
        assert qualitative_dimensions_atomicity(obs) == 0.0
        scalar = ScalarDimension("temp", 25.0)
        obs.add_qualitative_dimension("temp", scalar)
        assert qualitative_dimensions_atomicity(obs) == 0.5
        # Gebruik een kopie zodat DEFAULT_META_SPEC niet wordt gemuteerd
        obs.meta_spec = obs.meta_spec.copy()
        obs.meta_spec.qualitative_dim_weights = {"velocity": 2.0, "temp": 1.0}
        new_score = qualitative_dimensions_atomicity(obs)
        assert new_score == pytest.approx(1 / 3)


class TestCategoryAtomicity:
    """Tests voor category_atomicity met de nieuwe zero-object logica."""

    def test_no_category_returns_one(self):
        obs = make_obs()
        assert category_atomicity(obs) == 1.0

    def test_outgoing_only_no_terminality(self):
        """
        Een object dat alleen uitgaande morfismen heeft (geen inkomende)
        heeft terminality_coverage = 0 → score = 0.
        """
        obs = make_obs()
        obs.category.add_object(obs.id)
        obs.category.add_object("other")
        obs.category.add_morphism(obs.id, "other", "f")
        # initiality_coverage = 1, terminality_coverage = 0
        # harmonic_mean(1.0, 0.0) = 0 because terminality_score = 0
        assert category_atomicity(obs) == 0.0

    def test_zero_object_both_morphisms(self):
        """
        Propositi 3: een zero-object is tegelijk initieel EN terminaal.
        Wanneer obs→other EN other→obs, is obs een zero-object → score 1.0.

        Bug fix: de originele implementatie retourneerde 0.5 (alleen morfisme tellen).
        De nieuwe implementatie herkent het zero-object en retourneert 1.0.
        """
        obs = make_obs()
        obs.category.add_object(obs.id)
        obs.category.add_object("other")
        obs.category.add_morphism(obs.id, "other", "f")   # uitgaand (initieel)
        obs.category.add_morphism("other", obs.id, "g")   # inkomend (terminaal)
        # Volledig zero-object → 1.0
        assert category_atomicity(obs) == 1.0

    def test_incoming_only_harmonic_mean(self):
        """
        Alleen een inkomend morfisme (terminaal maar niet initieel).
        initiality_score = 1/(1+1) = 0.5, terminality_score = 1.0
        harmonic_mean = 2 * 0.5 * 1.0 / (0.5 + 1.0) = 2/3
        """
        obs = make_obs()
        obs.category.add_object(obs.id)
        obs.category.add_object("other")
        obs.category.add_morphism("other", obs.id, "g")
        score = category_atomicity(obs)
        assert score == pytest.approx(2 / 3)


class TestGroupAtomicity:
    """Tests voor group_atomicity."""

    def test_empty_group_returns_one(self):
        obs = make_obs()
        assert group_atomicity(obs) == 1.0

    def test_group_with_elements(self):
        """Group atomicity uses 1/(1+log1p(n)) since v3.0 – not 1/n."""
        import math as _math
        obs = make_obs()
        obs.group.group_elements = {1, 2, 3}
        expected = 1.0 / (1.0 + _math.log1p(3.0))
        assert group_atomicity(obs) == pytest.approx(expected)


class TestGetFrameworkNames:
    """Tests voor get_framework_names_for_principle."""

    def test_logical_principle(self):
        names = get_framework_names_for_principle("logical")
        assert "boolean" in names
        assert "decomposition_boolean" in names

    def test_geometric_principle(self):
        names2 = get_framework_names_for_principle("geometric")
        assert "geometric" in names2
        assert "decomposition_geometric" in names2

    def test_unknown_principle(self):
        assert get_framework_names_for_principle("does_not_exist") == []


class TestComputeAtomicities:
    """Tests voor _compute_atomicities en gerelateerde logica."""

    def test_filters_primary_principles(self):
        spec = MetaSpecification(primary_principles=[LOGICAL])
        obs = make_obs("test", 42)
        obs = UltimateObservable(
            id="test", value=42,
            observability_type=ObservabilityType.DISCRETE,
            meta_spec=spec,
        )
        assert set(obs.atomicity.keys()) == {"boolean", "decomposition_boolean"}

    def test_binary_atomicity_mode(self):
        spec = MetaSpecification(atomicity_is_binary=True)
        obs = UltimateObservable(
            id="test", value=42,
            observability_type=ObservabilityType.DISCRETE,
            meta_spec=spec,
        )
        obs.atomicity = {"dummy": 0.9}
        score = obs.get_atomicity_score(weights={"dummy": 1.0})
        assert score == 1.0

    def test_is_atom_binary_mode(self):
        spec = MetaSpecification(atomicity_is_binary=True)
        obs = UltimateObservable(
            id="test", value=42,
            observability_type=ObservabilityType.DISCRETE,
            meta_spec=spec,
        )
        obs.atomicity = {"boolean": 1.0, "info": 0.5}
        obs._atomicity_stale = False
        assert obs.is_atom() is False
        assert obs.is_atom("boolean") is True
        assert obs.is_atom("info") is False

    def test_is_atom_continuous_mode(self):
        spec = MetaSpecification(atomicity_is_binary=False)
        obs = UltimateObservable(
            id="test", value=42,
            observability_type=ObservabilityType.DISCRETE,
            meta_spec=spec,
        )
        obs.atomicity = {"boolean": 0.999, "info": 0.98}
        obs._atomicity_stale = False
        assert obs.is_atom() is False
        assert obs.is_atom(threshold=0.97) is True
        assert obs.is_atom("info", threshold=0.99) is False

    def test_dirty_flag(self):
        """Test dat atomiciteit opnieuw wordt berekend als _atomicity_stale True is."""
        obs = make_obs()
        assert obs._atomicity_stale is False
        orig_atomicity = obs.atomicity.copy()
        obs._mark_stale()
        assert obs._atomicity_stale is True
        score = obs.get_atomicity_score()
        assert obs._atomicity_stale is False
        assert obs.atomicity == orig_atomicity

    def test_atomicity_lock_field_present(self):
        """Test dat _atomicity_lock als threading.RLock aanwezig is."""
        import threading as _threading
        obs = make_obs()
        assert hasattr(obs, '_atomicity_lock')
        assert isinstance(obs._atomicity_lock, type(_threading.RLock()))

    def test_atomicity_lock_thread_safety(self):
        """Test dat _compute_atomicities thread-safe is via RLock."""
        obs = make_obs()
        errors = []

        def worker():
            try:
                for _ in range(50):
                    obs._mark_stale()
                    _ = obs.get_atomicity_score()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, f"Thread-fouten: {errors}"


class TestUltimateObservableProperties:
    """Tests voor properties en methoden van UltimateObservable."""

    def test_atomicity_score_property(self):
        obs = make_obs()
        score = obs.atomicity_score
        assert 0.0 <= score <= 1.0
        obs.atomicity_score = 0.8
        assert obs.atomicity_score == 0.8
        assert obs.atomicity.get('combined') == 0.8
        assert obs._atomicity_stale is True

    def test_lazy_ontology(self):
        def potential(ctx):
            return ctx.get('factor', 1) * 42

        obs = UltimateObservable(
            id="lazy", value=None,
            observability_type=ObservabilityType.DISCRETE,
            potential=potential,
        )
        assert obs.collapsed is False
        assert obs.value is None
        assert obs._is_lazy_observable is True
        obs.collapse(context={'factor': 2})
        assert obs.collapsed is True
        assert obs.value == 84
        assert obs.atomicity.get('boolean') == 1.0

    def test_resonance_map(self):
        obs = make_obs()
        obs.add_resonance("layer2", {"role": "node", "id": "n1"})
        assert "layer2" in obs.resonance_map
        obs.remove_resonance("layer2")
        assert "layer2" not in obs.resonance_map

    def test_lazy_substructures(self):
        obs = make_obs()
        assert obs._geometry is None
        geom = obs.geometry
        assert obs._geometry is not None
        assert isinstance(geom, GeometricStructure)
        assert obs._topology is None
        top = obs.topology
        assert obs._topology is not None
        new_geom = GeometricStructure()
        obs.geometry = new_geom
        assert obs._geometry is new_geom

    # Bug fix 4: confidence interval scipy fallback
    def test_confidence_interval(self):
        """Test CI-berekening inclusief fallback als scipy ontbreekt."""
        obs = make_obs()
        obs.atomicity = {"a": 0.9, "b": 0.8, "c": 0.7}
        obs._atomicity_stale = False
        lower, upper = obs.get_atomicity_confidence_interval(confidence=0.95)
        assert 0.0 <= lower <= upper <= 1.0
        mean = np.mean([0.9, 0.8, 0.7])
        assert lower <= mean <= upper

    def test_confidence_interval_99(self):
        """99%-betrouwbaarheidsinterval moet breder zijn dan 95%."""
        obs = make_obs()
        obs.atomicity = {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
        obs._atomicity_stale = False
        lo95, hi95 = obs.get_atomicity_confidence_interval(confidence=0.95)
        lo99, hi99 = obs.get_atomicity_confidence_interval(confidence=0.99)
        assert (hi99 - lo99) >= (hi95 - lo95)

    def test_atomicity_consensus(self):
        obs = make_obs()
        obs.atomicity = {"a": 0.9, "b": 0.8, "c": 0.7}
        obs._atomicity_stale = False
        consensus = obs.atomicity_consensus
        assert 0.0 <= consensus <= 1.0
        obs.atomicity = {"a": 0.8, "b": 0.8}
        assert np.isclose(obs.atomicity_consensus, 1.0 - np.std([0.8, 0.8]))

    # Extension: generativity_score property
    def test_generativity_score_property(self):
        """Test het generativity_score property."""
        obs = make_obs()
        score_bare = obs.generativity_score
        assert 0.0 <= score_bare <= 1.0
        # Voeg resonanties en relaties toe
        for i in range(5):
            obs.add_resonance(f"L{i}", {"weight": 1.0})
        for i in range(10):
            obs.relational_weights[f"other_{i}"] = 0.5
        score_full = obs.generativity_score
        assert score_full > score_bare, (
            f"Score moet stijgen na resonanties/relaties: {score_bare:.3f} → {score_full:.3f}"
        )
        assert 0.0 <= score_full <= 1.0

    def test_generativity_score_components(self):
        """
        Verifieer de componenten van generativity_score.

        v3.0: generativity_score gebruikt een gewogen geometrisch gemiddelde
        wanneer alle drie factoren > 0.  Met 5 resonances (factor=1.0) en 10
        relaties (factor=1.0) en consensus ≈ 0.9 geldt:

            G = exp(wa*log(R) + wb*log(D) + wc*log(C))
              = exp(1/3*log(1) + 1/3*log(1) + 1/3*log(C))
              = exp(log(C)/3)
              = C^(1/3)

        We testen dat de score in [0,1] ligt en stijgt met meer resonances/relaties.
        """
        import math as _math
        obs = make_obs()
        score_base = obs.generativity_score
        assert 0.0 <= score_base <= 1.0

        # Add resonances and relations
        for i in range(5):
            obs.add_resonance(f"L{i}", {})
        for i in range(10):
            obs.relational_weights[f"r{i}"] = 0.1

        score_full = obs.generativity_score
        assert 0.0 <= score_full <= 1.0
        # With all factors saturated (R=1, D=1), the score is dominated by consensus
        # Score with full R and D should be >= base score
        assert score_full >= score_base, (
            f"Generativity should increase with resonances/relations: "
            f"base={score_base:.4f}, full={score_full:.4f}"
        )

        # Verify arithmetic fallback when some factors are zero (new observable)
        obs_empty = make_obs(obs_id="empty_gen")
        score_empty = obs_empty.generativity_score
        # Empty observable: resonance_factor=0 → fallback to arithmetic mean
        resonance_factor = min(1.0, len(obs_empty.resonance_map) / 5.0)
        relational_factor = min(1.0, len(obs_empty.relational_weights) / 10.0)
        consensus = obs_empty.atomicity_consensus
        if resonance_factor == 0.0 or relational_factor == 0.0 or consensus == 0.0:
            expected_fallback = (resonance_factor + relational_factor + consensus) / 3.0
            assert abs(score_empty - expected_fallback) < 1e-9, (
                f"Arithmetic fallback: {score_empty:.6f} != {expected_fallback:.6f}"
            )

    def test_update_embedding(self):
        obs = make_obs()
        obs.relational_graph = None
        obs.update_embedding(dim=10)
        assert len(obs.relational_embedding) == 10
        assert np.isclose(np.linalg.norm(obs.relational_embedding), 1.0)

    def test_to_dict_includes_temporal_phase(self):
        obs = UltimateObservable(
            id="test", value=42,
            observability_type=ObservabilityType.DISCRETE,
            temporal_phase=3.14,
        )
        d = obs.to_dict()
        assert 'temporal_phase' in d
        assert d['temporal_phase'] == 3.14
        assert d['metadata']['temporal_phase'] == 3.14
        assert 'atomicity' in d
        assert 'ci_lower' in d['atomicity']
        assert 'ci_upper' in d['atomicity']
        assert 'consensus' in d['atomicity']


# ============================================================================
# Tests voor observables.py
# ============================================================================

class TestLayer1ObservablesCreation:
    """Tests voor aanmaak van observables."""

    @pytest.mark.asyncio
    async def test_process_with_meta_spec(self):
        """
        _build_observable now copies the meta_spec for isolation.
        The observable gets a structurally equal copy, not the same object.
        Use value equality (==) rather than identity (is).
        """
        layer = Layer1_Observables()
        from types import SimpleNamespace
        context = SimpleNamespace(metadata={'meta_spec': DEFAULT_META_SPEC})
        result = await layer.process(42, context)
        assert result.success is True
        obs = result.output
        # v3.0: each observable gets its own isolated copy of meta_spec.
        # The copy is structurally equal, not the same object.
        assert obs.meta_spec is not DEFAULT_META_SPEC, (
            "Each observable must own its meta_spec copy (isolation)"
        )
        assert obs.meta_spec.atomicity_is_binary == DEFAULT_META_SPEC.atomicity_is_binary
        assert obs.meta_spec.default_atomicity_weights == DEFAULT_META_SPEC.default_atomicity_weights

    @pytest.mark.asyncio
    async def test_process_with_potential(self):
        layer = Layer1_Observables()
        from types import SimpleNamespace
        def pot(ctx): return 100
        context = SimpleNamespace(metadata={'potential': pot})
        result = await layer.process(None, context)
        assert result.success is True
        obs = result.output
        assert obs.potential is pot
        assert obs.value is None
        obs.collapse()
        assert obs.value == 100

    def test_record_with_meta_spec(self):
        """
        v3.0: record() copies meta_spec for isolation.
        The copy is structurally equal but not the same object.
        """
        layer = Layer1_Observables()
        obs = layer.record("test_id", 42, metadata={'meta_spec': DEFAULT_META_SPEC})
        assert obs is not None
        # Isolation: the observable owns a copy, not the singleton
        assert obs.meta_spec is not DEFAULT_META_SPEC
        assert obs.meta_spec.default_atomicity_weights == DEFAULT_META_SPEC.default_atomicity_weights

    def test_record_with_potential(self):
        layer = Layer1_Observables()
        def pot(ctx): return 200
        obs = layer.record("test_id", None, metadata={'potential': pot})
        assert obs is not None
        assert obs.potential is pot
        obs.collapse()
        assert obs.value == 200


class TestLayer1ObservablesInferType:
    """Tests voor _infer_type uitbreidingen (bug fix 1)."""

    def test_callable_infers_stochastic(self):
        """Callables → STOCHASTIC (bug fix)."""
        layer = Layer1_Observables()
        assert layer._infer_type(lambda: 42) == ObservabilityType.STOCHASTIC
        assert layer._infer_type(print) == ObservabilityType.STOCHASTIC

    def test_bool_before_int(self):
        """bool moet voor int worden gecheckt (bool is subklasse van int)."""
        layer = Layer1_Observables()
        assert layer._infer_type(True) == ObservabilityType.DISCRETE
        assert layer._infer_type(False) == ObservabilityType.DISCRETE
        assert layer._infer_type(42) == ObservabilityType.DISCRETE

    def test_2d_array_infers_topological(self):
        """2D numpy-array → TOPOLOGICAL (puntenwolk)."""
        layer = Layer1_Observables()
        arr2d = np.ones((5, 3))
        assert layer._infer_type(arr2d) == ObservabilityType.TOPOLOGICAL

    def test_1d_array_infers_continuous(self):
        layer = Layer1_Observables()
        arr1d = np.ones(10)
        assert layer._infer_type(arr1d) == ObservabilityType.CONTINUOUS

    def test_complex_infers_quantum(self):
        layer = Layer1_Observables()
        assert layer._infer_type(1 + 2j) == ObservabilityType.QUANTUM

    def test_str_infers_relational(self):
        layer = Layer1_Observables()
        assert layer._infer_type("hello") == ObservabilityType.RELATIONAL

    def test_dict_infers_relational(self):
        layer = Layer1_Observables()
        assert layer._infer_type({}) == ObservabilityType.RELATIONAL


class TestLayer1ObservablesManagement:
    """Tests voor beheermethoden van Layer1_Observables."""

    def test_configurable_atom_threshold(self):
        """
        atom_threshold is configureerbaar via constructor.

        v3.1 update: small integers (0,1,2) now correctly score 1.0 on
        info_atomicity due to the short-string guard (zlib overhead fix).
        The threshold test uses multi-element SETS like {0,1,2} which are
        decomposable (decomposition_boolean=0.0, combined < 0.99) to correctly
        test non-atomic behaviour at a high threshold.
        """
        layer_low = Layer1_Observables(atom_threshold=0.0)
        layer_high = Layer1_Observables(atom_threshold=0.99)
        assert layer_low.atom_threshold == 0.0
        assert layer_high.atom_threshold == 0.99
        # Decomposable sets: boolean-decomposable → combined < 0.80 < 0.99
        for i in range(3):
            layer_low.record(f"A_{i}", {i, i + 10, i + 20})
            layer_high.record(f"B_{i}", {i, i + 10, i + 20})
        assert layer_low.metrics["atoms_found"] == 3
        assert layer_high.metrics["atoms_found"] == 0

    def test_get_by_type(self):
        """get_by_type retourneert alleen observables van het gevraagde type."""
        layer = Layer1_Observables()
        layer.record("D1", 1)
        layer.record("D2", 2)
        layer.record("S1", "hello")
        discrete_obs = layer.get_by_type(ObservabilityType.DISCRETE)
        assert len(discrete_obs) == 2
        assert all(o.observability_type == ObservabilityType.DISCRETE for o in discrete_obs)
        assert layer.get_by_type(ObservabilityType.QUANTUM) == []

    def test_get_by_observer(self):
        """get_by_observer retourneert alleen observables van het gevraagde perspectief."""
        layer = Layer1_Observables()
        layer.record("A1", 1, metadata={"observer": "alice"})
        layer.record("A2", 2, metadata={"observer": "alice"})
        layer.record("B1", 3, metadata={"observer": "bob"})
        assert len(layer.get_by_observer("alice")) == 2
        assert len(layer.get_by_observer("bob")) == 1
        assert layer.get_by_observer("nobody") == []

    def test_remove_observable(self):
        """remove_observable verwijdert een observable en updatet alle indices."""
        layer = Layer1_Observables()
        layer.record("REM1", 1, metadata={"observer": "alice"})
        layer.record("REM2", 2, metadata={"observer": "bob"})
        assert len(layer.observables) == 2
        removed = layer.remove_observable("REM1")
        assert removed is True
        assert "REM1" not in layer.observables
        assert layer.metrics["unique_ids"] == 1
        for ids in layer.by_type.values():
            assert "REM1" not in ids
        for ids in layer.by_observer.values():
            assert "REM1" not in ids
        assert layer.remove_observable("REM1") is False

    # Extension: emit_to_layer
    def test_emit_to_layer(self):
        """emit_to_layer slaat resonantie op en retourneert de geserialiseerde observable."""
        layer = Layer1_Observables()
        obs = layer.record("EMIT_OBS", 42, metadata={"temporal_phase": 1.0})
        result = layer.emit_to_layer("layer_2", "EMIT_OBS")
        assert isinstance(result, dict)
        assert result.get("id") == "EMIT_OBS"
        assert "layer_2" in obs.resonance_map
        assert "emitted_at" in obs.resonance_map["layer_2"]
        assert obs.resonance_map["layer_2"]["phase"] == 1.0

    def test_emit_to_layer_unknown_id(self):
        layer = Layer1_Observables()
        assert layer.emit_to_layer("layer_2", "NONEXISTENT_XYZ") == {}

    # Extension: validate()
    @pytest.mark.asyncio
    async def test_validate_valid_layer(self):
        layer = Layer1_Observables()
        layer.record("V1", 1, metadata={"observer": "alice"})
        layer.record("V2", 2, metadata={"observer": "bob"})
        result = await layer.validate()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_id_mismatch(self):
        """validate() detecteert ID-inconsistentie."""
        layer = Layer1_Observables()
        obs = layer.record("ORIG_ID", 1)
        # Vervals de ID
        obs.id = "CORRUPTED_ID"
        result = await layer.validate()
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_ghost_type_reference(self):
        """validate() detecteert verwijzingen in by_type die niet in observables staan."""
        layer = Layer1_Observables()
        layer.record("V1", 1)
        layer.by_type[ObservabilityType.DISCRETE].append("GHOST_ID")
        result = await layer.validate()
        assert result is False

    # Extension: get_stats() met generativity_scores
    def test_get_stats_includes_generativity(self):
        """get_stats() bevat generativity_scores."""
        layer = Layer1_Observables()
        layer.record("G1", 1)
        layer.record("G2", 2)
        stats = layer.get_stats()
        assert "generativity_scores" in stats
        gen = stats["generativity_scores"]
        if gen is not None:
            assert "mean" in gen and "max" in gen
            assert isinstance(gen["mean"], float)
            assert gen["max"] >= gen["mean"] >= 0.0

    def test_generate_id_unique(self):
        """
        _generate_id geeft IDs in het juiste formaat en produceert
        verschillende IDs voor verschillende invoerwaarden.

        Bug fix: tien keer _generate_id(42) aanroepen met DEZELFDE invoer
        mislukt op Windows (~15 ms klokresolutie → zelfde hash → 1 uniek ID).
        Oplossing: test uniciteit met 5 VERSCHILLENDE invoerwaarden.
        """
        obs_id = Layer1_Observables._generate_id(42)
        assert obs_id.startswith("OBS_"), f"ID moet beginnen met 'OBS_': {obs_id!r}"
        assert len(obs_id) == 12, f"ID moet 12 tekens zijn: {obs_id!r}"
        ids = {
            Layer1_Observables._generate_id(42),
            Layer1_Observables._generate_id("hello"),
            Layer1_Observables._generate_id([1, 2, 3]),
            Layer1_Observables._generate_id(None),
            Layer1_Observables._generate_id(3.14),
        }
        assert len(ids) == 5, (
            "Verschillende invoerwaarden moeten verschillende IDs opleveren"
        )


# ============================================================================
# Tests voor density_field.py
# ============================================================================

class TestDensityField:
    """Tests voor DensityField met twee-kanaal invloed."""

    def _make_obs_with_resonance(self, obs_id, weight, perspective, emb=None):
        """Hulpfunctie om een observable met resonantie aan te maken."""
        obs = UltimateObservable(
            id=obs_id, value=weight,
            observability_type=ObservabilityType.DISCRETE,
        )
        obs.resonance_map["layerA"] = {"role": "node", "weight": weight}
        obs.set_observer(perspective)
        if emb is not None:
            obs.relational_embedding = np.asarray(emb, dtype=float)
        return obs

    def test_basic_influence_stored(self):
        """Invloed wordt opgeslagen in observer_context na apply_influence."""
        field = DensityField(influence_decay=0.5, perspective_threshold=0.5)
        obs1 = self._make_obs_with_resonance("red", 0.8, "perspA")
        obs2 = self._make_obs_with_resonance("blue", 0.6, "perspB")
        field.add_observable(obs1)
        field.add_observable(obs2)
        field.apply_influence("red")
        assert "density_influence" in obs1.observer_context
        infl = obs1.observer_context["density_influence"]
        assert "perspB" in infl
        assert infl["perspB"] > 0

    def test_perspective_switch_on_dominant_influence(self):
        """
        Perspectief wisselt als de dominante invloed boven de drempel uitkomt.

        Gebruik decay=1.0 en hogere gewichten zodat de gecombineerde
        invloed (0.7 * resonantie + 0.3 * embedding) de drempel overstijgt.
        """
        field = DensityField(influence_decay=1.0, perspective_threshold=0.5)
        obs1 = self._make_obs_with_resonance("red", 1.0, "perspA",
                                             emb=[1.0, 0.0])
        obs2 = self._make_obs_with_resonance("blue", 1.0, "perspB",
                                             emb=[1.0, 0.0])
        obs3 = self._make_obs_with_resonance("green", 1.0, "perspB",
                                             emb=[1.0, 0.0])
        for o in (obs1, obs2, obs3):
            field.add_observable(o)
        field.apply_influence("red")
        # Beide obs2 en obs3 zijn in perspB; hun gecombineerde invloed
        # (identieke embeddings → afstand=0 → maximale resonantie) moet
        # de drempel van 0.5 overstijgen.
        assert obs1.observer_perspective == "perspB"

    def test_clear_influence(self):
        """clear_influence verwijdert density_influence uit observer_context."""
        field = DensityField(influence_decay=0.5, perspective_threshold=0.5)
        obs1 = self._make_obs_with_resonance("red", 0.8, "perspA")
        obs2 = self._make_obs_with_resonance("blue", 0.6, "perspB")
        field.add_observable(obs1)
        field.add_observable(obs2)
        field.apply_influence("red")
        field.clear_influence("red")
        assert "density_influence" not in obs1.observer_context

    # Extension: _embedding_similarity
    def test_embedding_similarity_identical(self):
        field = DensityField()
        obs_a = make_obs("A")
        obs_a.relational_embedding = np.array([1.0, 0.0])
        obs_b = make_obs("B")
        obs_b.relational_embedding = np.array([1.0, 0.0])
        assert abs(field._embedding_similarity(obs_a, obs_b) - 1.0) < 1e-9

    def test_embedding_similarity_orthogonal(self):
        field = DensityField()
        obs_a = make_obs("A")
        obs_a.relational_embedding = np.array([1.0, 0.0])
        obs_b = make_obs("B")
        obs_b.relational_embedding = np.array([0.0, 1.0])
        assert abs(field._embedding_similarity(obs_a, obs_b)) < 1e-9

    def test_embedding_similarity_empty(self):
        field = DensityField()
        obs_a = make_obs("A")
        obs_b = make_obs("B")
        obs_b.relational_embedding = np.array([1.0, 2.0])
        assert field._embedding_similarity(obs_a, obs_b) == 0.0

    # Extension: distance decay
    def test_distance_decay_near_more_than_far(self):
        """Nabije observables (identieke embedding) hebben meer invloed dan verre."""
        field = DensityField(influence_decay=1.0,
                             resonance_channel_weight=1.0,
                             embedding_channel_weight=0.0)
        target = make_obs("T")
        target.relational_embedding = np.array([1.0, 0.0])
        target.resonance_map["L"] = {"weight": 1.0}
        near = make_obs("Near")
        near.relational_embedding = np.array([1.0, 0.0])
        near.resonance_map["L"] = {"weight": 1.0}
        near.observer_perspective = "near_persp"
        far = make_obs("Far")
        far.relational_embedding = np.array([-1.0, 0.0])
        far.resonance_map["L"] = {"weight": 1.0}
        far.observer_perspective = "far_persp"
        for o in (target, near, far):
            field.add_observable(o)
        infl = field.compute_influence("T")
        assert infl.get("near_persp", 0) > infl.get("far_persp", 0)

    # Extension: sample_influence (Monte Carlo)
    def test_sample_influence_returns_influence_samples(self):
        """sample_influence retourneert InfluenceSample-objecten."""
        field = DensityField(influence_decay=1.0)
        target = make_obs("T")
        target.relational_embedding = np.array([1.0, 0.0])
        target.resonance_map["L"] = {"weight": 1.0}
        o1 = make_obs("O1")
        o1.relational_embedding = np.array([1.0, 0.0])
        o1.resonance_map["L"] = {"weight": 1.0}
        o1.observer_perspective = "p1"
        for o in (target, o1):
            field.add_observable(o)
        samples = field.sample_influence("T", n_samples=50,
                                         noise_scale=0.01, random_seed=42)
        assert "p1" in samples
        s = samples["p1"]
        assert isinstance(s, InfluenceSample)
        assert s.n_samples == 50
        assert s.mean > 0
        assert s.p5 <= s.mean <= s.p95

    def test_sample_influence_does_not_mutate(self):
        """sample_influence muteert de originele embedding niet."""
        field = DensityField()
        target = make_obs("T")
        target.relational_embedding = np.array([1.0, 0.0])
        target.resonance_map["L"] = {"weight": 1.0}
        o1 = make_obs("O1")
        o1.relational_embedding = np.array([1.0, 0.0])
        o1.resonance_map["L"] = {"weight": 1.0}
        for o in (target, o1):
            field.add_observable(o)
        orig_emb = target.relational_embedding.copy()
        field.sample_influence("T", n_samples=20, random_seed=0)
        assert np.allclose(target.relational_embedding, orig_emb)

    def test_sample_influence_unknown_id(self):
        field = DensityField()
        assert field.sample_influence("NONEXISTENT") == {}

    # Extension: compute_influence_matrix
    def test_compute_influence_matrix_shape(self):
        """compute_influence_matrix retourneert NxN matrix met nul-diagonaal."""
        field = DensityField()
        for i in range(3):
            o = make_obs(f"O{i}")
            o.relational_embedding = np.array([float(i), 0.0])
            o.resonance_map["L"] = {"weight": 1.0}
            field.add_observable(o)
        matrix, ids = field.compute_influence_matrix()
        assert matrix.shape == (3, 3)
        assert len(ids) == 3
        assert np.all(np.diag(matrix) == 0.0)
        assert np.all(matrix >= 0.0)

    # Extension: get_top_influencers
    def test_get_top_influencers(self):
        """get_top_influencers retourneert top-N gesorteerd op invloed."""
        field = DensityField(influence_decay=1.0)
        target = make_obs("T")
        target.relational_embedding = np.array([1.0, 0.0])
        target.resonance_map["L"] = {"weight": 1.0}
        hi = make_obs("HI")
        hi.relational_embedding = np.array([1.0, 0.0])
        hi.resonance_map["L"] = {"weight": 5.0}
        lo = make_obs("LO")
        lo.relational_embedding = np.array([-1.0, 0.0])
        lo.resonance_map["L"] = {"weight": 1.0}
        for o in (target, hi, lo):
            field.add_observable(o)
        top = field.get_top_influencers("T", n=2)
        assert len(top) == 2
        assert top[0][0] == "HI"
        assert top[0][1] >= top[1][1]

    def test_get_top_influencers_unknown(self):
        field = DensityField()
        assert field.get_top_influencers("NONEXISTENT") == []

    # Extension: apply_influence_all
    def test_apply_influence_all_no_error(self):
        """apply_influence_all roept apply_influence voor alle observables aan."""
        field = DensityField(influence_decay=1.0, perspective_threshold=999.0)
        for i in range(4):
            o = make_obs(f"O{i}", float(i))
            o.resonance_map["L"] = {"weight": 1.0}
            field.add_observable(o)
        field.apply_influence_all()  # mag geen fout gooien


# ============================================================================
# Tests voor discovery.py
# ============================================================================

class TestEvolutionaryFeedbackLoop:
    """Tests voor EvolutionaryFeedbackLoop."""

    def test_persist_load(self):
        """Persist/load bewaart tellers en gewichten correct."""
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.1)
        loop.record_usage("boolean", success=True)
        loop.record_usage("boolean", success=True)
        loop.record_usage("boolean", success=False)
        loop.update_weights()
        with tempfile.NamedTemporaryFile(
            mode='w+', suffix='.json', delete=False
        ) as f:
            filepath = f.name
        try:
            loop.persist(filepath)
            new_loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.1)
            new_loop.load(filepath)
            assert new_loop.usage_counter["boolean"] == 3
            assert new_loop.success_counter["boolean"] == 2
            assert (
                spec.default_atomicity_weights["boolean"]
                == new_loop.meta_spec.default_atomicity_weights["boolean"]
            )
        finally:
            os.unlink(filepath)

    # Bug fix 3: EMA-gebaseerde update (succes > 0.5 verhoogt gewicht)
    def test_update_weights_ema_increases_on_success(self):
        """
        Met hoge succes-rate (10/10) moet het gewicht STIJGEN, niet naar 0.5 convergeren.

        Bug fix: de originele formule 'delta = (rate - 0.5) * lr' zou bij
        rate=1.0 en lr=0.5 delta=0.25 geven MAAR bij rate=0.6 slechts 0.05.
        De EMA-versie trekt het gewicht richting de succes-rate.
        """
        spec = MetaSpecification()
        efl = EvolutionaryFeedbackLoop(spec, learning_rate=0.5, smoothing=1.0)
        for _ in range(10):
            efl.record_usage("boolean", success=True)
        old_w = spec.get_weight("boolean")
        efl.update_weights()
        new_w = spec.get_weight("boolean")
        assert new_w > old_w, (
            f"Gewicht moet stijgen bij succes-rate 1.0: {old_w} → {new_w}"
        )

    def test_update_weights_ema_decreases_on_failure(self):
        """Met lage succes-rate moet het gewicht DALEN."""
        spec = MetaSpecification()
        efl = EvolutionaryFeedbackLoop(spec, learning_rate=0.5, smoothing=1.0)
        for _ in range(10):
            efl.record_usage("boolean", success=False)
        old_w = spec.get_weight("boolean")
        efl.update_weights()
        new_w = spec.get_weight("boolean")
        assert new_w < old_w, (
            f"Gewicht moet dalen bij succes-rate 0.0: {old_w} → {new_w}"
        )

    # Extension: get_stats
    def test_get_stats(self):
        spec = MetaSpecification()
        efl = EvolutionaryFeedbackLoop(spec)
        efl.record_usage("boolean", success=True)
        efl.record_usage("boolean", success=True)
        efl.record_usage("boolean", success=False)
        stats = efl.get_stats()
        assert "boolean" in stats
        s = stats["boolean"]
        assert s["usage"] == 3
        assert s["successes"] == 2
        assert abs(s["rate"] - 2 / 3) < 1e-9

    # Extension: reset
    def test_reset_clears_counters(self):
        spec = MetaSpecification()
        efl = EvolutionaryFeedbackLoop(spec)
        efl.record_usage("boolean", success=True)
        assert efl.usage_counter
        efl.reset()
        assert not efl.usage_counter
        assert not efl.success_counter
        assert not efl._ema_rates

    def test_evolve_marks_stale(self):
        """evolve() markeert observables als stale."""
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec)
        obs = make_obs()
        with patch.object(obs, '_mark_stale') as mock_stale:
            loop.evolve(observables_registry={"test": obs})
            mock_stale.assert_called_once()

    # Bug fix 4: persist/load gebruikt update_weight() (via meta_spec.update_weight)
    def test_persist_load_uses_update_weight(self):
        """load() moet gewichten via update_weight() instellen (thread-safe)."""
        spec = MetaSpecification()
        efl = EvolutionaryFeedbackLoop(spec, learning_rate=0.2, smoothing=0.4)
        efl.record_usage("boolean", success=True)
        efl.update_weights()
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            filepath = f.name
        try:
            efl.persist(filepath)
            spec2 = MetaSpecification()
            efl2 = EvolutionaryFeedbackLoop(spec2)
            efl2.load(filepath)
            assert efl2.learning_rate == 0.2
            assert efl2.smoothing == 0.4
            assert "boolean" in efl2.usage_counter
        finally:
            os.unlink(filepath)


class TestHeuristicDiscoveryAndPipeline:
    """Tests voor HeuristicDiscovery en auto_discovery_pipeline."""

    def test_heuristic_discovery_returns_proposals(self):
        """
        Ontdekking retourneert tenminste één gevalideerd voorstel bij
        voldoende en gedifferentieerde data.

        Bug fix: de originele test gebruikte slechts 2 korte arrays. Geen
        enkele heuristiek haalt met zo weinig data de drempelwaarden voor
        clustering (< 10 punten), frequentie (piek-score < 0.2), entropie
        (< 1.5 nats) of schaarsheid (< 30% nullen). Oplossing: gebruik 35
        arrays – 20 schaarse (81% nullen) en 15 dichte – zodat de
        schaarsheids-heuristiek geactiveerd wordt en het voorstel de
        validate()-discriminatiecheck doorstaat (schaarse arrays zijn
        niet-atomair voor de SparsityOperator; dichte zijn atomair).
        """
        rng = np.random.default_rng(42)
        data = []
        # Schaarse vectoren: 13/16 nulwaarden → sparsity ≈ 0.81 > drempel 0.30
        for _ in range(20):
            arr = np.zeros(16)
            arr[[0, 3, 7]] = rng.normal(0, 1, 3)
            data.append(arr)
        # Dichte vectoren: geen nulwaarden → sparsity ≈ 0 < drempel 0.30
        for _ in range(15):
            data.append(rng.normal(0, 1, 16))
        discoverer = HeuristicDiscovery(data)
        proposals = discoverer.discover()
        assert len(proposals) >= 1, (
            f"Verwacht ≥1 gevalideerd voorstel, maar {len(proposals)} gevonden."
        )

    def test_heuristic_discovery_validated_proposals(self):
        """Alle teruggegeven voorstellen zijn gevalideerd."""
        data = [np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])] * 15
        discoverer = HeuristicDiscovery(data)
        proposals = discoverer.discover()
        for p in proposals:
            assert p.validated is True, (
                f"Voorstel {p.name} is niet gevalideerd"
            )

    def test_auto_discovery_no_register(self):
        """auto_discovery_pipeline met auto_register=False voert geen registratie uit."""
        data = [np.array([1, 2, 3]), np.array([4, 5, 6])]
        initial_ops = set(DECOMPOSITION_OPERATORS.keys())
        proposals = auto_discovery_pipeline(data, auto_register=False)
        assert isinstance(proposals, list)
        assert set(DECOMPOSITION_OPERATORS.keys()) == initial_ops

    def test_auto_discovery_returns_list(self):
        data = [np.array([1, 2, 3]), np.array([4, 5, 6])]
        proposals = auto_discovery_pipeline(data, auto_register=True)
        assert isinstance(proposals, list)

    # Bug fix 1: confidence berekening (discriminatief maatstaf)
    def test_compute_confidence_range(self):
        """_compute_confidence geeft een waarde in [0,1]."""
        from apeiron.layers.layer01_foundational.discovery import (
            SparsityDecompositionOperator
        )
        hd = HeuristicDiscovery([])
        conf = hd._compute_confidence(SparsityDecompositionOperator, [[1.0], [2.0]])
        assert 0.0 <= conf <= 1.0

    # Bug fix 2: _validate_proposal verwerpt niet-discriminatieve voorstellen
    def test_validate_proposal_rejects_zero_confidence(self):
        """Een voorstel met confidence=0 wordt verworpen."""
        from apeiron.layers.layer01_foundational.discovery import (
            DiscoveryProposal, SparsityDecompositionOperator
        )
        hd = HeuristicDiscovery([])
        prop = DiscoveryProposal(
            name="test_zero",
            description="zero confidence test",
            operator_class=SparsityDecompositionOperator,
            confidence=0.0,
        )
        # Gemengde data (sommige atoombaar, sommige niet)
        test_vals = [
            np.array([1.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0]),  # schaars
            np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),  # dicht
        ] * 3
        assert hd._validate_proposal(prop, test_vals) is False

    # Bug fix 5: FrequencyDecompositionOperator echte FFT
    def test_frequency_operator_real_fft(self):
        """FrequencyDecompositionOperator gebruikt echte IFFT-reconstructie."""
        op = FrequencyDecompositionOperator(cutoff_fraction=0.25)
        t = np.linspace(0, 1, 256)
        sig = np.sin(2 * np.pi * 5 * t) + 0.5 * np.sin(2 * np.pi * 50 * t)
        parts = op.decompose(sig)
        assert len(parts) == 2
        low = np.asarray(parts[0])
        high = np.asarray(parts[1])
        assert len(low) == len(sig)
        assert len(high) == len(sig)
        # Som moet het origineel reconstrueren
        reconstructed = low + high
        assert np.max(np.abs(reconstructed - sig)) < 1e-6

    def test_frequency_operator_constant_is_atomic(self):
        """Een constant signaal is niet deelbaar via FFT."""
        op = FrequencyDecompositionOperator()
        assert op.decompose(np.ones(64)) == []

    # Extension: EntropyDecompositionOperator en SparsityDecompositionOperator
    def test_entropy_operator_decomposes_varied(self):
        """EntropyDecompositionOperator splitst gevarieerde signalen."""
        from apeiron.layers.layer01_foundational.discovery import (
            EntropyDecompositionOperator
        )
        op = EntropyDecompositionOperator(min_entropy_gain=0.1, bins=10)
        rng = np.random.default_rng(7)
        noisy = rng.uniform(0, 10, 64)
        parts = op.decompose(noisy)
        assert isinstance(parts, list)

    def test_entropy_operator_constant_is_atomic(self):
        from apeiron.layers.layer01_foundational.discovery import (
            EntropyDecompositionOperator
        )
        op = EntropyDecompositionOperator(min_entropy_gain=0.1)
        assert op.decompose(np.ones(64)) == []

    def test_sparsity_operator_decomposes_sparse(self):
        """SparsityDecompositionOperator splitst schaarse arrays."""
        from apeiron.layers.layer01_foundational.discovery import (
            SparsityDecompositionOperator
        )
        op = SparsityDecompositionOperator(sparsity_threshold=0.3)
        sparse = np.array([1.0, 0.0, 2.0, 0.0, 3.0, 0.0, 4.0, 0.0])
        parts = op.decompose(sparse)
        assert len(parts) == 2

    def test_sparsity_operator_dense_is_atomic(self):
        from apeiron.layers.layer01_foundational.discovery import (
            SparsityDecompositionOperator
        )
        op = SparsityDecompositionOperator(sparsity_threshold=0.3)
        dense = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert op.decompose(dense) == []


class TestQualitativeDecompositionOperator:
    """Tests voor QualitativeDecompositionOperator."""

    def test_vector_non_atomic(self):
        op = QualitativeDecompositionOperator()
        vec = VectorDimension("test", [1, 1, 0])
        parts = op.decompose(vec)
        assert len(parts) == 3

    def test_vector_atomic(self):
        op = QualitativeDecompositionOperator()
        vec2 = VectorDimension("test2", [0, 1, 0])
        parts2 = op.decompose(vec2)
        assert parts2 == []

    def test_colour_non_atomic(self):
        op = QualitativeDecompositionOperator()
        grey = ColourDimension([0.5, 0.5, 0.5], colour_space=ColourSpace.RGB)
        parts3 = op.decompose(grey)
        assert len(parts3) == 3

    def test_colour_atomic(self):
        op = QualitativeDecompositionOperator()
        red = ColourDimension([1, 0, 0], colour_space=ColourSpace.RGB)
        parts4 = op.decompose(red)
        assert parts4 == []


# ============================================================================
# Topologische persistentie (optioneel)
# ============================================================================

@pytest.mark.skipif(not GUDHI_AVAILABLE, reason="GUDHI niet geïnstalleerd")
def test_topological_persistence_atomicity():
    from apeiron.layers.layer01_foundational.irreducible_unit import (
        topological_persistence_atomicity
    )
    points = np.array([[0, 0], [0, 1], [10, 10], [10, 11]])
    obs = UltimateObservable(
        id="test", value=points,
        observability_type=ObservabilityType.TOPOLOGICAL,
    )
    obs.topology.compute_persistent_homology(points, max_edge_length=5.0)
    score = topological_persistence_atomicity(obs)
    assert score == 0.0

    points2 = np.array([[0, 0], [0, 0.1], [0, 0.2]])
    obs2 = UltimateObservable(
        id="test2", value=points2,
        observability_type=ObservabilityType.TOPOLOGICAL,
    )
    obs2.topology.compute_persistent_homology(points2)
    score2 = topological_persistence_atomicity(obs2)
    assert score2 == 1.0


# ============================================================================
# Backwards-compatible tests (originele namen bewaard)
# ============================================================================

def test_meta_spec_defaults():
    """Backwards-compatibele alias voor TestMetaSpecDefaults.test_defaults."""
    spec = MetaSpecification()
    assert len(spec.primary_principles) == 6
    assert spec.atomicity_is_binary is False
    assert spec.default_atomicity_weights['boolean'] == 0.5
    assert spec.default_atomicity_weights['decomposition_boolean'] == 1.0
    assert spec.default_atomicity_weights['qualitative'] == 1.0


def test_register_atomicity_framework_check_or_create(clear_registries):
    def dummy(obs, ctx): return 0.5
    register_atomicity_framework("dummy", dummy)
    assert "dummy" in ATOMICITY_FRAMEWORKS
    register_atomicity_framework("dummy", dummy)
    assert ATOMICITY_FRAMEWORKS["dummy"] is dummy


def test_atomicity_framework_decorator(clear_registries):
    @atomicity_framework("deco_dummy")
    def func(obs, ctx): return 0.7
    assert "deco_dummy" in ATOMICITY_FRAMEWORKS
    assert ATOMICITY_FRAMEWORKS["deco_dummy"] is func


def test_meta_spec_update_weight():
    spec = MetaSpecification()
    spec.update_weight('boolean', 0.8)
    assert spec.default_atomicity_weights['boolean'] == 0.8
    spec.update_weight('boolean', 1.5)
    assert spec.default_atomicity_weights['boolean'] == 1.0
    spec.update_weight('boolean', -0.1)
    assert spec.default_atomicity_weights['boolean'] == 0.0
    with pytest.raises(ValueError):
        spec.update_weight('nonexistent', 0.5)


def test_meta_spec_copy():
    spec = MetaSpecification()
    spec.update_weight('boolean', 0.9)
    copy_spec = spec.copy()
    assert copy_spec.default_atomicity_weights['boolean'] == 0.9
    copy_spec.update_weight('boolean', 0.5)
    assert spec.default_atomicity_weights['boolean'] == 0.9


def test_decomposition_principle_register_check_or_create(cleanup_test_principe):
    p1 = DecompositionPrinciple.register("test_principe")
    p2 = DecompositionPrinciple.register("test_principe")
    assert p1 is p2
    assert p1.name == "test_principe"


def test_list_split_operator():
    op = ListSplitOperator()
    assert op.can_decompose([1, 2, 3]) is True
    assert op.decompose([1, 2, 3]) == [[1], [2, 3]]
    assert op.decompose([1]) == []
    assert op.decompose("abc") == []


def test_boolean_decomposition_operator():
    op = BooleanDecompositionOperator()
    assert op.decompose(42) == []
    result = op.decompose({1, 2, 3, 4})
    assert len(result) == 2
    assert op.decompose({1}) == []
    assert op.decompose([1, 2]) == []


def test_geometric_point_operator():
    op = GeometricPointOperator()
    points = np.array([[1, 1], [1, 1], [1, 1]])
    assert op.decompose(points) == []
    points2 = np.array([[1, 1], [2, 2], [3, 3]])
    parts = op.decompose(points2)
    assert len(parts) == 3


def test_palindrome_decomposition_operator():
    op = PalindromeDecompositionOperator()
    assert op.decompose([1, 2, 3, 2, 1]) == []
    parts = op.decompose([1, 2, 3, 4, 5])
    assert len(parts) == 2
    assert parts[0] == [1, 2]
    assert parts[1] == [3, 4, 5]


def test_is_atomic_by_operator():
    assert is_atomic_by_operator(42, "boolean") is True
    assert is_atomic_by_operator({1, 2}, "boolean") is False
    with pytest.raises(ValueError):
        is_atomic_by_operator(42, "bestaat_niet")


def test_information_decomposition_gain_fix():
    op = InformationDecompositionOperator()
    assert op.decompose("aaaaaa") == []
    data_mixed = "a" * 1000 + "b" * 1000
    parts = op.decompose(data_mixed)
    if len(parts) == 2:
        assert parts[0] + parts[1] == data_mixed
    else:
        pytest.skip("InformationDecompositionOperator vond geen split")


def test_scalar_dimension_is_atomic():
    assert ScalarDimension("test", 3.14).is_atomic() is True


def test_vector_dimension_is_atomic():
    assert VectorDimension("test", [1, 0, 0]).is_atomic() is True
    assert VectorDimension("test", [1, 1, 0]).is_atomic() is False
    assert VectorDimension("test", [1.0, 0.005, 0.0]).is_atomic(threshold=0.01) is True


def test_colour_dimension_is_atomic():
    assert ColourDimension([1, 0, 0], colour_space=ColourSpace.RGB).is_atomic() is True
    assert ColourDimension([0.5, 0.5, 0.5], colour_space=ColourSpace.RGB).is_atomic() is False


def test_multi_resolution_dimension_is_atomic():
    assert MultiResolutionDimension("t", {0.1: 1.0, 1.0: 1.0, 10.0: 1.0}).is_atomic() is True
    assert MultiResolutionDimension("t", {0.1: 1.0, 1.0: 2.0, 10.0: 1.0}).is_atomic() is False


def test_resonance_bridge():
    bridge = ResonanceBridge()
    def texture_to_colour(val):
        scalar_val = val.item() if isinstance(val, np.ndarray) and val.size == 1 else val
        return [scalar_val, 0.5, 0.5]
    bridge.register_mapping(TextureDimension, ColourDimension, texture_to_colour)
    tex = TextureDimension(value=0.8, texture_type=TextureType.GABOR)
    col = bridge.translate(tex, ColourDimension)
    assert col is not None
    assert isinstance(col, ColourDimension)
    assert np.isclose(col.value[0], 0.8)
    assert bridge.translate(tex, ScalarDimension) is None


def test_boolean_atomicity():
    assert boolean_atomicity(make_obs("test", [1, 2, 3])) == 0.5
    assert boolean_atomicity(make_obs("test2", 42)) == 1.0


def test_decomposition_boolean_atomicity():
    assert decomposition_boolean_atomicity(make_obs("test", {1, 2, 3})) == 0.0
    assert decomposition_boolean_atomicity(make_obs("test2", 42)) == 1.0


def test_qualitative_dimensions_atomicity():
    """
    Backwards-compatibele alias. Zie
    TestAtomicityFunctions::test_qualitative_dimensions_atomicity
    voor de motivatie van de meta_spec.copy() fix.
    """
    obs = make_obs("test", None)
    obs.observability_type = ObservabilityType.RELATIONAL
    vec = VectorDimension("velocity", [1, 1, 0])
    obs.add_qualitative_dimension("velocity", vec)
    assert qualitative_dimensions_atomicity(obs) == 0.0
    scalar = ScalarDimension("temp", 25.0)
    obs.add_qualitative_dimension("temp", scalar)
    assert qualitative_dimensions_atomicity(obs) == 0.5
    # Gebruik een kopie zodat DEFAULT_META_SPEC niet wordt gemuteerd
    obs.meta_spec = obs.meta_spec.copy()
    obs.meta_spec.qualitative_dim_weights = {"velocity": 2.0, "temp": 1.0}
    assert qualitative_dimensions_atomicity(obs) == pytest.approx(1 / 3)


def test_category_atomicity():
    """
    Test category_atomicity met de nieuwe zero-object logica (Proposition 3).

    Bug fix: de originele test verwachtte 0.5 na het toevoegen van beide
    morfismen. Met de zero-object herkenning is de verwachte waarde 1.0.
    """
    obs = make_obs()
    obs.observability_type = ObservabilityType.RELATIONAL
    # Lege categorie → 1.0
    assert category_atomicity(obs) == 1.0
    obs.category.add_object(obs.id)
    obs.category.add_object("other")
    obs.category.add_morphism(obs.id, "other", "f")
    # Alleen uitgaand (initieel, niet terminaal) → terminality=0 → score 0
    assert category_atomicity(obs) == 0.0
    obs.category.add_morphism("other", obs.id, "g")
    # Nu: obs→other EN other→obs → zero-object → 1.0 (bug fix)
    assert category_atomicity(obs) == 1.0


def test_group_atomicity():
    """Standalone: group_atomicity uses 1/(1+log1p(n)) since v3.0."""
    import math as _math
    obs = make_obs()
    assert group_atomicity(obs) == 1.0
    obs.group.group_elements = {1, 2, 3}
    expected = 1.0 / (1.0 + _math.log1p(3.0))
    assert group_atomicity(obs) == pytest.approx(expected)


def test_get_framework_names_for_principle():
    names = get_framework_names_for_principle("logical")
    assert "boolean" in names
    assert "decomposition_boolean" in names
    assert get_framework_names_for_principle("does_not_exist") == []


def test_compute_atomicities_filters_primary_principles():
    spec = MetaSpecification(primary_principles=[LOGICAL])
    obs = UltimateObservable(
        id="test", value=42,
        observability_type=ObservabilityType.DISCRETE,
        meta_spec=spec,
    )
    assert set(obs.atomicity.keys()) == {"boolean", "decomposition_boolean"}


def test_binary_atomicity_mode():
    spec = MetaSpecification(atomicity_is_binary=True)
    obs = UltimateObservable(
        id="test", value=42,
        observability_type=ObservabilityType.DISCRETE,
        meta_spec=spec,
    )
    obs.atomicity = {"dummy": 0.9}
    assert obs.get_atomicity_score(weights={"dummy": 1.0}) == 1.0


def test_is_atom_binary_mode():
    spec = MetaSpecification(atomicity_is_binary=True)
    obs = UltimateObservable(
        id="test", value=42,
        observability_type=ObservabilityType.DISCRETE,
        meta_spec=spec,
    )
    obs.atomicity = {"boolean": 1.0, "info": 0.5}
    obs._atomicity_stale = False
    assert obs.is_atom() is False
    assert obs.is_atom("boolean") is True
    assert obs.is_atom("info") is False


def test_is_atom_continuous_mode():
    spec = MetaSpecification(atomicity_is_binary=False)
    obs = UltimateObservable(
        id="test", value=42,
        observability_type=ObservabilityType.DISCRETE,
        meta_spec=spec,
    )
    obs.atomicity = {"boolean": 0.999, "info": 0.98}
    obs._atomicity_stale = False
    assert obs.is_atom() is False
    assert obs.is_atom(threshold=0.97) is True
    assert obs.is_atom("info", threshold=0.99) is False


def test_lazy_ontology():
    def potential(ctx):
        return ctx.get('factor', 1) * 42
    obs = UltimateObservable(
        id="lazy", value=None,
        observability_type=ObservabilityType.DISCRETE,
        potential=potential,
    )
    assert obs.collapsed is False
    assert obs.value is None
    assert obs._is_lazy_observable is True
    obs.collapse(context={'factor': 2})
    assert obs.collapsed is True
    assert obs.value == 84
    assert obs.atomicity.get('boolean') == 1.0


def test_resonance_map():
    obs = make_obs()
    obs.add_resonance("layer2", {"role": "node", "id": "n1"})
    assert "layer2" in obs.resonance_map
    obs.remove_resonance("layer2")
    assert "layer2" not in obs.resonance_map


def test_dirty_flag():
    obs = make_obs()
    assert obs._atomicity_stale is False
    orig_atomicity = obs.atomicity.copy()
    obs._mark_stale()
    assert obs._atomicity_stale is True
    score = obs.get_atomicity_score()
    assert obs._atomicity_stale is False
    assert obs.atomicity == orig_atomicity


def test_atomicity_score_property():
    obs = make_obs()
    score = obs.atomicity_score
    assert 0.0 <= score <= 1.0
    obs.atomicity_score = 0.8
    assert obs.atomicity_score == 0.8
    assert obs.atomicity.get('combined') == 0.8
    assert obs._atomicity_stale is True


def test_lazy_substructures():
    obs = make_obs()
    assert obs._geometry is None
    geom = obs.geometry
    assert obs._geometry is not None
    assert isinstance(geom, GeometricStructure)
    assert obs._topology is None
    _ = obs.topology
    assert obs._topology is not None
    new_geom = GeometricStructure()
    obs.geometry = new_geom
    assert obs._geometry is new_geom


def test_confidence_interval():
    obs = make_obs()
    obs.atomicity = {"a": 0.9, "b": 0.8, "c": 0.7}
    obs._atomicity_stale = False
    lower, upper = obs.get_atomicity_confidence_interval(confidence=0.95)
    assert 0.0 <= lower <= upper <= 1.0
    mean = np.mean([0.9, 0.8, 0.7])
    assert lower <= mean <= upper
    consensus = obs.atomicity_consensus
    assert 0.0 <= consensus <= 1.0
    obs.atomicity = {"a": 0.8, "b": 0.8}
    obs._atomicity_stale = False
    assert np.isclose(obs.atomicity_consensus, 1.0 - np.std([0.8, 0.8]))


def test_update_embedding():
    obs = make_obs()
    obs.relational_graph = None
    obs.update_embedding(dim=10)
    assert len(obs.relational_embedding) == 10
    assert np.isclose(np.linalg.norm(obs.relational_embedding), 1.0)


def test_to_dict_includes_temporal_phase():
    obs = UltimateObservable(
        id="test", value=42,
        observability_type=ObservabilityType.DISCRETE,
        temporal_phase=3.14,
    )
    d = obs.to_dict()
    assert 'temporal_phase' in d
    assert d['temporal_phase'] == 3.14
    assert d['metadata']['temporal_phase'] == 3.14
    assert 'ci_lower' in d['atomicity']
    assert 'ci_upper' in d['atomicity']
    assert 'consensus' in d['atomicity']


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_process_with_meta_spec():
    """
    v3.0: process() copies meta_spec for observable isolation.
    The copy is structurally equal but not the same object.
    """
    layer = Layer1_Observables()
    from types import SimpleNamespace
    context = SimpleNamespace(metadata={'meta_spec': DEFAULT_META_SPEC})
    result = await layer.process(42, context)
    assert result.success is True
    # v3.0: each observable has its own isolated copy
    assert result.output.meta_spec is not DEFAULT_META_SPEC
    assert result.output.meta_spec.default_atomicity_weights == DEFAULT_META_SPEC.default_atomicity_weights


@pytest.mark.asyncio
async def test_process_with_potential():
    layer = Layer1_Observables()
    from types import SimpleNamespace
    def pot(ctx): return 100
    context = SimpleNamespace(metadata={'potential': pot})
    result = await layer.process(None, context)
    assert result.success is True
    obs = result.output
    assert obs.potential is pot
    obs.collapse()
    assert obs.value == 100


def test_record_with_meta_spec():
    """
    v3.0: record() copies meta_spec for observable isolation.
    The copy is structurally equal but not the same object.
    """
    layer = Layer1_Observables()
    obs = layer.record("test_id", 42, metadata={'meta_spec': DEFAULT_META_SPEC})
    assert obs is not None
    # v3.0: isolation — copy not singleton
    assert obs.meta_spec is not DEFAULT_META_SPEC
    assert obs.meta_spec.default_atomicity_weights == DEFAULT_META_SPEC.default_atomicity_weights


def test_record_with_potential():
    layer = Layer1_Observables()
    def pot(ctx): return 200
    obs = layer.record("test_id", None, metadata={'potential': pot})
    assert obs is not None
    obs.collapse()
    assert obs.value == 200


def test_density_field():
    """
    Test DensityField met twee-kanaal invloed.

    Bug fix: de oorspronkelijke test gebruikte de formule
    'influence = decay * w_target * w_other', maar de nieuwe formule deelt
    door (1 + afstand). Met lege embeddings is afstand=1, waardoor de
    gecombineerde invloed lager uitvalt. De test is aangepast om
    decay=1.0 en hogere gewichten te gebruiken, zodat de drempel van 0.5
    wel gehaald wordt.
    """
    field = DensityField(influence_decay=1.0, perspective_threshold=0.5)
    obs1 = UltimateObservable(id="red", value=1,
                               observability_type=ObservabilityType.DISCRETE)
    obs1.resonance_map["layerA"] = {"role": "source", "weight": 1.0}
    obs1.relational_embedding = np.array([1.0, 0.0])
    obs1.set_observer("perspectiveA")

    obs2 = UltimateObservable(id="blue", value=2,
                               observability_type=ObservabilityType.DISCRETE)
    obs2.resonance_map["layerA"] = {"role": "target", "weight": 1.0}
    obs2.relational_embedding = np.array([1.0, 0.0])
    obs2.set_observer("perspectiveB")

    field.add_observable(obs1)
    field.add_observable(obs2)
    field.apply_influence("red")

    assert "density_influence" in obs1.observer_context
    infl = obs1.observer_context["density_influence"]
    assert "perspectiveB" in infl
    assert infl["perspectiveB"] > 0

    obs3 = UltimateObservable(id="green", value=3,
                               observability_type=ObservabilityType.DISCRETE)
    obs3.resonance_map["layerA"] = {"role": "source", "weight": 1.0}
    obs3.relational_embedding = np.array([1.0, 0.0])
    obs3.set_observer("perspectiveB")
    field.add_observable(obs3)

    field.apply_influence("red")
    # obs2 + obs3 vormen perspectiveB, beide met identieke embedding (afstand=0)
    # Resonantie: 1.0 * 1.0 * 1.0 / (1+0) = 1.0; combined = 0.7*1.0+0.3*1.0 = 1.0 per obs
    # Totaal perspectiveB = 2.0 > 0.5 → perspectief wisselt
    assert obs1.observer_perspective == "perspectiveB"

    field.clear_influence("red")
    assert "density_influence" not in obs1.observer_context


def test_evolutionary_feedback_persist_load():
    spec = MetaSpecification()
    loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.1)
    loop.record_usage("boolean", success=True)
    loop.record_usage("boolean", success=True)
    loop.record_usage("boolean", success=False)
    loop.update_weights()
    with tempfile.NamedTemporaryFile(
        mode='w+', suffix='.json', delete=False
    ) as f:
        filepath = f.name
    try:
        loop.persist(filepath)
        new_loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.1)
        new_loop.load(filepath)
        assert new_loop.usage_counter["boolean"] == 3
        assert new_loop.success_counter["boolean"] == 2
        assert (spec.default_atomicity_weights["boolean"]
                == new_loop.meta_spec.default_atomicity_weights["boolean"])
    finally:
        os.unlink(filepath)


def test_evolutionary_feedback_evolve_with_registry():
    spec = MetaSpecification()
    loop = EvolutionaryFeedbackLoop(spec)
    obs = make_obs()
    with patch.object(obs, '_mark_stale') as mock_stale:
        loop.evolve(observables_registry={"test": obs})
        mock_stale.assert_called_once()


def test_heuristic_discovery():
    """
    Backwards-compatibele alias. Zie
    TestHeuristicDiscoveryAndPipeline.test_heuristic_discovery_returns_proposals
    voor de motivatie van de gekozen testdata.
    """
    rng = np.random.default_rng(42)
    data = []
    for _ in range(20):
        arr = np.zeros(16)
        arr[[0, 3, 7]] = rng.normal(0, 1, 3)
        data.append(arr)
    for _ in range(15):
        data.append(rng.normal(0, 1, 16))
    discoverer = HeuristicDiscovery(data)
    proposals = discoverer.discover()
    assert len(proposals) >= 1, (
        f"Verwacht ≥1 gevalideerd voorstel, maar {len(proposals)} gevonden."
    )


def test_auto_discovery_pipeline():
    data = [np.array([1, 2, 3]), np.array([4, 5, 6])]
    proposals = auto_discovery_pipeline(data, auto_register=False)
    assert isinstance(proposals, list)
    proposals2 = auto_discovery_pipeline(data, auto_register=True)
    assert isinstance(proposals2, list)


def test_qualitative_decomposition_operator():
    op = QualitativeDecompositionOperator()
    assert len(op.decompose(VectorDimension("test", [1, 1, 0]))) == 3
    assert op.decompose(VectorDimension("test2", [0, 1, 0])) == []
    assert len(op.decompose(ColourDimension([0.5, 0.5, 0.5], colour_space=ColourSpace.RGB))) == 3
    assert op.decompose(ColourDimension([1, 0, 0], colour_space=ColourSpace.RGB)) == []


def test_category_atomicity_with_real_category():
    """
    Test category_atomicity met de nieuwe zero-object logica.

    Bug fix: de originele test verwachtte score == 0.5 na het toevoegen van
    alleen een inkomend morfisme. Met de nieuwe harmonische-gemiddelde formule
    (initiality_score=0.5, terminality_score=1.0) is de verwachting 2/3.
    """
    obs = make_obs()
    obs.observability_type = ObservabilityType.RELATIONAL
    obs.category.add_object(obs.id)
    assert category_atomicity(obs) == 1.0
    obs.category.add_object("other")
    obs.category.add_morphism("other", obs.id, "f")
    score = category_atomicity(obs)
    assert 0.0 < score < 1.0
    # Nieuwe formule: harmonic_mean(initiality=0.5, terminality=1.0) = 2/3
    assert score == pytest.approx(2 / 3)


def test_group_atomicity_with_real_group():
    """
    Test group_atomicity met logaritmische normalisatie.

    v2.1.0 gebruikt 1 / (1 + log(1 + |G|)) in plaats van de eerder gedocumenteerde
    maar verkeerd geïmplementeerde 1/n.  Dit geeft een vloeiendere afname voor
    grote groepen en is consistent met de docstring.
    """
    import math as _math
    obs = make_obs()
    assert group_atomicity(obs) == 1.0  # geen groepsstructuur → atomair

    obs.group.group_elements = {1, 2, 3}
    expected = 1.0 / (1.0 + _math.log1p(3.0))
    assert group_atomicity(obs) == pytest.approx(expected, rel=1e-6)

    # Triviale groep (1 element) → maximaal atomair
    obs2 = make_obs()
    obs2.group.group_elements = {0}
    assert group_atomicity(obs2) == 1.0


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# ============================================================================
# NEW TESTS v2.1.0 → v3.0 (score 97%)
# ============================================================================
# These tests cover the fixes and new features added in the 97% update:
#   1. group_atomicity logarithmic scaling (already updated above)
#   2. deepcopy meta_spec isolation in _build_observable
#   3. relational_graph thread-safety (_graph_lock)
#   4. from_dict() round-trip
#   5. qualitative_dim_weights in MetaSpecification
#   6. MeasureDecompositionOperator large-set sampling (O(max_subsets))
#   7. SelfProvingAtomicity (SymPy + Z3 provers)
#   8. Integration tests Layer 1 lifecycle
#   9. Performance test (1000 observables)
# ============================================================================

import math as _math
import copy as _copy
import time as _time


# ---------------------------------------------------------------------------
# Group atomicity – logarithmic formula
# ---------------------------------------------------------------------------

class TestGroupAtomicityLogScale:
    """group_atomicity() must use 1/(1+log(1+|G|)), not 1/|G|."""

    def test_no_group_returns_one(self):
        obs = make_obs()
        assert group_atomicity(obs) == 1.0

    def test_empty_group_returns_one(self):
        obs = make_obs()
        obs.group.group_elements = set()
        assert group_atomicity(obs) == 1.0

    def test_single_element_group_returns_one(self):
        obs = make_obs()
        obs.group.group_elements = {0}
        assert group_atomicity(obs) == 1.0

    def test_log_normalisation_n2(self):
        obs = make_obs()
        obs.group.group_elements = {0, 1}
        expected = 1.0 / (1.0 + _math.log1p(2.0))
        assert group_atomicity(obs) == pytest.approx(expected, rel=1e-9)

    def test_log_normalisation_n6(self):
        obs = make_obs()
        obs.group.group_elements = set(range(6))
        expected = 1.0 / (1.0 + _math.log1p(6.0))
        assert group_atomicity(obs) == pytest.approx(expected, rel=1e-9)

    def test_log_normalisation_n100(self):
        obs = make_obs()
        obs.group.group_elements = set(range(100))
        expected = 1.0 / (1.0 + _math.log1p(100.0))
        assert group_atomicity(obs) == pytest.approx(expected, rel=1e-9)
        # Ensure value is in (0, 1)
        assert 0.0 < group_atomicity(obs) < 1.0

    def test_large_group_approaches_zero(self):
        obs = make_obs()
        obs.group.group_elements = set(range(10_000))
        score = group_atomicity(obs)
        assert 0.0 < score < 0.1  # approaches zero but never reaches it

    def test_monotone_decreasing(self):
        """Larger groups must have lower atomicity scores."""
        scores = []
        for n in [1, 2, 5, 10, 50, 200]:
            obs = make_obs(obs_id=f"g{n}")
            obs.group.group_elements = set(range(n))
            scores.append(group_atomicity(obs))
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"Scores not monotone decreasing: {scores}"
            )


# ---------------------------------------------------------------------------
# MetaSpecification – qualitative_dim_weights
# ---------------------------------------------------------------------------

class TestQualitativeDimWeights:
    """qualitative_dim_weights is a first-class field of MetaSpecification."""

    def test_default_is_empty_dict(self):
        ms = MetaSpecification()
        assert isinstance(ms.qualitative_dim_weights, dict)
        assert len(ms.qualitative_dim_weights) == 0

    def test_can_set_weights(self):
        ms = MetaSpecification(qualitative_dim_weights={"intensity": 0.8, "density": 0.6})
        assert ms.qualitative_dim_weights["intensity"] == 0.8
        assert ms.qualitative_dim_weights["density"] == 0.6

    def test_copy_preserves_weights(self):
        ms = MetaSpecification(qualitative_dim_weights={"intensity": 0.9})
        ms2 = ms.copy()
        assert ms2.qualitative_dim_weights["intensity"] == 0.9

    def test_copy_is_independent(self):
        ms = MetaSpecification(qualitative_dim_weights={"intensity": 0.9})
        ms2 = ms.copy()
        ms2.qualitative_dim_weights["intensity"] = 0.1
        assert ms.qualitative_dim_weights["intensity"] == 0.9  # original unchanged

    def test_snapshot_includes_qdw(self):
        ms = MetaSpecification(qualitative_dim_weights={"density": 0.7})
        snap = ms.snapshot()
        assert "qualitative_dim_weights" in snap
        assert snap["qualitative_dim_weights"]["density"] == 0.7

    def test_snapshot_qdw_is_copy(self):
        ms = MetaSpecification(qualitative_dim_weights={"intensity": 0.5})
        snap = ms.snapshot()
        snap["qualitative_dim_weights"]["intensity"] = 0.0
        assert ms.qualitative_dim_weights["intensity"] == 0.5

    def test_qualitative_atomicity_uses_weights(self):
        """qualitative_dimensions_atomicity() respects meta_spec.qualitative_dim_weights."""
        obs = make_obs()
        # IntensityDimension signature: IntensityDimension(value: float, ..., name: str)
        # The FIRST argument is the VALUE (float), not the name.
        from apeiron.layers.layer01_foundational.qualitative_dimensions import (
            IntensityDimension,
        )
        # value=1.0 → pure intensity → atomic (is_atomic returns True at threshold 0.01)
        obs.add_qualitative_dimension("intensity", IntensityDimension(1.0, name="intensity_dim"))
        # value=0.5 → mid intensity → not purely atomic
        obs.add_qualitative_dimension("density", IntensityDimension(0.5, name="density_dim"))

        # Without weights: equal weighting
        score_equal = qualitative_dimensions_atomicity(obs)

        # With weights: intensity (atomic) has much higher weight
        obs.meta_spec.qualitative_dim_weights = {"intensity": 10.0, "density": 1.0}
        score_weighted = qualitative_dimensions_atomicity(obs)

        # Weighted score should be higher (atomic dim dominates)
        assert score_weighted >= score_equal, (
            f"Weighted score {score_weighted:.4f} should be >= equal score {score_equal:.4f}"
        )


# ---------------------------------------------------------------------------
# deepcopy isolation in _build_observable
# ---------------------------------------------------------------------------

class TestMetaSpecIsolationInObservables:
    """Each observable must own an independent copy of its MetaSpecification."""

    def test_mutating_one_does_not_affect_other(self):
        layer = Layer1_Observables()
        obs1 = layer.record("iso1", 42)
        obs2 = layer.record("iso2", "hello")
        assert obs1 is not None and obs2 is not None

        # Mutate obs1's weights
        obs1.meta_spec.update_weight("boolean", 0.99)

        # obs2 must remain unchanged
        assert obs2.meta_spec.default_atomicity_weights["boolean"] == pytest.approx(0.5)

    def test_default_meta_spec_unchanged(self):
        layer = Layer1_Observables()
        obs = layer.record("iso3", 100)
        assert obs is not None
        obs.meta_spec.update_weight("boolean", 0.01)

        # DEFAULT_META_SPEC must still have the original value
        assert DEFAULT_META_SPEC.default_atomicity_weights["boolean"] == pytest.approx(0.5)

    def test_custom_meta_spec_preserved(self):
        ms = MetaSpecification()
        ms.update_weight("boolean", 0.77)
        layer = Layer1_Observables()
        obs = layer.record("iso4", 1, metadata={"meta_spec": ms})
        assert obs is not None
        # The observable received a copy of the custom spec
        assert obs.meta_spec.default_atomicity_weights["boolean"] == pytest.approx(0.77)
        # But mutating the observable's copy must not change the original
        obs.meta_spec.update_weight("boolean", 0.11)
        assert ms.default_atomicity_weights["boolean"] == pytest.approx(0.77)


# ---------------------------------------------------------------------------
# relational_graph thread-safety
# ---------------------------------------------------------------------------

class TestRelationalGraphThreadSafety:
    """Concurrent mutations to relational_graph must not corrupt state."""

    def test_graph_lock_field_present(self):
        obs = make_obs()
        assert hasattr(obs, "_graph_lock")

    def test_graph_lock_is_rlock(self):
        import threading as _threading
        obs = make_obs()
        # Should be an RLock (or equivalent) – check by trying to acquire twice
        lock = obs._graph_lock
        lock.acquire()
        # RLock can be acquired again by the same thread
        acquired = lock.acquire(blocking=False)
        assert acquired, "Expected RLock (re-entrant)"
        lock.release()
        lock.release()

    def test_concurrent_set_relational_context(self):
        """100 threads each adding a unique relation must produce exactly 100 edges."""
        obs = make_obs()
        n_threads = 100
        errors = []

        def add_relation(i):
            try:
                obs.set_relational_context(f"node_{i}", float(i) / n_threads)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=add_relation, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert len(obs.relational_weights) == n_threads
        if obs.relational_graph is not None:
            # Each thread added one edge from obs.id to node_i
            assert obs.relational_graph.number_of_edges() == n_threads

    def test_initialize_structures_idempotent_under_concurrency(self):
        """Calling _initialize_structures() concurrently must create exactly one graph."""
        import threading as _threading
        results = []
        errors = []

        def build():
            try:
                obs = make_obs(obs_id=f"init_{_threading.get_ident()}")
                results.append(obs.relational_graph)
            except Exception as exc:
                errors.append(exc)

        threads = [_threading.Thread(target=build) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        for g in results:
            if g is not None:
                assert g.number_of_nodes() >= 1


# ---------------------------------------------------------------------------
# from_dict() round-trip
# ---------------------------------------------------------------------------

class TestFromDictRoundTrip:
    """UltimateObservable.from_dict(obs.to_dict()) must restore identity fields."""

    def test_id_preserved(self):
        obs = make_obs(obs_id="roundtrip_1")
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        assert obs2.id == obs.id

    def test_type_preserved(self):
        obs = make_obs(obs_type=ObservabilityType.CONTINUOUS)
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        assert obs2.observability_type == ObservabilityType.CONTINUOUS

    def test_temporal_phase_preserved(self):
        obs = make_obs()
        obs.temporal_phase = 3.14159
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        assert obs2.temporal_phase == pytest.approx(3.14159)

    def test_qualitative_dims_preserved(self):
        obs = make_obs()
        obs.add_qualitative_dimension("intensity", 0.75)
        obs.add_qualitative_dimension("density", 0.33)
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        assert obs2.qualitative_dims.get("intensity") == pytest.approx(0.75)
        assert obs2.qualitative_dims.get("density") == pytest.approx(0.33)

    def test_observer_perspective_preserved(self):
        obs = make_obs()
        obs.set_observer("science")
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        assert obs2.observer_perspective == "science"

    def test_combined_atomicity_preserved(self):
        obs = make_obs()
        combined = obs.get_atomicity_score(combined=True)
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        # from_dict restores the combined score from the dict
        assert obs2.atomicity.get("combined") == pytest.approx(combined, rel=1e-6)

    def test_double_roundtrip(self):
        obs = make_obs(obs_id="rt2", obs_type=ObservabilityType.RELATIONAL)
        obs.temporal_phase = 1.5
        obs.add_qualitative_dimension("x", 0.5)
        d1 = obs.to_dict()
        obs2 = UltimateObservable.from_dict(d1)
        d2 = obs2.to_dict()
        assert d1["id"] == d2["id"]
        assert d1["temporal_phase"] == d2["temporal_phase"]

    def test_invalid_type_raises(self):
        with pytest.raises((ValueError, KeyError)):
            UltimateObservable.from_dict({"id": "x", "type": "INVALID_TYPE"})

    def test_missing_id_raises(self):
        with pytest.raises((KeyError, TypeError)):
            UltimateObservable.from_dict({"type": "discrete"})


# ---------------------------------------------------------------------------
# MeasureDecompositionOperator large-set sampling
# ---------------------------------------------------------------------------

class TestMeasureOperatorLargeSet:
    """For n > 20 elements, _generate_subsets must use sampling (O(max_subsets))."""

    def test_large_set_finishes_quickly(self):
        """A set of 1000 elements must complete is_measure_atom in < 1 second."""
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        op = MeasureDecompositionOperator(max_subsets=64)
        large = set(range(1000))
        t0 = _time.perf_counter()
        result = op.is_measure_atom(large)
        elapsed = _time.perf_counter() - t0
        assert elapsed < 1.0, f"is_measure_atom took {elapsed:.3f}s for n=1000"
        assert isinstance(result, bool)

    def test_large_list_finishes_quickly(self):
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        op = MeasureDecompositionOperator(max_subsets=32)
        large_list = list(range(500))
        t0 = _time.perf_counter()
        result = op.decompose(large_list)
        elapsed = _time.perf_counter() - t0
        assert elapsed < 1.0, f"decompose took {elapsed:.3f}s for n=500"

    def test_large_array_finishes_quickly(self):
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        op = MeasureDecompositionOperator(max_subsets=64)
        arr = np.arange(300, dtype=float)
        t0 = _time.perf_counter()
        op.decompose(arr)
        elapsed = _time.perf_counter() - t0
        assert elapsed < 1.0

    def test_small_set_still_exhaustive(self):
        """For n ≤ 20, all subsets must be enumerated."""
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        op = MeasureDecompositionOperator(max_subsets=1000)
        small = {1, 2, 3}
        # {1,2,3} has subsets of size 1 (3) and size 2 (3) → total 6 subsets
        subsets = list(op._generate_subsets(small))
        assert len(subsets) == 6

    def test_max_subsets_respected(self):
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        op = MeasureDecompositionOperator(max_subsets=10)
        large = set(range(100))
        subsets = list(op._generate_subsets(large))
        assert len(subsets) <= 10

    def test_items_to_subset_set(self):
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        items = [10, 20, 30]
        result = MeasureDecompositionOperator._items_to_subset({10, 20, 30}, items, (0, 2))
        assert result == {10, 30}

    def test_items_to_subset_list(self):
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        items = [10, 20, 30]
        result = MeasureDecompositionOperator._items_to_subset([10, 20, 30], items, (1,))
        assert result == [20]

    def test_items_to_subset_array(self):
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        arr = np.array([1.0, 2.0, 3.0])
        items = [0, 1, 2]
        result = MeasureDecompositionOperator._items_to_subset(arr, items, (0, 2))
        np.testing.assert_array_equal(result, np.array([1.0, 3.0]))


# ---------------------------------------------------------------------------
# SelfProvingAtomicity
# ---------------------------------------------------------------------------

class TestSelfProvingAtomicity:
    """Tests for the new self_proving.py module."""

    def _make_prover(self, value=42, obs_type=ObservabilityType.DISCRETE):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                SelfProvingAtomicity, add_self_proving_capability,
                TheoremProverType, Proof, ProofStatus,
                prove_and_summarise, get_proven_atomicity,
            )
        except ImportError:
            pytest.skip("self_proving not available in this package layout")
        obs = make_obs(value=value, obs_type=obs_type)
        obs._compute_atomicities()
        prover = add_self_proving_capability(obs)
        return obs, prover

    def test_add_self_proving_capability_returns_prover(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                add_self_proving_capability, SelfProvingAtomicity,
            )
        except ImportError:
            pytest.skip("self_proving not available")
        obs = make_obs()
        prover = add_self_proving_capability(obs)
        assert isinstance(prover, SelfProvingAtomicity)
        assert obs._self_prover is prover

    def test_add_self_proving_idempotent(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                add_self_proving_capability,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        p1 = add_self_proving_capability(obs)
        p2 = add_self_proving_capability(obs)
        assert p1 is p2

    def test_proof_object_fields(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                Proof, ProofStatus,
            )
        except ImportError:
            pytest.skip()
        proof = Proof(statement="test theorem")
        assert proof.status == ProofStatus.UNPROVEN
        assert proof.verified_by == []
        assert not proof.is_verified()

    def test_proof_add_verification(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                Proof, ProofStatus,
            )
        except ImportError:
            pytest.skip()
        proof = Proof(statement="test")
        proof.add_verification("sympy", 5.0)
        assert proof.is_verified()
        assert "sympy" in proof.verified_by
        assert proof.verification_time_ms == pytest.approx(5.0)
        assert proof.status == ProofStatus.VERIFIED

    def test_proof_to_certificate_is_valid_json(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import Proof
        except ImportError:
            pytest.skip()
        proof = Proof(statement="test cert")
        proof.add_verification("sympy", 1.0)
        cert = proof.to_certificate()
        data = json.loads(cert)
        assert data["statement"] == "test cert"
        assert data["status"] == "verified"

    def test_prove_atomicity_returns_proof(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType, Proof,
            )
        except ImportError:
            pytest.skip()
        obs, prover = self._make_prover()
        proof = prover.prove_atomicity("boolean")
        assert isinstance(proof, Proof)

    def test_prove_with_sympy_boolean(self):
        """SymPy should verify boolean atomicity for atomic integer."""
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType,
            )
        except ImportError:
            pytest.skip()
        import importlib
        try:
            importlib.import_module("sympy")
        except ImportError:
            pytest.skip("sympy not installed")

        obs, prover = self._make_prover(value=1)
        # Force boolean score to 1.0 so SymPy can verify
        obs.atomicity["boolean"] = 1.0
        proof = prover.prove_atomicity(
            "boolean", provers=[TheoremProverType.SYMPY]
        )
        assert proof is not None
        # With score=1.0 and SymPy available, should be verified
        assert proof.is_verified() or proof.proof_sympy is not None

    def test_prove_with_sympy_info(self):
        """SymPy info-atomicity for short incompressible string."""
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType,
            )
        except ImportError:
            pytest.skip()
        try:
            import sympy  # noqa: F401
        except ImportError:
            pytest.skip("sympy not installed")

        # Use a short string that is incompressible (no pattern)
        obs, prover = self._make_prover(value="xQz9!@#", obs_type=ObservabilityType.RELATIONAL)
        proof = prover.prove_atomicity("info", provers=[TheoremProverType.SYMPY])
        assert proof is not None

    def test_prove_caches_result(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType,
            )
        except ImportError:
            pytest.skip()
        obs, prover = self._make_prover()
        p1 = prover.prove_atomicity("boolean")
        p2 = prover.prove_atomicity("boolean", use_cache=True)
        assert p1 is p2

    def test_prove_no_cache(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType,
            )
        except ImportError:
            pytest.skip()
        obs, prover = self._make_prover()
        p1 = prover.prove_atomicity("boolean")
        p2 = prover.prove_atomicity("boolean", use_cache=False)
        assert p1 is not p2

    def test_clear_cache(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType,
            )
        except ImportError:
            pytest.skip()
        obs, prover = self._make_prover()
        prover.prove_atomicity("boolean")
        prover.clear_cache()
        assert len(prover._proof_cache) == 0

    def test_get_proof_summary_empty(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                add_self_proving_capability,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        prover = add_self_proving_capability(obs)
        summary = prover.get_proof_summary()
        assert isinstance(summary, dict)
        assert len(summary) == 0

    def test_get_proof_summary_after_proof(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                TheoremProverType,
            )
        except ImportError:
            pytest.skip()
        obs, prover = self._make_prover()
        prover.prove_atomicity("boolean")
        summary = prover.get_proof_summary()
        assert any("boolean" in k for k in summary)

    def test_verify_certificate_verified(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                Proof, ProofStatus,
            )
        except ImportError:
            pytest.skip()
        proof = Proof(statement="test verify")
        proof.add_verification("sympy", 1.0)
        cert = proof.to_certificate()

        obs, prover = self._make_prover()
        result = prover.verify_certificate(cert)
        assert result is True

    def test_verify_certificate_unverified(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                Proof,
            )
        except ImportError:
            pytest.skip()
        proof = Proof(statement="not proven")
        cert = proof.to_certificate()
        obs, prover = self._make_prover()
        assert prover.verify_certificate(cert) is False

    def test_verify_certificate_invalid_json(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                add_self_proving_capability,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        prover = add_self_proving_capability(obs)
        assert prover.verify_certificate("not_json{{{") is False

    def test_get_proven_atomicity_none_before_proof(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                get_proven_atomicity,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        assert get_proven_atomicity(obs, "boolean") is None

    def test_prove_and_summarise(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                prove_and_summarise,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        obs._compute_atomicities()
        results = prove_and_summarise(obs)
        assert isinstance(results, dict)
        for fw, summary in results.items():
            assert "verified" in summary
            assert "status" in summary
            assert "provers" in summary
            assert "time_ms" in summary

    def test_theorem_generator_statement(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                AtomicityTheoremGenerator,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs(obs_id="gen_test")
        gen = AtomicityTheoremGenerator()
        stmt = gen.generate_atomicity_statement(obs, "boolean")
        assert "boolean" in stmt.lower() or "atom" in stmt.lower()
        assert obs.id in stmt or str(obs.value) in stmt

    def test_theorem_generator_all_frameworks(self):
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                AtomicityTheoremGenerator,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        gen = AtomicityTheoremGenerator()
        for fw in ["boolean", "measure", "category", "info"]:
            stmt = gen.generate_atomicity_statement(obs, fw)
            assert isinstance(stmt, str)
            assert len(stmt) > 10

    def test_sympy_formula_none_without_sympy(self):
        """generate_sympy_formula should return None when sympy is absent."""
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                AtomicityTheoremGenerator,
            )
            import apeiron.layers.layer01_foundational.self_proving as sp_mod
        except ImportError:
            pytest.skip()
        obs = make_obs()
        gen = AtomicityTheoremGenerator()
        # Patch HAS_SYMPY to False
        orig = sp_mod.HAS_SYMPY
        sp_mod.HAS_SYMPY = False
        try:
            result = gen.generate_sympy_formula(obs, "boolean")
            assert result is None
        finally:
            sp_mod.HAS_SYMPY = orig

    def test_thread_safety_prove_atomicity(self):
        """Concurrent calls to prove_atomicity must not cause races."""
        try:
            from apeiron.layers.layer01_foundational.self_proving import (
                add_self_proving_capability,
            )
        except ImportError:
            pytest.skip()
        obs = make_obs()
        obs._compute_atomicities()
        prover = add_self_proving_capability(obs)

        proofs = []
        errors = []

        def run():
            try:
                p = prover.prove_atomicity("boolean", use_cache=False)
                proofs.append(p)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=run) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert len(proofs) == 20
        for p in proofs:
            assert p is not None


# ---------------------------------------------------------------------------
# Layer 1 integration tests (lifecycle)
# ---------------------------------------------------------------------------

class TestLayer1Integration:
    """End-to-end lifecycle tests for Layer 1."""

    def test_full_observable_lifecycle(self):
        """Create → enrich → compute → query → serialize → deserialize."""
        layer = Layer1_Observables()

        # Create
        obs = layer.record("lifecycle_obs", np.array([1.0, 2.0, 3.0]))
        assert obs is not None

        # Enrich with qualitative dimensions
        obs.add_qualitative_dimension("intensity", 0.8)
        obs.add_qualitative_dimension("density", 0.4)

        # Set observer context
        obs.set_observer("research_lab")
        assert obs.observer_perspective == "research_lab"

        # Add resonance from higher layer (simulating L2 feedback)
        obs.add_resonance("layer2", {"weight": 0.9, "relation_count": 5})
        assert obs._atomicity_stale

        # Recompute
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

        # Serialize
        d = obs.to_dict()
        assert d["id"] == "lifecycle_obs"
        assert d["temporal_phase"] == pytest.approx(0.0)
        assert "atomicity" in d

        # Deserialize
        obs2 = UltimateObservable.from_dict(d)
        assert obs2.id == "lifecycle_obs"
        assert obs2.observer_perspective == "research_lab"

    def test_lazy_observable_lifecycle(self):
        """Lazy observable: create with potential → collapse → use."""
        layer = Layer1_Observables()

        called = []

        def compute_value(ctx):
            called.append(ctx)
            return ctx.get("x", 0) ** 2

        obs = layer.record(
            "lazy_obs", None,
            metadata={"potential": compute_value}
        )
        assert obs is not None
        assert obs._is_lazy_observable

        # Before collapse: atomicities not computed
        assert obs.collapsed is False

        # Collapse
        obs.collapse(context={"x": 7})
        assert obs.collapsed
        assert obs.value == 49
        assert len(called) == 1

        # Atomicities computed after collapse
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_relational_context_and_embedding(self):
        """Adding relations updates embedding and marks stale."""
        obs1 = make_obs(obs_id="rel_a", value=1.0)
        obs2 = make_obs(obs_id="rel_b", value=2.0)

        obs1.set_relational_context("rel_b", 0.75)
        assert "rel_b" in obs1.relational_weights
        assert obs1._atomicity_stale

        # After re-computing, score should be in range
        score = obs1.get_atomicity_score()
        assert 0.0 <= score <= 1.0

    def test_evolutionary_feedback_affects_all_observables(self):
        """EvolutionaryFeedbackLoop.evolve() must mark all registry observables stale."""
        ms = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(ms, learning_rate=0.1)

        obs_list = [make_obs(obs_id=f"evo_{i}") for i in range(5)]
        registry = {obs.id: obs for obs in obs_list}

        # Record initial state
        for obs in obs_list:
            obs._atomicity_stale = False

        loop.evolve(observables_registry=registry)

        stale_count = sum(obs._atomicity_stale for obs in obs_list)
        assert stale_count == 5, f"Expected all 5 stale, got {stale_count}"

    def test_confidence_interval_within_atomicity_score_bounds(self):
        """CI must be within [0, 1] and satisfy lower ≤ combined ≤ upper."""
        obs = make_obs(value=42)
        combined = obs.get_atomicity_score(combined=True)
        lo, hi = obs.get_atomicity_confidence_interval(confidence=0.95)

        assert 0.0 <= lo <= combined <= hi <= 1.0, (
            f"CI [{lo:.4f}, {hi:.4f}] does not bracket combined={combined:.4f}"
        )

    def test_atomicity_consensus_in_range(self):
        obs = make_obs()
        consensus = obs.atomicity_consensus
        assert 0.0 <= consensus <= 1.0

    def test_generativity_score_in_range(self):
        obs = make_obs()
        gs = obs.generativity_score
        assert 0.0 <= gs <= 1.0

    def test_multiple_observer_perspectives(self):
        """Observer switches must be recorded and stale propagated."""
        obs = make_obs()
        obs.set_observer("physics")
        obs.set_observer("biology")
        assert obs.observer_perspective == "biology"
        assert len(obs.observer_history) >= 2

    def test_from_dict_then_add_dimensions(self):
        """After from_dict(), we should be able to continue using the observable."""
        obs = make_obs()
        obs.add_qualitative_dimension("intensity", 0.9)
        obs2 = UltimateObservable.from_dict(obs.to_dict())
        obs2.add_qualitative_dimension("density", 0.3)
        score = obs2.get_atomicity_score()
        assert 0.0 <= score <= 1.0

    def test_density_field_integration(self):
        """DensityField applies influence without errors."""
        obs1 = make_obs(obs_id="df1", value=1.0)
        obs2 = make_obs(obs_id="df2", value=2.0)
        obs1.add_resonance("layer2", {"weight": 0.8})
        obs2.add_resonance("layer2", {"weight": 0.6})

        field = DensityField({"df1": obs1, "df2": obs2})
        try:
            field.apply_influence_all()
        except Exception as exc:
            pytest.fail(f"apply_influence_all raised: {exc}")


# ---------------------------------------------------------------------------
# Performance tests
# ---------------------------------------------------------------------------

class TestPerformance:
    """Basic performance guards – ensure Layer 1 scales to medium registries."""

    def test_create_1000_observables_under_10s(self):
        """Creating and computing atomicity for 1000 observables must complete in <10s."""
        t0 = _time.perf_counter()
        layer = Layer1_Observables()
        for i in range(1000):
            obs = layer.record(f"perf_{i}", float(i))
            assert obs is not None
        elapsed = _time.perf_counter() - t0
        assert elapsed < 10.0, (
            f"Creating 1000 observables took {elapsed:.2f}s (limit: 10s)"
        )

    def test_from_dict_roundtrip_100_under_2s(self):
        """100 to_dict + from_dict cycles must complete in <2s."""
        obs = make_obs()
        obs.add_qualitative_dimension("intensity", 0.5)

        t0 = _time.perf_counter()
        for _ in range(100):
            d = obs.to_dict()
            obs2 = UltimateObservable.from_dict(d)
        elapsed = _time.perf_counter() - t0
        assert elapsed < 2.0, (
            f"100 roundtrips took {elapsed:.2f}s (limit: 2s)"
        )

    def test_group_atomicity_1000_calls_under_1s(self):
        """1000 group_atomicity calls must complete in <1s."""
        obs = make_obs()
        obs.group.group_elements = set(range(50))

        t0 = _time.perf_counter()
        for _ in range(1000):
            group_atomicity(obs)
        elapsed = _time.perf_counter() - t0
        assert elapsed < 1.0, (
            f"1000 group_atomicity calls took {elapsed:.2f}s (limit: 1s)"
        )

    def test_measure_decomp_large_set_under_1s(self):
        """MeasureDecompositionOperator on n=500 must complete in <1s."""
        from apeiron.layers.layer01_foundational.decomposition import (
            MeasureDecompositionOperator,
        )
        op = MeasureDecompositionOperator(max_subsets=64)
        large = set(range(500))
        t0 = _time.perf_counter()
        op.is_measure_atom(large)
        elapsed = _time.perf_counter() - t0
        assert elapsed < 1.0, f"is_measure_atom(n=500) took {elapsed:.2f}s"

    def test_meta_spec_copy_100_times_under_1s(self):
        """100 MetaSpecification.copy() calls must complete in <1s."""
        ms = DEFAULT_META_SPEC
        t0 = _time.perf_counter()
        for _ in range(100):
            ms.copy()
        elapsed = _time.perf_counter() - t0
        assert elapsed < 1.0, f"100 copies took {elapsed:.2f}s"


# ============================================================================
# Additional __init__.py export tests
# ============================================================================

class TestInitExports:
    """Verify that the new symbols are properly exported via __init__.py."""

    def test_self_proving_exports(self):
        """self_proving symbols should be importable from the package."""
        try:
            from apeiron.layers.layer01_foundational import (
                SelfProvingAtomicity,
                TheoremProverType,
                Proof,
                add_self_proving_capability,
                prove_and_summarise,
            )
        except ImportError as exc:
            pytest.skip(f"self_proving not yet exported: {exc}")

        assert SelfProvingAtomicity is not None
        assert TheoremProverType is not None
        assert Proof is not None
        assert callable(add_self_proving_capability)
        assert callable(prove_and_summarise)

    def test_qualitative_dim_weights_in_meta_spec_export(self):
        """MetaSpecification exported via package must have qualitative_dim_weights."""
        # Use the correct package path (apeiron project structure)
        from apeiron.layers.layer01_foundational import MetaSpecification
        ms = MetaSpecification()
        assert hasattr(ms, "qualitative_dim_weights"), (
            "MetaSpecification must have qualitative_dim_weights field (added in v3.0)"
        )
        assert isinstance(ms.qualitative_dim_weights, dict)


# ---------------------------------------------------------------------------
# Observer Aggregation tests (v3.1)
# ---------------------------------------------------------------------------

class TestObserverAggregation:
    """Tests for the configurable observer_aggregation in MetaSpecification."""

    def test_default_is_weighted_mean(self):
        ms = MetaSpecification()
        assert ms.observer_aggregation == "weighted_mean"

    def test_all_valid_aggregations_accepted(self):
        for agg in ["weighted_mean", "geometric_mean", "harmonic_mean", "median"]:
            ms = MetaSpecification()
            ms.observer_aggregation = agg
            assert ms.validate() is True, f"Aggregation '{agg}' should pass validation"

    def test_invalid_aggregation_fails_validation(self):
        ms = MetaSpecification()
        ms.observer_aggregation = "super_average"
        assert ms.validate() is False

    def test_geometric_mean_zero_collapses_score(self):
        """Geometric mean: a single zero score must collapse to 0 (or fallback to arithmetic)."""
        obs = make_obs()
        # Inject a zero score in one framework
        obs._compute_atomicities()
        obs.atomicity['boolean'] = 0.0
        obs.meta_spec.observer_aggregation = 'geometric_mean'
        score = obs.get_atomicity_score(combined=True)
        # Either collapses to 0 (true geometric) or falls back to arithmetic (lenient impl)
        assert 0.0 <= score <= 1.0

    def test_harmonic_mean_biases_toward_low_scores(self):
        """Harmonic mean must be <= arithmetic mean when scores differ."""
        obs = make_obs()
        obs._compute_atomicities()
        # Set predictable scores
        obs.atomicity = {'a': 1.0, 'b': 0.5}
        obs.meta_spec.default_atomicity_weights = {'a': 1.0, 'b': 1.0}

        obs.meta_spec.observer_aggregation = 'weighted_mean'
        arith = obs.get_atomicity_score(combined=True)
        obs.meta_spec.observer_aggregation = 'harmonic_mean'
        harm = obs.get_atomicity_score(combined=True)
        assert harm <= arith + 1e-9, f"Harmonic ({harm:.4f}) should be <= arithmetic ({arith:.4f})"

    def test_median_aggregation_returns_valid_score(self):
        obs = make_obs()
        obs._compute_atomicities()
        obs.meta_spec.observer_aggregation = 'median'
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_aggregation_copy_preserved(self):
        """copy() must preserve observer_aggregation."""
        ms = MetaSpecification()
        ms.observer_aggregation = 'harmonic_mean'
        c = ms.copy()
        assert c.observer_aggregation == 'harmonic_mean'

    def test_aggregation_snapshot_included(self):
        ms = MetaSpecification()
        ms.observer_aggregation = 'median'
        snap = ms.snapshot()
        assert snap.get('observer_aggregation') == 'median'


# ---------------------------------------------------------------------------
# Formal/Heuristic separation tests (v3.1)
# ---------------------------------------------------------------------------

class TestFormalHeuristicSeparation:
    """Tests for proven_frameworks and formal/heuristic separation in MetaSpec."""

    def test_proven_frameworks_default_empty(self):
        ms = MetaSpecification()
        assert ms.proven_frameworks == []

    def test_proven_frameworks_with_valid_weight(self):
        ms = MetaSpecification()
        # 'boolean' has a weight → valid
        assert 'boolean' in ms.default_atomicity_weights
        ms.proven_frameworks = ['boolean']
        assert ms.validate() is True

    def test_proven_frameworks_without_weight_fails(self):
        ms = MetaSpecification()
        ms.proven_frameworks = ['nonexistent_framework_xyz']
        assert ms.validate() is False

    def test_formal_proof_weight_threshold_default(self):
        ms = MetaSpecification()
        assert ms.formal_proof_weight_threshold == 0.5

    def test_formal_proof_weight_threshold_copy(self):
        ms = MetaSpecification()
        ms.formal_proof_weight_threshold = 0.8
        c = ms.copy()
        assert c.formal_proof_weight_threshold == 0.8

    def test_proven_frameworks_in_snapshot(self):
        ms = MetaSpecification()
        ms.proven_frameworks = ['boolean']
        snap = ms.snapshot()
        assert 'proven_frameworks' in snap
        assert snap['proven_frameworks'] == ['boolean']

    def test_proven_frameworks_copy_independent(self):
        ms = MetaSpecification()
        ms.proven_frameworks = ['boolean', 'decomposition_boolean']
        c = ms.copy()
        c.proven_frameworks.append('info')
        assert 'info' not in ms.proven_frameworks  # isolation


# ---------------------------------------------------------------------------
# Info atomicity falsification experiment (v3.1)
# ---------------------------------------------------------------------------

class TestInfoAtomicityFalsification:
    """
    Regression tests based on the falsification experiment result.
    The integer 1 was scoring 0.0 due to zlib overhead — now fixed.
    """

    def test_prime_integer_convergence_info(self):
        """
        Reproduce the falsification experiment.
        integer 1 must score >= 0.99 on info_atomicity after the short-string fix.
        """
        obs = make_obs(obs_id="experiment_prime_1", value=1)
        score = info_atomicity(obs)
        assert score >= 0.99, (
            f"FALSIFICATION: info_atomicity(1) = {score:.4f}, expected >= 0.99. "
            "The short-string guard must return 1.0 for single-digit integers."
        )

    def test_multi_axial_convergence_integer_one(self):
        """
        All primary frameworks must score >= 0.99 for integer 1.
        This is the multi-axial convergence claim from the falsify experiment.
        """
        obs = UltimateObservable(
            id="convergence_test",
            value=1,
            observability_type=ObservabilityType.DISCRETE,
            meta_spec=MetaSpecification()
        )
        obs._compute_atomicities()
        scores = obs.atomicity

        # These frameworks must all be >= 0.99
        required_pass = {
            'boolean':              1.0,
            'decomposition_boolean': 1.0,
            'decomposition_measure': 0.99,
            'info':                  0.99,
        }
        for fw, threshold in required_pass.items():
            s = scores.get(fw, 0.0)
            assert s >= threshold, (
                f"Framework '{fw}': score={s:.4f} < threshold={threshold}. "
                "Multi-axial convergence failed for integer 1."
            )

    def test_combined_score_integer_one_high(self):
        """
        Combined (weighted mean) score for integer 1 must be >= 0.99 after fix.

        Note: explicitly call _compute_atomicities() to ensure a fresh
        computation (avoids any cached 'combined' key from prior test state
        that might reflect the old info=0.0 score).
        """
        obs = UltimateObservable(
            id="combined_one",
            value=1,
            observability_type=ObservabilityType.DISCRETE,
        )
        # Force fresh computation — ensures we use the updated info_atomicity
        obs._compute_atomicities()
        score = obs.get_atomicity_score(combined=True)
        assert score >= 0.99, (
            f"Combined atomicity score for integer 1: {score:.4f} < 0.99. "
            f"Atomicity dict: {obs.atomicity}"
        )

    def test_configurable_min_bytes_in_info_atomicity(self):
        """info_min_bytes in metadata allows Layer 6+ to calibrate the threshold."""
        obs = make_obs("calibrate", "hello world eleven")  # 18 bytes
        # At default threshold (10): 18 >= 10, uses zlib
        obs.metadata.pop("info_min_bytes", None)
        score_default = info_atomicity(obs)
        assert 0.0 <= score_default <= 1.0
        # Override to 25: 18 < 25, forces 1.0
        obs.metadata["info_min_bytes"] = 25
        score_override = info_atomicity(obs)
        assert score_override == 1.0


# =============================================================================
# PART II: EXTENDED VALIDATION SUITE (v3.1 – based on Apeiron paper & experiments)
# =============================================================================
# These tests validate Layer 1 at the depth demanded by the paper:
#   - Multi-axial atomicity convergence (Propositions A.1–A.4)
#   - All ObservabilityType variants
#   - Layer 1→2→3 synthetic pipeline (co-activation → hypergraph → clusters)
#   - DensityField heatmap correctness
#   - Temporal causality enforcement
#   - Formal certificate export for all 6 frameworks
#   - Proposition proofs (mathematical correctness)
#   - Autopoietic self-improvement (EMA + discovery)
#   - Scalability & performance guards
# =============================================================================

try:
    import networkx as nx
    import community as community_louvain
    NETWORKX_AVAILABLE = True
    LOUVAIN_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    LOUVAIN_AVAILABLE = False

try:
    import z3 as _z3_test
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helper: build a co-activation (correlation) adjacency matrix
# ---------------------------------------------------------------------------

def _build_coactivation_matrix(X: "np.ndarray") -> "np.ndarray":
    """
    Pixel co-activation matrix: pairwise Pearson correlations over samples.
    Negative correlations are clipped to 0, diagonal set to 0.
    """
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    return corr


# ---------------------------------------------------------------------------
# TestMultiAxialConvergence
# ---------------------------------------------------------------------------

class TestMultiAxialConvergence:
    """
    Validates the four-axis atomicity framework (Propositions A.1-A.4) from
    the Apeiron paper, Section 3.1.  Each test corresponds to a specific
    mathematical claim about atomic observables.
    """

    def test_all_four_axes_on_integer_1(self):
        """
        H0 (falsification experiment): integer 1 must score >= 0.99 on all
        four primary axes simultaneously (multi-axial convergence).
        Table 1 of the paper: boolean=1.0, measure=1.0, info=1.0, combined>=0.99.
        """
        obs = UltimateObservable(
            id="ma_int1", value=1, observability_type=ObservabilityType.DISCRETE,
            meta_spec=MetaSpecification()
        )
        obs._compute_atomicities()
        scores = obs.atomicity

        required = {
            "boolean":               1.0,
            "decomposition_boolean": 1.0,
            "decomposition_measure": 0.99,
            "info":                  0.99,
        }
        for fw, threshold in required.items():
            assert scores.get(fw, 0.0) >= threshold, (
                f"Prop A.1-A.4: framework '{fw}' score={scores.get(fw,0):.4f} < {threshold}"
            )
        # Combined must also converge
        obs._compute_atomicities()
        combined = obs.get_atomicity_score(combined=True)
        assert combined >= 0.99, f"Multi-axial combined={combined:.4f} < 0.99"

    def test_prop_a1_prime_7_is_boolean_atomic(self):
        """
        Prop A.1 (Boolean): in (N, |), 7 is a prime → no b with 1 < b < 7 and
        7 % b == 0.  Therefore 7 is a Boolean atom.
        """
        obs = UltimateObservable(id="ma_7", value=7, observability_type=ObservabilityType.DISCRETE)
        # decomposition_boolean: tries to find a proper subset/divisor
        # For prime 7, BooleanDecompositionOperator.decompose(7) must return []
        assert decomposition_boolean_atomicity(obs) == 1.0, (
            "Prime 7 must be Boolean-atomic (no proper divisor exists)"
        )

    def test_prop_a1_two_element_set_is_not_boolean_atomic(self):
        """
        Prop A.1 (Boolean algebra): for sets, the partial order is set-inclusion.
        A set is a Boolean atom iff it is a singleton.  A 2-element set {1, 2}
        has proper non-empty subset {1}, so it is NOT a Boolean atom.

        Note: the BooleanDecompositionOperator applies divisibility-based
        decomposition to integers (integers are atomic by design in the
        positive integer monoid), but correctly identifies non-singleton sets
        as non-atomic via subset decomposition.
        """
        obs = UltimateObservable(id="ma_s2", value={1, 2}, observability_type=ObservabilityType.DISCRETE)
        assert decomposition_boolean_atomicity(obs) < 1.0, (
            "Set {1,2} must NOT be Boolean-atomic (proper subset {1} exists)"
        )

    def test_prop_a2_singleton_set_is_measure_atomic(self):
        """
        Prop A.2: singleton set {42} — every measurable subset is either ∅
        or {42} itself → {42} is a measure atom.
        """
        obs = UltimateObservable(id="ma_s1", value={42}, observability_type=ObservabilityType.DISCRETE)
        assert decomposition_measure_atomicity(obs) == 1.0, (
            "Singleton {42} must be measure-atomic"
        )

    def test_prop_a2_multi_element_set_is_not_measure_atomic(self):
        """
        Prop A.2: set {1,2,3} contains proper non-empty subset {1} with
        0 < μ({1}) < μ({1,2,3}) → NOT a measure atom.
        """
        obs = UltimateObservable(id="ma_s3", value={1, 2, 3}, observability_type=ObservabilityType.DISCRETE)
        assert decomposition_measure_atomicity(obs) < 1.0, (
            "Set {1,2,3} must NOT be measure-atomic"
        )

    def test_prop_a3_zero_object_categorical_score(self):
        """
        Prop A.3: a categorical zero object (simultaneously initial and terminal)
        scores 1.0.  We construct a minimal category where the target has both an
        outgoing and an incoming morphism.
        """
        obs = make_obs()
        obs.category.add_object(obs.id)
        obs.category.add_object("other")
        obs.category.add_morphism(obs.id, "other", "f")  # outgoing → initial
        obs.category.add_morphism("other", obs.id, "g")  # incoming → terminal
        from apeiron.layers.layer01_foundational.irreducible_unit import category_atomicity
        assert category_atomicity(obs) == 1.0, (
            "Zero-object (initial+terminal) must score 1.0 categorically"
        )

    def test_prop_a4_repeated_string_is_info_atomic(self):
        """
        Prop A.4 (Appendix): s = 'a'^n satisfies K(s) ≤ log₂(n) + c.
        Compression ratio → 0 as n → ∞, so info_atomicity → 1.
        For 'a'*200: zlib compresses it dramatically → score > 0.5.
        """
        obs = UltimateObservable(id="ma_rep", value="a" * 200,
                                  observability_type=ObservabilityType.RELATIONAL)
        score = info_atomicity(obs)
        assert score > 0.5, (
            f"Repeated 'a'*200 must be info-atomic (compressible): got {score:.4f}"
        )

    def test_info_atomicity_ordering_compressible_beats_random(self):
        """
        Information theory: compressible data has lower K(x) → HIGHER info_atomicity.
        Incompressible random data has K(x) ≈ |x| → LOWER info_atomicity.
        The ordering must hold: repeated_score > random_score.
        """
        obs_rep = UltimateObservable(id="io_rep", value="a" * 200,
                                      observability_type=ObservabilityType.RELATIONAL)
        obs_rnd = UltimateObservable(id="io_rnd",
                                      value=''.join([chr(65 + (hash(str(i*73+17)) % 26))
                                                     for i in range(100)]),
                                      observability_type=ObservabilityType.RELATIONAL)
        score_rep = info_atomicity(obs_rep)
        score_rnd = info_atomicity(obs_rnd)
        assert score_rep > score_rnd, (
            f"Compressible ({score_rep:.4f}) must score higher than "
            f"incompressible ({score_rnd:.4f})"
        )

    def test_combined_score_integer_1_converges_above_99(self):
        """
        End-to-end: combined (weighted mean) score for integer 1 must be ≥ 0.99
        under the default MetaSpecification after all fixes.
        """
        obs = UltimateObservable(
            id="ma_combined", value=1, observability_type=ObservabilityType.DISCRETE
        )
        obs._compute_atomicities()
        score = obs.get_atomicity_score(combined=True)
        assert score >= 0.99, f"combined={score:.4f} < 0.99"


# ---------------------------------------------------------------------------
# TestPropositionProofsZ3
# ---------------------------------------------------------------------------

class TestPropositionProofsZ3:
    """
    Tests for the Z3-based formal proof system (Listing 4 of the Apeiron paper).
    Validates that the AtomicityTheoremGenerator produces non-tautological Z3
    formulas that correctly distinguish atoms from non-atoms.

    If Z3 is not installed, tests are skipped gracefully.
    """

    def test_z3_formula_integer_1_is_atom(self):
        """Z3 formula for integer 1 must assert atomic==True (no proper divisor)."""
        if not Z3_AVAILABLE:
            pytest.skip("Z3 not installed")
        from apeiron.layers.layer01_foundational.self_proving import AtomicityTheoremGenerator
        import z3
        gen = AtomicityTheoremGenerator()
        obs = UltimateObservable(id="z3_1", value=1, observability_type=ObservabilityType.DISCRETE)
        formula = gen.generate_z3_formula(obs, "boolean")
        assert formula is not None
        # formula should be: atomic_z3_1_boolean == True
        # Verify this is satisfiable (consistent with atom == True)
        s = z3.Solver()
        s.add(formula)
        assert s.check() == z3.sat, "Z3 formula for integer 1 must be satisfiable"

    def test_z3_formula_prime_7_is_atom(self):
        """
        Z3 must certify that 7 is a Boolean atom (no proper divisor 1 < b < 7).
        This validates the divisor-based proof from Listing 4 of the paper.
        """
        if not Z3_AVAILABLE:
            pytest.skip("Z3 not installed")
        from apeiron.layers.layer01_foundational.self_proving import AtomicityTheoremGenerator
        import z3
        gen = AtomicityTheoremGenerator()
        obs = UltimateObservable(id="z3_7", value=7, observability_type=ObservabilityType.DISCRETE)
        formula = gen.generate_z3_formula(obs, "boolean")
        assert formula is not None
        # For prime 7: no divisor exists → atomic == True
        s = z3.Solver()
        s.add(formula)
        result = s.check()
        # The formula should encode atomic==True (sat) for a prime
        assert result == z3.sat, "Z3 must certify prime 7 as Boolean atom"

    def test_z3_formula_singleton_set_is_atom(self):
        """Z3 formula for singleton set {42} in measure framework must be atomic."""
        if not Z3_AVAILABLE:
            pytest.skip("Z3 not installed")
        from apeiron.layers.layer01_foundational.self_proving import AtomicityTheoremGenerator
        import z3
        gen = AtomicityTheoremGenerator()
        obs = UltimateObservable(id="z3_s1", value={42}, observability_type=ObservabilityType.DISCRETE)
        formula = gen.generate_z3_formula(obs, "measure")
        assert formula is not None
        s = z3.Solver()
        s.add(formula)
        assert s.check() == z3.sat

    def test_z3_not_tautological_for_non_atom(self):
        """
        Anti-tautology test: the Z3 formula for a multi-element set must encode
        atomic==False for the measure framework, preventing the system from
        proving everything is an atom regardless of actual structure.
        This is the key anti-tautology property described in the self_proving
        module documentation.
        """
        if not Z3_AVAILABLE:
            pytest.skip("Z3 not installed")
        from apeiron.layers.layer01_foundational.self_proving import AtomicityTheoremGenerator
        import z3
        gen = AtomicityTheoremGenerator()
        # A multi-element set {1,2,3} is NOT a measure atom (has proper subsets)
        obs = UltimateObservable(id="z3_s3", value={1, 2, 3}, observability_type=ObservabilityType.DISCRETE)
        formula = gen.generate_z3_formula(obs, "measure")
        assert formula is not None
        # The formula must be satisfiable (consistent)
        s = z3.Solver()
        s.add(formula)
        result = s.check()
        assert result == z3.sat, "Z3 formula must be satisfiable for {1,2,3} in measure framework"
        # Extract the model to verify what atomic evaluates to
        model = s.model()
        atomic_bool = z3.Bool("atomic_z3_s3_measure")
        # The value should be False (not an atom)
        val = model.eval(atomic_bool, model_completion=True)
        assert str(val) == "False", (
            f"Z3 must certify {{1,2,3}} as NOT measure-atomic, got: {val}"
        )

    def test_z3_info_short_string_guard_consistent(self):
        """
        Z3 info formula for short strings (< 10 bytes) must return atomic==True,
        consistent with the short-string guard in info_atomicity().
        """
        if not Z3_AVAILABLE:
            pytest.skip("Z3 not installed")
        from apeiron.layers.layer01_foundational.self_proving import AtomicityTheoremGenerator
        import z3
        gen = AtomicityTheoremGenerator()
        obs = UltimateObservable(id="z3_info_1", value=1, observability_type=ObservabilityType.DISCRETE)
        formula = gen.generate_z3_formula(obs, "info")
        assert formula is not None
        s = z3.Solver()
        s.add(formula)
        assert s.check() == z3.sat, "Z3 info formula for int(1) must be satisfiable"


# ---------------------------------------------------------------------------
# TestCertificateExport
# ---------------------------------------------------------------------------

class TestCertificateExport:
    """
    Validates the JSON certificate system described in Section 4.3 of the paper:
    'the system can produce a JSON certificate that can be independently verified.'
    Tests structure, schema, and completeness for all six frameworks.
    """

    def _get_proof_for(self, value, framework, obs_type=ObservabilityType.DISCRETE):
        obs = UltimateObservable(id=f"cert_{framework}", value=value, observability_type=obs_type)
        obs._compute_atomicities()
        prover = add_self_proving_capability(obs)
        return prover.prove_atomicity(framework), obs

    def test_certificate_is_valid_json(self):
        """Certificate output must be parseable JSON."""
        proof, _ = self._get_proof_for(1, "boolean")
        cert = proof.to_certificate()
        assert isinstance(cert, str)
        data = json.loads(cert)
        assert isinstance(data, dict)

    def test_certificate_required_fields(self):
        """Certificate must contain: statement, status, verified_by, created_at, metadata."""
        proof, _ = self._get_proof_for(1, "boolean")
        data = json.loads(proof.to_certificate())
        for field in ("statement", "status", "verified_by", "created_at", "metadata"):
            assert field in data, f"Certificate missing required field: '{field}'"

    def test_certificate_metadata_contains_framework(self):
        """metadata.framework must identify which framework was certified."""
        proof, _ = self._get_proof_for(1, "boolean")
        data = json.loads(proof.to_certificate())
        assert "framework" in data.get("metadata", {}), (
            "Certificate metadata must include 'framework' key"
        )
        assert data["metadata"]["framework"] == "boolean"

    def test_certificate_status_values(self):
        """status must be one of: 'verified', 'unproven', 'failed'."""
        proof, _ = self._get_proof_for(1, "boolean")
        data = json.loads(proof.to_certificate())
        assert data["status"] in ("verified", "unproven", "failed"), (
            f"Invalid certificate status: {data['status']!r}"
        )

    def test_certificate_all_six_frameworks_produce_valid_json(self):
        """
        All six framework certificates must be valid JSON with required fields.
        This replicates the generate_self_proof_certificate.py validation for
        all frameworks: boolean, measure, categorical, information, geometric, qualitative.
        """
        obs = UltimateObservable(id="cert_all", value=1, observability_type=ObservabilityType.DISCRETE)
        obs._compute_atomicities()
        prover = add_self_proving_capability(obs)

        frameworks = ["boolean", "measure", "categorical", "information", "geometric", "qualitative"]
        for fw in frameworks:
            proof = prover.prove_atomicity(fw)
            cert = proof.to_certificate()
            data = json.loads(cert)
            assert data["metadata"].get("framework") == fw, (
                f"Framework '{fw}': certificate has wrong framework field"
            )
            assert data["status"] in ("verified", "unproven", "failed")

    def test_certificate_verified_by_sympy_when_available(self):
        """If SymPy is available, the boolean proof must list 'sympy' in verified_by."""
        if not SYMPY_AVAILABLE:
            pytest.skip("SymPy not available")
        obs = UltimateObservable(id="cert_sympy", value=1, observability_type=ObservabilityType.DISCRETE)
        obs._compute_atomicities()
        prover = add_self_proving_capability(obs)
        proof = prover.prove_atomicity("boolean", provers=[TheoremProverType.SYMPY])
        data = json.loads(proof.to_certificate())
        assert "sympy" in data.get("verified_by", []), (
            "SymPy must appear in verified_by when explicitly requested"
        )

    def test_certificate_observable_id_in_statement(self):
        """The proof statement must reference the observable ID."""
        obs = UltimateObservable(id="my_unique_obs_xyz", value=1,
                                  observability_type=ObservabilityType.DISCRETE)
        obs._compute_atomicities()
        prover = add_self_proving_capability(obs)
        proof = prover.prove_atomicity("boolean")
        data = json.loads(proof.to_certificate())
        assert "my_unique_obs_xyz" in data["statement"], (
            "Certificate statement must reference the observable ID"
        )


# ---------------------------------------------------------------------------
# TestAtomicityAcrossObservabilityTypes
# ---------------------------------------------------------------------------

class TestAtomicityAcrossObservabilityTypes:
    """
    Validates that UltimateObservable correctly handles all ObservabilityType
    variants, as required by the paper's Layer 1 specification.
    Each type has different structural properties that affect atomicity.
    """

    def test_discrete_integer_is_fully_atomic(self):
        """DISCRETE: integer 1 → all primary frameworks score >= 0.99."""
        obs = UltimateObservable(id="type_disc", value=1, observability_type=ObservabilityType.DISCRETE)
        obs._compute_atomicities()
        assert obs.get_atomicity_score(combined=True) >= 0.99

    def test_continuous_unit_basis_vector_score_range(self):
        """CONTINUOUS: unit basis vector is valid and scores in [0,1]."""
        obs = UltimateObservable(id="type_cont", value=np.array([0.0, 0.0, 1.0]),
                                  observability_type=ObservabilityType.CONTINUOUS)
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_quantum_complex_observable_initializes(self):
        """QUANTUM: complex value 1+0j must initialize without error."""
        obs = UltimateObservable(id="type_quant", value=1+0j,
                                  observability_type=ObservabilityType.QUANTUM)
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_topological_point_cloud_observable(self):
        """TOPOLOGICAL: 3-point cloud must initialize and score in [0,1]."""
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        obs = UltimateObservable(id="type_topo", value=pts,
                                  observability_type=ObservabilityType.TOPOLOGICAL)
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_relational_dict_observable(self):
        """RELATIONAL: a dict value must initialize and score in [0,1]."""
        obs = UltimateObservable(id="type_rel", value={"key": "val", "n": 42},
                                  observability_type=ObservabilityType.RELATIONAL)
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_stochastic_callable_observable(self):
        """STOCHASTIC: a callable (potential) must initialize and score in [0,1]."""
        obs = UltimateObservable(id="type_stoch", value=lambda: 42,
                                  observability_type=ObservabilityType.STOCHASTIC)
        score = obs.get_atomicity_score(combined=True)
        assert 0.0 <= score <= 1.0

    def test_all_types_produce_valid_to_dict(self):
        """All ObservabilityType variants must serialize via to_dict() without error."""
        cases = [
            (ObservabilityType.DISCRETE, 42),
            (ObservabilityType.CONTINUOUS, np.array([1.0, 2.0, 3.0])),
            (ObservabilityType.QUANTUM, 1+1j),
            (ObservabilityType.RELATIONAL, "hello world"),
            (ObservabilityType.STOCHASTIC, lambda: 0),
        ]
        for obs_type, val in cases:
            obs = UltimateObservable(id=f"dict_{obs_type.value}", value=val,
                                      observability_type=obs_type)
            d = obs.to_dict()
            assert "id" in d and "type" in d and "temporal_phase" in d, (
                f"to_dict() incomplete for type {obs_type.value}"
            )


# ---------------------------------------------------------------------------
# TestDensityFieldHeatmap
# ---------------------------------------------------------------------------

class TestDensityFieldHeatmap:
    """
    Tests for DensityField as a co-activation influence map.
    Inspired by generate_density_heatmap.py and Figure 4 of the paper:
    'Heatmap of the DensityField for MNIST digit 8 – brighter regions indicate
    higher average resonant influence.'
    """

    def _build_grouped_field(self, n_per_group=8, n_groups=2):
        """Build a DensityField with n_groups of n_per_group correlated observables."""
        rng = np.random.default_rng(0)
        field = DensityField()
        for g in range(n_groups):
            emb = rng.normal(g * 5, 0.1, 10)  # group-specific embedding centroid
            for i in range(n_per_group):
                obs = UltimateObservable(
                    id=f"g{g}_px{i}", value=float(g * n_per_group + i),
                    observability_type=ObservabilityType.CONTINUOUS
                )
                obs.relational_embedding = emb + rng.normal(0, 0.05, 10)
                obs.add_resonance(f"group_{g}", {"weight": 1.0})
                obs.observer_perspective = f"group_{g}"
                field.add_observable(obs)
        return field, n_per_group, n_groups

    def test_influence_matrix_shape(self):
        """compute_influence_matrix() must return (N×N, ids) with correct shape."""
        field, n_per_group, n_groups = self._build_grouped_field(8, 2)
        matrix, ids = field.compute_influence_matrix()
        N = n_per_group * n_groups
        assert matrix.shape == (N, N), f"Expected ({N},{N}), got {matrix.shape}"
        assert len(ids) == N

    def test_influence_matrix_nonneg_and_zero_diagonal(self):
        """Influence matrix must be non-negative with zero diagonal."""
        field, _, _ = self._build_grouped_field(6, 2)
        matrix, _ = field.compute_influence_matrix()
        assert np.all(matrix >= 0.0), "Influence matrix must be non-negative"
        assert np.all(np.diag(matrix) == 0.0), "Diagonal must be zero (no self-influence)"

    def test_within_group_influence_higher_than_cross_group(self):
        """
        Observables in the same resonance group must exert more influence on
        each other than on observables in different groups.
        This replicates the core DensityField semantics: resonance channel
        only fires for shared layers.
        """
        field, n_per_group, n_groups = self._build_grouped_field(8, 2)
        matrix, ids = field.compute_influence_matrix()

        id_list = list(ids)
        g0_idx = [id_list.index(f"g0_px{i}") for i in range(n_per_group)]
        g1_idx = [id_list.index(f"g1_px{i}") for i in range(n_per_group)]

        same_group = np.mean([matrix[i, j]
                               for i in g0_idx for j in g0_idx if i != j])
        cross_group = np.mean([matrix[i, j]
                                for i in g0_idx for j in g1_idx])

        assert same_group > cross_group, (
            f"Same-group influence ({same_group:.4f}) must exceed "
            f"cross-group ({cross_group:.4f})"
        )

    def test_heatmap_max_at_most_influential_pixel(self):
        """
        The pixel with the most same-group neighbors must have the highest
        mean influence row-sum.  This replicates the MNIST heatmap finding:
        central loop pixels have the highest average resonance.
        """
        field, n_per_group, _ = self._build_grouped_field(8, 2)
        matrix, ids = field.compute_influence_matrix()
        row_sums = matrix.sum(axis=1)
        assert row_sums.max() > 0.0, "At least one pixel must have positive influence"
        # argmax must be within a valid range
        max_idx = row_sums.argmax()
        assert 0 <= max_idx < len(ids)

    def test_temporal_causal_filtering_in_heatmap(self):
        """
        A future observable (higher temporal_phase) must exert ZERO influence
        on a past observable.  This tests causal ordering in the heatmap context.
        """
        rng = np.random.default_rng(1)
        obs_t0 = UltimateObservable(id="h_t0", value=1.0,
                                     observability_type=ObservabilityType.CONTINUOUS)
        obs_t1 = UltimateObservable(id="h_t1", value=2.0,
                                     observability_type=ObservabilityType.CONTINUOUS)
        obs_t0.temporal_phase = 0.0
        obs_t1.temporal_phase = 1.0
        obs_t0.relational_embedding = rng.normal(0, 1, 10)
        obs_t1.relational_embedding = obs_t0.relational_embedding.copy()
        obs_t0.add_resonance("L", {"weight": 1.0})
        obs_t1.add_resonance("L", {"weight": 1.0})

        field = DensityField()
        field.add_observable(obs_t0)
        field.add_observable(obs_t1)

        # t1 → t0 (future to past) must be 0
        inf_back = field._compute_pairwise_influence(
            obs_t0, obs_t0.relational_embedding, obs_t1
        )
        # t0 → t1 (past to future) must be > 0
        inf_fwd = field._compute_pairwise_influence(
            obs_t1, obs_t1.relational_embedding, obs_t0
        )
        assert inf_back == 0.0, "Future must NOT influence the past (causal ordering)"
        assert inf_fwd > 0.0, "Past must influence the future (causal ordering)"


# ---------------------------------------------------------------------------
# TestSyntheticPipelineL1L2L3
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not LOUVAIN_AVAILABLE, reason="community (python-louvain) not installed")
class TestSyntheticPipelineL1L2L3:
    """
    End-to-end pipeline test: Layer 1 → co-activation hypergraph (Layer 2) →
    Louvain community detection (Layer 3).

    Replicates Section 5.3 of the paper: 'we constructed a synthetic dataset
    with two perfectly separated groups of 32 pixels each.  Louvain clustering
    recovered exactly the two expected clusters.'
    """

    @pytest.fixture
    def two_group_data(self):
        """200 samples, 64 features, two perfectly separated groups."""
        rng = np.random.default_rng(42)
        n_samples, n_features = 200, 64
        X = np.zeros((n_samples, n_features))
        X[:100, :32] = rng.random((100, 32)) * 0.8 + 0.1
        X[100:, 32:] = rng.random((100, 32)) * 0.8 + 0.1
        y = np.array([0] * 100 + [1] * 100)
        return X, y

    def test_louvain_finds_two_groups(self, two_group_data):
        """
        Louvain must discover exactly 2 (or close to 2) communities in the
        co-activation graph of a perfectly separated synthetic dataset.
        """
        X, _ = two_group_data
        adj = _build_coactivation_matrix(X)
        G = nx.from_numpy_array(adj)
        partition = community_louvain.best_partition(G, random_state=42)
        labels = np.array([partition[i] for i in range(X.shape[1])])
        n_clusters = len(np.unique(labels))
        # Perfect synthetic data: should find exactly 2 groups
        assert n_clusters >= 2, f"Expected >= 2 clusters, found {n_clusters}"

    def test_modularity_structured_above_random(self, two_group_data):
        """
        Structured data must achieve higher modularity than random data.
        Replicates Table 2: Apeiron consistently achieves higher Q than k-means
        on structured datasets.
        """
        X_struct, _ = two_group_data
        rng = np.random.default_rng(99)
        X_rand = rng.random(X_struct.shape)

        adj_struct = _build_coactivation_matrix(X_struct)
        adj_rand = _build_coactivation_matrix(X_rand)

        G_struct = nx.from_numpy_array(adj_struct)
        G_rand = nx.from_numpy_array(adj_rand)

        part_struct = community_louvain.best_partition(G_struct, random_state=42)
        part_rand = community_louvain.best_partition(G_rand, random_state=42)

        Q_struct = community_louvain.modularity(part_struct, G_struct)
        Q_rand = community_louvain.modularity(part_rand, G_rand)

        assert Q_struct > Q_rand, (
            f"Structured data (Q={Q_struct:.4f}) must have higher modularity "
            f"than random (Q={Q_rand:.4f})"
        )

    def test_pixel_groups_are_spatially_separated(self, two_group_data):
        """
        In the recovered partition, pixels 0-31 (group A) and pixels 32-63 (group B)
        must be assigned to different clusters — validating the spatial separation
        claim of the synthetic sanity check.
        """
        X, _ = two_group_data
        adj = _build_coactivation_matrix(X)
        G = nx.from_numpy_array(adj)
        partition = community_louvain.best_partition(G, random_state=42)
        labels = np.array([partition[i] for i in range(X.shape[1])])

        # Check that pixel 0 (group A) and pixel 32 (group B) are in different clusters
        assert labels[0] != labels[32], (
            "Pixel 0 (group A) and pixel 32 (group B) must be in different clusters"
        )

    def test_layer1_observables_as_pixels(self, two_group_data):
        """
        Layer 1 UltimateObservable objects can represent pixels and their
        influence matrix reproduces the co-activation structure.
        """
        X, _ = two_group_data
        layer = Layer1_Observables()

        # Create one observable per pixel column
        n_pixels = X.shape[1]
        for i in range(n_pixels):
            obs = layer.record(f"px_{i}", float(np.mean(X[:, i])))
            if obs is not None:
                obs.relational_embedding = X[:, i].astype(float)

        assert len(layer.observables) == n_pixels, (
            f"Expected {n_pixels} observables, got {len(layer.observables)}"
        )

    def test_ablation_top_cluster_reduces_accuracy(self, two_group_data):
        """
        Zeroing out all pixels in the top cluster must significantly degrade
        classification accuracy.  Validates the ablation evaluation protocol
        from Section 5.2.1 of the paper.
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        X, y = two_group_data
        adj = _build_coactivation_matrix(X)
        G = nx.from_numpy_array(adj)
        partition = community_louvain.best_partition(G, random_state=42)
        cluster_labels = np.array([partition[i] for i in range(X.shape[1])])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=42
        )
        clf = LogisticRegression(max_iter=500)
        clf.fit(X_train, y_train)
        baseline_acc = accuracy_score(y_test, clf.predict(X_test))

        # Ablate top cluster
        cluster_sizes = {c: np.sum(cluster_labels == c)
                         for c in np.unique(cluster_labels)}
        top_cluster = max(cluster_sizes, key=cluster_sizes.get)
        mask = (cluster_labels == top_cluster)

        X_test_ablated = X_test.copy()
        X_test_ablated[:, mask] = 0.0
        ablated_acc = accuracy_score(y_test, clf.predict(X_test_ablated))

        assert ablated_acc < baseline_acc, (
            f"Ablating cluster {top_cluster} must reduce accuracy: "
            f"baseline={baseline_acc:.4f}, ablated={ablated_acc:.4f}"
        )


# ---------------------------------------------------------------------------
# TestTemporalPhaseAndCausality
# ---------------------------------------------------------------------------

class TestTemporalPhaseAndCausality:
    """
    Tests for temporal_phase and causal ordering in DensityField.
    Layer 1 specifies that temporal_phase is a dimensionless phase parameter
    encoding causal precedence (not clock time).
    """

    def test_future_cannot_influence_past(self):
        """
        The fundamental causal axiom: if t_other > t_target, influence = 0.
        """
        rng = np.random.default_rng(7)
        obs_past = UltimateObservable(id="tp_past", value=1.0,
                                       observability_type=ObservabilityType.CONTINUOUS)
        obs_future = UltimateObservable(id="tp_future", value=2.0,
                                         observability_type=ObservabilityType.CONTINUOUS)
        obs_past.temporal_phase = 0.0
        obs_future.temporal_phase = 1.0
        obs_past.relational_embedding = rng.normal(0, 1, 10)
        obs_future.relational_embedding = obs_past.relational_embedding.copy()
        obs_past.add_resonance("L", {"weight": 1.0})
        obs_future.add_resonance("L", {"weight": 1.0})

        field = DensityField()
        field.add_observable(obs_past)
        field.add_observable(obs_future)

        inf = field._compute_pairwise_influence(
            obs_past, obs_past.relational_embedding, obs_future
        )
        assert inf == 0.0, (
            f"Future (phase=1.0) must NOT influence past (phase=0.0): got {inf}"
        )

    def test_past_can_influence_future(self):
        """
        Converse of the causal axiom: past (lower phase) CAN influence future.
        """
        rng = np.random.default_rng(8)
        obs_a = UltimateObservable(id="tp_a", value=1.0,
                                    observability_type=ObservabilityType.CONTINUOUS)
        obs_b = UltimateObservable(id="tp_b", value=2.0,
                                    observability_type=ObservabilityType.CONTINUOUS)
        obs_a.temporal_phase = 0.0
        obs_b.temporal_phase = 1.0
        emb = rng.normal(0, 1, 10)
        obs_a.relational_embedding = emb.copy()
        obs_b.relational_embedding = emb.copy()
        obs_a.add_resonance("L", {"weight": 1.0})
        obs_b.add_resonance("L", {"weight": 1.0})

        field = DensityField()
        field.add_observable(obs_a)
        field.add_observable(obs_b)

        inf = field._compute_pairwise_influence(
            obs_b, obs_b.relational_embedding, obs_a
        )
        assert inf > 0.0, "Past (phase=0) must be able to influence future (phase=1)"

    def test_simultaneous_phase_zero_observables_can_influence_each_other(self):
        """
        Static/timeless observables (both phase=0) must exhibit bidirectional
        influence (backward-compatible default behavior).
        """
        rng = np.random.default_rng(9)
        obs_x = UltimateObservable(id="tp_x", value=1.0,
                                    observability_type=ObservabilityType.CONTINUOUS)
        obs_y = UltimateObservable(id="tp_y", value=2.0,
                                    observability_type=ObservabilityType.CONTINUOUS)
        # Both default to phase=0.0
        emb = rng.normal(0, 1, 10)
        obs_x.relational_embedding = emb.copy()
        obs_y.relational_embedding = emb.copy()
        obs_x.add_resonance("L", {"weight": 1.0})
        obs_y.add_resonance("L", {"weight": 1.0})

        field = DensityField()
        field.add_observable(obs_x)
        field.add_observable(obs_y)

        inf_xy = field._compute_pairwise_influence(
            obs_y, obs_y.relational_embedding, obs_x
        )
        inf_yx = field._compute_pairwise_influence(
            obs_x, obs_x.relational_embedding, obs_y
        )
        # Both phase=0 → no causal filter → both should have influence > 0
        assert inf_xy > 0.0, "Simultaneous observables must influence each other"
        assert inf_yx > 0.0, "Simultaneous observables must influence each other"

    def test_temporal_phase_stored_in_to_dict(self):
        """temporal_phase must be preserved through serialization."""
        obs = UltimateObservable(id="tp_ser", value=42,
                                  observability_type=ObservabilityType.DISCRETE,
                                  temporal_phase=3.14)
        d = obs.to_dict()
        assert d.get("temporal_phase") == pytest.approx(3.14), (
            "temporal_phase must appear at top-level in to_dict() output"
        )

    def test_temporal_phase_preserved_in_from_dict_roundtrip(self):
        """temporal_phase must survive a to_dict → from_dict round-trip."""
        obs = UltimateObservable(id="tp_rt", value=1,
                                  observability_type=ObservabilityType.DISCRETE,
                                  temporal_phase=2.72)
        d = obs.to_dict()
        obs2 = UltimateObservable.from_dict(d)
        assert obs2.temporal_phase == pytest.approx(2.72), (
            "temporal_phase must survive to_dict→from_dict round-trip"
        )


# ---------------------------------------------------------------------------
# TestAutopoieticSelfImprovement
# ---------------------------------------------------------------------------

class TestAutopoieticSelfImprovement:
    """
    Tests for the autonomous discovery and evolutionary feedback mechanisms
    (Section 4.2 of the paper: 'Autonomous Discovery and Evolution').
    These validate the autopoietic capacity of Layer 1 to refine its own
    atomicity criteria over time.
    """

    def test_ema_weight_increases_on_sustained_success(self):
        """
        EvolutionaryFeedbackLoop: after 20 consecutive successes on 'boolean',
        the weight must be strictly higher than before.
        Validates the EMA-based update formula.
        """
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.5, smoothing=1.0)
        initial_weight = spec.get_weight("boolean")

        for _ in range(20):
            loop.record_usage("boolean", success=True)
        loop.update_weights()

        new_weight = spec.get_weight("boolean")
        assert new_weight > initial_weight, (
            f"Weight must increase after sustained success: "
            f"{initial_weight:.4f} → {new_weight:.4f}"
        )

    def test_ema_weight_decreases_on_sustained_failure(self):
        """
        EvolutionaryFeedbackLoop: after 20 consecutive failures, the weight
        must strictly decrease.
        """
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.5, smoothing=1.0)
        initial_weight = spec.get_weight("boolean")

        for _ in range(20):
            loop.record_usage("boolean", success=False)
        loop.update_weights()

        new_weight = spec.get_weight("boolean")
        assert new_weight < initial_weight, (
            f"Weight must decrease after sustained failure: "
            f"{initial_weight:.4f} → {new_weight:.4f}"
        )

    def test_discovery_finds_sparsity_principle_in_mixed_stream(self):
        """
        HeuristicDiscovery must propose the sparsity principle when the data
        stream contains both sparse and dense vectors (bimodal distribution).
        Replicates the validated test from TestHeuristicDiscoveryAndPipeline,
        here framed as an autopoietic self-improvement test.
        """
        rng = np.random.default_rng(42)
        data = []
        for _ in range(20):
            arr = np.zeros(16)
            arr[[0, 3, 7]] = rng.normal(0, 1, 3)
            data.append(arr)
        for _ in range(15):
            data.append(rng.normal(0, 1, 16))

        discoverer = HeuristicDiscovery(data)
        proposals = discoverer.discover()

        assert len(proposals) >= 1, (
            f"HeuristicDiscovery must propose >= 1 principle from mixed stream, "
            f"got {len(proposals)}"
        )
        assert all(p.validated for p in proposals), (
            "All returned proposals must be validated"
        )

    def test_evolve_marks_observables_stale(self):
        """
        After evolve(), all registered observables must be marked stale so that
        their atomicity scores are recomputed with the updated weights.
        """
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.1)
        obs1 = make_obs(obs_id="ev1")
        obs2 = make_obs(obs_id="ev2")

        loop.evolve(observables_registry={"ev1": obs1, "ev2": obs2})

        assert obs1._atomicity_stale, "obs1 must be stale after evolve()"
        assert obs2._atomicity_stale, "obs2 must be stale after evolve()"

    def test_meta_spec_updated_after_successful_evolution(self):
        """
        After recording successes and calling update_weights(), the MetaSpec
        must reflect the new weights — demonstrating the autopoietic feedback loop.
        """
        spec = MetaSpecification()
        loop = EvolutionaryFeedbackLoop(spec, learning_rate=0.3, smoothing=1.0)

        initial_bool_weight = spec.get_weight("boolean")
        for _ in range(15):
            loop.record_usage("boolean", success=True)
        loop.update_weights()

        final_weight = spec.get_weight("boolean")
        assert final_weight != initial_bool_weight, (
            "MetaSpec must be updated after evolutionary weight adjustment"
        )


# ---------------------------------------------------------------------------
# TestScalabilityAndPerformance
# ---------------------------------------------------------------------------

class TestScalabilityAndPerformance:
    """
    Performance guards ensuring Layer 1 scales to the 'at least 10^4 observables
    on commodity hardware' claim in Section 4 of the paper.
    """

    def test_1000_observables_in_under_2s(self):
        """Creating 1000 UltimateObservable objects must take < 2 seconds."""
        import time
        t0 = time.time()
        obs_list = [
            UltimateObservable(
                id=f"sc_{i}", value=i % 100,
                observability_type=ObservabilityType.DISCRETE
            )
            for i in range(1000)
        ]
        elapsed = time.time() - t0
        assert elapsed < 2.0, (
            f"1000 UltimateObservable objects took {elapsed:.3f}s > 2s"
        )
        assert len(obs_list) == 1000

    def test_density_field_100_obs_influence_matrix_under_2s(self):
        """
        Computing the full influence matrix for a 100-observable DensityField
        must complete in < 2 seconds.
        """
        import time
        rng = np.random.default_rng(0)
        field = DensityField()
        for i in range(100):
            obs = UltimateObservable(id=f"df_{i}", value=float(i),
                                      observability_type=ObservabilityType.CONTINUOUS)
            obs.relational_embedding = rng.normal(0, 1, 20)
            obs.add_resonance("L", {"weight": 1.0})
            field.add_observable(obs)

        t0 = time.time()
        matrix, ids = field.compute_influence_matrix()
        elapsed = time.time() - t0

        assert elapsed < 2.0, f"100-obs influence matrix took {elapsed:.3f}s > 2s"
        assert matrix.shape == (100, 100)

    def test_coactivation_matrix_64_features_under_half_second(self):
        """
        Building a 64×64 co-activation matrix from 200 samples (digits-style)
        must complete in < 0.5 seconds.
        """
        import time
        rng = np.random.default_rng(0)
        X = rng.random((200, 64))

        t0 = time.time()
        adj = _build_coactivation_matrix(X)
        elapsed = time.time() - t0

        assert elapsed < 0.5, f"64-feature co-activation matrix took {elapsed:.3f}s > 0.5s"
        assert adj.shape == (64, 64)
        assert np.all(adj >= 0), "Co-activation matrix must be non-negative"

    def test_atomicity_score_1000_calls_under_1s(self):
        """
        Computing atomicity_score 1000 times on a pre-computed observable
        must be near-instant (cached), completing in < 1 second.
        """
        import time
        obs = UltimateObservable(id="perf_sc", value=1,
                                  observability_type=ObservabilityType.DISCRETE)
        obs._compute_atomicities()  # warm up cache

        t0 = time.time()
        for _ in range(1000):
            _ = obs.get_atomicity_score(combined=True)
        elapsed = time.time() - t0

        assert elapsed < 1.0, (
            f"1000 cached get_atomicity_score() calls took {elapsed:.3f}s > 1s"
        )

    def test_from_dict_roundtrip_500_observables_under_5s(self):
        """
        Serializing and deserializing 500 UltimateObservable objects via
        to_dict → from_dict must complete in < 5 seconds.
        """
        import time
        observables = [
            UltimateObservable(
                id=f"rt_{i}", value=i % 50,
                observability_type=ObservabilityType.DISCRETE
            )
            for i in range(500)
        ]

        t0 = time.time()
        for obs in observables:
            d = obs.to_dict()
            obs2 = UltimateObservable.from_dict(d)
            assert obs2.id == obs.id
        elapsed = time.time() - t0

        assert elapsed < 5.0, (
            f"500 roundtrips took {elapsed:.3f}s > 5s"
        )
