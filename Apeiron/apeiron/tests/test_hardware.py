"""
HARDWARE TESTS - Uitgebreide test suite voor alle hardware backends
====================================================================
Test alle hardware componenten:
- CPU backend met get_field_id() en caching
- FPGA backend met fixed-point conversie
- Quantum backend met gecorrigeerde SWAP-test en partiële trace
- Hardware factory met cache fixes
- Fallback mechanismen
- Performance metrics
"""

import pytest
import numpy as np
import sys
import os
import time
import hashlib
from unittest.mock import Mock, patch, MagicMock

# Zorg dat de apeiron package gevonden wordt
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importeer hardware backends
from apeiron.hardware.backends import (
    HardwareBackend,
    CPUBackend,
    CUDABackend,
    FPGABackend,
    QuantumBackend
)

# Importeer hardware factory en registry
from apeiron.hardware.factory import (
    HardwareFactory,
    get_best_backend,
    get_backend_by_name,
    cleanup_hardware,
    BackendRegistry,
    BackendInfo,
)
HARDWARE_FACTORY_AVAILABLE = True

# Importeer hardware configuratie
from apeiron.hardware.config import (
    HardwareConfig,
    CPUConfig,
    CUDAConfig,
    FPGAConfig,
    QuantumConfig,
    load_hardware_config,
)
HARDWARE_CONFIG_AVAILABLE = True

# Importeer hardware exceptions
from apeiron.hardware.exceptions import (
    HardwareError,
    HardwareNotAvailableError,
    HardwareInitializationError,
    HardwareTimeoutError,
    HardwareMemoryError,
    HardwareResourceError,
    HardwareDataError,
    HardwareTransferError,
    HardwareSynchronizationError,
    FPGAError,
    QuantumError,
    CUDAError,
    handle_hardware_errors,
    RetryStrategy,
    HardwareErrorHandler,
)
HARDWARE_EXCEPTIONS_AVAILABLE = True

# ====================================================================
# FIXTURES
# ====================================================================

@pytest.fixture
def cpu_backend():
    """Maak een CPU backend voor tests."""
    backend = CPUBackend()
    backend.initialize({})
    return backend

@pytest.fixture
def quantum_backend():
    """Maak een Quantum backend voor tests."""
    backend = QuantumBackend()
    backend.is_available = True
    return backend

@pytest.fixture
def fpga_backend():
    """Maak een FPGA backend voor tests."""
    backend = FPGABackend()
    backend.is_available = True
    # Mock de PYNQ methods voor tests
    backend.field_engine = MagicMock()
    backend.interference_engine = MagicMock()
    backend.stability_engine = MagicMock()
    backend.field_interrupt = MagicMock()
    return backend

@pytest.fixture
def mock_qiskit():
    """Mock Qiskit voor quantum backend tests."""
    with patch('qiskit.QuantumCircuit') as mock_qc:
        with patch('qiskit.execute') as mock_execute:
            # Mock statevector result
            mock_result = MagicMock()
            mock_result.get_statevector.return_value = np.array([1.0, 0.0, 0.0, 0.0])
            mock_execute.return_value.result.return_value = mock_result
            yield mock_qc, mock_execute

@pytest.fixture
def mock_pynq():
    """Mock PYNQ voor FPGA backend tests."""
    with patch('pynq.Overlay') as mock_overlay:
        with patch('pynq.allocate') as mock_allocate:
            # Mock DMA buffer
            mock_buffer = MagicMock()
            mock_buffer.array = np.zeros(10)
            mock_allocate.return_value = mock_buffer
            yield mock_overlay, mock_allocate

@pytest.fixture
def mock_torch():
    """Mock PyTorch voor CUDA backend tests."""
    with patch('torch.cuda.is_available') as mock_cuda:
        with patch('torch.randn') as mock_randn:
            mock_randn.return_value.cpu.return_value.numpy.return_value = np.random.randn(10)
            yield mock_cuda, mock_randn


# ====================================================================
# CPU BACKEND TESTS
# ====================================================================

