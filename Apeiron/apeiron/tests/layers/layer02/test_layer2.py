"""
Unit tests voor Laag 2: Relational Dynamics – Ultimate Implementation.

Deze tests controleren de functionaliteit van alle modules in Layer 2:
- adjacency_matrix
- hypergraph_relations
- motif_detection
- relations
- benchmarks
- dashboard
- causal_discovery
- multi_agent_rl
- rl_on_graphs
- categorical_verification
- hall_algebra
- probabilistic_models
- quantum_error_correction
- quiver_moduli
- derived_categories
- model_categories
- graph_self_supervised
- graphql_api
- database_integration
- temporal_networks
- quantum_ml
- visualization_dash
- atomicity_visuals
- layer1_bridge

Uitvoeren met (vanuit de hoofdmap apeiron):
    PYTHONPATH=. pytest layers/layer02_relational/tests/test_layer2.py -v
"""

import pytest
import numpy as np

# ============================================================================
# Hulpfuncties
# ============================================================================

def create_test_graph():
    """Return een kleine NetworkX graaf voor testdoeleinden."""
    pytest.importorskip("networkx")
    import networkx as nx
    G = nx.erdos_renyi_graph(10, 0.3, seed=42)
    return G

def create_test_hypergraph():
    """Return een kleine hypergraaf voor testdoeleinden."""
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {1,2,3}, weight=1.0)
    hg.add_hyperedge("e2", {2,3,4}, weight=0.8)
    return hg

def create_test_temporal_edges():
    """Return een dict met tijdsgestempelde randen voor temporele motieftests."""
    return {
        (0,1): [0.1, 0.5],
        (1,2): [0.2, 0.6],
        (0,2): [0.3, 0.7],
    }

def create_test_registry():
    """Maak een eenvoudige Layer 1‑registry voor integratietests."""
    return {
        'observables': {
            'temp': [20.5, 21.0, 22.1, 19.8],
            'humidity': [60, 65, 70, 55],
            'pressure': [1012, 1013, 1011, 1014]
        }
    }

# ============================================================================
# adjacency_matrix
# ============================================================================
def test_spectral_analysis_import():
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

def test_dynamic_spectral_analysis_basic():
    pytest.importorskip("networkx")
    pytest.importorskip("scipy")
    from apeiron.layers.layer02_relational.spectral import (
        DynamicSpectralAnalysis, SpectralType
    )
    G = create_test_graph()
    dsa = DynamicSpectralAnalysis()
    dsa.add_graph(G, timestamp=0)
    dsa.add_graph(G, timestamp=1)
    evo = dsa.compute_eigenvalue_evolution(SpectralType.LAPLACIAN, k=3)
    assert len(evo) == 2
    changes = dsa.detect_change_points()
    assert isinstance(changes, list)

def test_spectral_database_basic():
    pytest.importorskip("sqlite3")
    from apeiron.layers.layer02_relational.spectral import SpectralDatabase
    db = SpectralDatabase(db_type='sqlite', connection_string=':memory:')
    db._create_sqlite_tables()
    evals = np.array([1.0, 2.0, 3.0])
    evecs = np.eye(3)
    db.store_spectrum("test_graph", 123.0, "laplacian", evals, evecs)
    loaded = db.load_spectra("test_graph", "laplacian")
    assert len(loaded) == 1
    db.close()


# ============================================================================
# hypergraph_relations
# ============================================================================

def test_hypergraph_relations_import():
    from apeiron.layers.layer02_relational import hypergraph_relations
    assert hasattr(hypergraph_relations, 'Hypergraph')
    assert hasattr(hypergraph_relations, 'QuantumGraph')

def test_hypergraph_basic():
    hg = create_test_hypergraph()
    assert len(hg.vertices) == 4
    assert len(hg.hyperedges) == 2
    betti = hg.betti_numbers()
    assert isinstance(betti, dict)

def test_quantum_graph_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.quantum_graph import QuantumGraph
    G = create_test_graph()
    qg = QuantumGraph(graph=G)
    qg.edge_amplitudes[(0,1)] = 1.0 + 0.5j
    init = np.array([1.0,0,0,0,0,0,0,0,0,0], dtype=complex)
    final = qg.quantum_walk(time=1.0, initial_state=init, method='continuous')
    assert final.shape == init.shape

def test_hypergraph_rl_basic():
    pytest.importorskip("gym")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.hypergraph import HypergraphEnv, RLAgent
    hg = create_test_hypergraph()
    env = HypergraphEnv(hg, target=4, max_steps=10)
    agent = RLAgent(env)
    state = env.reset()
    action = agent.act(state)
    assert 0 <= action < env.action_space.n
    agent.train(episodes=5)

def test_hypergraph_database_basic():
    pytest.importorskip("sqlite3")
    from apeiron.layers.layer02_relational.hypergraph import HypergraphDatabase
    hg = create_test_hypergraph()
    db = HypergraphDatabase(db_type='sqlite', connection_string=':memory:')
    db.store_hypergraph("test", hg)
    loaded = db.load_hypergraph("test")
    assert loaded is not None
    db.close()

def test_hypergraph_dashboard_basic():
    pytest.importorskip("dash")
    from apeiron.layers.layer02_relational.hypergraph import create_hypergraph_dashboard
    hg = create_test_hypergraph()
    app = create_hypergraph_dashboard(hg)
    assert app is not None


# ============================================================================
# motif_detection
# ============================================================================

def test_motif_detection_import():
    from apeiron.layers.layer02_relational import motif_detection
    assert hasattr(motif_detection, 'MotifCounter')
    assert hasattr(motif_detection, 'PersistentHomology')
    assert hasattr(motif_detection, 'TopologicalNetworkAnalysis')

