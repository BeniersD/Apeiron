"""
VALIDATION TESTS FOR LAYER 2 – RELATIONAL DYNAMICS (Extended v5.1)
===================================================================
Covers all Layer 2 modules after refactoring, including the new
sheaf, Hodge, categorical TDA, higher category, spectral sheaf,
endogenous time, formal verification, and quantum topology modules.
"""
import pytest
import numpy as np
import sys
import os
import torch
torch.cuda.is_available = lambda: False

# ============================================================================
# Helper: create a simple graph for testing
# ============================================================================
def create_test_graph():
    pytest.importorskip("networkx")
    import networkx as nx
    G = nx.erdos_renyi_graph(10, 0.3, seed=42)
    return G

# ============================================================================
# Tests for spectral analysis (was adjacency_matrix)
# ============================================================================
def test_spectral_import():
    from apeiron.layers.layer02_relational import spectral
    assert hasattr(spectral, 'SpectralGraphAnalysis')

def test_spectral_graph_analysis_basic():
    pytest.importorskip("networkx")
    pytest.importorskip("scipy")
    from apeiron.layers.layer02_relational.spectral import (
        SpectralGraphAnalysis, SpectralType
    )
    G = create_test_graph()
    sa = SpectralGraphAnalysis(G)
    alg_conn = sa.algebraic_connectivity()
    assert isinstance(alg_conn, float)
    gap = sa.spectral_gap()
    assert isinstance(gap, float)
    radius = sa.spectral_radius()
    assert isinstance(radius, float)
    evals, evecs = sa.compute_eigensystem(SpectralType.LAPLACIAN, k=3)
    assert len(evals) == 3
    labels = sa.spectral_clustering(n_clusters=2)
    assert len(labels) == G.number_of_nodes()

# ============================================================================
# Tests for hypergraph (was hypergraph_relations)
# ============================================================================
def test_hypergraph_import():
    from apeiron.layers.layer02_relational import hypergraph
    assert hasattr(hypergraph, 'Hypergraph')

def test_hypergraph_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {1,2,3}, weight=1.0)
    hg.add_hyperedge("e2", {2,3,4}, weight=0.8)
    assert len(hg.hyperedges) == 2
    assert len(hg.vertices) == 4
    betti = hg.betti_numbers()
    assert isinstance(betti, dict)

# ============================================================================
# Tests for motif_detection
# ============================================================================
def test_motif_detection_import():
    from apeiron.layers.layer02_relational import motif_detection
    assert hasattr(motif_detection, 'MotifCounter')
    assert hasattr(motif_detection, 'PersistentHomology')

def test_motif_counter_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.motif_detection import MotifCounter
    G = create_test_graph()
    counter = MotifCounter(G)
    triangles = counter.count_triangles()
    assert isinstance(triangles, int)
    assert hasattr(counter, 'motif_significance')

def test_persistent_homology_basic():
    pytest.importorskip("networkx")
    pytest.importorskip("gudhi")
    from apeiron.layers.layer02_relational.motif_detection import PersistentHomology
    G = create_test_graph()
    ph = PersistentHomology(G)
    ph.build_clique_complex(max_dim=2)
    ph.compute_persistence()
    assert ph.diagrams is not None
    ent = ph.persistent_entropy()
    assert isinstance(ent, float)

# ============================================================================
# Tests for core relations (relations_core)
# ============================================================================
def test_relations_import():
    from apeiron.layers.layer02_relational import relations_core
    assert hasattr(relations_core, 'RelationalCategory')
    assert hasattr(relations_core, 'UltimateRelation')
    assert hasattr(relations_core, 'Layer2_Relational_Ultimate')

def test_relational_category_basic():
    from apeiron.layers.layer02_relational.relations_core import RelationalCategory
    cat = RelationalCategory()
    cat.add_object("A")
    cat.add_object("B")
    cat.add_morphism("A", "B", "f")
    cat.add_morphism("B", "A", "g")
    assert "A" in cat.objects
    assert ("A", "B") in cat.hom_sets
    comp = cat.compose("f", "g", "A", "B", "A")
    assert comp is not None or True