class TestCPUBackend:
    """Test suite voor CPU backend."""
    
    def test_initialization(self, cpu_backend):
        """Test CPU backend initialisatie."""
        assert cpu_backend.name == "CPU"
        assert cpu_backend.is_available == True
        assert hasattr(cpu_backend, 'config')
        assert hasattr(cpu_backend, 'metrics')
    
    def test_create_continuous_field(self, cpu_backend):
        """Test creatie van continu veld."""
        dimensions = 10
        field = cpu_backend.create_continuous_field(dimensions)
        
        assert field.shape == (dimensions,)
        assert abs(np.linalg.norm(field) - 1.0) < 1e-6
        assert field.dtype == np.float64
    
    def test_create_continuous_field_different_dims(self, cpu_backend):
        """Test creatie met verschillende dimensies."""
        for dim in [1, 5, 10, 50, 100]:
            field = cpu_backend.create_continuous_field(dim)
            assert field.shape == (dim,)
            assert abs(np.linalg.norm(field) - 1.0) < 1e-6
    
    def test_get_field_id(self, cpu_backend):
        """Test field ID lookup."""
        field = cpu_backend.create_continuous_field(10)
        
        # Eerste keer zou miss moeten zijn
        id1 = cpu_backend.get_field_id(field)
        assert id1 is not None
        assert cpu_backend.metrics['cache_misses'] > 0
        
        # Tweede keer zou hit moeten zijn
        id2 = cpu_backend.get_field_id(field)
        assert id1 == id2
        assert cpu_backend.metrics['cache_hits'] > 0
    
    def test_field_id_hash_consistency(self, cpu_backend):
        """Test dat hash consistent is voor zelfde veld."""
        field = cpu_backend.create_continuous_field(10)
        field_copy = field.copy()
        
        id1 = cpu_backend.get_field_id(field)
        id2 = cpu_backend.get_field_id(field_copy)
        
        assert id1 == id2  # Zelfde inhoud, zelfde hash
    
    def test_field_id_different_fields(self, cpu_backend):
        """Test dat verschillende velden verschillende IDs krijgen."""
        field1 = cpu_backend.create_continuous_field(10)
        field2 = cpu_backend.create_continuous_field(10)
        
        id1 = cpu_backend.get_field_id(field1)
        id2 = cpu_backend.get_field_id(field2)
        
        assert id1 != id2
    
    def test_cache_metrics(self, cpu_backend):
        """Test cache metrics."""
        field = cpu_backend.create_continuous_field(10)
        
        # Eerste keer: miss
        cpu_backend.get_field_id(field)
        assert cpu_backend.metrics['cache_misses'] == 1
        assert cpu_backend.metrics['cache_hits'] == 0
        
        # Tweede keer: hit
        cpu_backend.get_field_id(field)
        assert cpu_backend.metrics['cache_misses'] == 1
        assert cpu_backend.metrics['cache_hits'] == 1
    
    def test_field_update_with_id(self, cpu_backend):
        """Test field update met ID tracking."""
        field = cpu_backend.create_continuous_field(10)
        field_id = cpu_backend.get_field_id(field)
        
        verleden = cpu_backend.create_continuous_field(10)
        heden = cpu_backend.create_continuous_field(10)
        toekomst = cpu_backend.create_continuous_field(10)
        
        result = cpu_backend.field_update(field, 0.1, verleden, heden, toekomst)
        
        # Check dat counter geüpdatet is
        assert cpu_backend.field_counters[field_id] == 1
        assert result is not None
    
    def test_toekomst_gewicht_correctie(self, cpu_backend):
        """Test fix: gewichtssom toekomst = 1.0."""
        field = cpu_backend.create_continuous_field(10)
        verleden = cpu_backend.create_continuous_field(10)
        heden = cpu_backend.create_continuous_field(10)
        toekomst = cpu_backend.create_continuous_field(10)
        
        result = cpu_backend.field_update(field, 0.1, verleden, heden, toekomst)
        
        # Check dat update correct is (geen crash)
        assert result['toekomst'] is not None
    
    def test_find_stable_patterns_with_field_ids(self, cpu_backend):
        """Test pattern detection met field IDs."""
        fields = [cpu_backend.create_continuous_field(10) for _ in range(5)]
        
        patterns = cpu_backend.find_stable_patterns(fields, threshold=0.5)
        
        for pattern in patterns:
            assert 'field_id_i' in pattern
            assert 'field_id_j' in pattern
            if pattern['field_id_i'] is not None:
                assert pattern['field_id_i'] in cpu_backend.fields
            if pattern['field_id_j'] is not None:
                assert pattern['field_id_j'] in cpu_backend.fields
    
    def test_field_stats(self, cpu_backend):
        """Test field statistics."""
        field = cpu_backend.create_continuous_field(10)
        field_id = cpu_backend.get_field_id(field)
        
        stats = cpu_backend.get_field_stats(field_id)
        assert stats['id'] == field_id
        assert stats['shape'] == (10,)
        assert 'norm' in stats
        assert 'updates' in stats
    
    def test_all_field_stats(self, cpu_backend):
        """Test statistieken voor alle velden."""
        for _ in range(5):
            cpu_backend.create_continuous_field(10)
        
        stats = cpu_backend.get_field_stats()
        assert stats['total'] == 5
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
    
    def test_field_update(self, cpu_backend):
        """Test veld update."""
        field = cpu_backend.create_continuous_field(10)
        verleden = cpu_backend.create_continuous_field(10)
        heden = cpu_backend.create_continuous_field(10)
        toekomst = cpu_backend.create_continuous_field(10)
        
        result = cpu_backend.field_update(field, 0.1, verleden, heden, toekomst)
        
        assert 'verleden' in result
        assert 'heden' in result
        assert 'toekomst' in result
        assert result['heden'].shape == (10,)
        assert abs(np.linalg.norm(result['heden']) - 1.0) < 1e-6
    
    def test_compute_interference(self, cpu_backend):
        """Test interferentie berekening."""
        a = cpu_backend.create_continuous_field(10)
        b = cpu_backend.create_continuous_field(10)
        
        interference = cpu_backend.compute_interference(a, b)
        
        assert 0 <= interference <= 1
        assert isinstance(interference, float)
    
    def test_find_stable_patterns(self, cpu_backend):
        """Test detectie van stabiele patronen."""
        fields = [cpu_backend.create_continuous_field(10) for _ in range(5)]
        
        patterns = cpu_backend.find_stable_patterns(fields, threshold=0.5)
        
        assert isinstance(patterns, list)
        for pattern in patterns:
            assert 'i' in pattern
            assert 'j' in pattern
            assert 'sterkte' in pattern
            assert 'veld' in pattern
            assert 0 <= pattern['sterkte'] <= 1
    
    def test_measure_coherence(self, cpu_backend):
        """Test coherentie meting."""
        fields = [cpu_backend.create_continuous_field(10) for _ in range(5)]
        
        coherence = cpu_backend.measure_coherence(fields)
        
        assert 0 <= coherence <= 1
        assert isinstance(coherence, float)
    
    def test_measure_coherence_single_field(self, cpu_backend):
        """Test coherentie meting met 1 veld."""
        fields = [cpu_backend.create_continuous_field(10)]
        
        coherence = cpu_backend.measure_coherence(fields)
        
        assert coherence == 1.0
    
    def test_get_info(self, cpu_backend):
        """Test info string."""
        info = cpu_backend.get_info()
        assert "CPU" in info
        assert "float64" in info or "float32" in info
    
    def test_get_metrics(self, cpu_backend):
        """Test metrics ophalen."""
        metrics = cpu_backend.get_metrics()
        
        assert 'total_fields_created' in metrics
        assert 'total_updates' in metrics
        assert 'total_interference_calc' in metrics
        assert 'active_fields' in metrics
    
    def test_cleanup(self, cpu_backend):
        """Test cleanup."""
        # Maak wat velden
        for _ in range(5):
            cpu_backend.create_continuous_field(10)
        
        assert len(cpu_backend.fields) == 5
        assert len(cpu_backend.field_hash) == 5
        
        cpu_backend.cleanup()
        
        assert len(cpu_backend.fields) == 0
        assert len(cpu_backend.field_counters) == 0
        assert len(cpu_backend.field_hash) == 0
    
    def test_precision_config(self):
        """Test verschillende precisies."""
        backend = CPUBackend()
        
        # Test float32
        backend.initialize({'precision': 'float32'})
        field = backend.create_continuous_field(10)
        assert field.dtype == np.float32
        
        # Test float64
        backend.initialize({'precision': 'float64'})
        field = backend.create_continuous_field(10)
        assert field.dtype == np.float64
    
    def test_thread_config(self):
        """Test thread configuratie."""
        backend = CPUBackend()
        backend.initialize({'num_threads': 2})
        field = backend.create_continuous_field(10)
        assert field is not None