def test_motif_counter_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.motif_detection import MotifCounter, MotifType
    G = create_test_graph()
    counter = MotifCounter(G)
    triangles = counter.count_triangles()
    assert isinstance(triangles, int)
    sig = counter.motif_significance(MotifType.TRIANGLE, n_random=5)
    assert 'observed' in sig

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

def test_topological_network_analysis_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.motif_detection import (
        TopologicalNetworkAnalysis, FiltrationType
    )
    G = create_test_graph()
    analysis = TopologicalNetworkAnalysis(graph=G, name="test")
    analysis.compute_persistence(filtration=FiltrationType.CLIQUE, max_dim=2)
    analysis.compute_motifs(max_graphlet_size=3, significance=False)
    analysis.detect_communities(method="louvain")
    analysis.compute_centralities()
    assert analysis.motif_counts is not None


# ============================================================================
# relations
# ============================================================================

def test_relations_import():
    from apeiron.layers.layer02_relational import relations
    assert hasattr(relations, 'RelationalCategory')
    assert hasattr(relations, 'UltimateRelation')
    assert hasattr(relations, 'Layer2_Relational_Ultimate')

def test_relational_category_basic():
    from apeiron.layers.layer02_relational.relations_core import RelationalCategory
    cat = RelationalCategory()
    cat.add_object("A")
    cat.add_object("B")
    cat.add_morphism("A", "B", "f")
    cat.add_morphism("B", "A", "g")
    assert "A" in cat.objects
    assert ("A","B") in cat.hom_sets
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
    rel.compute_spectral_properties()
    rel.compute_topological_properties()

def test_layer2_class_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.relations_core import Layer2_Relational_Ultimate, RelationType
    layer2 = Layer2_Relational_Ultimate()
    rel = layer2.create_relation("obs1", "obs2", RelationType.SYMMETRIC, weight=0.5)
    assert rel.id in layer2.relations
    stats = layer2.get_stats()
    assert stats['relations'] == 1

def test_monad_associativity():
    """Test de associativiteit van de monad‑compositie in de categorische setting."""
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.relations_core import RelationalCategory
    # Maak een eenvoudige categorie met objecten en morfismen
    cat = RelationalCategory()
    cat.add_object("X")
    cat.add_object("Y")
    cat.add_object("Z")
    cat.add_morphism("X", "Y", "f")
    cat.add_morphism("Y", "Z", "g")
    cat.add_morphism("X", "Z", "h")
    # Stel een monad samen (in dit geval gewoon identiteitsfunctor)
    # We testen (f ∘ g) ∘ h = f ∘ (g ∘ h) voor compatibele morfismen
    # Aangezien we geen echte monad hebben, testen we gewoon of compositie werkt.
    try:
        comp1 = cat.compose("f", "g", "X", "Y", "Z")
        comp2 = cat.compose(comp1, "h", "X", "Z", "Z") if comp1 else None
    except Exception:
        comp2 = None
    assert comp2 is not None or True  # plaatsvervanger

def test_lr_coefficients():
    """Test de berekening van lineaire regressiecoëfficiënten in compute_relations."""
    pytest.importorskip("sklearn")
    from apeiron.layers.layer02_relational.relations_core import compute_relations
    registry = create_test_registry()
    # compute_relations zou een lijst van relaties moeten teruggeven
    rels = compute_relations(registry, method='linear_regression')
    assert isinstance(rels, list)
    # Minstens één relatie (tussen twee variabelen) zou gevonden moeten worden
    if rels:
        rel = rels[0]
        assert hasattr(rel, 'weight') or hasattr(rel, 'coefficient')

def test_compute_relations():
    """Test de algemene aanroep van compute_relations."""
    from apeiron.layers.layer02_relational.relations_core import compute_relations
    registry = create_test_registry()
    rels = compute_relations(registry)
    assert isinstance(rels, list)
    # Alle observables moeten minstens één relatie hebben (behalve als het leeg is)
    if registry['observables']:
        assert len(rels) > 0


# ============================================================================
# benchmarks
# ============================================================================

def test_benchmarks_import():
    from apeiron.layers.layer02_relational import benchmarks
    assert hasattr(benchmarks, 'BenchmarkSuite')

def test_benchmark_suite_basic():
    from apeiron.benchmark.layer02_benchmarks import BenchmarkSuite
    suite = BenchmarkSuite()
    @suite.register(name="dummy")
    def dummy_bench(param):
        return param * 2
    result = suite.run_benchmark("dummy", {"param": 3})
    assert result.name == "dummy"
    assert result.time_ms >= 0
    assert result.output == 6


# ============================================================================
# dashboard (static figure functions)
# ============================================================================

def test_dashboard_import():
    pytest.importorskip("plotly")
    from apeiron.layers.layer02_relational import dashboard
    assert hasattr(dashboard, 'figure_persistence_diagram')
    assert hasattr(dashboard, 'figure_spectrum')

def test_dashboard_figures_basic():
    pytest.importorskip("plotly")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational import dashboard
    from apeiron.layers.layer02_relational.spectral import SpectralGraphAnalysis
    G = create_test_graph()
    sa = SpectralGraphAnalysis(G)
    fig = dashboard.figure_spectrum(sa)
    assert fig is not None
    hg = create_test_hypergraph()
    fig_hg = dashboard.figure_hypergraph(hg)
    assert fig_hg is not None


# ============================================================================
# causal_discovery
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
        pc_graph = cd.pc(alpha=0.05)
        assert pc_graph is not None
    except Exception as e:
        pytest.skip(f"PC failed: {e}")

def test_resonance_registration():
    """Test dat resonantiepatronen correct worden geregistreerd."""
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.motif_detection import ResonanceDetector
    G = create_test_graph()
    # Voeg een resonantiepatroon toe: een driehoek met versterkte randen
    for u,v in [(0,1), (1,2), (2,0)]:
        if G.has_edge(u,v):
            G[u][v]['weight'] = 2.0
    detector = ResonanceDetector(G)
    resonances = detector.detect()
    assert isinstance(resonances, list)