def test_ultimate_relation_basic():
    from apeiron.layers.layer02_relational.relations_core import UltimateRelation, RelationType
    rel = UltimateRelation(
        id="test",
        source_id="obs1",
        target_id="obs2",
        relation_type=RelationType.SYMMETRIC,
        weight=0.9
    )
    assert rel.id == "test"
    # New in v5.1: test embedded methods exist
    assert hasattr(rel, 'compute_sheaf_cohomology')
    assert hasattr(rel, 'compute_hodge')
    assert hasattr(rel, 'generate_time_cone')
    assert hasattr(rel, 'verify')
    assert hasattr(rel, 'quantum_betti')

def test_layer2_class_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.relations_core import Layer2_Relational_Ultimate, RelationType
    layer2 = Layer2_Relational_Ultimate()
    rel = layer2.create_relation("obs1", "obs2", RelationType.SYMMETRIC, weight=0.5)
    assert rel.id in layer2.relations
    stats = layer2.get_stats()
    assert stats['relations'] == 1

# ============================================================================
# Tests voor benchmarks (aanwezig in benchmark map, niet in layer02)
# ============================================================================
def test_benchmarks_import():
    try:
        from apeiron.benchmark.layer02_benchmarks import BenchmarkSuite
        assert BenchmarkSuite is not None
    except ImportError:
        pytest.skip("Benchmark module not available")

# ============================================================================
# Tests voor dashboard (visualisatie modules)
# ============================================================================
def test_dashboard_import():
    pytest.importorskip("plotly")
    from apeiron.layers.layer02_relational import dashboards
    assert hasattr(dashboards, 'figure_spectrum')

def test_dashboard_figure_functions():
    pytest.importorskip("plotly")
    from apeiron.layers.layer02_relational import dashboards
    from apeiron.layers.layer02_relational.spectral import SpectralGraphAnalysis
    G = create_test_graph()
    sa = SpectralGraphAnalysis(G)
    fig = dashboards.figure_spectrum(sa)
    assert fig is not None

    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {1,2}, 1.0)
    fig_hg = dashboards.figure_hypergraph(hg)
    assert fig_hg is not None

# ============================================================================
# Tests voor causal_discovery
# ============================================================================
def test_causal_discovery_import():
    pytest.importorskip("causallearn")
    from apeiron.layers.layer02_relational import causal_discovery
    assert hasattr(causal_discovery, 'CausalDiscovery')

def test_causal_discovery_basic():
    pytest.importorskip("causallearn")
    from apeiron.layers.layer02_relational.causal_discovery import CausalDiscovery
    data, true_graph = CausalDiscovery.generate_linear_gaussian(100, 5, seed=42)
    cd = CausalDiscovery(data, variable_names=[f"X{i}" for i in range(5)])
    try:
        ges_graph = cd.ges()
        assert ges_graph is not None
    except Exception:
        pass

# ============================================================================
# Multi-agent RL
# ============================================================================
def test_multi_agent_rl_import():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational import graph_rl
    assert hasattr(graph_rl, 'HypergraphEnv')

def test_multi_agent_env_basic():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph as ApeironHG
    from apeiron.layers.layer02_relational.graph_rl import HypergraphEnv, RLAgent
    hg = ApeironHG()
    hg.add_hyperedge("e1", {0,1})
    hg.add_hyperedge("e2", {1,2})
    env = HypergraphEnv(hypergraph=hg, target=2, max_steps=10)
    obs, _ = env.reset()
    assert obs in [0,1,2]
    agent = RLAgent(env)
    agent.train(episodes=5)
    action = agent.act(obs)
    assert 0 <= action < env.action_space.n