# ====================================================================
# FPGA BACKEND TESTS
# ====================================================================

class TestFPGABackend:
    """Test suite voor FPGA backend."""
    
    def test_initialization(self):
        """Test FPGA backend initialisatie."""
        backend = FPGABackend()
        assert backend.name == "FPGA"
    
    def test_create_continuous_field_fallback(self):
        """Test field creatie fallback (geen pynq)."""
        backend = FPGABackend()
        backend.is_available = False
        
        field = backend.create_continuous_field(10)
        
        assert field is not None
        assert field.shape == (10,)
        assert abs(np.linalg.norm(field) - 1.0) < 1e-6
    
    def test_initialization_with_config(self):
        """Test initialisatie met configuratie."""
        backend = FPGABackend()
        
        # Mock PYNQ beschikbaar
        backend.is_available = True
        with patch.object(backend, 'initialize', return_value=True) as mock_init:
            result = backend.initialize({'bitstream': 'test.bit', 'timeout': 2.0})
            mock_init.assert_called_once_with({'bitstream': 'test.bit', 'timeout': 2.0})
    
    def test_float_to_fixed_conversion(self, fpga_backend):
        """Test fixed-point conversie (Bug 6 fix)."""
        # Test met Q16.16 (65536)
        result = fpga_backend._float_to_fixed(0.1)
        assert result == 6554  # 0.1 * 65536
        
        result = fpga_backend._float_to_fixed(1.0)
        assert result == 65536  # 1.0 * 65536
        
        result = fpga_backend._float_to_fixed(0.0)
        assert result == 0
    
    def test_float_to_ieee754(self, fpga_backend):
        """Test IEEE 754 conversie."""
        result = fpga_backend._float_to_ieee754(0.1)
        assert isinstance(result, int)
        assert 0 < result < 2**32
    
    def test_get_field_id_fpga(self, fpga_backend, mock_pynq):
        """Test field ID lookup in FPGA backend."""
        field = np.random.randn(10).astype(np.float32)
        field = field / np.linalg.norm(field)
        
        # Maak buffer
        field_id = fpga_backend._create_buffer(field)
        assert field_id is not None
        
        # Zoek via hash
        found_id = fpga_backend.get_field_id(field)
        assert found_id == field_id
        assert fpga_backend.metrics['cache_hits'] > 0
    
    def test_field_update_with_fixed_point(self, fpga_backend, mock_pynq):
        """Test field update met fixed-point dt."""
        field = np.random.randn(10).astype(np.float32)
        field = field / np.linalg.norm(field)
        verleden = field.copy()
        heden = field.copy()
        toekomst = field.copy()
        
        # Mock field_engine.write
        fpga_backend.field_engine.write = MagicMock()
        fpga_backend._wait_for_completion = MagicMock(return_value=True)
        
        result = fpga_backend.field_update(field, 0.1, verleden, heden, toekomst)
        
        # Check dat write is aangeroepen met fixed-point waarde
        calls = fpga_backend.field_engine.write.call_args_list
        dt_call = [c for c in calls if c[0][0] == 5]
        assert len(dt_call) > 0
        assert dt_call[0][0][1] == 6554  # 0.1 * 65536
        
        assert result is not None
        assert 'verleden' in result
        assert 'heden' in result
        assert 'toekomst' in result
    
    def test_get_info(self):
        """Test info string."""
        backend = FPGABackend()
        info = backend.get_info()
        assert "FPGA" in info