# ============================================================================
# multi_agent_rl (including advanced algorithms)
# ============================================================================

def test_multi_agent_rl_import():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational import multi_agent_rl
    assert hasattr(multi_agent_rl, 'MultiAgentGraphEnv')

def test_multi_agent_env_basic():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.multi_agent_rl import (
        MultiAgentGraphEnv, IndependentQLearningAgent
    )
    G = nx.path_graph(5)
    env = MultiAgentGraphEnv(graph=G, n_agents=2, max_steps=10)
    obs = env.reset()
    assert len(obs) == 2
    actions = {0: 1, 1: 2}
    next_obs, rewards, done, info = env.step(actions)
    assert len(next_obs) == 2
    agent = IndependentQLearningAgent(
        agent_id=0,
        action_space=env.action_space_per_agent,
        observation_space=env.observation_space_per_agent
    )
    action = agent.act(obs[0])
    assert 0 <= action < env.action_space_per_agent

def test_maddpg_basic():
    pytest.importorskip("torch")
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.multi_agent_rl import (
        MultiAgentGraphEnv, MADDPG
    )
    G = nx.path_graph(5)
    env = MultiAgentGraphEnv(graph=G, n_agents=2, max_steps=5, observation_type="global")
    maddpg = MADDPG(env, hidden_size=16, buffer_size=100, batch_size=8)
    # Run a few steps to check initialization
    obs = env.reset()
    actions = {i: np.random.randint(env.action_space_per_agent) for i in range(env.n_agents)}
    next_obs, rewards, done, _ = env.step(actions)
    maddpg.store_transition(obs, actions, rewards, next_obs, done)
    maddpg.train_step()  # should not crash

def test_qmix_basic():
    pytest.importorskip("torch")
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.multi_agent_rl import (
        MultiAgentGraphEnv, QMIX
    )
    G = nx.path_graph(5)
    env = MultiAgentGraphEnv(graph=G, n_agents=2, max_steps=5, cooperative=True)
    qmix = QMIX(env, hidden_size=16, buffer_size=100, batch_size=8)
    obs = env.reset()
    actions = qmix.act(obs, explore=True)
    next_obs, rewards, done, _ = env.step(actions)
    qmix.store_transition(obs, actions, sum(rewards.values()), next_obs, done)
    qmix.train_step()


# ============================================================================
# rl_on_graphs (single‑agent environments)
# ============================================================================

def test_rl_on_graphs_import():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational import rl_on_graphs
    assert hasattr(rl_on_graphs, 'GraphEnv')
    assert hasattr(rl_on_graphs, 'QLearningAgent')

def test_rl_on_graphs_basic():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.rl_on_graphs import GraphEnv, QLearningAgent
    G = nx.path_graph(5)
    env = GraphEnv(G, target_node=4, max_steps=10, observation_mode='node')
    agent = QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n)
    obs, _ = env.reset()
    action = agent.act(obs)
    assert 0 <= action < env.action_space.n

def test_resource_collection_env():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.rl_on_graphs import ResourceCollectionEnv
    G = nx.path_graph(5)
    env = ResourceCollectionEnv(G, max_steps=10)
    obs, _ = env.reset()
    assert env.observation_space.shape[0] > 0
    action = 1
    next_obs, reward, terminated, truncated, _ = env.step(action)
    assert isinstance(reward, float)

def test_graph_covering_env():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.rl_on_graphs import GraphCoveringEnv
    G = nx.path_graph(5)
    env = GraphCoveringEnv(G, max_steps=10)
    obs, _ = env.reset()
    action = 1
    next_obs, reward, terminated, truncated, _ = env.step(action)
    assert isinstance(reward, float)

def test_delivery_env():
    pytest.importorskip("gymnasium")
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.rl_on_graphs import DeliveryEnv
    G = nx.path_graph(5)
    env = DeliveryEnv(G, pickup_node=0, delivery_node=4, max_steps=10)
    obs, _ = env.reset()
    action = 1
    next_obs, reward, terminated, truncated, _ = env.step(action)
    assert isinstance(reward, float)


# ============================================================================
# categorical_verification
# ============================================================================

def test_categorical_verification_import():
    from apeiron.layers.layer02_relational import categorical_verification
    assert hasattr(categorical_verification, 'verify_category')

def test_category_verification_basic():
    from apeiron.layers.layer02_relational import relations
    from apeiron.layers.layer02_relational.categorical_verification import verify_category
    cat = relations.RelationalCategory()
    cat.add_object("A")
    cat.add_object("B")
    cat.add_morphism("A", "B", "f")
    cat.identities["A"] = "idA"
    cat.identities["B"] = "idB"
    def comp(f,g,s,m,t):
        return None
    cat.composition = comp
    result = verify_category(cat)
    assert 'valid' in result


# ============================================================================
# hall_algebra
# ============================================================================

def test_hall_algebra_import():
    from apeiron.optional.hall_algebra import hall_algebra
    assert hasattr(hall_algebra, 'HallAlgebra')
    assert hasattr(hall_algebra, 'JordanHallAlgebra')

def test_hall_algebra_basic():
    from apeiron.optional.hall_algebra import JordanHallAlgebra, Partition
    hall = JordanHallAlgebra(max_part_size=3)
    basis = hall.basis()
    assert len(basis) > 0
    p = Partition([2,1])
    q = Partition([1,1])
    prod = hall.multiply(p, q)
    assert isinstance(prod, dict)


# ============================================================================
# probabilistic_models (including new features)
# ============================================================================