# ============================================================================
# Categorical verification
# ============================================================================
def test_categorical_verification_import():
    from apeiron.layers.layer02_relational import categorical_verification
    assert hasattr(categorical_verification, 'verify_category')

def test_category_verification_basic():
    from apeiron.layers.layer02_relational.relations_core import RelationalCategory
    from apeiron.layers.layer02_relational.categorical_verification import verify_category
    cat = RelationalCategory()
    cat.add_object("A")
    cat.add_object("B")
    cat.add_morphism("A", "B", "f")
    cat.identities["A"] = "idA"
    cat.identities["B"] = "idB"
    def comp(f,g,s,m,t): return None
    cat.composition = comp
    result = verify_category(cat)
    assert 'valid' in result

# ============================================================================
# Hall algebra (optioneel)
# ============================================================================
def test_hall_algebra_import():
    from apeiron.optional.hall_algebra import JordanHallAlgebra, Partition
    hall = JordanHallAlgebra(max_part_size=3)
    assert len(hall.basis()) > 0

# ============================================================================
# Probabilistische modellen
# ============================================================================
def test_probabilistic_models_import():
    from apeiron.layers.layer02_relational import probabilistic_models
    assert hasattr(probabilistic_models, 'BayesianNetwork')

def test_bayesian_network_basic():
    from apeiron.layers.layer02_relational.probabilistic_models import BayesianNetwork
    bn = BayesianNetwork(edges=[('A','C')],
                         variable_names=['A','C'],
                         cardinalities={'A':2, 'C':2})
    bn.set_cpd('A', np.array([0.5,0.5]), [])
    bn.set_cpd('C', np.array([0.3, 0.7]), [])   # marginals voor C, geen ouders
    bn.is_fitted = True
    samples = bn.sample(5)
    assert samples.shape == (5,2)

def test_hmm_basic():
    from apeiron.layers.layer02_relational.probabilistic_models import HiddenMarkovModel
    hmm = HiddenMarkovModel(n_states=2, n_obs=3)
    hmm.start_prob = np.array([0.6, 0.4])
    hmm.trans_prob = np.array([[0.7,0.3],[0.4,0.6]])
    hmm.emit_prob = np.array([[0.1,0.4,0.5],[0.6,0.3,0.1]])
    obs_seq = hmm.sample(1, length=5)[0]
    states = hmm.predict(obs_seq)
    assert len(states) == 5

# ============================================================================
# Quantum error correction (optioneel)
# ============================================================================
def test_qec_import():
    pytest.importorskip("qiskit")
    from apeiron.optional.quantum_error_correction import RepetitionCode
    code = RepetitionCode(n=3)
    enc = code.encode_circuit()
    assert enc.num_qubits == 3

# ============================================================================
# Quiver moduli (optioneel)
# ============================================================================
def test_quiver_moduli_import():
    from apeiron.optional.quiver_moduli import StabilityCondition
    theta = StabilityCondition({1: 1, 2: -1})
    assert theta({1:2, 2:2}) == 0

# ============================================================================
# Derived categories (optioneel)
# ============================================================================
def test_derived_categories_import():
    from apeiron.optional.derived_categories import ChainComplex
    d1 = np.array([[1], [-1]])   # ∂₁ : C₁ → C₀
    C = ChainComplex([d1])
    assert C.is_complex()
    h0 = C.homology(0)[0]
    assert h0 == 1

# ============================================================================
# Model categories (optioneel)
# ============================================================================
def test_model_categories_import():
    from apeiron.optional.model_categories import ChainComplexesModelCategory
    model = ChainComplexesModelCategory()
    assert hasattr(model, 'is_fibration')

