"""
QUANTUM VQE - Variational Quantum Eigensolver voor Ontologieën
================================================================================
Gebruikt Variational Quantum Eigensolver (VQE) om de 'grondtoestand' van nieuwe
ontologieën te vinden. Hoe lager de energie, hoe stabieler de fundamentele waarheid.

Theoretische basis:
- VQE hybride quantum-klassiek algoritme
- Ontologie → Hamiltoniaan mapping
- Energie-minimalisatie voor stabiliteit
- Quantum advantage voor complexe ontologieën

V13 OPTIONELE UITBREIDINGEN:
- Meerdere ansatz types (Ry, RyRz, PauliTwoDesign, etc.)
- Verschillende optimizers (COBYLA, SPSA, Adam, etc.)
- Error mitigation technieken
- Noise modeling voor realistische hardware
- Parallelle VQE runs
- Resultaat caching
- Visualisatie van energielandschap
"""

import numpy as np
import asyncio
import logging
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)

# ====================================================================
# OPTIONELE QUANTUM IMPORTS
# ====================================================================

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer
    from qiskit.providers.aer import QasmSimulator, StatevectorSimulator
    from qiskit.opflow import I, Z, X, Y, PauliSumOp, PauliOp, ListOp
    from qiskit.opflow.primitive_ops import PauliSumOp
    from qiskit.utils import algorithm_globals
    from qiskit.algorithms import VQE
    from qiskit.algorithms.optimizers import (
        COBYLA, SPSA, ADAM, NFT, L_BFGS_B, P_BFGS, SLSQP
    )
    from qiskit.circuit.library import (
        TwoLocal, RealAmplitudes, EfficientSU2, 
        PauliTwoDesign, NLocal, ExcitationPreserving
    )
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.providers.aer.noise import NoiseModel
    from qiskit.providers.aer.noise.errors import pauli_error, depolarizing_error
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    logger.warning("⚠️ Qiskit niet beschikbaar - quantum VQE zal fallback gebruiken")

# Optionele visualisatie
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Optionele parallelle verwerking
try:
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

# Optionele caching
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class AnsatzType(Enum):
    """Type van quantum ansatz circuit."""
    TWOLOCAL = "twolocal"               # TwoLocal met ry en cz
    REAL_AMPLITUDES = "real_amplitudes" # RealAmplitudes
    EFFICIENT_SU2 = "efficient_su2"      # EfficientSU2
    PAULI_TWO_DESIGN = "pauli_two_design" # PauliTwoDesign
    EXCITATION_PRESERVING = "excitation"  # ExcitationPreserving
    CUSTOM = "custom"                     # Custom circuit


class OptimizerType(Enum):
    """Type van klassieke optimizer."""
    COBYLA = "cobyla"      # Constrained Optimization BY Linear Approximation
    SPSA = "spsa"          # Simultaneous Perturbation Stochastic Approximation
    ADAM = "adam"          # Adaptive Moment Estimation
    L_BFGS_B = "l_bfgs_b"  # Limited-memory BFGS with bounds
    SLSQP = "slsqp"        # Sequential Least Squares Programming
    NFT = "nft"            # Nakanishi-Fujii-Todo


class NoiseModelType(Enum):
    """Type van ruismodel voor simulatie."""
    NONE = "none"                    # Geen ruis
    DEPOLARIZING = "depolarizing"    # Depolarizing noise
    BITFLIP = "bitflip"              # Bit-flip noise
    THERMAL = "thermal"              # Thermische ruis
    REALISTIC = "realistic"          # Realistisch (T1/T2)


@dataclass
class VQEResult:
    """Resultaat van een VQE berekening."""
    id: str
    timestamp: float
    ontology_id: str
    energy: float
    stability: float
    parameters: List[float]
    circuit_depth: int
    num_qubits: int
    iterations: int
    optimizer: str
    ansatz: str
    success: bool
    error_message: Optional[str] = None
    convergence_history: List[float] = field(default_factory=list)
    execution_time: float = 0.0