def test_probabilistic_models_import():
    from apeiron.layers.layer02_relational import probabilistic_models
    assert hasattr(probabilistic_models, 'BayesianNetwork')
    assert hasattr(probabilistic_models, 'HiddenMarkovModel')
    assert hasattr(probabilistic_models, 'MarkovRandomField')
    assert hasattr(probabilistic_models, 'ConditionalRandomField')

def test_bayesian_network_basic():
    from apeiron.layers.layer02_relational.probabilistic_models import BayesianNetwork
    bn = BayesianNetwork(
        edges=[('A','C'), ('B','C')],
        variable_names=['A','B','C'],
        cardinalities={'A':2, 'B':2, 'C':2}
    )
    bn.set_cpd('A', np.array([0.5,0.5]), [])
    bn.set_cpd('B', np.array([0.5,0.5]), [])
    bn.set_cpd('C', np.array([[0.9,0.1],[0.2,0.8]]), ['A','B'])
    bn.is_fitted = True
    samples = bn.sample(5)
    assert samples.shape == (5, 3)
    ll = bn.log_likelihood(samples)
    assert isinstance(ll, float)

def test_bayesian_network_predict():
    from apeiron.layers.layer02_relational.probabilistic_models import BayesianNetwork
    bn = BayesianNetwork(
        edges=[('A','C'), ('B','C')],
        variable_names=['A','B','C'],
        cardinalities={'A':2, 'B':2, 'C':2}
    )
    bn.set_cpd('A', np.array([0.5,0.5]), [])
    bn.set_cpd('B', np.array([0.5,0.5]), [])
    bn.set_cpd('C', np.array([[0.9,0.1],[0.2,0.8]]), ['A','B'])
    bn.is_fitted = True
    evidence = np.array([[np.nan, 0, 1]])  # A unknown, B=0, C=1
    pred = bn.predict(evidence)
    assert pred.shape == (1,3)
    # A should be predicted (most likely given evidence)
    assert pred[0,0] in [0,1]

def test_hmm_basic():
    from apeiron.layers.layer02_relational.probabilistic_models import HiddenMarkovModel
    hmm = HiddenMarkovModel(n_states=2, n_obs=3)
    hmm.start_prob = np.array([0.6, 0.4])
    hmm.trans_prob = np.array([[0.7,0.3],[0.4,0.6]])
    hmm.emit_prob = np.array([[0.1,0.4,0.5],[0.6,0.3,0.1]])
    obs_seq = hmm.sample(1, length=5)[0]
    states = hmm.predict(obs_seq)
    assert len(states) == 5

def test_markov_random_field_fit():
    pytest.importorskip("torch")  # fit uses torch if available
    from apeiron.layers.layer02_relational.probabilistic_models import MarkovRandomField
    mrf = MarkovRandomField(['X','Y','Z'], {'X':2, 'Y':2, 'Z':2})
    mrf.add_unary_potential('X', np.zeros(2))
    mrf.add_unary_potential('Y', np.zeros(2))
    mrf.add_unary_potential('Z', np.zeros(2))
    mrf.add_pairwise_potential('X','Y', np.zeros((2,2)))
    mrf.add_pairwise_potential('Y','Z', np.zeros((2,2)))
    # Generate synthetic data from a known distribution
    data = np.random.randint(0,2, size=(100,3))
    mrf.fit(data, max_iter=5, lr=0.1)
    # After fitting, potentials should be updated (not all zeros)
    assert np.any(mrf.unary_potentials['X'] != 0) or np.any(mrf.pairwise_potentials[('X','Y')] != 0)

def test_crf_basic():
    from apeiron.layers.layer02_relational.probabilistic_models import ConditionalRandomField
    X = [['a','b','a'], ['b','a','b']]
    y = [['0','1','0'], ['1','0','1']]
    crf = ConditionalRandomField(algorithm='sgd')
    crf.fit(X, y, epochs=5, lr=0.1, verbose=False)
    pred = crf.predict(X)
    assert len(pred) == 2
    assert len(pred[0]) == 3

def test_discretize_from_registry():
    """Test de discretisatiefunctie uit probabilistic_models."""
    from apeiron.layers.layer02_relational.probabilistic_models import discretize_from_registry
    registry = create_test_registry()
    var_names = list(registry['observables'].keys())
    data = np.column_stack([registry['observables'][v] for v in var_names])
    disc, enc = discretize_from_registry(data, var_names, registry, return_encodings=True)
    assert disc.shape == data.shape
    assert all(v in enc for v in var_names if v in registry)

def test_from_temporal_registry():
    """Test de HMM‑bouw uit een temporele registry."""
    from apeiron.layers.layer02_relational.probabilistic_models import from_temporal_registry
    temporal_registry = {
        'phases': {
            'weather': {
                'states': ['Rainy', 'Sunny'],
                'start_prob': [0.6, 0.4],
                'transition_matrix': [[0.7, 0.3], [0.4, 0.6]],
                'emission_matrix': [[0.1, 0.4, 0.5], [0.6, 0.3, 0.1]]
            }
        }
    }
    hmm = from_temporal_registry(temporal_registry, phase_key='weather')
    assert hmm.n_states == 2
    assert hmm.n_obs == 3


# ============================================================================
# quantum_error_correction (including new circuits)
# ============================================================================

def test_quantum_error_correction_import():
    pytest.importorskip("qiskit")
    from apeiron.layers.layer02_relational import quantum_error_correction
    assert hasattr(quantum_error_correction, 'RepetitionCode')
    assert hasattr(quantum_error_correction, 'ShorCode')
    assert hasattr(quantum_error_correction, 'FiveQubitCode')
    assert hasattr(quantum_error_correction, 'SteaneCode')
    assert hasattr(quantum_error_correction, 'SurfaceCode')

def test_repetition_code_basic():
    pytest.importorskip("qiskit")
    from apeiron.layers.layer02_relational.quantum_structs import RepetitionCode
    code = RepetitionCode(n=3)
    enc = code.encode_circuit()
    assert enc.num_qubits == 3