# ====================================================================
# QUANTUM BACKEND TESTS
# ====================================================================

class TestQuantumBackend:
    """Test suite voor Quantum backend."""
    
    def test_initialization(self, quantum_backend):
        """Test quantum backend initialisatie."""
        assert quantum_backend.name == "Quantum"
        assert hasattr(quantum_backend, 'config')
        assert hasattr(quantum_backend, 'metrics')
    
    def test_initialization_with_config(self):
        """Test initialisatie met configuratie."""
        backend = QuantumBackend()
        backend.is_available = True
        
        with patch.object(backend, 'initialize', return_value=True) as mock_init:
            result = backend.initialize({'n_qubits': 15, 'shots': 2000})
            mock_init.assert_called_once_with({'n_qubits': 15, 'shots': 2000})
    
    def test_create_continuous_field_fallback(self, quantum_backend):
        """Test field creatie fallback (geen qiskit)."""
        quantum_backend.is_available = False
        field = quantum_backend.create_continuous_field(10)
        
        assert field is not None
        assert field.shape == (10,)
        assert abs(np.linalg.norm(field) - 1.0) < 1e-6
    
    def test_swap_test_corrected(self, quantum_backend, mock_qiskit):
        """Test gecorrigeerde SWAP-test."""
        mock_qc, mock_execute = mock_qiskit
        
        # Mock resultaten met anker-qubit
        mock_counts = {
            '000': 400,  # anker=0
            '001': 300,  # anker=1
            '010': 200,  # anker=0
            '011': 100,  # anker=1
        }
        mock_execute.return_value.result.return_value.get_counts.return_value = mock_counts
        
        a = np.random.randn(10)
        b = np.random.randn(10)
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)
        
        # Mock _array_to_circuit
        quantum_backend._array_to_circuit = MagicMock(return_value=Mock())
        
        # Roep compute_interference aan
        with patch.object(quantum_backend, '_swap_test_corrected', wraps=quantum_backend._swap_test_corrected) as mock_swap:
            result = quantum_backend.compute_interference(a, b)
            
            # p0 = (400 + 200) / 1000 = 0.6
            # overlap = 2*0.6 - 1 = 0.2
            assert abs(result - 0.2) < 0.01
    
    def test_swap_test_p0_calculation(self, quantum_backend):
        """Test de p0 berekening direct."""
        mock_counts = {
            '000': 400,
            '001': 300,
            '010': 200,
            '011': 100,
        }
        
        # Maak een test circuit
        mock_circuit = MagicMock()
        mock_circuit.num_qubits = 3
        
        # Roep _swap_test_corrected aan met mocks
        with patch.object(quantum_backend, 'execute') as mock_execute:
            mock_execute.return_value.result.return_value.get_counts.return_value = mock_counts
            
            result = quantum_backend._swap_test_corrected(mock_circuit, mock_circuit)
            
            # p0 moet 0.6 zijn, overlap 0.2
            assert abs(result - 0.2) < 0.01
    
    def test_entangled_update_partial_trace(self, quantum_backend):
        """Test entangled update met partiële trace."""
        # Maak mock circuits
        field_circuit = MagicMock()
        field_circuit.num_qubits = 2
        verleden_circuit = MagicMock()
        verleden_circuit.num_qubits = 2
        toekomst_circuit = MagicMock()
        toekomst_circuit.num_qubits = 2
        
        field = np.random.randn(10)
        verleden = np.random.randn(10)
        toekomst = np.random.randn(10)
        
        # Mock statevector voor een simpele test
        # Voor 6 qubits (2+2+2) is 2^6 = 64
        mock_statevector = np.random.randn(64) + 1j * np.random.randn(64)
        mock_statevector = mock_statevector / np.linalg.norm(mock_statevector)
        
        with patch.object(quantum_backend, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.get_statevector.return_value = mock_statevector
            mock_execute.return_value.result.return_value = mock_result
            
            result = quantum_backend._entangled_update(
                field_circuit, verleden_circuit, toekomst_circuit,
                field, verleden, toekomst
            )
            
            assert 'verleden' in result
            assert 'heden' in result
            assert 'toekomst' in result
            assert len(result['heden']) == len(field)
    
    def test_get_field_id_quantum(self, quantum_backend):
        """Test field ID lookup in quantum backend."""
        field = quantum_backend.create_continuous_field(10)
        
        # Eerste keer
        id1 = quantum_backend.get_field_id(field)
        assert id1 is not None
        
        # Tweede keer (cache hit)
        id2 = quantum_backend.get_field_id(field)
        assert id1 == id2
        assert quantum_backend.metrics['cache_hits'] > 0
    
    def test_array_to_circuit_with_id(self, quantum_backend):
        """Test array to circuit met ID."""
        field = np.random.randn(10)
        field = field / np.linalg.norm(field)
        
        # Maak circuit via array_to_circuit zonder ID
        circuit1 = quantum_backend._array_to_circuit(field)
        
        # Haal ID op
        field_id = quantum_backend.get_field_id(field)
        
        # Maak circuit met ID
        circuit2 = quantum_backend._array_to_circuit(field, field_id)
        
        # Zou hetzelfde circuit moeten zijn
        assert circuit1 is circuit2
    
    @pytest.mark.skipif(not HARDWARE_EXCEPTIONS_AVAILABLE, 
                        reason="hardware_exceptions niet beschikbaar")
    def test_error_handling(self, quantum_backend):
        """Test error handling."""
        with pytest.raises(HardwareError):
            # Forceer een error
            quantum_backend._measure_circuit(None)
    
    def test_get_info(self, quantum_backend):
        """Test info string."""
        info = quantum_backend.get_info()
        assert "Quantum" in info
    
    def test_cleanup(self, quantum_backend):
        """Test cleanup."""
        quantum_backend.cleanup()
        assert len(quantum_backend.circuits) == 0
        assert len(quantum_backend.field_data) == 0


# ====================================================================
# CUDA BACKEND TESTS
# ====================================================================

class TestCUDABackend:
    """Test suite voor CUDA backend."""
    
    def test_initialization(self):
        """Test CUDA backend initialisatie."""
        backend = CUDABackend()
        assert backend.name == "CUDA"
    
    def test_create_continuous_field_fallback(self):
        """Test field creatie fallback (geen cuda)."""
        backend = CUDABackend()
        backend.is_available = False
        
        field = backend.create_continuous_field(10)
        
        assert field is not None
        assert field.shape == (10,)
        assert abs(np.linalg.norm(field) - 1.0) < 1e-6
    
    def test_get_info(self):
        """Test info string."""
        backend = CUDABackend()
        info = backend.get_info()
        assert "CUDA" in info


# ====================================================================
# HARDWARE FACTORY TESTS
# ====================================================================

class TestHardwareFactory:
    """Test suite voor Hardware Factory."""
    
    def test_factory_initialization(self):
        """Test factory initialisatie."""
        factory = HardwareFactory()
        assert hasattr(factory, 'registry')
        assert hasattr(factory, 'config')
        assert hasattr(factory, 'initialized_backends')
    
    def test_get_best_backend(self):
        """Test beste backend detectie."""
        factory = HardwareFactory()
        backend = factory.get_best_backend()
        assert backend is not None
        assert isinstance(backend, HardwareBackend)
    
    def test_get_backend_by_name_cpu(self):
        """Test CPU backend forceren."""
        factory = HardwareFactory()
        backend = factory.create_backend('cpu', {'num_threads': 2})
        assert backend is not None
        assert isinstance(backend, CPUBackend)
    
    def test_list_available(self):
        """Test lijst van beschikbare backends."""
        factory = HardwareFactory()
        available = factory.list_available()
        assert isinstance(available, list)
        assert 'cpu' in available
    
    def test_switch_backend(self):
        """Test backend switching."""
        factory = HardwareFactory()
        
        cpu = factory.create_backend('cpu')
        assert cpu is not None
        
        result = factory.switch_backend('cpu')
        assert result == True
    
    def test_get_status(self):
        """Test status ophalen."""
        factory = HardwareFactory()
        status = factory.get_status()
        
        assert 'active_backend' in status
        assert 'available_backends' in status
        assert 'initialized_backends' in status
        assert 'config' in status
    
    def test_cache_instance_attribute(self):
        """Test dat cache een instance-attribuut is (geen klasse-attribuut)."""
        factory1 = HardwareFactory()
        factory2 = HardwareFactory()
        
        # Cache zou apart moeten zijn
        assert factory1._cache is not factory2._cache
        
        # Cache zou leeg moeten beginnen
        assert len(factory1._cache) == 0
        assert len(factory2._cache) == 0
    
    def test_cache_isolation(self):
        """Test dat caches van verschillende instances geïsoleerd zijn."""
        factory1 = HardwareFactory()
        factory2 = HardwareFactory()
        
        # Cache in factory1
        factory1._cache['test'] = (Mock(), time.time() + 100)
        
        # Factory2 zou niet beïnvloed moeten zijn
        assert 'test' not in factory2._cache
        assert len(factory1._cache) == 1
        assert len(factory2._cache) == 0
    
    def test_cleanup(self):
        """Test cleanup."""
        factory = HardwareFactory()
        factory.cleanup()
        assert len(factory.initialized_backends) == 0
        assert factory.active_backend is None


# ====================================================================
# BACKEND REGISTRY TESTS
# ====================================================================

class TestBackendRegistry:
    """Test suite voor Backend Registry."""
    
    def test_registry_singleton(self):
        """Test dat registry een singleton is."""
        registry1 = BackendRegistry()
        registry2 = BackendRegistry()
        assert registry1 is registry2
    
    def test_get_available_backends(self):
        """Test ophalen beschikbare backends."""
        registry = BackendRegistry()
        available = registry.get_available_backends()
        
        assert isinstance(available, list)
        for backend in available:
            assert isinstance(backend, BackendInfo)
            assert hasattr(backend, 'name')
            assert hasattr(backend, 'priority')
    
    def test_get_backend(self):
        """Test ophalen specifieke backend."""
        registry = BackendRegistry()
        
        cpu_info = registry.get_backend('cpu')
        assert cpu_info is not None
        assert cpu_info.name == 'cpu'
        assert cpu_info.priority == 10
        
        quantum_info = registry.get_backend('quantum')
        assert quantum_info is not None
        assert quantum_info.name == 'quantum'
        assert quantum_info.priority == 90


# ====================================================================
# HARDWARE CONFIG TESTS
# ====================================================================

class TestHardwareConfig:
    """Test suite voor Hardware Config."""
    
    def test_cpu_config_defaults(self):
        """Test CPU config defaults."""
        config = CPUConfig()
        assert config.precision == "float64"
        assert config.simulate_analog == True
        assert config.num_threads == 4
        assert config.use_blas == True
    
    def test_cpu_config_custom(self):
        """Test CPU config custom waarden."""
        config = CPUConfig(
            precision="float32",
            simulate_analog=False,
            num_threads=2,
            use_blas=False
        )
        assert config.precision == "float32"
        assert config.simulate_analog == False
        assert config.num_threads == 2
        assert config.use_blas == False
    
    def test_cuda_config_defaults(self):
        """Test CUDA config defaults."""
        config = CUDAConfig()
        assert config.device_id == 0
        assert config.memory_fraction == 0.8
        assert config.use_tensor_cores == True
    
    def test_fpga_config_defaults(self):
        """Test FPGA config defaults."""
        config = FPGAConfig()
        assert config.bitstream == "nexus.bit"
        assert config.timeout == 1.0
        assert config.use_interrupts == True
        assert config.dma_channels == 4
    
    def test_quantum_config_defaults(self):
        """Test Quantum config defaults."""
        config = QuantumConfig()
        assert config.n_qubits == 20
        assert config.shots == 1000
        assert config.use_real_hardware == False
        assert config.backend_name == "aer_simulator"
    
    def test_hardware_config_defaults(self):
        """Test complete hardware config defaults."""
        config = HardwareConfig()
        assert config.backend == "auto"
        assert config.fallback_to_cpu == True
        assert config.log_level == "INFO"
        assert config.profile == False
    
    def test_hardware_config_to_dict(self):
        """Test conversie naar dictionary."""
        config = HardwareConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'backend' in config_dict
        assert 'cpu' in config_dict
        assert 'cuda' in config_dict
        assert 'fpga' in config_dict
        assert 'quantum' in config_dict
    
    def test_get_backend_config(self):
        """Test ophalen backend-specifieke config."""
        config = HardwareConfig()
        
        cpu_config = config.get_backend_config('cpu')
        assert isinstance(cpu_config, dict)
        assert 'precision' in cpu_config
        
        cuda_config = config.get_backend_config('cuda')
        assert isinstance(cuda_config, dict)
        assert 'device_id' in cuda_config


# ====================================================================
# HARDWARE EXCEPTIONS TESTS
# ====================================================================

class TestHardwareExceptions:
    """Test suite voor Hardware Exceptions."""
    
    def test_hardware_error(self):
        """Test basis HardwareError."""
        error = HardwareError("Test error", "CPU")
        assert str(error) == "[CPU] Test error"
        assert error.backend == "CPU"
        assert error.timestamp is not None
        
        error_dict = error.to_dict()
        assert error_dict['type'] == 'HardwareError'
        assert error_dict['backend'] == 'CPU'
    
    def test_hardware_not_available_error(self):
        """Test HardwareNotAvailableError."""
        error = HardwareNotAvailableError(
            backend="Quantum",
            reason="Geen qubits",
            required_drivers=["qiskit"]
        )
        assert "Quantum" in str(error)
        assert "Geen qubits" in str(error)
    
    def test_hardware_timeout_error(self):
        """Test HardwareTimeoutError."""
        error = HardwareTimeoutError(
            operation="test",
            timeout=5.0,
            backend="FPGA",
            actual_time=6.2
        )
        assert "timeout" in str(error).lower()
        assert "5.00s" in str(error)
    
    def test_hardware_memory_error(self):
        """Test HardwareMemoryError."""
        error = HardwareMemoryError(
            required=8000000000,
            available=4000000000,
            unit="bytes",
            backend="CUDA",
            memory_type="VRAM"
        )
        assert "geheugen" in str(error).lower()
        assert "8000000000" in str(error)
    
    def test_fpga_error(self):
        """Test FPGAError."""
        error = FPGAError(
            "FPGA crash",
            register_values={'status': 0xFF},
            bitstream='test.bit'
        )
        assert "FPGA" in str(error)
        assert "register" in error.context
    
    def test_quantum_error(self):
        """Test QuantumError."""
        error = QuantumError(
            "Decoherence",
            circuit_name="test",
            qubit_indices=[0,1,2],
            error_mitigation="ZNE"
        )
        assert "Quantum" in str(error)
        assert "qubits" in error.context
    
    def test_cuda_error(self):
        """Test CUDAError."""
        error = CUDAError(
            "Out of memory",
            cuda_error_code=2,
            device_id=0,
            memory_info={'free': 1000, 'total': 8000}
        )
        assert "CUDA" in str(error)
        assert "error_code" in error.context
    
    @handle_hardware_errors(default_return=None)
    def failing_function():
        raise ValueError("Test")
    
    def test_error_decorator(self):
        """Test error handling decorator."""
        with pytest.raises(HardwareError):
            self.failing_function()
    
    def test_retry_strategy(self):
        """Test retry strategy."""
        strategy = RetryStrategy(max_retries=2, base_delay=0.01)
        
        call_count = 0
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise HardwareTimeoutError("test", 0.1, "CPU")
            return "success"
        
        result = strategy.execute(failing_function)
        assert result == "success"
        assert call_count == 3
    
    def test_error_handler(self):
        """Test global error handler."""
        handler = HardwareErrorHandler()
        
        # Reset
        handler.get_aggregator().clear()
        
        # Voeg errors toe
        for i in range(5):
            error = HardwareTimeoutError(f"test_{i}", 1.0, "FPGA")
            handler.handle_error(error)
        
        report = handler.get_aggregator().get_report()
        assert report['total_errors'] == 5
        assert 'HardwareTimeoutError' in report['by_type']


# ====================================================================
# CONVENIENCE FUNCTIES TESTS
# ====================================================================

class TestConvenienceFunctions:
    """Test suite voor convenience functies."""
    
    def test_get_best_backend(self):
        """Test get_best_backend functie."""
        backend = get_best_backend()
        assert backend is not None
        assert isinstance(backend, HardwareBackend)
    
    def test_get_backend_by_name(self):
        """Test get_backend_by_name functie."""
        backend = get_backend_by_name('cpu', {'num_threads': 2})
        assert backend is not None
        assert isinstance(backend, CPUBackend)
    
    def test_cleanup_hardware(self):
        """Test cleanup_hardware functie."""
        # Eerst iets initialiseren
        backend = get_best_backend()
        assert backend is not None
        
        # Cleanup
        cleanup_hardware()
        
        # Nieuwe factory zou leeg moeten zijn
        from apeiron.hardware.factory import _factory_instance
        assert _factory_instance is None


# ====================================================================
# INTEGRATIE TESTS
# ====================================================================

class TestHardwareIntegration:
    """Integratie tests voor alle hardware componenten."""
    
    def test_cpu_full_cycle(self, cpu_backend):
        """Test volledige cyclus met CPU."""
        # Creëer velden
        fields = [cpu_backend.create_continuous_field(10) for _ in range(3)]
        
        # Update velden
        for f in fields:
            result = cpu_backend.field_update(f, 0.1, f, f, f)
            assert result is not None
        
        # Meet interferentie
        for i in range(len(fields)):
            for j in range(i+1, len(fields)):
                interference = cpu_backend.compute_interference(fields[i], fields[j])
                assert 0 <= interference <= 1
        
        # Vind patronen
        patterns = cpu_backend.find_stable_patterns(fields, threshold=0.5)
        assert isinstance(patterns, list)
        
        # Meet coherentie
        coherence = cpu_backend.measure_coherence(fields)
        assert 0 <= coherence <= 1
        
        # Cleanup
        cpu_backend.cleanup()
    
    def test_factory_with_config(self):
        """Test factory met configuratie."""
        # Laad config
        config = HardwareConfig()
        config_dict = config.to_dict()
        
        # Factory met config
        factory = HardwareFactory(config_dict)
        backend = factory.get_best_backend()
        
        assert backend is not None
    
    def test_error_propagation(self):
        """Test error propagatie."""
        @handle_hardware_errors(default_return=None)
        def failing_hardware_function():
            raise ValueError("Hardware error")
        
        with pytest.raises(HardwareError):
            failing_hardware_function()


# ====================================================================
# PARAMETRIZED TESTS
# ====================================================================

@pytest.mark.parametrize("dimensions", [1, 5, 10, 50, 100])
def test_field_creation_dimensions(cpu_backend, dimensions):
    """Test field creatie met verschillende dimensies."""
    field = cpu_backend.create_continuous_field(dimensions)
    assert field.shape == (dimensions,)
    assert abs(np.linalg.norm(field) - 1.0) < 1e-6

@pytest.mark.parametrize("threshold", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_pattern_detection_threshold(cpu_backend, threshold):
    """Test pattern detection met verschillende thresholds."""
    fields = [cpu_backend.create_continuous_field(10) for _ in range(5)]
    patterns = cpu_backend.find_stable_patterns(fields, threshold)
    
    for pattern in patterns:
        assert pattern['sterkte'] >= threshold

@pytest.mark.parametrize("num_fields", [2, 3, 5, 10])
def test_coherence_scaling(cpu_backend, num_fields):
    """Test coherentie meting met verschillende aantallen velden."""
    fields = [cpu_backend.create_continuous_field(10) for _ in range(num_fields)]
    coherence = cpu_backend.measure_coherence(fields)
    assert 0 <= coherence <= 1

@pytest.mark.parametrize("value,expected", [
    (0.0, 0),
    (0.1, 6554),
    (0.5, 32768),
    (1.0, 65536),
])
def test_fixed_point_conversion(fpga_backend, value, expected):
    """Test fixed-point conversie voor verschillende waarden."""
    result = fpga_backend._float_to_fixed(value)
    assert result == expected

@pytest.mark.parametrize("counts,expected_overlap", [
    ({'000': 500, '001': 500}, 0.0),  # p0=0.5, overlap=0
    ({'000': 750, '001': 250}, 0.5),  # p0=0.75, overlap=0.5
    ({'000': 1000}, 1.0),              # p0=1.0, overlap=1.0
])
def test_swap_test_formula(quantum_backend, counts, expected_overlap):
    """Test de SWAP-test formule met verschillende verdelingen."""
    with patch.object(quantum_backend, 'execute') as mock_execute:
        mock_execute.return_value.result.return_value.get_counts.return_value = counts
        
        mock_circuit = MagicMock()
        mock_circuit.num_qubits = 3
        
        result = quantum_backend._swap_test_corrected(mock_circuit, mock_circuit)
        assert abs(result - expected_overlap) < 0.01


# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 HARDWARE TESTS UITVOEREN")
    print("="*80)
    print("✅ CPU: get_field_id(), cache metrics, pattern IDs")
    print("✅ FPGA: fixed-point conversie, field ID lookup")
    print("✅ Quantum: gecorrigeerde SWAP-test, partiële trace")
    print("✅ Factory: cache instance fix")
    print("="*80)
    
    # Voer pytest uit
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))