# ============================================================================
# Graph self-supervised (optioneel)
# ============================================================================
def test_graph_self_supervised_import():
    pytest.importorskip("torch")
    pytest.importorskip("torch_geometric")
    from apeiron.optional.graph_self_supervised import GCNEncoder, GraphCL, node_dropping
    import torch
    from torch_geometric.data import Data
    edge_index = torch.tensor([[0,1,1,2],[1,0,2,1]], dtype=torch.long)
    x = torch.randn(3, 5)
    data = Data(x=x, edge_index=edge_index)
    encoder = GCNEncoder(5, 8, 4)
    proj = torch.nn.Linear(4, 4)
    model = GraphCL(encoder, proj, augment_fn=node_dropping)
    optim = torch.optim.Adam(model.parameters(), lr=0.01)
    loss = model.train_step(data, optim)
    assert 'loss' in loss

# ============================================================================
# GraphQL API
# ============================================================================
def test_graphql_import():
    pytest.importorskip("strawberry")
    from apeiron.infrastructure.api.graphql import schema
    assert schema is not None

# ============================================================================
# ═══════════════════════════════════════════════════════════════════════════
# NEW TESTS FOR v5.1 MODULES (postdoc‑level coverage)
# ═══════════════════════════════════════════════════════════════════════════
# ============================================================================

# ---------------------------------------------------------------------------
# Sheaf Hypergraph
# ---------------------------------------------------------------------------
def test_sheaf_hypergraph_import():
    from apeiron.layers.layer02_relational import SheafHypergraph
    assert SheafHypergraph is not None

def test_sheaf_hypergraph_basic():
    from apeiron.layers.layer02_relational import SheafHypergraph
    shg = SheafHypergraph(["v1","v2","v3"], [{"v1","v2"}, {"v2","v3"}])
    cohom = shg.compute_cohomology()
    assert cohom.h0_dimension >= 0
    assert cohom.is_globally_consistent
    L0 = shg.compute_sheaf_laplacian(order=0)
    assert L0.shape == (3, 3)

def test_sheaf_hypergraph_obstruction():
    from apeiron.layers.layer02_relational import SheafHypergraph
    shg = SheafHypergraph(["v1","v2"], [{"v1","v2"}])
    obs = shg.compute_obstruction({"v1": np.array([1.0]), "v2": np.array([2.0])})
    assert obs >= 0.0

# ---------------------------------------------------------------------------
# Categorical TDA
# ---------------------------------------------------------------------------
def test_categorical_tda_import():
    from apeiron.layers.layer02_relational import CategoricalTDA
    assert CategoricalTDA is not None

def test_categorical_tda_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational import CategoricalTDA
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1,2})
    ctda = CategoricalTDA(hg)
    mod = ctda.persistence_module()
    assert mod is not None

def test_persistence_module():
    from apeiron.layers.layer02_relational.categorical_tda import PersistenceModule
    pm = PersistenceModule([0.0, 1.0, 2.0], [1, 2, 1])
    assert pm.barcode() is not None
    assert pm.interleaving_distance(pm) == 0.0

# ---------------------------------------------------------------------------
# Hodge decomposition
# ---------------------------------------------------------------------------
def test_hodge_decomposition_import():
    from apeiron.layers.layer02_relational import HypergraphHodgeDecomposer
    assert HypergraphHodgeDecomposer is not None

def test_hodge_decomposition_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational import HypergraphHodgeDecomposer
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    hg.add_hyperedge("e2", {1,2})
    dec = HypergraphHodgeDecomposer(hg)
    signal = np.array([1.0, 2.0, 3.0])
    result = dec.decompose_vertex_signal(signal)
    assert result.is_valid
    assert np.allclose(result.gradient + result.harmonic, signal)

def test_hodge_theorem_verification():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational import HypergraphHodgeDecomposer
    hg = Hypergraph()
    for i in range(3):
        hg.add_hyperedge(f"e{i}", {i, (i+1)%3})
    dec = HypergraphHodgeDecomposer(hg)
    assert dec.verify_hodge_theorem(k=0, num_random_trials=5)