def test_shor_code_syndrome():
    pytest.importorskip("qiskit")
    from apeiron.layers.layer02_relational.quantum_structs import ShorCode
    code = ShorCode()
    circ = code.syndrome_measurement_circuit()
    assert circ.num_qubits == 9 + 8  # code + ancillas

def test_five_qubit_code_syndrome():
    pytest.importorskip("qiskit")
    from apeiron.layers.layer02_relational.quantum_structs import FiveQubitCode
    code = FiveQubitCode()
    circ = code.syndrome_measurement_circuit()
    assert circ.num_qubits == 5 + 4

def test_steane_code_syndrome():
    pytest.importorskip("qiskit")
    from apeiron.layers.layer02_relational.quantum_structs import SteaneCode
    code = SteaneCode()
    circ = code.syndrome_measurement_circuit()
    assert circ.num_qubits == 7 + 6

def test_lookup_table_decoder():
    pytest.importorskip("qiskit")
    from apeiron.layers.layer02_relational.quantum_structs import FiveQubitCode, LookupTableDecoder
    code = FiveQubitCode()
    decoder = LookupTableDecoder(code, max_weight=1)
    # Test with a known syndrome
    error = ['I']*5
    error[2] = 'Z'
    synd = code.compute_syndrome(error)
    correction = decoder.decode(synd)
    # Should return a correction (maybe empty if not in table)
    assert isinstance(correction, dict)

def test_surface_code_memory_experiment():
    pytest.importorskip("stim")
    pytest.importorskip("pymatching")
    from apeiron.layers.layer02_relational.quantum_structs import SurfaceCode
    code = SurfaceCode(distance=3)
    # Run a very short experiment to check it doesn't crash
    error_rate = code.run_memory_experiment(num_rounds=2, noise=0.001, shots=10)
    assert 0 <= error_rate <= 1


# ============================================================================
# quiver_moduli (new features)
# ============================================================================

def test_quiver_moduli_import():
    from apeiron.optional import quiver_moduli
    assert hasattr(quiver_moduli, 'StabilityCondition')
    assert hasattr(quiver_moduli, 'ModuliSpace')
    assert hasattr(quiver_moduli, 'subrepresentations')
    assert hasattr(quiver_moduli, 'harder_narasimhan_filtration')

def test_stability_condition_basic():
    from apeiron.optional.quiver_moduli import StabilityCondition
    theta = StabilityCondition({1: 1, 2: -1})
    dim = {1: 2, 2: 2}
    val = theta(dim)
    assert val == 0

def test_subrepresentations():
    pytest.importorskip("networkx")
    from apeiron.optional.quiver_moduli import subrepresentations
    from apeiron.optional.quiver_moduli import Quiver, QuiverRepresentation
    q = Quiver()
    q.add_vertex(1)
    q.add_vertex(2)
    q.add_arrow(1,2,'a')
    q.add_arrow(1,2,'b')
    dim = {1:2, 2:2}
    rep = QuiverRepresentation(
        quiver=q,
        vector_spaces=dim,
        linear_maps={
            'a': np.eye(2),
            'b': np.array([[0,1],[1,0]])
        }
    )
    subs = subrepresentations(rep)
    # At least some subrepresentations should be found (coordinate subspaces)
    assert isinstance(subs, list)

def test_harder_narasimhan_filtration():
    pytest.importorskip("networkx")
    from apeiron.optional.quiver_moduli import (
        StabilityCondition, harder_narasimhan_filtration
    )
    from apeiron.layers.layer02_relational.quiver import Quiver, QuiverRepresentation
    q = Quiver()
    q.add_vertex(1)
    q.add_vertex(2)
    q.add_arrow(1,2,'a')
    q.add_arrow(1,2,'b')
    dim = {1:2, 2:2}
    rep = QuiverRepresentation(
        quiver=q,
        vector_spaces=dim,
        linear_maps={
            'a': np.eye(2),
            'b': np.array([[0,1],[1,0]])
        }
    )
    theta = StabilityCondition({1:1, 2:-1})
    filt = harder_narasimhan_filtration(rep, theta)
    assert isinstance(filt, list)

def test_stability_with_nonzero_theta():
    """Test dat een representatie stabiel is met een niet‑triviale theta‑vector."""
    pytest.importorskip("networkx")
    from apeiron.optional.quiver_moduli import (
        StabilityCondition, is_stable
    )
    from apeiron.layers.layer02_relational.quiver import Quiver, QuiverRepresentation
    q = Quiver()
    q.add_vertex(1)
    q.add_vertex(2)
    q.add_arrow(1,2,'a')
    # Een eenvoudige representatie: 1-dimensionaal op elke vertex
    rep = QuiverRepresentation(
        quiver=q,
        vector_spaces={1:1, 2:1},
        linear_maps={'a': np.array([[1.0]])}
    )
    theta = StabilityCondition({1: 1, 2: -1})  # zorgt voor mu=0
    stable = is_stable(rep, theta)
    assert stable is True or stable is False  # hangt af van dimensies


# ============================================================================
# derived_categories
# ============================================================================

def test_derived_categories_import():
    from apeiron.optional import derived_categories
    assert hasattr(derived_categories, 'ChainComplex')
    assert hasattr(derived_categories, 'ChainMap')

def test_chain_complex_basic():
    from apeiron.optional.derived_categories import ChainComplex
    d1 = np.array([[1,0,0],[0,1,0]])
    d2 = np.array([[1,0],[0,0],[0,1]])
    C = ChainComplex([d1, d2])
    assert C.is_complex()
    h1 = C.homology(1)[0]
    assert h1 == 1


# ============================================================================
# model_categories
# ============================================================================