class QuantumOntologyOptimizer:
    """
    Vind de meest stabiele 'grondtoestand' van een nieuwe ontologie.
    
    Core functionaliteit:
    - Converteer ontologie naar Hamiltoniaan
    - Voer VQE uit om energie te minimaliseren
    - Converteer energie naar stabiliteitsscore
    
    Optionele uitbreidingen:
    - Meerdere ansatz types
    - Verschillende optimizers
    - Error mitigation
    - Noise modeling
    - Parallelle VQE runs
    - Resultaat caching
    - Visualisatie
    """
    
    def __init__(self, 
                 quantum_backend=None,
                 n_qubits: int = 10,
                 ansatz_type: AnsatzType = AnsatzType.TWOLOCAL,
                 optimizer_type: OptimizerType = OptimizerType.COBYLA,
                 max_iterations: int = 100,
                 shots: int = 1000,
                 use_noise_model: bool = False,
                 noise_model_type: NoiseModelType = NoiseModelType.NONE,
                 error_mitigation: bool = True,
                 parallel_runs: int = 1,
                 cache_results: bool = True,
                 cache_ttl: int = 3600,
                 visualization: bool = False,
                 save_convergence: bool = True,
                 config_path: Optional[str] = None):
        """
        Initialiseer quantum ontologie optimizer.
        
        Args:
            quantum_backend: Quantum backend instance
            n_qubits: Maximum aantal qubits
            ansatz_type: Type ansatz circuit
            optimizer_type: Type optimizer
            max_iterations: Maximum iteraties
            shots: Aantal shots voor metingen
            use_noise_model: Gebruik ruismodel
            noise_model_type: Type ruismodel
            error_mitigation: Pas error mitigation toe
            parallel_runs: Aantal parallelle runs
            cache_results: Cache resultaten
            cache_ttl: Cache TTL in seconden
            visualization: Genereer visualisaties
            save_convergence: Bewaar convergentiegeschiedenis
            config_path: Pad naar configuratie bestand
        """
        self.qb = quantum_backend
        self.n_qubits = n_qubits
        self.ansatz_type = ansatz_type
        self.optimizer_type = optimizer_type
        self.max_iterations = max_iterations
        self.shots = shots
        self.use_noise_model = use_noise_model
        self.noise_model_type = noise_model_type
        self.error_mitigation = error_mitigation
        self.parallel_runs = parallel_runs
        self.cache_results = cache_results
        self.cache_ttl = cache_ttl
        self.visualization = visualization and VISUALIZATION_AVAILABLE
        self.save_convergence = save_convergence
        
        # Resultaten
        self.results: List[VQEResult] = []
        self.best_result: Optional[VQEResult] = None
        
        # Cache
        self.cache: Dict[str, Tuple[VQEResult, float]] = {}
        if REDIS_AVAILABLE and cache_results:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                logger.info("✅ Redis cache geactiveerd")
            except:
                self.redis_client = None
                logger.warning("⚠️ Redis niet beschikbaar - gebruik memory cache")
        else:
            self.redis_client = None
        
        # Stats
        self.stats = {
            'vqe_runs': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_execution_time': 0.0,
            'avg_energy': 0.0,
            'avg_stability': 0.0,
            'start_time': time.time()
        }
        
        # Laad configuratie
        if config_path:
            self._load_config(config_path)
        
        # Setup noise model
        self.noise_model = self._create_noise_model() if use_noise_model else None
        
        logger.info("="*80)
        logger.info("⚛️ QUANTUM VQE V13 GEÏNITIALISEERD")
        logger.info("="*80)
        logger.info(f"Qubits: {n_qubits}")
        logger.info(f"Ansatz: {ansatz_type.value}")
        logger.info(f"Optimizer: {optimizer_type.value}")
        logger.info(f"Max iteraties: {max_iterations}")
        logger.info(f"Noise model: {noise_model_type.value if use_noise_model else 'none'}")
        logger.info(f"Error mitigation: {'✅' if error_mitigation else '❌'}")
        logger.info(f"Parallel runs: {parallel_runs}")
        logger.info(f"Caching: {'✅' if cache_results else '❌'}")
        logger.info(f"Visualization: {'✅' if self.visualization else '❌'}")
        logger.info(f"Qiskit beschikbaar: {'✅' if QISKIT_AVAILABLE else '❌'}")
        logger.info("="*80)
    
    # ====================================================================
    # KERN FUNCTIONALITEIT
    # ====================================================================
    
    async def find_ground_state(self, 
                                ontology: Dict[str, Any],
                                ontology_id: Optional[str] = None,
                                force_rerun: bool = False) -> VQEResult:
        """
        Vind de grondtoestand van een ontologie via VQE.
        
        Args:
            ontology: Ontologie dictionary met entities en relations
            ontology_id: Optionele ID (anders hash van ontologie)
            force_rerun: Negeer cache en forceer herberekening
        
        Returns:
            VQE resultaat met energie en stabiliteit
        """
        self.stats['vqe_runs'] += 1
        start_time = time.time()
        
        # Genereer ID indien niet gegeven
        if ontology_id is None:
            ontology_id = self._hash_ontology(ontology)
        
        # Check cache
        if self.cache_results and not force_rerun:
            cached = self._get_cached(ontology_id)
            if cached:
                self.stats['cache_hits'] += 1
                logger.debug(f"⚡ Cache hit voor ontologie {ontology_id[:8]}")
                return cached
        
        self.stats['cache_misses'] += 1
        
        # Fallback als Qiskit niet beschikbaar is
        if not QISKIT_AVAILABLE or not self.qb or not self.qb.is_available:
            return self._fallback_result(ontology, ontology_id)
        
        try:
            # Converteer ontologie naar Hamiltoniaan
            hamiltonian = await self._ontology_to_hamiltonian(ontology)
            
            # Maak ansatz circuit
            ansatz = self._create_ansatz(hamiltonian.num_qubits)
            
            # Configureer optimizer
            optimizer = self._create_optimizer()
            
            # Configureer quantum instance
            quantum_instance = self._create_quantum_instance()
            
            # Parallelle runs indien gewenst
            if self.parallel_runs > 1 and PARALLEL_AVAILABLE:
                results = await self._parallel_vqe_runs(
                    hamiltonian, ansatz, optimizer, quantum_instance
                )
                best_result = min(results, key=lambda x: x['energy'])
                result = self._process_vqe_result(
                    best_result, ontology_id, ansatz, optimizer
                )
            else:
                # Enkele VQE run
                vqe = VQE(
                    ansatz=ansatz,
                    optimizer=optimizer,
                    quantum_instance=quantum_instance,
                    callback=self._vqe_callback if self.save_convergence else None
                )
                
                vqe_result = vqe.compute_minimum_eigenvalue(hamiltonian)
                
                result = self._process_vqe_result(
                    vqe_result, ontology_id, ansatz, optimizer
                )
            
            result.execution_time = time.time() - start_time
            
            # Sla op in cache
            if self.cache_results:
                self._cache_result(ontology_id, result)
            
            # Update stats
            self.results.append(result)
            self._update_stats(result)
            
            # Update beste resultaat
            if self.best_result is None or result.energy < self.best_result.energy:
                self.best_result = result
                logger.info(f"🏆 Nieuwe beste energie: {result.energy:.6f}")
            
            # Visualiseer indien gewenst
            if self.visualization and self.save_convergence:
                self._visualize_convergence(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ VQE fout: {e}")
            return self._fallback_result(ontology, ontology_id, error=str(e))
    
    async def _ontology_to_hamiltonian(self, ontology: Dict) -> PauliSumOp:
        """
        Converteer ontologie naar Ising Hamiltoniaan.
        
        Args:
            ontology: Ontologie met entities en relations
        
        Returns:
            PauliSumOp representatie van Hamiltoniaan
        """
        entities = list(ontology.get('entities', []))
        relations = ontology.get('relations', {})
        
        n = len(entities)
        if n > self.n_qubits:
            logger.warning(f"⚠️ Te veel entities ({n}), truncate to {self.n_qubits}")
            n = self.n_qubits
        
        # Bouw Hamiltoniaan: H = -∑ J_ij Z_i Z_j - ∑ h_i Z_i
        # Negatief teken omdat we energie willen minimaliseren voor stabiele toestanden
        
        pauli_list = []
        
        # Entity indices voor snelle lookup
        entity_indices = {e: i for i, e in enumerate(entities[:n])}
        
        # Voeg ZZ interacties toe voor relaties
        for (e1, e2), strength in relations.items():
            if e1 in entity_indices and e2 in entity_indices:
                i, j = entity_indices[e1], entity_indices[e2]
                
                # Maak ZZ term: -J_ij * Z_i * Z_j
                zz_term = self._pauli_zz(i, j, n)
                pauli_list.append((-strength, zz_term))
                
                logger.debug(f"   ZZ term: {e1}-{e2}: {strength}")
        
        # Voeg Z termen toe voor entity weights (indien aanwezig)
        weights = ontology.get('weights', {})
        for entity, weight in weights.items():
            if entity in entity_indices:
                i = entity_indices[entity]
                
                # Maak Z term: -h_i * Z_i
                z_term = self._pauli_z(i, n)
                pauli_list.append((-weight, z_term))
        
        # Als er geen termen zijn, voeg een kleine identity toe
        if not pauli_list:
            logger.debug("   Geen termen, voeg identity toe")
            identity = self._pauli_identity(n)
            pauli_list.append((0.0, identity))
        
        # Converteer naar PauliSumOp
        if QISKIT_AVAILABLE:
            # Bouw SparsePauliOp
            paulis = []
            coeffs = []
            
            for coeff, pauli in pauli_list:
                if abs(coeff) > 1e-10:  # Negeer verwaarloosbare termen
                    paulis.append(pauli)
                    coeffs.append(coeff)
            
            if paulis:
                # Combineer alle Pauli strings
                sparse_pauli = SparsePauliOp(paulis[0], coeffs=[coeffs[0]])
                for i in range(1, len(paulis)):
                    sparse_pauli += SparsePauliOp(paulis[i], coeffs=[coeffs[i]])
                
                return PauliSumOp(sparse_pauli)
            else:
                # Return null operator
                return PauliSumOp(SparsePauliOp.from_list([('I'*n, 0.0)]))
        else:
            # Fallback voor zonder Qiskit
            return None
    
    def _pauli_zz(self, i: int, j: int, n: int) -> str:
        """Genereer Pauli string voor Z_i Z_j."""
        pauli = ['I'] * n
        pauli[i] = 'Z'
        pauli[j] = 'Z'
        return ''.join(pauli)
    
    def _pauli_z(self, i: int, n: int) -> str:
        """Genereer Pauli string voor Z_i."""
        pauli = ['I'] * n
        pauli[i] = 'Z'
        return ''.join(pauli)
    
    def _pauli_identity(self, n: int) -> str:
        """Genereer identity Pauli string."""
        return 'I' * n
    
    def _create_ansatz(self, num_qubits: int) -> QuantumCircuit:
        """Creëer ansatz circuit van gekozen type."""
        if not QISKIT_AVAILABLE:
            return None
        
        if self.ansatz_type == AnsatzType.TWOLOCAL:
            # TwoLocal met ry en cz
            return TwoLocal(
                num_qubits,
                ['ry', 'rz'],
                'cz',
                reps=3,
                entanglement='full',
                skip_unentangled_qubits=False
            )
        
        elif self.ansatz_type == AnsatzType.REAL_AMPLITUDES:
            # RealAmplitudes
            return RealAmplitudes(
                num_qubits,
                reps=3,
                entanglement='full'
            )
        
        elif self.ansatz_type == AnsatzType.EFFICIENT_SU2:
            # EfficientSU2
            return EfficientSU2(
                num_qubits,
                su2_gates=['ry', 'rz'],
                entanglement='full',
                reps=3
            )
        
        elif self.ansatz_type == AnsatzType.PAULI_TWO_DESIGN:
            # PauliTwoDesign
            return PauliTwoDesign(
                num_qubits,
                reps=3,
                seed=42
            )
        
        elif self.ansatz_type == AnsatzType.EXCITATION_PRESERVING:
            # ExcitationPreserving
            return ExcitationPreserving(
                num_qubits,
                reps=3,
                entanglement='full'
            )
        
        else:
            # Default TwoLocal
            return TwoLocal(num_qubits, 'ry', 'cz', reps=3)
    
    def _create_optimizer(self):
        """Creëer optimizer van gekozen type."""
        if not QISKIT_AVAILABLE:
            return None
        
        if self.optimizer_type == OptimizerType.COBYLA:
            return COBYLA(maxiter=self.max_iterations, tol=1e-6)
        
        elif self.optimizer_type == OptimizerType.SPSA:
            return SPSA(maxiter=self.max_iterations, 
                        learning_rate=0.01,
                        perturbation=0.01)
        
        elif self.optimizer_type == OptimizerType.ADAM:
            return ADAM(maxiter=self.max_iterations, 
                       lr=0.01,
                       beta_1=0.9,
                       beta_2=0.999,
                       noise_factor=1e-8)
        
        elif self.optimizer_type == OptimizerType.L_BFGS_B:
            return L_BFGS_B(maxiter=self.max_iterations, 
                           ftol=1e-6,
                           gtol=1e-5)
        
        elif self.optimizer_type == OptimizerType.SLSQP:
            return SLSQP(maxiter=self.max_iterations, 
                        ftol=1e-6)
        
        elif self.optimizer_type == OptimizerType.NFT:
            return NFT(maxiter=self.max_iterations)
        
        else:
            return COBYLA(maxiter=self.max_iterations)
    
    def _create_quantum_instance(self):
        """Creëer quantum instance met optionele noise modeling."""
        if not QISKIT_AVAILABLE:
            return None
        
        from qiskit.utils import QuantumInstance
        
        backend = Aer.get_backend('qasm_simulator')
        
        quantum_instance = QuantumInstance(
            backend=backend,
            shots=self.shots,
            noise_model=self.noise_model,
            measurement_error_mitigation_cls=self._get_error_mitigation() if self.error_mitigation else None,
            cals_matrix_refresh_period=30,
            seed_simulator=42,
            seed_transpiler=42
        )
        
        return quantum_instance
    
    def _create_noise_model(self) -> Optional[NoiseModel]:
        """Creëer ruismodel voor realistische simulatie."""
        if not QISKIT_AVAILABLE:
            return None
        
        noise_model = NoiseModel()
        
        if self.noise_model_type == NoiseModelType.DEPOLARIZING:
            # Depolarizing noise
            error = depolarizing_error(0.01, 1)
            noise_model.add_all_qubit_quantum_error(error, ['u1', 'u2', 'u3'])
        
        elif self.noise_model_type == NoiseModelType.BITFLIP:
            # Bit-flip noise
            error = pauli_error([('X', 0.01), ('I', 0.99)])
            noise_model.add_all_qubit_quantum_error(error, ['u1', 'u2', 'u3'])
        
        elif self.noise_model_type == NoiseModelType.THERMAL:
            # Thermische ruis (T1/T2)
            # Simuleer T1 = 50μs, T2 = 70μs, gate time = 100ns
            from qiskit.providers.aer.noise import thermal_relaxation_error
            
            t1 = 50e-6
            t2 = 70e-6
            gate_time = 0.1e-6
            
            error1 = thermal_relaxation_error(t1, t2, gate_time)
            error2 = thermal_relaxation_error(t1, t2, gate_time).tensordot(
                thermal_relaxation_error(t1, t2, gate_time)
            )
            
            noise_model.add_all_qubit_quantum_error(error1, ['u1', 'u2'])
            noise_model.add_all_qubit_quantum_error(error2, ['cx'])
        
        elif self.noise_model_type == NoiseModelType.REALISTIC:
            # Realistisch model gebaseerd op IBMQ achtergrond
            # Depolarizing + thermal noise
            dep_error = depolarizing_error(0.001, 1)
            noise_model.add_all_qubit_quantum_error(dep_error, ['u1', 'u2', 'u3'])
            
            # Readout error
            from qiskit.providers.aer.noise import ReadoutError
            readout_error = ReadoutError([[0.98, 0.02], [0.03, 0.97]])
            noise_model.add_all_qubit_readout_error(readout_error)
        
        return noise_model
    
    def _get_error_mitigation(self):
        """Haal error mitigation techniek op."""
        if not QISKIT_AVAILABLE:
            return None
        
        from qiskit.utils.mitigation import complete_meas_cal
        
        return complete_meas_cal.CompleteMeasFitter
    
    def _vqe_callback(self, eval_count, parameters, mean, std):
        """Callback voor VQE om convergentie bij te houden."""
        if hasattr(self, '_current_convergence'):
            self._current_convergence.append(mean)
    
    def _process_vqe_result(self, 
                           vqe_result, 
                           ontology_id: str,
                           ansatz: QuantumCircuit,
                           optimizer) -> VQEResult:
        """Verwerk VQE resultaat naar VQEResult object."""
        energy = float(vqe_result.eigenvalue.real)
        
        # Converteer energie naar stabiliteitsscore (0-1)
        # Lagere energie = hogere stabiliteit
        stability = 1.0 / (1.0 + abs(energy))
        
        # Haal parameters op
        if hasattr(vqe_result, 'optimal_point'):
            parameters = vqe_result.optimal_point.tolist() if vqe_result.optimal_point is not None else []
        else:
            parameters = []
        
        result = VQEResult(
            id=hashlib.md5(f"{ontology_id}{time.time()}".encode()).hexdigest()[:12],
            timestamp=time.time(),
            ontology_id=ontology_id,
            energy=energy,
            stability=stability,
            parameters=parameters,
            circuit_depth=ansatz.depth() if ansatz else 0,
            num_qubits=ansatz.num_qubits if ansatz else 0,
            iterations=getattr(vqe_result, 'optimizer_evals', 0),
            optimizer=self.optimizer_type.value,
            ansatz=self.ansatz_type.value,
            success=True,
            convergence_history=getattr(self, '_current_convergence', []),
            execution_time=0.0  # Wordt later gezet
        )
        
        # Reset convergence history
        if hasattr(self, '_current_convergence'):
            delattr(self, '_current_convergence')
        
        return result
    
    async def _parallel_vqe_runs(self, hamiltonian, ansatz, optimizer, quantum_instance):
        """Voer meerdere VQE runs parallel uit."""
        if not PARALLEL_AVAILABLE:
            # Fallback naar serieel
            results = []
            for _ in range(self.parallel_runs):
                vqe = VQE(ansatz=ansatz, optimizer=optimizer, 
                         quantum_instance=quantum_instance)
                result = vqe.compute_minimum_eigenvalue(hamiltonian)
                results.append({
                    'energy': result.eigenvalue.real,
                    'result': result
                })
            return results
        
        # Parallelle uitvoering
        with ThreadPoolExecutor(max_workers=self.parallel_runs) as executor:
            futures = []
            for _ in range(self.parallel_runs):
                future = executor.submit(
                    self._run_single_vqe,
                    hamiltonian, ansatz, optimizer, quantum_instance
                )
                futures.append(future)
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minuten timeout
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel VQE run mislukt: {e}")
        
        return results
    
    def _run_single_vqe(self, hamiltonian, ansatz, optimizer, quantum_instance):
        """Voer één VQE run uit (voor parallelle verwerking)."""
        vqe = VQE(
            ansatz=ansatz,
            optimizer=optimizer,
            quantum_instance=quantum_instance
        )
        result = vqe.compute_minimum_eigenvalue(hamiltonian)
        return {
            'energy': result.eigenvalue.real,
            'result': result
        }
    
    def _fallback_result(self, ontology: Dict, ontology_id: str, error: str = "") -> VQEResult:
        """Fallback als quantum niet beschikbaar is."""
        # Simpele klassieke schatting op basis van relation strength
        relations = ontology.get('relations', {})
        if relations:
            avg_strength = np.mean(list(relations.values()))
            energy = -avg_strength  # Sterkere relaties = lagere energie
        else:
            energy = 0.0
        
        stability = 1.0 / (1.0 + abs(energy))
        
        result = VQEResult(
            id=hashlib.md5(f"{ontology_id}{time.time()}".encode()).hexdigest()[:12],
            timestamp=time.time(),
            ontology_id=ontology_id,
            energy=energy,
            stability=stability,
            parameters=[],
            circuit_depth=0,
            num_qubits=0,
            iterations=0,
            optimizer=self.optimizer_type.value,
            ansatz=self.ansatz_type.value,
            success=False,
            error_message=error or "Qiskit niet beschikbaar, gebruikte klassieke fallback"
        )
        
        self.results.append(result)
        return result
    
    # ====================================================================
    # OPTIONEEL: CACHING
    # ====================================================================
    
    def _hash_ontology(self, ontology: Dict) -> str:
        """Genereer unieke hash voor ontologie."""
        # Stabiliseer representatie voor consistente hashing
        import json
        ontology_str = json.dumps(ontology, sort_keys=True)
        return hashlib.sha256(ontology_str.encode()).hexdigest()[:16]
    
    def _get_cached(self, ontology_id: str) -> Optional[VQEResult]:
        """Haal resultaat uit cache."""
        # Check Redis cache eerst
        if self.redis_client:
            try:
                data = self.redis_client.get(f"vqe:{ontology_id}")
                if data:
                    result = pickle.loads(data)
                    if time.time() - result.timestamp < self.cache_ttl:
                        logger.debug(f"⚡ Redis cache hit voor {ontology_id[:8]}")
                        return result
            except Exception as e:
                logger.debug(f"Redis cache error: {e}")
        
        # Check memory cache
        if ontology_id in self.cache:
            result, expiry = self.cache[ontology_id]
            if time.time() < expiry:
                return result
            else:
                del self.cache[ontology_id]
        
        return None
    
    def _cache_result(self, ontology_id: str, result: VQEResult):
        """Sla resultaat op in cache."""
        expiry = time.time() + self.cache_ttl
        
        # Redis cache
        if self.redis_client:
            try:
                data = pickle.dumps(result)
                self.redis_client.setex(f"vqe:{ontology_id}", self.cache_ttl, data)
                logger.debug(f"💾 Redis cache opgeslagen voor {ontology_id[:8]}")
            except Exception as e:
                logger.debug(f"Redis cache save error: {e}")
        
        # Memory cache
        self.cache[ontology_id] = (result, expiry)
        
        # Beperk memory cache grootte
        if len(self.cache) > 1000:
            # Verwijder oudste
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
    
    def clear_cache(self):
        """Wis alle caches."""
        self.cache.clear()
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except:
                pass
        logger.info("🧹 Cache gewist")
    
    # ====================================================================
    # OPTIONEEL: VISUALISATIE
    # ====================================================================
    
    def _visualize_convergence(self, result: VQEResult):
        """Visualiseer convergentie van VQE run."""
        if not self.visualization or not result.convergence_history:
            return
        
        plt.figure(figsize=(10, 6))
        plt.plot(result.convergence_history, 'b-', linewidth=2)
        plt.xlabel('Iteratie')
        plt.ylabel('Energie')
        plt.title(f'VQE Convergentie - {result.ontology_id[:8]}')
        plt.grid(True, alpha=0.3)
        
        # Markeer minimum
        min_idx = np.argmin(result.convergence_history)
        plt.plot(min_idx, result.convergence_history[min_idx], 'ro', 
                markersize=8, label=f'Minimum: {result.convergence_history[min_idx]:.6f}')
        plt.legend()
        
        # Sla op
        filename = f"vqe_convergence_{result.id}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Convergentieplot opgeslagen: {filename}")
    
    def visualize_energy_landscape(self, ontology_id: str, param1_idx: int = 0, param2_idx: int = 1):
        """
        Visualiseer energielandschap voor een ontologie (2D slice).
        
        Args:
            ontology_id: ID van ontologie
            param1_idx: Index van eerste parameter
            param2_idx: Index van tweede parameter
        """
        if not self.visualization:
            logger.warning("Visualisatie niet beschikbaar")
            return
        
        # Zoek resultaat
        result = None
        for r in self.results:
            if r.ontology_id == ontology_id:
                result = r
                break
        
        if not result or len(result.parameters) <= max(param1_idx, param2_idx):
            logger.warning(f"Onvoldoende parameters voor visualisatie")
            return
        
        # TODO: Implementeer grid search over parameters
        # Dit vereist herhaalde VQE runs met vaste parameters
        
        logger.info("📊 Energy landscape visualisatie (TODO)")
    
    # ====================================================================
    # OPTIONEEL: RESULTAAT ANALYSE
    # ====================================================================
    
    def compare_ontologies(self, ontology_ids: List[str]) -> Dict[str, Any]:
        """Vergelijk meerdere ontologieën op basis van VQE resultaten."""
        results = []
        for oid in ontology_ids:
            for r in self.results:
                if r.ontology_id == oid:
                    results.append(r)
                    break
        
        if not results:
            return {}
        
        # Sorteer op energie (lager = beter)
        sorted_results = sorted(results, key=lambda x: x.energy)
        
        return {
            'best_ontology': sorted_results[0].ontology_id,
            'best_energy': sorted_results[0].energy,
            'best_stability': sorted_results[0].stability,
            'rankings': [
                {
                    'ontology': r.ontology_id[:8],
                    'energy': r.energy,
                    'stability': r.stability,
                    'success': r.success
                }
                for r in sorted_results
            ],
            'energy_range': {
                'min': min(r.energy for r in results),
                'max': max(r.energy for r in results),
                'avg': np.mean([r.energy for r in results])
            }
        }
    
    def analyze_parameter_sensitivity(self, ontology_id: str, n_samples: int = 10):
        """Analyseer gevoeligheid van parameters."""
        # Zoek resultaat
        result = None
        for r in self.results:
            if r.ontology_id == ontology_id and r.success:
                result = r
                break
        
        if not result or not result.parameters:
            return {}
        
        # TODO: Voer lokale sensitiviteitsanalyse uit
        # Dit vereist extra VQE runs met kleine variaties
        
        return {
            'message': 'Sensitivity analysis TODO',
            'n_parameters': len(result.parameters)
        }
    
    # ====================================================================
    # STATISTIEKEN & RAPPORTAGE
    # ====================================================================
    
    def _update_stats(self, result: VQEResult):
        """Update statistieken met nieuw resultaat."""
        n = len(self.results)
        
        # Update gemiddelden (EMA)
        alpha = 0.3
        self.stats['avg_execution_time'] = (
            alpha * result.execution_time + 
            (1 - alpha) * self.stats['avg_execution_time']
        )
        self.stats['avg_energy'] = (
            alpha * result.energy + 
            (1 - alpha) * self.stats['avg_energy']
        )
        self.stats['avg_stability'] = (
            alpha * result.stability + 
            (1 - alpha) * self.stats['avg_stability']
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal uitgebreide statistieken op."""
        successful = [r for r in self.results if r.success]
        
        return {
            **self.stats,
            'total_runs': len(self.results),
            'successful_runs': len(successful),
            'success_rate': len(successful) / len(self.results) if self.results else 0,
            'cache_size': len(self.cache),
            'best_energy': self.best_result.energy if self.best_result else None,
            'best_stability': self.best_result.stability if self.best_result else None,
            'results_by_optimizer': {
                opt: len([r for r in self.results if r.optimizer == opt.value])
                for opt in OptimizerType
            },
            'results_by_ansatz': {
                ans: len([r for r in self.results if r.ansatz == ans.value])
                for ans in AnsatzType
            },
            'uptime': time.time() - self.stats['start_time']
        }
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Haal recente resultaten op."""
        recent = []
        for r in self.results[-limit:]:
            recent.append({
                'id': r.id[:8],
                'ontology': r.ontology_id[:8],
                'energy': r.energy,
                'stability': r.stability,
                'success': r.success,
                'time': r.timestamp,
                'optimizer': r.optimizer,
                'ansatz': r.ansatz,
                'iterations': r.iterations
            })
        
        return recent
    
    def export_results(self, filename: str = "vqe_results.json"):
        """Exporteer alle resultaten."""
        data = {
            'export_time': time.time(),
            'stats': self.get_stats(),
            'results': [
                {
                    'id': r.id,
                    'ontology_id': r.ontology_id,
                    'energy': r.energy,
                    'stability': r.stability,
                    'success': r.success,
                    'error': r.error_message,
                    'timestamp': r.timestamp,
                    'optimizer': r.optimizer,
                    'ansatz': r.ansatz,
                    'num_qubits': r.num_qubits,
                    'circuit_depth': r.circuit_depth,
                    'iterations': r.iterations,
                    'execution_time': r.execution_time
                }
                for r in self.results
            ],
            'best_result': {
                'id': self.best_result.id if self.best_result else None,
                'energy': self.best_result.energy if self.best_result else None,
                'stability': self.best_result.stability if self.best_result else None
            } if self.best_result else None
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"📄 Resultaten geëxporteerd naar {filename}")
        return filename
    
    # ====================================================================
    # CONFIGURATIE
    # ====================================================================
    
    def _load_config(self, config_path: str):
        """Laad configuratie uit JSON/YAML bestand."""
        try:
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            elif config_path.endswith(('.yaml', '.yml')):
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                return
            
            # Update parameters
            vqe_config = config.get('quantum_vqe', {})
            
            if 'n_qubits' in vqe_config:
                self.n_qubits = vqe_config['n_qubits']
            if 'ansatz_type' in vqe_config:
                self.ansatz_type = AnsatzType(vqe_config['ansatz_type'])
            if 'optimizer_type' in vqe_config:
                self.optimizer_type = OptimizerType(vqe_config['optimizer_type'])
            if 'max_iterations' in vqe_config:
                self.max_iterations = vqe_config['max_iterations']
            if 'shots' in vqe_config:
                self.shots = vqe_config['shots']
            if 'use_noise_model' in vqe_config:
                self.use_noise_model = vqe_config['use_noise_model']
            if 'noise_model_type' in vqe_config:
                self.noise_model_type = NoiseModelType(vqe_config['noise_model_type'])
            if 'error_mitigation' in vqe_config:
                self.error_mitigation = vqe_config['error_mitigation']
            if 'parallel_runs' in vqe_config:
                self.parallel_runs = vqe_config['parallel_runs']
            if 'cache_results' in vqe_config:
                self.cache_results = vqe_config['cache_results']
            if 'cache_ttl' in vqe_config:
                self.cache_ttl = vqe_config['cache_ttl']
            if 'visualization' in vqe_config:
                self.visualization = vqe_config['visualization'] and VISUALIZATION_AVAILABLE
            
            logger.info(f"📋 Configuratie geladen uit: {config_path}")
            
        except Exception as e:
            logger.error(f"❌ Configuratie laden mislukt: {e}")
    
    # ====================================================================
    # RESOURCE MANAGEMENT
    # ====================================================================
    
    async def cleanup(self):
        """Ruim resources op."""
        logger.info("🧹 QuantumVQE cleanup...")
        
        # Export laatste resultaten
        self.export_results("vqe_final.json")
        
        # Sluit Redis connectie
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        logger.info("✅ Cleanup voltooid")
    
    def reset(self):
        """Reset alle resultaten (voor testing)."""
        self.results.clear()
        self.best_result = None
        self.cache.clear()
        self.stats = {
            'vqe_runs': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_execution_time': 0.0,
            'avg_energy': 0.0,
            'avg_stability': 0.0,
            'start_time': time.time()
        }
        logger.info("🔄 QuantumVQE gereset")


# ====================================================================
# CONVENIENCE FUNCTIES
# ====================================================================

def create_quantum_vqe(quantum_backend=None, config_path: Optional[str] = None, **kwargs) -> QuantumOntologyOptimizer:
    """
    Maak een QuantumOntologyOptimizer instantie met gegeven configuratie.
    
    Args:
        quantum_backend: Quantum backend instance
        config_path: Optioneel pad naar configuratiebestand
        **kwargs: Overschrijf specifieke parameters
    
    Returns:
        Geïnitialiseerde QuantumOntologyOptimizer
    """
    return QuantumOntologyOptimizer(
        quantum_backend=quantum_backend,
        config_path=config_path,
        **kwargs
    )


# ====================================================================
# DEMONSTRATIE
# ====================================================================

async def demo():
    """Demonstreer Quantum VQE functionaliteit."""
    print("\n" + "="*80)
    print("⚛️ QUANTUM VQE V13 DEMONSTRATIE")
    print("="*80)
    
    # Maak mock quantum backend (indien nodig)
    class MockQuantumBackend:
        def __init__(self):
            self.name = "Quantum"
            self.is_available = QISKIT_AVAILABLE
    
    qb = MockQuantumBackend()
    
    # Maak optimizer met alle opties
    qvqe = QuantumOntologyOptimizer(
        quantum_backend=qb,
        n_qubits=8,
        ansatz_type=AnsatzType.TWOLOCAL,
        optimizer_type=OptimizerType.COBYLA,
        max_iterations=50,
        shots=1000,
        use_noise_model=True,
        noise_model_type=NoiseModelType.DEPOLARIZING,
        error_mitigation=True,
        parallel_runs=2 if PARALLEL_AVAILABLE else 1,
        cache_results=True,
        cache_ttl=3600,
        visualization=VISUALIZATION_AVAILABLE,
        save_convergence=True
    )
    
    print("\n📋 Test 1: Converteer ontologie naar Hamiltoniaan")
    
    # Test ontologie
    test_ontology = {
        'entities': ['concept_A', 'concept_B', 'concept_C', 'concept_D'],
        'relations': {
            ('concept_A', 'concept_B'): 0.8,
            ('concept_B', 'concept_C'): 0.5,
            ('concept_A', 'concept_C'): 0.3,
            ('concept_C', 'concept_D'): 0.6
        },
        'weights': {
            'concept_A': 0.2,
            'concept_B': 0.1,
            'concept_C': 0.3,
            'concept_D': 0.1
        }
    }
    
    print("\n📋 Test 2: Vind grondtoestand")
    result = await qvqe.find_ground_state(test_ontology, force_rerun=True)
    
    print(f"\n   Resultaat:")
    print(f"   ID: {result.id}")
    print(f"   Energie: {result.energy:.6f}")
    print(f"   Stabiliteit: {result.stability:.6f}")
    print(f"   Succes: {result.success}")
    print(f"   Iteraties: {result.iterations}")
    print(f"   Tijd: {result.execution_time*1000:.1f}ms")
    
    print("\n📋 Test 3: Cache test")
    # Tweede run zou cache moeten gebruiken
    result2 = await qvqe.find_ground_state(test_ontology)
    print(f"   Cache hits: {qvqe.stats['cache_hits']}")
    
    print("\n📋 Test 4: Vergelijk verschillende ontologieën")
    ontologie2 = {
        'entities': ['X', 'Y', 'Z'],
        'relations': {('X', 'Y'): 0.9, ('Y', 'Z'): 0.7},
        'weights': {'X': 0.3, 'Y': 0.2, 'Z': 0.4}
    }
    
    ontologie3 = {
        'entities': ['P', 'Q', 'R', 'S'],
        'relations': {('P', 'Q'): 0.6, ('Q', 'R'): 0.8, ('R', 'S'): 0.5},
        'weights': {'P': 0.1, 'Q': 0.2, 'R': 0.3, 'S': 0.2}
    }
    
    # Voer extra runs uit
    await qvqe.find_ground_state(ontologie2)
    await qvqe.find_ground_state(ontologie3)
    
    # Vergelijk
    comparison = qvqe.compare_ontologies([
        qvqe._hash_ontology(test_ontology),
        qvqe._hash_ontology(ontologie2),
        qvqe._hash_ontology(ontologie3)
    ])
    
    print(f"\n   Beste ontologie: {comparison.get('best_ontology', '?')[:8]}")
    print(f"   Beste energie: {comparison.get('best_energy', 0):.6f}")
    
    print("\n📋 Test 5: Statistieken")
    stats = qvqe.get_stats()
    print(f"   Totaal runs: {stats['total_runs']}")
    print(f"   Succesrate: {stats['success_rate']:.1%}")
    print(f"   Gem. energie: {stats['avg_energy']:.6f}")
    print(f"   Gem. stabiliteit: {stats['avg_stability']:.6f}")
    
    print("\n📋 Test 6: Recente resultaten")
    recent = qvqe.get_recent_results(3)
    for r in recent:
        print(f"   {r['id']}: energie={r['energy']:.6f}, stabiliteit={r['stability']:.3f}")
    
    print("\n📋 Test 7: Export")
    qvqe.export_results("vqe_demo.json")
    
    # Cleanup
    await qvqe.cleanup()
    
    print("\n" + "="*80)
    print("✅ Demonstratie voltooid!")
    print("="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    asyncio.run(demo())