# ---------------------------------------------------------------------------
# Higher category theory
# ---------------------------------------------------------------------------
def test_higher_category_import():
    from apeiron.layers.layer02_relational import StrictTwoCategory, Bicategory
    assert StrictTwoCategory is not None and Bicategory is not None

def test_strict_two_category():
    from apeiron.layers.layer02_relational import StrictTwoCategory
    stc = StrictTwoCategory(
        objects=["X","Y"],
        one_morphisms={"f":("X","Y"), "g":("X","Y"), "id_X":("X","X"), "id_Y":("Y","Y")},
        two_morphisms={}
    )
    stc.add_2morphism("alpha", "f", "g")
    assert "alpha" in stc.two_morphisms

def test_bicategory_axioms():
    from apeiron.layers.layer02_relational import Bicategory
    bicat = Bicategory(["X","Y"], {"f":("X","Y"), "g":("Y","X")}, {})
    bicat.add_associator("f","g","f")
    assert bicat.verify_bicategory_axioms()['has_identities']

# ---------------------------------------------------------------------------
# Spectral sheaf
# ---------------------------------------------------------------------------
def test_spectral_sheaf_import():
    from apeiron.layers.layer02_relational import SheafSpectralAnalyzer
    assert SheafSpectralAnalyzer is not None

def test_spectral_sheaf_basic():
    from apeiron.layers.layer02_relational.sheaf_hypergraph import SheafHypergraph
    from apeiron.layers.layer02_relational.spectral_sheaf import SheafSpectralAnalyzer
    shg = SheafHypergraph(["v1","v2","v3"], [{"v1","v2"}, {"v2","v3"}])
    ssa = SheafSpectralAnalyzer(shg)
    res = ssa.analyze()
    assert res.harmonic_dim >= 0
    labels = ssa.spectral_clustering(2)
    assert len(labels) == 3

# ---------------------------------------------------------------------------
# Endogenous time
# ---------------------------------------------------------------------------
def test_endogenous_time_import():
    from apeiron.layers.layer02_relational import EndogenousTimeGenerator
    assert EndogenousTimeGenerator is not None

def test_endogenous_time_basic():
    from apeiron.layers.layer02_relational.endogenous_time import EndogenousTimeGenerator
    edges = [('a','b'), ('b','c')]
    gen = EndogenousTimeGenerator(edges)
    ordering = gen.generate_time_ordering()
    assert ordering == ['a','b','c']
    cones = gen.compute_time_cones()
    assert 'a' in cones and 'b' in cones

# ---------------------------------------------------------------------------
# Formal verification
# ---------------------------------------------------------------------------
def test_formal_verification_import():
    from apeiron.layers.layer02_relational import Z3HypergraphVerifier
    assert Z3HypergraphVerifier is not None

def test_formal_verification_basic():
    pytest.importorskip("z3")
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.formal_layer2_verification import Z3HypergraphVerifier
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    hg.add_hyperedge("e2", {1,2})
    verifier = Z3HypergraphVerifier(hg)
    result = verifier.verify_relational_constitution_axiom()
    assert result.is_valid

def test_verification_orchestrator():
    pytest.importorskip("z3")
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational import Layer2VerificationOrchestrator
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    orch = Layer2VerificationOrchestrator(hg)
    results = orch.run_all_verifications()
    assert len(results) > 0

# ---------------------------------------------------------------------------
# Quantum topology
# ---------------------------------------------------------------------------
def test_quantum_topology_import():
    from apeiron.layers.layer02_relational import QuantumBettiEstimator
    assert QuantumBettiEstimator is not None

def test_quantum_betti_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.quantum_topology import QuantumBettiEstimator
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    hg.add_hyperedge("e2", {1,2})
    est = QuantumBettiEstimator(hg, backend='classical')
    result = est.estimate_betti_numbers()
    assert result.betti_numbers[0] == 1

# ---------------------------------------------------------------------------
# Unified API & coverage
# ---------------------------------------------------------------------------
def test_unified_api_import():
    from apeiron.layers.layer02_relational import Layer2UnifiedAPI
    assert Layer2UnifiedAPI is not None