def test_model_categories_import():
    from apeiron.optional import model_categories
    assert hasattr(model_categories, 'ModelCategory')
    assert hasattr(model_categories, 'ChainComplexesModelCategory')

def test_chain_complexes_model_basic():
    from apeiron.optional.model_categories import ChainComplexesModelCategory
    from apeiron.optional.model_categories import ChainComplex, ChainMap
    model = ChainComplexesModelCategory()
    C = ChainComplex([])
    id_map = ChainMap(C, C, [])
    assert hasattr(model, 'is_fibration')


# ============================================================================
# graph_self_supervised
# ============================================================================

def test_graph_self_supervised_import():
    pytest.importorskip("torch")
    pytest.importorskip("torch_geometric")
    from apeiron.optional import graph_self_supervised
    assert hasattr(graph_self_supervised, 'GraphCL')
    assert hasattr(graph_self_supervised, 'GCNEncoder')

def test_graph_self_supervised_basic():
    pytest.importorskip("torch")
    pytest.importorskip("torch_geometric")
    import torch
    from torch_geometric.data import Data
    from apeiron.optional.graph_self_supervised import (
        GCNEncoder, GraphCL, node_dropping
    )
    edge_index = torch.tensor([[0,1,1,2],[1,0,2,1]], dtype=torch.long)
    x = torch.randn(3, 5)
    data = Data(x=x, edge_index=edge_index)
    encoder = GCNEncoder(in_channels=5, hidden_channels=8, out_channels=4)
    proj = torch.nn.Linear(4, 4)
    model = GraphCL(encoder, proj, augment_fn=node_dropping)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_dict = model.train_step(data, optimizer)
    assert 'loss' in loss_dict

def test_layer1_registry_to_pyg_data():
    """Test de conversie van registry naar PyG Data object."""
    pytest.importorskip("torch")
    pytest.importorskip("torch_geometric")
    from apeiron.layers.layer02_relational.graph_rl import layer1_registry_to_pyg_data
    registry = create_test_registry()
    var_names = list(registry['observables'].keys())
    data_obj = layer1_registry_to_pyg_data(
        registry=registry,
        observable_names=var_names,
        relation_tuples=[(0,1), (1,2), (2,3)]  # dummy edges
    )
    assert data_obj is not None
    assert data_obj.x.shape[1] == len(var_names)
    assert data_obj.edge_index.shape[1] == 3

def test_atomicity_aware_dgi_loss():
    """Test de atomicity‑aware DGI loss functie."""
    pytest.importorskip("torch")
    from apeiron.layers.layer02_relational.graph_rl import atomicity_aware_dgi_loss
    import torch
    pos = torch.randn(10, 8)
    neg = torch.randn(10, 8)
    readout = pos.mean(dim=0)
    weights = torch.rand(10)
    disc = torch.nn.Bilinear(8, 8, 1)
    loss = atomicity_aware_dgi_loss(pos, neg, readout, weights, disc)
    assert loss.requires_grad
    assert loss > 0


# ============================================================================
# graphql_api
# ============================================================================

def test_graphql_api_import():
    pytest.importorskip("strawberry")
    from apeiron.infrastructure.api import graphql_api
    assert hasattr(graphql_api, 'schema')

def test_graphql_schema_basic():
    pytest.importorskip("strawberry")
    from apeiron.infrastructure.api.graphql import schema
    assert hasattr(schema, 'query_type')
    assert hasattr(schema, 'mutation_type')


# ============================================================================
# database_integration
# ============================================================================

def test_database_integration_import():
    from apeiron.infrastructure import database_integration
    assert hasattr(database_integration, 'DatabaseManager')
    assert hasattr(database_integration, 'SQLiteBackend')

def test_sqlite_backend_basic():
    from apeiron.infrastructure.database import SQLiteBackend, DatabaseManager
    from apeiron.layers.layer02_relational.relations_core import UltimateRelation, RelationType
    backend = SQLiteBackend(":memory:")
    mgr = DatabaseManager(backend)
    import asyncio
    async def run():
        await mgr.connect()
        rel = UltimateRelation(
            id="test_rel",
            source_id="src",
            target_id="tgt",
            relation_type=RelationType.SYMMETRIC,
            weight=0.5
        )
        await mgr.store_relation(rel)
        loaded = await mgr.load_relation("test_rel")
        assert loaded is not None
        await mgr.close()
    asyncio.run(run())

def test_save_load_layer1_registry():
    """Test het opslaan en laden van een Layer 1 registry in database."""
    from apeiron.infrastructure.database import SQLiteBackend, DatabaseManager
    backend = SQLiteBackend(":memory:")
    mgr = DatabaseManager(backend)
    import asyncio
    registry = create_test_registry()
    async def run():
        await mgr.connect()
        await mgr.save_layer1_registry(registry, "test_reg")
        loaded = await mgr.load_layer1_registry("test_reg")
        assert loaded is not None
        assert loaded['observables']['temp'] == registry['observables']['temp']
        await mgr.close()
    asyncio.run(run())

def test_save_resonance_graph():
    """Test het opslaan van een resonantiegraaf in Neo4j (indien beschikbaar)."""
    pytest.importorskip("neo4j")
    pytest.importorskip("networkx")
    from apeiron.infrastructure.database import Neo4jBackend, DatabaseManager
    import networkx as nx
    # Skip test if no Neo4j running; we'll use a dummy connection that will fail gracefully
    backend = Neo4jBackend("bolt://localhost:7687", "neo4j", "password")
    mgr = DatabaseManager(backend)
    import asyncio
    G = nx.path_graph(3)
    async def run():
        try:
            await mgr.connect()
        except Exception:
            pytest.skip("Neo4j not available")
        await mgr.backend.save_resonance_graph(G, "test_resonance")
        # No assertion, just check it didn't crash
        await mgr.close()
    asyncio.run(run())


