#!/usr/bin/env python3
"""
Tests voor alle optionele modules van het APEIRON Framework
=============================================================
Valideert de importeerbaarheid en basiswerking van elke module
in apeiron/optional/. Waar externe libraries (qiskit, pennylane,
torch, gudhi, etc.) ontbreken, worden de tests overgeslagen.
"""
import pytest
import numpy as np
import sys
import os

# ===========================================================================
# Helper: create a minimal hypergraph for tests
# ===========================================================================
def create_test_hypergraph():
    pytest.importorskip("networkx")
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
    hg = Hypergraph()
    hg.add_hyperedge("e1", {0,1}, 1.0)
    hg.add_hyperedge("e2", {1,2}, 0.8)
    return hg

# ===========================================================================
# Oorspronkelijke optionele modules (10)
# ===========================================================================

def test_quiver_moduli_import():
    from apeiron.optional.quiver_moduli import StabilityCondition, ModuliSpace
    theta = StabilityCondition({1: 1, 2: -1})
    assert theta({1:2, 2:2}) == 0

def test_quantum_vqe_optimizer_import():
    pytest.importorskip("qiskit")
    from apeiron.optional.quantum_vqe_optimizer import QuantumGroundStateOptimizer
    # Cannot instantiate without ontology, just check import
    assert QuantumGroundStateOptimizer is not None

def test_quantum_vqe_import():
    pytest.importorskip("qiskit")
    from apeiron.optional.quantum_vqe import QuantumVQE
    assert QuantumVQE is not None

def test_quantum_ml_import():
    pytest.importorskip("pennylane")
    from apeiron.optional.quantum_ml import QuantumKernel, QSVM
    assert QuantumKernel is not None

def test_quantum_ml_kernel():
    pytest.importorskip("pennylane")
    from apeiron.optional.quantum_ml import QuantumKernel
    kernel = QuantumKernel(n_qubits=2, encoding='angle')
    X = np.random.randn(3, 2)
    K = kernel.kernel_matrix(X)
    assert K.shape == (3, 3)

def test_quantum_error_correction_import():
    pytest.importorskip("qiskit")
    from apeiron.optional.quantum_error_correction import RepetitionCode, ShorCode
    code = RepetitionCode(n=3)
    enc = code.encode_circuit()
    assert enc.num_qubits == 3

def test_model_categories_import():
    from apeiron.optional.model_categories import ChainComplexesModelCategory
    model = ChainComplexesModelCategory()
    assert hasattr(model, 'is_fibration')

def test_hall_algebra_import():
    from apeiron.optional.hall_algebra import JordanHallAlgebra, Partition
    hall = JordanHallAlgebra(max_part_size=3)
    assert len(hall.basis()) > 0

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

def test_derived_categories_import():
    from apeiron.optional.derived_categories import ChainComplex
    d1 = np.array([[1,0,0],[0,1,0]])
    d2 = np.array([[1,0],[0,0],[0,1]])
    C = ChainComplex([d1, d2])
    assert C.is_complex()

def test_code_genesis_import():
    from apeiron.optional.code_genesis import CodeGenesis
    assert CodeGenesis is not None

# ===========================================================================
# Extreme optionele modules (v6.0) (6)
# ===========================================================================

def test_functorial_learning_basic():
    from apeiron.optional.functorial_learning import functorial_embedding
    emb = functorial_embedding({'a': np.array([1.0])}, {'a': 'a_prime'}, ['a_prime', 'b'])
    assert 'a_prime' in emb
    assert 'b' in emb

def test_quantum_sheaf_cohomology_classical():
    pytest.importorskip("scipy")
    from apeiron.layers.layer02_relational import SheafHypergraph
    from apeiron.optional.quantum_sheaf_cohomology import quantum_sheaf_cohomology_pipeline
    shg = SheafHypergraph(["v1","v2"], [{"v1","v2"}])
    result = quantum_sheaf_cohomology_pipeline(shg, backend='classical')
    assert result['h0'] >= 0
    assert result['h1'] >= 0

def test_hott_certificates_generation():
    from apeiron.layers.layer02_relational.hott_category import UnivalentCategory, univalent_category_from_hypergraph
    from apeiron.optional.hott_certificates import HoTTCertificateGenerator
    hg = create_test_hypergraph()
    uc = univalent_category_from_hypergraph(hg)
    gen = HoTTCertificateGenerator(uc)
    certs = gen.generate_certificates()
    assert 'coq_script' in certs
    assert 'lean_script' in certs

def test_topological_quantum_correction_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.topological_quantum_correction import TopologicalErrorCorrector
    corrector = TopologicalErrorCorrector(hg, n_repetitions=3)
    result = corrector.correct_partition_function()
    assert 'Z_corrected' in result

def test_cosmological_bridge_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.cosmological_bridge import CosmologicalBridge
    bridge = CosmologicalBridge(hg)
    params = bridge.compute_cosmology()
    assert params.spectral_dimension > 0

def test_consciousness_interface_basic():
    pytest.importorskip("scipy")
    hg = create_test_hypergraph()
    from apeiron.optional.consciousness_interface import GlobalWorkspace
    ws = GlobalWorkspace(hg)
    moment = ws.conscious_update()
    assert moment is not None

# ===========================================================================
# Grensoverschrijdende modules (v7.0) (7)
# ===========================================================================

def test_hott_relations_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.hott_relations import HomotopyGroupoid, homotopy_analysis
    result = homotopy_analysis(hg)
    assert 'is_simply_connected' in result

def test_entropy_flux_analyzer_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.entropy_flux_analyzer import EntropyFluxAnalyzer
    analyzer = EntropyFluxAnalyzer(hg)
    ranking = analyzer.causal_flux_ordering([(0,1)])
    assert len(ranking) > 0

def test_von_neumann_algebra_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.von_neumann_algebra import VonNeumannAlgebra
    alg = VonNeumannAlgebra(hg)
    result = alg.global_commutativity_graph()
    assert 'num_incompatible_pairs' in result

def test_kan_imagination_engine_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.kan_imagination_engine import KanImaginationEngine
    engine = KanImaginationEngine(hg, {0: np.array([1.0, 0.0]), 1: np.array([0.0, 1.0])})
    new_concepts = engine.imagine_missing_concepts({0,1,2})
    # Vertex 2 should be generated
    assert 2 in new_concepts

def test_scale_invariant_monitor_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.scale_invariant_monitor import ScaleInvariantMonitor
    monitor = ScaleInvariantMonitor(hg, n_scales=5)
    profile = monitor.compute_profile()
    assert 0.0 <= profile.scale_invariance_score <= 1.0

def test_reflexive_engine_basic():
    import tempfile, os
    # Create a temporary dummy Python file for the engine to analyse
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("x = 1\ny = 2\n")
        temp_path = f.name
    try:
        from apeiron.optional.reflexive_engine import ReflexiveEngine
        engine = ReflexiveEngine(temp_path, safety_sandbox=True)
        consistency = engine.check_self_consistency()
        assert 'consistent' in consistency
    finally:
        os.unlink(temp_path)

def test_topological_generation_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.topological_generation import TopologicalGenerator
    gen = TopologicalGenerator(hg, max_generations=2)
    result = gen.generate_and_fill()
    assert 'status' in result

def test_topological_fault_tolerance_basic():
    hg = create_test_hypergraph()
    from apeiron.optional.topological_fault_tolerance import FaultTolerancePipeline
    pipeline = FaultTolerancePipeline(hg, max_iterations=3)
    result = pipeline.run()
    assert 'iterations' in result
    assert 'final_obstruction' in result
    assert 'fully_corrected' in result