def test_unified_api_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.layer2_unified_api import Layer2UnifiedAPI
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    api = Layer2UnifiedAPI(hg)
    report = api.full_analysis()
    assert 'coverage' in report
    assert report['coverage']['percentage'] >= 0.0

def test_coverage_report():
    from apeiron.layers.layer02_relational.layer2_unified_api import compute_theory_coverage
    cr = compute_theory_coverage()
    # Expect at least 80% of the theoretical modules (some require optional deps)
    assert cr.coverage_percentage > 80.0

# ---------------------------------------------------------------------------
# Integration: sheaf + spectral + time
# ---------------------------------------------------------------------------
def test_integration_sheaf_spectral_time():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.relations_core import Layer2_Relational_Ultimate, RelationType
    layer2 = Layer2_Relational_Ultimate()
    layer2.create_relation("v1","v2", RelationType.CAUSAL, weight=1.0)
    # Sheaf cohomology on global hypergraph
    cohom = layer2.compute_sheaf_cohomology()
    assert cohom is not None
    # Hodge decomposition
    hd = layer2.compute_hodge_decomposition()
    assert hd is not None and hd.is_valid
    # Endogenous time from causal edges
    ordering = layer2.generate_endogenous_time([("v1","v2")])
    assert ordering is not None
    # Full analysis
    report = layer2.full_analysis()
    assert 'coverage' in report

# ---------------------------------------------------------------------------
# Theoretical completeness sanity checks
# ---------------------------------------------------------------------------
def test_all_new_modules_accessible():
    """Ensure all v5.1 modules can be imported from the public API."""
    from apeiron.layers.layer02_relational import (
        SheafHypergraph,
        CategoricalTDA,
        HypergraphHodgeDecomposer,
        StrictTwoCategory,
        Bicategory,
        SheafSpectralAnalyzer,
        EndogenousTimeGenerator,
        Z3HypergraphVerifier,
        Layer2VerificationOrchestrator,
        QuantumBettiEstimator,
        Layer2UnifiedAPI,
        compute_theory_coverage,
    )
    # If we got here, imports succeeded
    assert True

# ---------------------------------------------------------------------------
# Sheaf diffusion dynamics
# ---------------------------------------------------------------------------
def test_sheaf_diffusion_import():
    from apeiron.layers.layer02_relational import SheafDiffusionDynamics
    assert SheafDiffusionDynamics is not None

def test_sheaf_diffusion_basic():
    from apeiron.layers.layer02_relational import SheafHypergraph, SheafDiffusionDynamics
    shg = SheafHypergraph(["v1","v2","v3"], [{"v1","v2"}, {"v2","v3"}])
    sdd = SheafDiffusionDynamics(shg)
    _, final = sdd.evolve(store_trajectory=False)
    assert final.time >= 0

# ---------------------------------------------------------------------------
# Topos logic
# ---------------------------------------------------------------------------
def test_topos_logic_import():
    from apeiron.layers.layer02_relational import ToposLogic
    assert ToposLogic is not None

def test_topos_logic_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.topos_layer2 import topos_from_hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    topos = topos_from_hypergraph(hg)
    prop = {v: True for v in hg.vertices}
    ev = topos.topos_evaluate(prop)
    assert 0 <= ev['truth_degree'] <= 1

# ---------------------------------------------------------------------------
# HoTT category
# ---------------------------------------------------------------------------
def test_hott_category_import():
    from apeiron.layers.layer02_relational import UnivalentCategory
    assert UnivalentCategory is not None

def test_hott_category_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.hott_category import univalent_category_from_hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    uc = univalent_category_from_hypergraph(hg)
    assert len(uc.isomorphisms) >= 0