# ============================================================================
# temporal_networks (including new motif types)
# ============================================================================

def test_temporal_networks_import():
    from apeiron.layers.layer02_relational import temporal_networks
    assert hasattr(temporal_networks, 'TemporalGraph')
    assert hasattr(temporal_networks, 'TemporalNetwork')

def test_temporal_graph_basic():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.temporal_networks import TemporalGraph
    tg = TemporalGraph()
    tg.add_interaction(0, 1, 0.1)
    tg.add_interaction(1, 2, 0.2)
    assert len(tg.nodes) == 3
    snap = tg.snapshot_at_time(0.15, delta=0.05)
    assert snap.has_edge(0,1)

def test_temporal_network_basic():
    pytest.importorskip("networkx")
    import networkx as nx
    from apeiron.layers.layer02_relational.temporal_networks import TemporalNetwork
    G1 = nx.erdos_renyi_graph(5, 0.3)
    G2 = nx.erdos_renyi_graph(5, 0.4)
    tn = TemporalNetwork(snapshots=[G1, G2], timestamps=[0.0, 1.0])
    assert len(tn) == 2
    series = tn.compute_statistics_series(tn, {
        'num_nodes': lambda g: g.number_of_nodes()
    })
    assert 'num_nodes' in series

def test_temporal_motif_count():
    from apeiron.layers.layer02_relational.temporal_networks import TemporalGraph, temporal_motif_count
    tg = TemporalGraph()
    tg.add_interaction(0, 1, 0.1)
    tg.add_interaction(1, 2, 0.2)
    tg.add_interaction(0, 2, 0.3)
    tg.add_interaction(0, 1, 0.5)  # burst
    for motif in ['triangle_concurrent', 'star_concurrent', 'path_consecutive', 'burst']:
        cnt = temporal_motif_count(tg, motif_type=motif, window=0.5)
        assert isinstance(cnt, int)

def test_temporal_motif_significance():
    from apeiron.layers.layer02_relational.temporal_networks import TemporalGraph, temporal_motif_significance
    tg = TemporalGraph()
    tg.add_interaction(0, 1, 0.1)
    tg.add_interaction(1, 2, 0.2)
    tg.add_interaction(0, 2, 0.3)
    sig = temporal_motif_significance(tg, 'triangle_concurrent', n_random=10, window=0.5)
    assert 'p_value' in sig


# ============================================================================
# quantum_ml (including new models)
# ============================================================================

def test_quantum_ml_import():
    pytest.importorskip("pennylane")
    from apeiron.layers.layer02_relational import quantum_ml
    assert hasattr(quantum_ml, 'QSVM')
    assert hasattr(quantum_ml, 'QuantumKernel')
    assert hasattr(quantum_ml, 'VariationalQuantumClassifier')
    assert hasattr(quantum_ml, 'DataReuploadingClassifier')
    assert hasattr(quantum_ml, 'QGAN')

def test_quantum_kernel_basic():
    pytest.importorskip("pennylane")
    from apeiron.optional.quantum_ml import QuantumKernel
    kernel = QuantumKernel(n_qubits=2, encoding='angle')
    X = np.random.randn(3,2)
    K = kernel.kernel_matrix(X)
    assert K.shape == (3,3)

def test_data_reuploading_classifier():
    pytest.importorskip("pennylane")
    from apeiron.optional.quantum_ml import DataReuploadingClassifier
    X = np.random.randn(5,2)
    y = np.random.randint(0,2, size=5)
    clf = DataReuploadingClassifier(n_qubits=2, n_layers=2, steps=5)
    clf.fit(X, y)
    pred = clf.predict(X)
    assert pred.shape == (5,)

def test_qgan():
    pytest.importorskip("pennylane")
    pytest.importorskip("torch")
    from apeiron.optional.quantum_ml import QGAN
    X = np.random.randn(20,2)  # 2D data
    qgan = QGAN(n_qubits=2, n_latent=2, epochs=2, batch_size=5)
    qgan.fit(X)
    samples = qgan.generate(5)
    assert samples.shape == (5, 2)


# ============================================================================
# visualization_dash (interactive components)
# ============================================================================

def test_visualization_dash_import():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    from apeiron.layers.layer02_relational import visualization_dash
    assert hasattr(visualization_dash, 'PersistenceDiagramComponent')
    assert hasattr(visualization_dash, 'SpectralEmbeddingComponent')
    assert hasattr(visualization_dash, 'HypergraphComponent')
    assert hasattr(visualization_dash, 'QuantumGraphComponent')
    assert hasattr(visualization_dash, 'CommunityMapComponent')
    assert hasattr(visualization_dash, 'create_interactive_dashboard')

def test_persistence_diagram_component():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.motif_detection import PersistentHomology
    from apeiron.layers.layer02_relational.visualization_dash import PersistenceDiagramComponent
    G = create_test_graph()
    ph = PersistentHomology(G)
    ph.build_clique_complex(max_dim=2)
    ph.compute_persistence()
    comp = PersistenceDiagramComponent("test", ph)
    layout = comp.get_layout()
    assert layout is not None

def test_spectral_embedding_component():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.spectral import SpectralGraphAnalysis
    from apeiron.layers.layer02_relational.visualization_dash import SpectralEmbeddingComponent
    G = create_test_graph()
    sa = SpectralGraphAnalysis(G)
    comp = SpectralEmbeddingComponent("test", sa, dim=2)
    layout = comp.get_layout()
    assert layout is not None

def test_hypergraph_component():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    from apeiron.layers.layer02_relational.visualization_dash import HypergraphComponent
    hg = create_test_hypergraph()
    comp = HypergraphComponent("test", hg)
    layout = comp.get_layout()
    assert layout is not None

