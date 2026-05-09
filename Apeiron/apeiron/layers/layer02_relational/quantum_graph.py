"""
quantum_graph.py – Quantum graph structures for Layer 2
========================================================
Provides the `QuantumGraph` class: a graph where edges and vertices carry
complex amplitudes, enabling continuous‑time and discrete‑time quantum walks,
quantum PageRank, and entanglement measures.

All heavy quantum libraries (Qiskit, PennyLane, QuTiP) are optional.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Caching decorator (replicated from spectral.py)
# ---------------------------------------------------------------------------
def cached(ttl: int = 3600, key_prefix: str = "qgraph"):
    """Simple in‑memory cache with optional Redis (if available)."""
    def decorator(func):
        _cache: Dict[str, Tuple[Any, float]] = {}
        def wrapper(self, *args, **kwargs):
            import hashlib, pickle
            key = hashlib.md5(
                (func.__name__ + str(args) + str(sorted(kwargs.items()))).encode()
            ).hexdigest()
            full_key = f"{key_prefix}:{key}"
            if full_key in _cache:
                val, exp = _cache[full_key]
                if time.time() < exp:
                    return val
                del _cache[full_key]
            result = func(self, *args, **kwargs)
            _cache[full_key] = (result, time.time() + ttl)
            return result
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Optional imports – graceful degradation
# ---------------------------------------------------------------------------
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    from scipy.linalg import expm, sqrtm
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import torch
    HAS_TORCH = True
    CUDA_AVAILABLE = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
except ImportError:
    HAS_TORCH = False
    CUDA_AVAILABLE = False

# Qiskit
try:
    from qiskit import QuantumCircuit, Aer, execute, IBMQ
    from qiskit.quantum_info import Statevector, partial_trace, entropy
    from qiskit.providers.aer import QasmSimulator
    from qiskit.providers.aer.noise import NoiseModel
    from qiskit_machine_learning.algorithms import QSVC, VQC
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

# PennyLane
try:
    import pennylane as qml
    from pennylane import numpy as pnp
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False

# QuTiP
try:
    import qutip as qt
    QUTIP_AVAILABLE = True
except ImportError:
    QUTIP_AVAILABLE = False

# SymPy
try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


# ============================================================================
# QuantumGraph
# ============================================================================

@dataclass
class QuantumGraph:
    """
    A graph with quantum mechanical amplitudes on edges and vertices.

    Supports continuous‑time quantum walks, discrete‑time walks (with coin,
    Szegedy, Grover, lackadaisical), quantum PageRank, entanglement measures,
    and integration with Qiskit / PennyLane for quantum machine learning.

    Attributes:
        graph: NetworkX graph (directed or undirected)
        edge_amplitudes: dict mapping (u, v) → complex amplitude
        vertex_amplitudes: dict mapping vertex → complex amplitude
        hamiltonian: dense Hamiltonian matrix (constructed lazily)
        entanglement_matrix: density matrix for entanglement analysis
    """
    graph: Optional[Any] = None
    edge_amplitudes: Dict[Tuple[int, int], complex] = field(default_factory=dict)
    vertex_amplitudes: Dict[int, complex] = field(default_factory=dict)
    hamiltonian: Optional[np.ndarray] = None
    entanglement_matrix: Optional[np.ndarray] = None
    _cache: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------------
    # Hamiltonian construction
    # ------------------------------------------------------------------------
    def _build_hamiltonian(self, method: str = 'adjacency') -> None:
        if not HAS_NETWORKX or self.graph is None:
            return
        n = self.graph.number_of_nodes()
        if method == 'adjacency':
            adj = nx.adjacency_matrix(self.graph).todense()
            self.hamiltonian = -np.array(adj, dtype=complex)
        elif method == 'laplacian':
            L = nx.laplacian_matrix(self.graph).todense()
            self.hamiltonian = -np.array(L, dtype=complex)
        else:
            self.hamiltonian = np.zeros((n, n), dtype=complex)
        for v, amp in self.vertex_amplitudes.items():
            if 0 <= v < n:
                self.hamiltonian[v, v] += amp
        for (i, j), amp in self.edge_amplitudes.items():
            if 0 <= i < n and 0 <= j < n:
                self.hamiltonian[i, j] += amp
                self.hamiltonian[j, i] += np.conj(amp)

    # ------------------------------------------------------------------------
    # Quantum walk – unified interface
    # ------------------------------------------------------------------------
    def quantum_walk(
        self,
        time: float,
        initial_state: np.ndarray,
        method: str = 'continuous',
        **kwargs,
    ) -> np.ndarray:
        if method == 'continuous':
            return self._ctqw(time, initial_state)
        elif method == 'discrete':
            return self._dtqw(int(time), initial_state)
        elif method == 'discrete_coin':
            return self._dtqw_coin(int(time), initial_state, **kwargs)
        elif method == 'szegedy':
            return self._szegedy_walk(int(time), initial_state, **kwargs)
        elif method == 'grover':
            return self._grover_search(int(time), initial_state, **kwargs)
        elif method == 'lackadaisical':
            return self._lackadaisical_walk(int(time), initial_state, **kwargs)
        else:
            raise ValueError(f"Unknown quantum walk method: {method}")

    def _ctqw(self, time: float, initial_state: np.ndarray) -> np.ndarray:
        if self.hamiltonian is None:
            self._build_hamiltonian()
        if HAS_SCIPY:
            U = expm(-1j * self.hamiltonian * time)
            return U @ initial_state
        return initial_state

    def _dtqw(self, steps: int, initial_state: np.ndarray) -> np.ndarray:
        if self.graph is None or not HAS_NETWORKX:
            return initial_state
        if self.hamiltonian is None:
            self._build_hamiltonian()
        dt = 0.1
        U = expm(-1j * self.hamiltonian * dt)
        state = initial_state.copy()
        for _ in range(steps):
            state = U @ state
        return state

    def _dtqw_coin(
        self,
        steps: int,
        initial_state: np.ndarray,
        coin_type: str = 'grover',
    ) -> np.ndarray:
        if self.graph is None or not HAS_NETWORKX:
            return initial_state
        n = self.graph.number_of_nodes()
        max_deg = max(dict(self.graph.degree()).values())
        if max_deg == 0:
            return initial_state
        if coin_type == 'grover':
            C = 2.0 / max_deg * np.ones((max_deg, max_deg)) - np.eye(max_deg)
        elif coin_type == 'hadamard':
            C = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
            if max_deg != 2:
                C = np.eye(max_deg)
        else:
            C = np.eye(max_deg)
        adj = {i: list(self.graph.neighbors(i)) for i in range(n)}
        coin_dim = max_deg
        if len(initial_state) != n * coin_dim:
            new_state = np.zeros(n * coin_dim, dtype=complex)
            for i in range(min(n, len(initial_state))):
                new_state[i * coin_dim] = initial_state[i]
            initial_state = new_state
        state = initial_state.copy()
        for _ in range(steps):
            for v in range(n):
                idx = v * coin_dim
                state[idx:idx + coin_dim] = C @ state[idx:idx + coin_dim]
            new_state = np.zeros_like(state)
            for v in range(n):
                for c, w in enumerate(adj[v]):
                    if c < coin_dim:
                        new_state[w * coin_dim + c] += state[v * coin_dim + c]
            state = new_state
        return state

    def _szegedy_walk(self, steps: int, initial_state: np.ndarray) -> np.ndarray:
        if self.graph is None or not HAS_NETWORKX:
            return initial_state
        n = self.graph.number_of_nodes()
        edges = list(self.graph.edges())
        if self.graph.is_directed():
            d_edges = edges + [(v, u) for u, v in edges if (v, u) not in edges]
        else:
            d_edges = edges + [(v, u) for u, v in edges]
        edge_idx = {e: i for i, e in enumerate(d_edges)}
        m = len(d_edges)
        psi = np.ones(m) / np.sqrt(m)
        R = 2 * np.outer(psi, psi) - np.eye(m)
        S = np.zeros((m, m))
        for (u, v), i in edge_idx.items():
            if (v, u) in edge_idx:
                S[i, edge_idx[(v, u)]] = 1.0
        U = S @ R
        state = initial_state.copy()
        for _ in range(steps):
            state = U @ state
        return state

    def _grover_search(
        self,
        steps: int,
        initial_state: np.ndarray,
        marked_vertices: Optional[List[int]] = None,
        marked_function: Optional[Callable[[int], bool]] = None,
    ) -> np.ndarray:
        if self.graph is None or not HAS_NETWORKX:
            return initial_state
        n = self.graph.number_of_nodes()
        s = np.ones(n) / np.sqrt(n)
        D = 2 * np.outer(s, s) - np.eye(n)
        def oracle(state):
            new = state.copy()
            if marked_vertices:
                for v in marked_vertices:
                    if 0 <= v < n:
                        new[v] *= -1
            if marked_function:
                for v in range(n):
                    if marked_function(v):
                        new[v] *= -1
            return new
        state = initial_state.copy()
        for _ in range(steps):
            state = oracle(state)
            state = D @ state
        return state

    def _lackadaisical_walk(
        self,
        steps: int,
        initial_state: np.ndarray,
        self_loop_weight: float = 1.0,
    ) -> np.ndarray:
        if self.graph is None or not HAS_NETWORKX:
            return initial_state
        n = self.graph.number_of_nodes()
        max_deg = max(dict(self.graph.degree()).values())
        coin_dim = max_deg + 1
        C = 2.0 / coin_dim * np.ones((coin_dim, coin_dim)) - np.eye(coin_dim)
        adj = {i: list(self.graph.neighbors(i)) for i in range(n)}
        if len(initial_state) != n * coin_dim:
            new_state = np.zeros(n * coin_dim, dtype=complex)
            for i in range(min(n, len(initial_state))):
                new_state[i * coin_dim] = initial_state[i]
            initial_state = new_state
        state = initial_state.copy()
        for _ in range(steps):
            for v in range(n):
                idx = v * coin_dim
                state[idx:idx + coin_dim] = C @ state[idx:idx + coin_dim]
            new_state = np.zeros_like(state)
            for v in range(n):
                for c, w in enumerate(adj[v]):
                    if c < coin_dim - 1:
                        new_state[w * coin_dim + c] += state[v * coin_dim + c]
                new_state[v * coin_dim + coin_dim - 1] += state[v * coin_dim + coin_dim - 1]
            state = new_state
        return state

    # ------------------------------------------------------------------------
    # Quantum PageRank
    # ------------------------------------------------------------------------
    def quantum_pagerank(self, alpha: float = 0.85, time: float = 1.0) -> np.ndarray:
        if not HAS_NETWORKX or self.graph is None:
            return np.array([])
        n = self.graph.number_of_nodes()
        A = nx.adjacency_matrix(self.graph).todense()
        J = np.ones((n, n))
        H = -(alpha * A + (1 - alpha) * J / n)
        if HAS_SCIPY:
            U = expm(-1j * H * time)
            init = np.ones(n, dtype=complex) / np.sqrt(n)
            final = U @ init
            return np.abs(final) ** 2
        return np.array([])

    # ------------------------------------------------------------------------
    # Entanglement measures
    # ------------------------------------------------------------------------
    def entanglement_entropy(self, partition: List[int]) -> float:
        if self.entanglement_matrix is None:
            return 0.0
        n = self.entanglement_matrix.shape[0]
        subsystem = [i for i in range(n) if i in partition]
        rho_A = self.entanglement_matrix[np.ix_(subsystem, subsystem)]
        evals = np.linalg.eigvalsh(rho_A)
        evals = evals[evals > 1e-12]
        return -np.sum(evals * np.log(evals))

    def concurrence(self, qubit_indices: Tuple[int, int]) -> float:
        if self.entanglement_matrix is None:
            return 0.0
        n = self.entanglement_matrix.shape[0]
        if n != 4:
            return 0.0
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        YY = np.kron(sigma_y, sigma_y)
        rho = self.entanglement_matrix.reshape(4, 4)
        rho_tilde = YY @ rho.conj() @ YY
        R = rho @ rho_tilde
        if HAS_SCIPY:
            sqrt_R = sqrtm(R)
        else:
            sqrt_R = np.sqrt(np.abs(R))
        evals = np.linalg.eigvalsh(sqrt_R)
        evals = np.sort(evals)[::-1]
        return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])

    def entanglement_of_formation(self, qubit_indices: Tuple[int, int]) -> float:
        C = self.concurrence(qubit_indices)
        if C >= 1.0:
            return 1.0
        x = (1 + np.sqrt(1 - C**2)) / 2
        if x <= 0 or x >= 1:
            return 0.0
        return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

    # ------------------------------------------------------------------------
    # Qiskit integration
    # ------------------------------------------------------------------------
    def to_qiskit_circuit(
        self,
        vertices: Optional[List[int]] = None,
        use_real_hardware: bool = False,
        backend_name: str = 'qasm_simulator',
    ) -> Any:
        if not QISKIT_AVAILABLE or self.graph is None:
            return None
        n = self.graph.number_of_nodes() if vertices is None else len(vertices)
        qc = QuantumCircuit(n, n)
        if self.vertex_amplitudes:
            for v, amp in self.vertex_amplitudes.items():
                if v < n:
                    qc.initialize([amp, np.sqrt(1 - abs(amp)**2)], v)
        return qc

    def run_on_ibmq(
        self,
        circuit: Any,
        backend_name: str = 'ibmq_qasm_simulator',
        shots: int = 1024,
    ) -> Dict[str, int]:
        if not QISKIT_AVAILABLE:
            return {}
        try:
            IBMQ.load_account()
            provider = IBMQ.get_provider()
            backend = provider.get_backend(backend_name)
            job = execute(circuit, backend, shots=shots)
            from qiskit.tools.monitor import job_monitor
            job_monitor(job)
            return job.result().get_counts()
        except Exception as e:
            logger.error(f"IBMQ execution failed: {e}")
            return {}

    # ------------------------------------------------------------------------
    # Quantum machine learning (QSVM)
    # ------------------------------------------------------------------------
    def qsvm(
        self,
        train_data: np.ndarray,
        train_labels: np.ndarray,
        test_data: np.ndarray,
        test_labels: np.ndarray,
        n_qubits: int = 4,
    ) -> float:
        if PENNYLANE_AVAILABLE:
            return self._qsvm_pennylane(train_data, train_labels, test_data, test_labels, n_qubits)
        elif QISKIT_AVAILABLE:
            return self._qsvm_qiskit(train_data, train_labels, test_data, test_labels)
        logger.warning("No quantum ML library available")
        return 0.5

    def _qsvm_pennylane(
        self,
        X_train, y_train, X_test, y_test, n_qubits,
    ) -> float:
        try:
            dev = qml.device('default.qubit', wires=n_qubits)
            @qml.qnode(dev)
            def kernel_circuit(x1, x2):
                for i in range(len(x1)):
                    qml.RY(x1[i], wires=i)
                qml.adjoint(lambda: [qml.RY(x2[i], wires=i) for i in range(len(x2))])
                return qml.probs(wires=range(n_qubits))
            n_train = len(X_train)
            K_train = np.zeros((n_train, n_train))
            for i in range(n_train):
                for j in range(i, n_train):
                    val = kernel_circuit(X_train[i], X_train[j])[0]
                    K_train[i, j] = K_train[j, i] = val
            from sklearn.svm import SVC
            clf = SVC(kernel='precomputed')
            clf.fit(K_train, y_train)
            n_test = len(X_test)
            K_test = np.zeros((n_test, n_train))
            for i in range(n_test):
                for j in range(n_train):
                    K_test[i, j] = kernel_circuit(X_test[i], X_train[j])[0]
            return clf.score(K_test, y_test)
        except Exception as e:
            logger.error(f"PennyLane QSVM failed: {e}")
            return 0.5

    def _qsvm_qiskit(self, X_train, y_train, X_test, y_test) -> float:
        try:
            feature_map = ZZFeatureMap(feature_dimension=X_train.shape[1], reps=2)
            kernel = FidelityQuantumKernel(feature_map=feature_map)
            qsvc = QSVC(quantum_kernel=kernel)
            qsvc.fit(X_train, y_train)
            return qsvc.score(X_test, y_test)
        except Exception as e:
            logger.error(f"Qiskit QSVM failed: {e}")
            return 0.5

    # ------------------------------------------------------------------------
    # Decoherence (Lindblad)
    # ------------------------------------------------------------------------
    def lindblad_evolution(
        self,
        rho0: np.ndarray,
        t: float,
        collapse_ops: List[np.ndarray],
    ) -> np.ndarray:
        if not QUTIP_AVAILABLE:
            logger.warning("QuTiP not available – returning input state.")
            return rho0
        n = rho0.shape[0]
        H = qt.Qobj(self.hamiltonian) if self.hamiltonian is not None else qt.Qobj(np.zeros((n, n)))
        rho = qt.Qobj(rho0)
        c_ops = [qt.Qobj(L) for L in collapse_ops]
        result = qt.mesolve(H, rho, [0, t], c_ops, [])
        return result.states[-1].full()

    def kraus_operators(self, noise: str = 'depolarizing', p: float = 0.1) -> List[np.ndarray]:
        if noise == 'depolarizing':
            I = np.eye(2)
            X = np.array([[0, 1], [1, 0]])
            Y = np.array([[0, -1j], [1j, 0]])
            Z = np.array([[1, 0], [0, -1]])
            return [
                np.sqrt(1 - p) * I,
                np.sqrt(p / 3) * X,
                np.sqrt(p / 3) * Y,
                np.sqrt(p / 3) * Z,
            ]
        return []

    # ------------------------------------------------------------------------
    # Symbolic Hamiltonian (SymPy)
    # ------------------------------------------------------------------------
    def symbolic_hamiltonian(self, symbols_dict: Optional[Dict] = None) -> Any:
        if not SYMPY_AVAILABLE or self.graph is None:
            return None
        n = self.graph.number_of_nodes()
        H = sp.zeros(n)
        if symbols_dict is None:
            symbols_dict = {
                f'H_{i}{j}': sp.symbols(f'H_{i}{j}') for i in range(n) for j in range(i, n)
            }
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    H[i, i] = symbols_dict.get(f'H_{i}{i}', 0)
                elif self.graph.has_edge(i, j):
                    H[i, j] = symbols_dict.get(f'H_{i}{j}', 0)
                    H[j, i] = sp.conjugate(H[i, j])
        return H

    # ------------------------------------------------------------------------
    # GPU acceleration (PyTorch)
    # ------------------------------------------------------------------------
    def to_gpu(self) -> QuantumGraph:
        if HAS_TORCH and CUDA_AVAILABLE:
            if self.hamiltonian is not None:
                self.hamiltonian = torch.as_tensor(self.hamiltonian, dtype=torch.complex128, device='cuda')
            if self.entanglement_matrix is not None:
                self.entanglement_matrix = torch.as_tensor(self.entanglement_matrix, dtype=torch.complex128, device='cuda')
        return self

    def from_gpu(self) -> QuantumGraph:
        if HAS_TORCH:
            if isinstance(self.hamiltonian, torch.Tensor):
                self.hamiltonian = self.hamiltonian.cpu().numpy()
            if isinstance(self.entanglement_matrix, torch.Tensor):
                self.entanglement_matrix = self.entanglement_matrix.cpu().numpy()
        return self

    # ------------------------------------------------------------------------
    # Layer‑1 integration: walk from an observable state
    # ------------------------------------------------------------------------
    def quantum_walk_from_observable(
        self,
        observable: Any,
        time: float,
        method: str = 'continuous',
        observable_to_state: Optional[Callable[[Any], np.ndarray]] = None,
        **kwargs,
    ) -> np.ndarray:
        if self.graph is None or not HAS_NETWORKX:
            raise RuntimeError("No graph available for quantum walk")
        n = self.graph.number_of_nodes()
        if observable_to_state is not None:
            state = observable_to_state(observable)
        elif hasattr(observable, 'state_vector'):
            state = observable.state_vector
            if len(state) != n:
                raise ValueError(f"State vector length {len(state)} != graph size {n}")
        else:
            logger.warning("Using uniform superposition as fallback initial state.")
            state = np.ones(n, dtype=complex) / np.sqrt(n)
        return self.quantum_walk(time, state, method=method, **kwargs)

    # ------------------------------------------------------------------------
    # Visualisation (stub)
    # ------------------------------------------------------------------------
    def visualize(self, *args, **kwargs) -> None:
        logger.info("Quantum graph visualisation delegated to dashboards module.")