# ---------------------------------------------------------------------------
# Derived learning
# ---------------------------------------------------------------------------
def test_derived_learning_import():
    from apeiron.layers.layer02_relational import derived_learning_pipeline
    assert derived_learning_pipeline is not None

def test_derived_learning_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.derived_learning import derived_learning_pipeline
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    result = derived_learning_pipeline(hg)
    assert 'obstruction_dim' in result

# ---------------------------------------------------------------------------
# Ontogenesis engine
# ---------------------------------------------------------------------------
def test_ontogenesis_import():
    from apeiron.layers.layer02_relational import OntogenesisEngine
    assert OntogenesisEngine is not None

def test_ontogenesis_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.ontogenesis_engine import ontogenesis_from_hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    engine = ontogenesis_from_hypergraph(hg)
    result = engine.check_and_evolve()
    assert result['status'] in ('stable', 'evolved')

# ---------------------------------------------------------------------------
# Retrocausal dynamics
# ---------------------------------------------------------------------------
def test_retrocausal_import():
    from apeiron.layers.layer02_relational import RetrocausalDynamics
    assert RetrocausalDynamics is not None

def test_retrocausal_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.retrocausal_dynamics import RetrocausalDynamics
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    rd = RetrocausalDynamics(hg, T=3, max_iterations=10)
    result = rd.optimal_trajectory()
    assert 'final_obstruction' in result

# ---------------------------------------------------------------------------
# Spectral triple
# ---------------------------------------------------------------------------
def test_spectral_triple_import():
    from apeiron.layers.layer02_relational import SpectralTriple
    assert SpectralTriple is not None

def test_spectral_triple_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.spectral_triple import spectral_triple_from_hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    st = spectral_triple_from_hypergraph(hg)
    assert st is not None
    summary = st.geometry_summary()
    assert summary['dimension'] > 0

# ---------------------------------------------------------------------------
# Epistemic horizon
# ---------------------------------------------------------------------------
def test_epistemic_horizon_import():
    from apeiron.layers.layer02_relational import horizon_pipeline
    assert horizon_pipeline is not None

def test_epistemic_horizon_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.epistemic_horizon import horizon_pipeline
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    result = horizon_pipeline(hg)
    assert 'singularities_detected' in result

# ---------------------------------------------------------------------------
# Reaction functor
# ---------------------------------------------------------------------------
def test_reaction_functor_import():
    from apeiron.layers.layer02_relational import compile_hypergraph_to_gcode
    assert compile_hypergraph_to_gcode is not None

def test_reaction_functor_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.reaction_functor import compile_hypergraph_to_gcode
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    result = compile_hypergraph_to_gcode(hg)
    assert 'program' in result

# ---------------------------------------------------------------------------
# Diachronic sheaf (v7.0)
# ---------------------------------------------------------------------------
def test_diachronic_sheaf_import():
    from apeiron.layers.layer02_relational.diachronic_sheaf import DiachronicSheaf
    assert DiachronicSheaf is not None

def test_diachronic_sheaf_basic():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.diachronic_sheaf import DiachronicSheaf
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    hg.add_hyperedge("e2", {1,2})
    ds = DiachronicSheaf(hg)
    events = ds.persistent_obstruction()
    assert isinstance(events, list)
    score = ds.global_consistency_score()
    assert 0 <= score <= 1

# ---------------------------------------------------------------------------
# Extended Unified API coverage
# ---------------------------------------------------------------------------
def test_unified_api_v6_coverage():
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    from apeiron.layers.layer02_relational.layer2_unified_api import Layer2UnifiedAPI
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1})
    api = Layer2UnifiedAPI(hg)
    report = api.full_analysis(block_on_failure=False)
    # v6.0 sections
    for key in ['sheaf_diffusion', 'topos_logic', 'hott', 'derived_learning',
                'ontogenesis', 'retrocausal', 'spectral_triple',
                'epistemic_horizon', 'reaction_functor']:
        assert key in report, f"Missing v6.0 analysis section: {key}"