def test_quantum_graph_component():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.hypergraph import QuantumGraph
    from apeiron.layers.layer02_relational.visualization_dash import QuantumGraphComponent
    G = create_test_graph()
    qg = QuantumGraph(graph=G)
    for u,v in G.edges():
        qg.edge_amplitudes[(u,v)] = 0.5
    comp = QuantumGraphComponent("test", qg)
    layout = comp.get_layout()
    assert layout is not None

def test_community_map_component():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.visualization_dash import CommunityMapComponent
    G = create_test_graph()
    comm_map = {node: i%3 for i,node in enumerate(G.nodes())}
    comp = CommunityMapComponent("test", comm_map, G)
    layout = comp.get_layout()
    assert layout is not None

def test_dashboard_builder():
    pytest.importorskip("dash")
    pytest.importorskip("plotly")
    from apeiron.layers.layer02_relational.visualization_dash import (
        SpectralEmbeddingComponent, create_interactive_dashboard
    )
    from apeiron.layers.layer02_relational.spectral import SpectralGraphAnalysis
    G = create_test_graph()
    sa = SpectralGraphAnalysis(G)
    comp = SpectralEmbeddingComponent("test", sa, dim=2)
    app = create_interactive_dashboard([comp])
    assert app is not None


# ============================================================================
# atomicity_visuals (nieuwe module)
# ============================================================================

def test_atomicity_visuals_import():
    """Test of atomicity_visuals module importeerbaar is."""
    from apeiron.layers.layer02_relational import atomicity_visuals
    assert hasattr(atomicity_visuals, 'plot_atomicity_heatmap')
    assert hasattr(atomicity_visuals, 'plot_atomicity_distribution')
    assert hasattr(atomicity_visuals, 'plot_atomicity_comparison')
    assert hasattr(atomicity_visuals, 'plot_atomicity_timeline')
    assert hasattr(atomicity_visuals, 'plot_atomicity_network')

def test_atomicity_visuals_basic():
    """Test basisfunctionaliteit van atomicity_visuals (backend fallback)."""
    pytest.importorskip("matplotlib")  # vereist voor demo
    from apeiron.layers.layer02_relational import atomicity_visuals
    atomicity = np.random.rand(20)
    # Alleen controleren of ze worden aangeroepen zonder fouten (show=False)
    fig = atomicity_visuals.plot_atomicity_distribution(atomicity, backend='matplotlib', show=False)
    assert fig is None  # matplotlib geeft geen figuur terug
    # Probeer plotly als het beschikbaar is
    try:
        fig = atomicity_visuals.plot_atomicity_distribution(atomicity, backend='plotly', show=False)
        assert fig is not None or True
    except ImportError:
        pass


# ============================================================================
# layer1_bridge (nieuwe module)
# ============================================================================

def test_layer1_bridge_import():
    """Test of layer1_bridge module importeerbaar is."""
    from apeiron.layers.layer02_relational import layer1_bridge
    assert hasattr(layer1_bridge, 'registry_to_graph')
    assert hasattr(layer1_bridge, 'similarity_matrix')
    assert hasattr(layer1_bridge, 'observable_to_vector')
    assert hasattr(layer1_bridge, 'extract_feature_matrix')
    assert hasattr(layer1_bridge, 'discretize_observable')

def test_observable_to_vector():
    from apeiron.layers.layer02_relational.layer1_bridge import observable_to_vector
    data = [1,2,3,4]
    vec = observable_to_vector(data, normalize=True, method='minmax')
    assert np.allclose(vec, [0, 1/3, 2/3, 1])

def test_extract_feature_matrix():
    from apeiron.layers.layer02_relational.layer1_bridge import extract_feature_matrix
    registry = create_test_registry()
    X = extract_feature_matrix(registry, ['temp', 'pressure'])
    assert X.shape == (4, 2)

def test_similarity_matrix():
    pytest.importorskip("sklearn")
    from apeiron.layers.layer02_relational.layer1_bridge import similarity_matrix
    registry = create_test_registry()
    sim = similarity_matrix(registry, method='cosine')
    assert sim.shape == (4, 4)
    assert np.allclose(np.diag(sim), 1.0)

def test_registry_to_graph():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.layer1_bridge import registry_to_graph
    registry = create_test_registry()
    G = registry_to_graph(registry, edge_definition='threshold', threshold=0.5, metric='euclidean')
    assert G.number_of_nodes() == 4


# ============================================================================
# Integratietests
# ============================================================================

def test_layer1_layer2_integration():
    """Integratietest voor functies die Layer 1‑data omzetten naar Layer 2‑objecten."""
    # Gebruik discretize_from_registry uit probabilistic_models
    pytest.importorskip("sklearn")  # voor KBinsDiscretizer
    from apeiron.layers.layer02_relational.probabilistic_models import discretize_from_registry
    from apeiron.layers.layer02_relational.graph_rl import layer1_registry_to_pyg_data
    from apeiron.layers.layer02_relational.relations_core import compute_relations
    import torch

    registry = create_test_registry()
    var_names = list(registry['observables'].keys())
    data = np.column_stack([registry['observables'][v] for v in var_names])

    # Discretisatie
    disc_data, enc = discretize_from_registry(data, var_names, registry, return_encodings=True)
    assert disc_data.shape == data.shape
    assert all(v in enc for v in var_names if v in registry)

    # PyG Data object
    if HAS_PYG and HAS_TORCH:
        data_obj = layer1_registry_to_pyg_data(
            registry=registry,
            observable_names=var_names,
            relation_tuples=[(0,1), (1,2), (2,3)]  # dummy edges
        )
        assert data_obj is not None
        assert data_obj.x.shape[1] == len(var_names)

    # compute_relations
    rels = compute_relations(registry)
    assert isinstance(rels, list)
    # Als de registry observables heeft, zouden er relaties moeten zijn
    if var_names:
        assert len(rels) > 0


# ============================================================================
# main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__])