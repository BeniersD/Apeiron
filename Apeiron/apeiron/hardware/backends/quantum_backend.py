"""
Quantum Backend - ECHTE SUPERPOSITIE!
Alle mogelijkheden bestaan tegelijk.
================================================================================
Biedt volledige integratie met:
- hardware_factory.py voor centrale hardware detectie
- hardware_config.py voor gestandaardiseerde configuratie
- hardware_exceptions.py voor uniforme error handling

Belangrijke correcties:
- SWAP-test: p0‑kans wordt nu correct berekend (ankerbith positie rechts)
- Partiële trace: gebruikt numpy‑reshape in plaats van drie losse metingen
- Veld‑ID systeem voor O(1) lookups via hashing
- Circuit caching met hashing
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
import time
import hashlib
import random
import struct

# --- Relatieve import binnen de backends package ---
from .backend import HardwareBackend

# Importeer hardware exceptions (optioneel)
try:
    from hardware_exceptions import (
        QuantumError,
        HardwareTimeoutError,
        HardwareInitializationError,
        handle_hardware_errors
    )
    EXCEPTIONS_AVAILABLE = True
except ImportError:
    EXCEPTIONS_AVAILABLE = False
    # Fallback decorator
    def handle_hardware_errors(default_return=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ Hardware fout: {e}")
                    return default_return
            return wrapper
        return decorator

# Qiskit import met betere error handling
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer
    from qiskit.providers.aer import QasmSimulator, StatevectorSimulator
    from qiskit.quantum_info import state_fidelity, partial_trace
    from qiskit.compiler import transpile
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
except Exception as e:
    QISKIT_AVAILABLE = False
    print(f"⚠️ Fout bij laden Qiskit: {e}")


class QuantumBackend(HardwareBackend):
    """
    Quantum backend - gebruikt superpositie voor ECHTE tijdloosheid.
    Alle mogelijke oceaan-toestanden bestaan TEGELIJK.
    
    Features:
    - Superpositie van alle mogelijke toestanden
    - Quantum verstrengeling voor correlaties
    - SWAP test voor overlap meting
    - Statevector simulatie voor exacte resultaten
    
    Verbeteringen:
    - GECORRIGEERDE SWAP-test (kijkt naar anker-qubit)
    - PARTIËLE TRACE via numpy reshape (geen drie metingen)
    - O(1) lookups via hashing
    - Uitgebreide metrics
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Quantum"
        self.qubits = None
        self.circuit = None
        self.simulator = None
        self.statevector_sim = None
        
        # O(1) lookups via dictionaries
        self.circuits: Dict[int, QuantumCircuit] = {}  # id -> circuit
        self.field_data: Dict[int, np.ndarray] = {}    # id -> array
        self.circuit_counters: Dict[int, int] = {}     # id -> usage counter
        self.circuit_hash: Dict[str, int] = {}         # hash -> id voor lookup
        
        self.logger = logging.getLogger('Quantum')
        self.is_available = QISKIT_AVAILABLE
        
        # Configuratie
        self.config = {
            'n_qubits': 20,
            'shots': 1000,
            'use_real_hardware': False,
            'backend_name': 'aer_simulator',
            'optimization_level': 1,
            'noise_model': True,
            'coupling_map': False,
            'initial_layout': None,
            'use_entanglement': True,
            'max_circuit_depth': 100
        }
        
        # Performance metrics
        self.metrics = {
            'total_circuits': 0,
            'total_executions': 0,
            'total_swap_tests': 0,
            'total_timeouts': 0,
            'avg_execution_time': 0.0,
            'min_execution_time': float('inf'),
            'max_execution_time': 0.0,
            'total_qubit_seconds': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Volgende ID
        self._next_id = 0
        
        if self.is_available:
            self.logger.info("🌀 Quantum Backend geladen - ALLES IN SUPERPOSITIE!")
        else:
            self.logger.warning("⚠️ Qiskit niet beschikbaar - quantum backend niet actief")
    
    # ====================================================================
    # INITIALISATIE
    # ====================================================================
    
    @handle_hardware_errors(default_return=False)
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialiseer quantum simulator of echte quantum computer.
        
        Args:
            config: Configuratie dictionary met o.a.:
                - n_qubits: Aantal qubits
                - shots: Aantal metingen
                - use_real_hardware: Gebruik echte quantum hardware
                - backend_name: Naam van backend
                - noise_model: Gebruik ruis model
        
        Returns:
            True als initialisatie gelukt is
        """
        if not QISKIT_AVAILABLE:
            error_msg = "Qiskit niet beschikbaar - kan quantum niet laden"
            self.logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise HardwareInitializationError(
                    backend="Quantum",
                    component="Qiskit",
                    details=error_msg
                )
            return False
        
        # Update config
        self.config.update(config)
        
        try:
            # Gebruik simulatoren
            self.simulator = QasmSimulator()
            self.statevector_sim = StatevectorSimulator()
            
            # Aantal qubits
            self.n_qubits = self.config.get('n_qubits', 20)
            self.qubits = QuantumRegister(self.n_qubits, 'q')
            
            # Hoofd circuit voor de oceaan
            self.circuit = QuantumCircuit(self.qubits)
            
            # Zet ALLE qubits in superpositie
            for i in range(self.n_qubits):
                self.circuit.h(i)  # Hadamard = superpositie
            
            # Test initialisatie
            self._test_initialization()
            
            self.logger.info(f"  ✅ {self.n_qubits} qubits in superpositie")
            self.logger.info(f"  ⚛️  {2**self.n_qubits} toestanden tegelijk!")
            self.logger.info(f"  🎯 Shots: {self.config.get('shots')}")
            
            if self.config.get('use_real_hardware'):
                self.logger.info(f"  🔬 Real hardware: {self.config.get('backend_name')}")
            
            return True
            
        except Exception as e:
            error_msg = f"Quantum init mislukt: {e}"
            self.logger.error(error_msg)
            
            if EXCEPTIONS_AVAILABLE:
                raise HardwareInitializationError(
                    backend="Quantum",
                    details=str(e)
                ) from e
            return False
    
    def _test_initialization(self):
        """Test quantum backend met een kleine operatie."""
        try:
            # Maak test circuit
            qr = QuantumRegister(2, 'q')
            test = QuantumCircuit(qr)
            test.h(0)
            test.cx(0, 1)
            
            # Voer uit
            job = execute(test, self.statevector_sim)
            result = job.result()
            statevector = result.get_statevector()
            
            self.logger.debug(f"  ✅ Quantum test geslaagd: {statevector}")
            
        except Exception as e:
            self.logger.warning(f"  ⚠️ Quantum test warning: {e}")
    
    # ====================================================================
    # KERN FUNCTIONALITEIT
    # ====================================================================
    
    @handle_hardware_errors(default_return=None)
    def create_continuous_field(self, dimensions: int) -> np.ndarray:
        """
        Creëer een quantum veld in superpositie.
        
        Args:
            dimensions: Dimensie van het veld
            
        Returns:
            Numpy array met het gecreëerde veld
        """
        if not QISKIT_AVAILABLE:
            # CPU fallback
            return self._cpu_create_field(dimensions)
        
        # Beperk dimensies tot beschikbare qubits
        n_qubits = min(dimensions, self.n_qubits)
        
        try:
            # Nieuw circuit voor dit veld
            qr = QuantumRegister(n_qubits, 'q')
            cr = ClassicalRegister(n_qubits, 'c')
            circuit = QuantumCircuit(qr, cr)
            
            # Zet in superpositie
            for i in range(n_qubits):
                circuit.h(i)
            
            # Voeg kleine random rotaties toe voor variatie
            for i in range(n_qubits):
                circuit.rz(random.uniform(0, 2*np.pi), i)
            
            # Genereer unieke ID
            field_id = self._next_id
            self._next_id += 1
            
            self.circuits[field_id] = circuit
            self.circuit_counters[field_id] = 0
            
            # Meet de statevector voor klassieke representatie
            start_time = time.time()
            job = execute(circuit, self.statevector_sim)
            statevector = job.result().get_statevector()
            
            # Update metrics
            exec_time = time.time() - start_time
            self.metrics['total_executions'] += 1
            self.metrics['total_qubit_seconds'] += n_qubits * exec_time
            self.metrics['avg_execution_time'] = (
                self.metrics['avg_execution_time'] * 0.95 + exec_time * 0.05
            )
            self.metrics['min_execution_time'] = min(self.metrics['min_execution_time'], exec_time)
            self.metrics['max_execution_time'] = max(self.metrics['max_execution_time'], exec_time)
            
            # Converteer naar numpy array
            field_array = np.abs(statevector[:dimensions].real)
            if len(field_array) < dimensions:
                field_array = np.pad(field_array, (0, dimensions - len(field_array)))
            field_array = self._normalize(field_array)
            
            self.field_data[field_id] = field_array
            self.metrics['total_circuits'] += 1
            
            # Sla hash op voor snelle lookup
            field_hash = hashlib.md5(field_array.tobytes()).hexdigest()
            self.circuit_hash[field_hash] = field_id
            
            return field_array
            
        except Exception as e:
            error_msg = f"Quantum field creatie mislukt: {e}"
            self.logger.error(error_msg)
            
            if EXCEPTIONS_AVAILABLE:
                raise QuantumError(
                    message=error_msg,
                    circuit_name="create_field",
                    qubit_indices=list(range(n_qubits))
                ) from e
            
            return self._cpu_create_field(dimensions)
    
    def get_field_id(self, field: np.ndarray) -> Optional[int]:
        """
        Haal field ID op via O(1) lookup.
        
        Args:
            field: Het veld waarvoor de ID gezocht wordt
            
        Returns:
            Field ID of None als niet gevonden
        """
        # Gebruik hash voor O(1) lookup
        try:
            field_hash = hashlib.md5(field.tobytes()).hexdigest()
            if field_hash in self.circuit_hash:
                self.metrics['cache_hits'] += 1
                return self.circuit_hash[field_hash]
        except:
            pass
        
        # Fallback: lineaire scan (voor als hash niet werkt)
        self.metrics['cache_misses'] += 1
        for fid, stored in self.field_data.items():
            if np.array_equal(stored, field):
                # Update hash voor toekomst
                try:
                    field_hash = hashlib.md5(field.tobytes()).hexdigest()
                    self.circuit_hash[field_hash] = fid
                except:
                    pass
                return fid
        
        return None
    
    def _cpu_create_field(self, dimensions: int) -> np.ndarray:
        """CPU fallback voor field creatie."""
        field = np.random.randn(dimensions)
        return self._normalize(field)
    
    @handle_hardware_errors(default_return=None)
    def field_update(self, field: np.ndarray, dt: float,
                    verleden: np.ndarray, heden: np.ndarray,
                    toekomst: np.ndarray) -> Dict:
        """
        Update veld via quantum gates.
        ALLES GEBEURT IN SUPERPOSITIE!
        
        Args:
            field: Huidig veld (numpy array)
            dt: Tijdstap
            verleden: Verleden veld
            heden: Heden veld
            toekomst: Toekomst veld
            
        Returns:
            Dict met 'verleden', 'heden', 'toekomst' als numpy arrays
        """
        if not QISKIT_AVAILABLE:
            return self._cpu_update(field, dt, verleden, heden, toekomst)
        
        # Gebruik get_field_id voor O(1) lookups
        field_id = self.get_field_id(field)
        verleden_id = self.get_field_id(verleden)
        heden_id = self.get_field_id(heden)
        toekomst_id = self.get_field_id(toekomst)
        
        # Zoek of maak quantum circuits
        field_circuit = self._array_to_circuit(field, field_id)
        verleden_circuit = self._array_to_circuit(verleden, verleden_id)
        heden_circuit = self._array_to_circuit(heden, heden_id)
        toekomst_circuit = self._array_to_circuit(toekomst, toekomst_id)
        
        if field_circuit is None:
            return self._cpu_update(field, dt, verleden, heden, toekomst)
        
        try:
            # Update counters
            if field_id is not None:
                self.circuit_counters[field_id] = self.circuit_counters.get(field_id, 0) + 1
            
            # Voeg ruis toe via kleine rotaties
            n_qubits = field_circuit.num_qubits
            for i in range(n_qubits):
                field_circuit.rz(dt * 0.1, i)  # Kleine fase draaiing
                field_circuit.rx(random.gauss(0, 0.01), i)  # Quantum ruis
            
            # Verstrengel met verleden en toekomst (ALS ze bestaan en gewenst)
            if (verleden_circuit and toekomst_circuit and 
                self.config.get('use_entanglement', True)):
                return self._entangled_update(
                    field_circuit, verleden_circuit, toekomst_circuit,
                    field, verleden, toekomst,
                    field_id, verleden_id, toekomst_id
                )
            
            # Geen verstrengeling - gewoon het geüpdate veld
            field_array = self._measure_circuit(field_circuit)
            return {
                'verleden': verleden,
                'heden': field_array if field_array is not None else field,
                'toekomst': toekomst
            }
            
        except Exception as e:
            self.logger.error(f"Quantum update mislukt: {e}")
            return self._cpu_update(field, dt, verleden, heden, toekomst)
    
    def _entangled_update(self, field_circuit, verleden_circuit, toekomst_circuit,
                         field, verleden, toekomst,
                         field_id=None, verleden_id=None, toekomst_id=None) -> Dict:
        """
        Verstrengelde update met partiële trace.
        """
        n_qubits = field_circuit.num_qubits
        total_qubits = n_qubits * 3
        
        from qiskit import QuantumCircuit, execute
        
        # Combineer circuits voor verstrengeling
        combined = QuantumCircuit(total_qubits)
        combined.append(field_circuit, range(n_qubits))
        combined.append(verleden_circuit, range(n_qubits, 2*n_qubits))
        combined.append(toekomst_circuit, range(2*n_qubits, 3*n_qubits))
        
        # Verstrengel veld met verleden
        for i in range(min(n_qubits, verleden_circuit.num_qubits)):
            combined.cx(i, n_qubits + i)
        
        # Verstrengel veld met toekomst
        for i in range(min(n_qubits, toekomst_circuit.num_qubits)):
            combined.cx(i, 2*n_qubits + i)
        
        start_time = time.time()
        
        # Voer ÉÉN keer uit voor statevector
        job = execute(combined, self.statevector_sim)
        statevector = job.result().get_statevector()
        
        # Update metrics
        exec_time = time.time() - start_time
        self.metrics['total_executions'] += 1
        self.metrics['total_qubit_seconds'] += total_qubits * exec_time
        
        # Partiële trace via numpy reshape
        # Converteer naar tensor met vorm [2] * total_qubits
        sv = np.array(statevector).reshape([2] * total_qubits)
        
        # Partiële trace voor field (trace over verleden en toekomst)
        rho_field = np.zeros((2**n_qubits, 2**n_qubits), dtype=complex)
        
        # Itereer over alle basistoestanden van verleden en toekomst
        for i in range(2**n_qubits):
            for j in range(2**n_qubits):
                # Converteer i en j naar qubit indices (little-endian)
                bits_i = [(i >> k) & 1 for k in range(n_qubits)]
                bits_j = [(j >> k) & 1 for k in range(n_qubits)]
                
                # Bouw slices voor alle qubits
                field_slice = [slice(None)] * n_qubits
                verleden_slice = bits_i
                toekomst_slice = bits_j
                
                # Combineer alle slices
                slices = field_slice + verleden_slice + toekomst_slice
                
                # Haal de relevante amplitudes
                amplitudes = sv[tuple(slices)]
                rho_field[i, j] = amplitudes
        
        # Haal diagonale elementen (kansen) voor field
        field_probs = np.abs(np.diag(rho_field))
        if np.sum(field_probs) > 0:
            field_probs = field_probs / np.sum(field_probs)
        
        # Zelfde voor verleden (trace over field en toekomst)
        rho_verleden = np.zeros((2**n_qubits, 2**n_qubits), dtype=complex)
        for i in range(2**n_qubits):
            for j in range(2**n_qubits):
                bits_i = [(i >> k) & 1 for k in range(n_qubits)]
                bits_j = [(j >> k) & 1 for k in range(n_qubits)]
                
                field_slice = bits_i
                verleden_slice = [slice(None)] * n_qubits
                toekomst_slice = bits_j
                
                slices = field_slice + verleden_slice + toekomst_slice
                amplitudes = sv[tuple(slices)]
                rho_verleden[i, j] = amplitudes
        
        verleden_probs = np.abs(np.diag(rho_verleden))
        if np.sum(verleden_probs) > 0:
            verleden_probs = verleden_probs / np.sum(verleden_probs)
        
        # Zelfde voor toekomst (trace over field en verleden)
        rho_toekomst = np.zeros((2**n_qubits, 2**n_qubits), dtype=complex)
        for i in range(2**n_qubits):
            for j in range(2**n_qubits):
                bits_i = [(i >> k) & 1 for k in range(n_qubits)]
                bits_j = [(j >> k) & 1 for k in range(n_qubits)]
                
                field_slice = bits_i
                verleden_slice = bits_j
                toekomst_slice = [slice(None)] * n_qubits
                
                slices = field_slice + verleden_slice + toekomst_slice
                amplitudes = sv[tuple(slices)]
                rho_toekomst[i, j] = amplitudes
        
        toekomst_probs = np.abs(np.diag(rho_toekomst))
        if np.sum(toekomst_probs) > 0:
            toekomst_probs = toekomst_probs / np.sum(toekomst_probs)
        
        # Converteer kansverdelingen naar arrays van de juiste lengte
        field_array = np.pad(field_probs, (0, max(0, len(field) - len(field_probs))))
        verleden_array = np.pad(verleden_probs, (0, max(0, len(verleden) - len(verleden_probs))))
        toekomst_array = np.pad(toekomst_probs, (0, max(0, len(toekomst) - len(toekomst_probs))))
        
        # Normaliseer
        if np.linalg.norm(field_array) > 0:
            field_array = field_array / np.linalg.norm(field_array)
        if np.linalg.norm(verleden_array) > 0:
            verleden_array = verleden_array / np.linalg.norm(verleden_array)
        if np.linalg.norm(toekomst_array) > 0:
            toekomst_array = toekomst_array / np.linalg.norm(toekomst_array)
        
        # Update cached data als IDs bekend zijn
        if field_id is not None:
            self.field_data[field_id] = field_array
        if verleden_id is not None:
            self.field_data[verleden_id] = verleden_array
        if toekomst_id is not None:
            self.field_data[toekomst_id] = toekomst_array
        
        return {
            'verleden': verleden_array if len(verleden_array) > 0 else verleden,
            'heden': field_array if len(field_array) > 0 else field,
            'toekomst': toekomst_array if len(toekomst_array) > 0 else toekomst
        }
    
    def _partial_trace_fast(self, statevector, keep_qubits, total_qubits):
        """Snelle partiële trace voor kleine systemen."""
        if total_qubits > 12:
            self.logger.warning(f"Partiële trace voor {total_qubits} qubits kan traag zijn")
        
        dim = 2 ** total_qubits
        sv = np.array(statevector).reshape(-1)
        
        # Dichtheidsmatrix
        rho = np.outer(sv, sv.conj())
        
        # Dimensie van het te behouden systeem
        keep_dim = 2 ** len(keep_qubits)
        trace_dim = dim // keep_dim
        
        # Partiële trace
        rho_keep = np.zeros((keep_dim, keep_dim), dtype=complex)
        for i in range(trace_dim):
            offset = i * keep_dim
            rho_keep += rho[offset:offset+keep_dim, offset:offset+keep_dim]
        
        return rho_keep
    
    def _cpu_update(self, field: np.ndarray, dt: float,
                   verleden: np.ndarray, heden: np.ndarray,
                   toekomst: np.ndarray) -> Dict:
        """CPU fallback voor field update."""
        new_field = field + 0.01 * np.random.randn(*field.shape) * np.sqrt(dt)
        new_field = self._normalize(new_field)
        
        return {
            'verleden': verleden,
            'heden': new_field,
            'toekomst': toekomst
        }
    
    def _array_to_circuit(self, array: np.ndarray, field_id: Optional[int] = None) -> Optional[QuantumCircuit]:
        """Converteer numpy array naar quantum circuit (of vind bestaande)."""
        if array is None or not QISKIT_AVAILABLE:
            return None
        
        # Als ID gegeven is, gebruik die
        if field_id is not None and field_id in self.circuits:
            return self.circuits.get(field_id)
        
        # Zoek via hash (O(1))
        field_id_from_hash = self.get_field_id(array)
        if field_id_from_hash is not None and field_id_from_hash in self.circuits:
            return self.circuits.get(field_id_from_hash)
        
        # Maak nieuw circuit
        n_qubits = min(len(array), self.n_qubits)
        qr = QuantumRegister(n_qubits, 'q')
        circuit = QuantumCircuit(qr)
        
        # Initialiseer met array-waarden (vereenvoudigd)
        for i in range(n_qubits):
            if array[i] > 0.5:
                circuit.x(i)  # Zet qubit als de waarde hoog is
            # Voeg fase informatie toe
            if i < len(array) and array[i] != 0:
                circuit.rz(array[i] * np.pi, i)
        
        # Sla op met nieuw ID
        new_id = self._next_id
        self._next_id += 1
        
        self.circuits[new_id] = circuit
        self.field_data[new_id] = array.copy()
        self.circuit_counters[new_id] = 0
        
        # Sla hash op
        try:
            field_hash = hashlib.md5(array.tobytes()).hexdigest()
            self.circuit_hash[field_hash] = new_id
        except:
            pass
        
        return circuit
    
    def _measure_circuit(self, circuit: QuantumCircuit, 
                        qubit_range=None) -> Optional[np.ndarray]:
        """Meet een quantum circuit en retourneer numpy array."""
        if not QISKIT_AVAILABLE:
            return None
        
        try:
            start_time = time.time()
            
            # Bepaal qubit bereik
            if qubit_range is None:
                n_qubits = circuit.num_qubits
                qubit_range = range(n_qubits)
            elif isinstance(qubit_range, slice):
                n_qubits = (qubit_range.stop - qubit_range.start) if qubit_range.stop else 0
            else:
                n_qubits = len(qubit_range)
            
            if n_qubits == 0:
                return None
            
            # Optioneel: transpile voor optimalisatie
            if self.config.get('optimization_level', 1) > 0:
                circuit = transpile(
                    circuit, 
                    optimization_level=self.config.get('optimization_level', 1)
                )
            
            # Voer uit op statevector simulator
            job = execute(circuit, self.statevector_sim)
            statevector = job.result().get_statevector()
            
            # Converteer naar array
            if isinstance(qubit_range, slice):
                # Neem subset van qubits
                step = 2 ** (circuit.num_qubits - qubit_range.stop)
                start_idx = qubit_range.start
                indices = range(start_idx, len(statevector), step)
                array = np.abs([statevector[i].real for i in indices if i < len(statevector)])
            else:
                array = np.abs(statevector[:n_qubits].real)
            
            # Update metrics
            exec_time = time.time() - start_time
            self.metrics['total_executions'] += 1
            self.metrics['total_qubit_seconds'] += n_qubits * exec_time
            self.metrics['avg_execution_time'] = (
                self.metrics['avg_execution_time'] * 0.95 + exec_time * 0.05
            )
            
            # Normaliseer
            if np.linalg.norm(array) > 0:
                array = array / np.linalg.norm(array)
            
            return array
            
        except Exception as e:
            self.logger.error(f"Metingsfout: {e}")
            return np.zeros(10)
    
    # ====================================================================
    # INTERFERENTIE & PATRONEN
    # ====================================================================
    
    @handle_hardware_errors(default_return=0.5)
    def compute_interference(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Bereken interferentie via quantum overlap.
        Dit is ECHTE quantum interferentie!
        
        Args:
            a, b: numpy arrays om interferentie van te berekenen
            
        Returns:
            Interferentie sterkte (0-1)
        """
        self.metrics['total_swap_tests'] += 1
        start_time = time.time()
        
        if not QISKIT_AVAILABLE:
            # CPU fallback
            return self._cpu_interference(a, b)
        
        a_id = self.get_field_id(a)
        b_id = self.get_field_id(b)
        
        a_circuit = self._array_to_circuit(a, a_id)
        b_circuit = self._array_to_circuit(b, b_id)
        
        if a_circuit is None or b_circuit is None:
            return self._cpu_interference(a, b)
        
        try:
            # SWAP test voor overlap
            overlap = self._swap_test_corrected(a_circuit, b_circuit)
            
            self.metrics['interference_time'] = time.time() - start_time
            self.logger.debug(f"Quantum overlap: {overlap:.3f}")
            return float(overlap)
            
        except Exception as e:
            self.logger.error(f"Swap test mislukt: {e}")
            return self._cpu_interference(a, b)
    
    def _swap_test_corrected(self, circuit_a: QuantumCircuit, circuit_b: QuantumCircuit) -> float:
        """
        GECORRIGEERDE SWAP-test met correcte p0 berekening.
        """
        n_qubits_a = circuit_a.num_qubits
        n_qubits_b = circuit_b.num_qubits
        total_qubits = n_qubits_a + n_qubits_b + 1  # +1 voor anker
        
        qr = QuantumRegister(total_qubits, 'q')
        test = QuantumCircuit(qr)
        
        # Voeg beide velden toe
        test.append(circuit_a, range(1, n_qubits_a + 1))
        test.append(circuit_b, range(n_qubits_a + 1, total_qubits))
        
        # SWAP test voor overlap
        test.h(0)  # Anker qubit in superpositie
        
        # Gecontroleerde SWAPs
        for i in range(min(n_qubits_a, n_qubits_b)):
            test.cswap(0, i+1, i+1+n_qubits_a)
        
        test.h(0)
        test.measure_all()
        
        # Voer uit
        shots = self.config.get('shots', 1000)
        job = execute(test, self.simulator, shots=shots)
        result = job.result().get_counts()
        
        # p0 = kans dat anker-qubit (rechts in bitstring) |0⟩ is
        # In Qiskit little-endian: qubit 0 is meest rechtse karakter
        shots_total = sum(result.values())
        p0 = sum(count for bitstring, count in result.items() if bitstring[-1] == '0') / shots_total
        
        # Overlap = 2*p0 - 1
        overlap = max(0.0, min(1.0, 2 * p0 - 1))
        
        self.logger.debug(f"SWAP test: p0={p0:.3f}, overlap={overlap:.3f}")
        
        return overlap
    
    def _cpu_interference(self, a: np.ndarray, b: np.ndarray) -> float:
        """CPU fallback voor interferentie."""
        a_norm = a / np.linalg.norm(a)
        b_norm = b / np.linalg.norm(b)
        return float(np.dot(a_norm, b_norm))
    
    @handle_hardware_errors(default_return=[])
    def find_stable_patterns(self, fields: List[np.ndarray],
                            threshold: float) -> List[Dict]:
        """
        Vind stabiele patronen via quantum parallellisme.
        
        Args:
            fields: Lijst van numpy arrays
            threshold: Minimum sterkte voor rapportage
            
        Returns:
            Lijst van dicts met 'i', 'j', 'sterkte', 'veld'
        """
        n = len(fields)
        if n < 2:
            return []
        
        if not QISKIT_AVAILABLE or n > 10:  # Bij veel velden, gebruik CPU
            return self._cpu_find_patterns(fields, threshold)
        
        results = []
        
        # Gebruik quantum voor overlap metingen
        for i in range(n):
            for j in range(i+1, n):
                sterkte = self.compute_interference(fields[i], fields[j])
                
                if sterkte >= threshold:
                    field_id_i = self.get_field_id(fields[i])
                    field_id_j = self.get_field_id(fields[j])
                    
                    results.append({
                        'i': i,
                        'j': j,
                        'field_id_i': field_id_i,
                        'field_id_j': field_id_j,
                        'sterkte': sterkte,
                        'veld': self._normalize(fields[i] + fields[j])
                    })
        
        return sorted(results, key=lambda x: x['sterkte'], reverse=True)
    
    def _cpu_find_patterns(self, fields: List[np.ndarray],
                          threshold: float) -> List[Dict]:
        """CPU implementatie voor pattern detection."""
        n = len(fields)
        results = []
        
        for i in range(n):
            for j in range(i+1, n):
                sterkte = float(np.dot(fields[i], fields[j]))
                if sterkte > threshold:
                    field_id_i = self.get_field_id(fields[i])
                    field_id_j = self.get_field_id(fields[j])
                    
                    results.append({
                        'i': i,
                        'j': j,
                        'field_id_i': field_id_i,
                        'field_id_j': field_id_j,
                        'sterkte': sterkte,
                        'veld': self._normalize(fields[i] + fields[j])
                    })
        
        return sorted(results, key=lambda x: x['sterkte'], reverse=True)
    
    # ====================================================================
    # COHERENTIE METING
    # ====================================================================
    
    @handle_hardware_errors(default_return=0.5)
    def measure_coherence(self, fields: List[np.ndarray]) -> float:
        """
        Meet coherentie via quantum tomography.
        Alle mogelijke coherenties bestaan tegelijk!
        
        Args:
            fields: Lijst van numpy arrays
            
        Returns:
            Coherentie score (0-1)
        """
        if len(fields) < 2:
            return 1.0
        
        if not QISKIT_AVAILABLE:
            return self._cpu_measure_coherence(fields)
        
        # Bereken gemiddelde overlap tussen alle paren
        n = len(fields)
        total_overlap = 0.0
        n_pairs = 0
        
        # Neem een steekproef van paren (te veel paren is duur)
        max_pairs = min(20, n * (n-1) // 2)
        sampled_pairs = set()
        
        for _ in range(max_pairs):
            i, j = random.sample(range(n), 2)
            if (i, j) in sampled_pairs or (j, i) in sampled_pairs:
                continue
            sampled_pairs.add((i, j))
            
            overlap = self.compute_interference(fields[i], fields[j])
            total_overlap += overlap
            n_pairs += 1
        
        if n_pairs == 0:
            return 0.5
        
        coherence = total_overlap / n_pairs
        
        # Valideer met CPU berekening (alleen in debug)
        if self.logger.isEnabledFor(logging.DEBUG):
            cpu_coherence = self._cpu_measure_coherence(fields)
            self.logger.debug(f"Coherentie: quantum={coherence:.3f}, CPU={cpu_coherence:.3f}")
        
        return coherence
    
    def _cpu_measure_coherence(self, fields: List[np.ndarray]) -> float:
        """CPU implementatie voor coherentie meting."""
        n = len(fields)
        matrix = np.array([f.flatten()[:20] for f in fields])
        gram = matrix @ matrix.T
        coherence = (np.sum(gram) - n) / (n * (n - 1)) if n > 1 else 1.0
        return float(coherence)
    
    # ====================================================================
    # HULP FUNCTIES
    # ====================================================================
    
    def _normalize(self, field: np.ndarray) -> np.ndarray:
        """Normaliseer een veld."""
        norm = np.linalg.norm(field)
        if norm > 0:
            return field / norm
        return field
    
    def get_info(self) -> str:
        """Haal informatie op over de quantum backend."""
        info = f"Quantum ({self.n_qubits} qubits)"
        if self.is_available:
            info += f" - {self.metrics['total_circuits']} circuits"
            info += f", {self.metrics['total_executions']} execs"
            info += f", {self.metrics['total_swap_tests']} swaps"
            info += f", {self.metrics['total_qubit_seconds']:.1f} qubit-s"
            info += f", cache: {self.metrics['cache_hits']}/{self.metrics['cache_misses']}"
        else:
            info += " - NIET BESCHIKBAAR (simulatie)"
        return info
    
    def get_metrics(self) -> Dict[str, Any]:
        """Haal performance metrics op."""
        return {
            **self.metrics,
            'active_circuits': len(self.circuits),
            'cached_fields': len(self.field_data),
            'config': {k: v for k, v in self.config.items() 
                      if k not in ['initial_layout']},
            'qiskit_available': QISKIT_AVAILABLE,
            'n_qubits': self.n_qubits,
            'total_states': 2 ** self.n_qubits,
            'cache_hit_ratio': self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'] + 1),
            'next_id': self._next_id
        }
    
    # ====================================================================
    # RESOURCE MANAGEMENT
    # ====================================================================
    
    @handle_hardware_errors(default_return=False)
    def cleanup(self):
        """Opruimen van quantum resources."""
        self.logger.info("🧹 Quantum resources opruimen...")
        
        n_circuits = len(self.circuits)
        n_fields = len(self.field_data)
        
        self.circuits.clear()
        self.field_data.clear()
        self.circuit_counters.clear()
        self.circuit_hash.clear()
        
        self.logger.info(f"🧹 {n_circuits} circuits en {n_fields} fields opgeruimd")
        self.logger.info(f"🧹 {len(self.circuit_hash)} hashes opgeruimd")
        
        # Reset metrics
        self.metrics = {
            'total_circuits': 0,
            'total_executions': 0,
            'total_swap_tests': 0,
            'total_timeouts': 0,
            'avg_execution_time': 0.0,
            'min_execution_time': float('inf'),
            'max_execution_time': 0.0,
            'total_qubit_seconds': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self._next_id = 0


# ====================================================================
# DEMONSTRATIE
# ====================================================================

def demo():
    """Demonstreer quantum backend functionaliteit."""
    print("\n" + "="*80)
    print("🌀 QUANTUM BACKEND DEMONSTRATIE")
    print("="*80)
    print("✅ SWAP-test p0 key gecorrigeerd")
    print("✅ Partiële trace via numpy reshape")
    print("✅ Veld-ID systeem voor efficiëntie")
    print("="*80)
    
    # Creëer backend
    backend = QuantumBackend()
    print(f"\n📋 Backend status:")
    print(f"   Beschikbaar: {backend.is_available}")
    
    # Initialiseer
    if backend.initialize({'n_qubits': 10, 'shots': 500}):
        print(f"   Geïnitialiseerd: ✓")
        
        # Test field creatie met ID
        field = backend.create_continuous_field(10)
        field_id = backend.get_field_id(field)
        print(f"\n📋 Test veld:")
        print(f"   ID: {field_id}")
        print(f"   Shape: {field.shape}")
        print(f"   Norm: {np.linalg.norm(field):.3f}")
        print(f"   Eerste 5: {field[:5]}")
        
        # Test SWAP-test correctie
        print(f"\n📋 SWAP-test test:")
        field2 = backend.create_continuous_field(10)
        interference = backend.compute_interference(field, field2)
        print(f"   Zelf-interferentie: {interference:.3f}")
        
        # Test cache efficiëntie
        print(f"\n📋 Cache test:")
        for _ in range(10):
            backend.get_field_id(field)  # Zou cache hits moeten zijn
        metrics = backend.get_metrics()
        print(f"   Cache hits: {metrics['cache_hits']}")
        print(f"   Cache misses: {metrics['cache_misses']}")
        print(f"   Hit ratio: {metrics['cache_hit_ratio']:.1%}")
        
        # Test coherentie
        fields = [backend.create_continuous_field(10) for _ in range(5)]
        coherence = backend.measure_coherence(fields)
        print(f"\n📋 Coherentie test:")
        print(f"   Coherentie (5 velden): {coherence:.3f}")
        
        # Test pattern detection
        patterns = backend.find_stable_patterns(fields, threshold=0.5)
        print(f"\n📋 Pattern detection:")
        print(f"   {len(patterns)} stabiele patronen gevonden")
        for i, p in enumerate(patterns[:3]):  # Top 3
            field_id_i = p.get('field_id_i', '?')
            field_id_j = p.get('field_id_j', '?')
            print(f"   {i+1}. {p['i']}({field_id_i})↔{p['j']}({field_id_j}): {p['sterkte']:.3f}")
        
        # Toon metrics
        print(f"\n📊 Metrics:")
        for key, value in backend.get_metrics().items():
            if key not in ['config', 'field_data', 'circuits']:
                if isinstance(value, float):
                    print(f"   {key}: {value:.3f}")
                else:
                    print(f"   {key}: {value}")
        
        # Toon info
        print(f"\nℹ️  Info: {backend.get_info()}")
        
        # Cleanup
        backend.cleanup()
        print(f"\n✅ Cleanup voltooid")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    demo()