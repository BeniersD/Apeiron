"""
quantum_structs.py – Quantum state and channel structures for Layer 2
=====================================================================
Provides:
  - QuantumState: density matrix on a set of qubits, with methods for
    reduced density, entanglement entropy, and concurrence.
  - QuantumChannel: CPTP map defined by Kraus operators.
  - TensorNetwork: placeholder for tensor network representations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import opt_einsum as oe
    HAS_OPT_EINSUM = True
except ImportError:
    HAS_OPT_EINSUM = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional import for concurrence (requires sqrtm)
# ---------------------------------------------------------------------------
try:
    from scipy.linalg import sqrtm
    HAS_SCIPY_LINALG = True
except ImportError:
    sqrtm = None
    HAS_SCIPY_LINALG = False


# ============================================================================
# QuantumState
# ============================================================================

@dataclass
class QuantumState:
    """
    Quantum state (density matrix) on a set of qubits.

    Attributes:
        n_qubits: number of qubits.
        density_matrix: 2^n × 2^n complex numpy array representing the state.
    """
    n_qubits: int
    density_matrix: np.ndarray  # shape (2**n_qubits, 2**n_qubits)

    def reduced_density(self, qubits: List[int]) -> np.ndarray:
        """
        Compute the reduced density matrix for a subset of qubits.

        Args:
            qubits: indices of qubits to keep (0-indexed).

        Returns:
            Reduced density matrix of shape (2**k, 2**k) where k = len(qubits).
        """
        n = self.n_qubits
        keep = sorted(qubits)
        trace_out = [i for i in range(n) if i not in keep]

        # Reshape the full density matrix into a tensor with 2n axes,
        # each of dimension 2 (one for bra and one for ket per qubit).
        rho_tensor = self.density_matrix.reshape([2] * (2 * n))

        # Trace out qubits in reverse order to maintain axis positions.
        for q in reversed(trace_out):
            # The bra and ket axes for qubit q are at position q and q + n.
            rho_tensor = np.trace(rho_tensor, axis1=q, axis2=q + n)

        # The remaining axes are in the order of `keep` (bra then ket).
        k = len(keep)
        return rho_tensor.reshape(2**k, 2**k)

    def entanglement_entropy(self, partition: List[int]) -> float:
        """
        Compute the von Neumann entropy of the reduced state on a subset.

        Args:
            partition: indices of qubits in the subsystem.

        Returns:
            Entanglement entropy in nats (natural logarithm).
        """
        rho_A = self.reduced_density(partition)
        evals = np.linalg.eigvalsh(rho_A)
        evals = evals[evals > 1e-12]  # discard numerical zeros
        return -np.sum(evals * np.log(evals))

    def concurrence(self, qubit_i: int, qubit_j: int) -> float:
        """
        Compute the concurrence between two qubits.

        The state is first reduced to the two qubits of interest;
        then the concurrence formula C(ρ) = max(0, λ₁ - λ₂ - λ₃ - λ₄)
        is applied, where λᵢ are the square roots of the eigenvalues of
        R = ρ (σ_y ⊗ σ_y) ρ^* (σ_y ⊗ σ_y) in decreasing order.

        Requires scipy.linalg.sqrtm for the matrix square root;
        otherwise returns 0.0 with a warning.

        Args:
            qubit_i: index of the first qubit.
            qubit_j: index of the second qubit.

        Returns:
            Concurrence (0 ≤ C ≤ 1).
        """
        if self.n_qubits < 2:
            return 0.0

        # Reduce to the two qubits
        rho_ij = self.reduced_density([qubit_i, qubit_j])

        # Helper Pauli Y matrix
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        YY = np.kron(sigma_y, sigma_y)

        # Compute the "spin-flipped" state
        rho_conj = rho_ij.conj()
        rho_tilde = YY @ rho_conj @ YY

        # R = ρ * ρ_tilde
        R = rho_ij @ rho_tilde

        if HAS_SCIPY_LINALG and sqrtm is not None:
            sqrt_R = sqrtm(R)
        else:
            logger.warning(
                "scipy.linalg.sqrtm not available; concurrence may be inaccurate. "
                "Falling back to element-wise sqrt."
            )
            sqrt_R = np.sqrt(np.abs(R))  # fallback (not theoretically correct)

        evals = np.linalg.eigvalsh(sqrt_R)
        evals = np.sort(evals)[::-1]  # descending
        # evals should be real and non-negative
        evals = np.maximum(evals, 0.0)
        return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])


# ============================================================================
# QuantumChannel
# ============================================================================

@dataclass
class QuantumChannel:
    """
    Quantum channel (CPTP map) defined by a set of Kraus operators.

    Attributes:
        kraus_ops: list of numpy matrices (K_i) satisfying Σ K_i† K_i = I.
    """
    kraus_ops: List[np.ndarray]

    def apply(self, rho: np.ndarray) -> np.ndarray:
        """
        Apply the channel to a density matrix ρ.

        Returns Σ_i K_i ρ K_i†.
        """
        result = np.zeros_like(rho, dtype=complex)
        for K in self.kraus_ops:
            result += K @ rho @ K.conj().T
        return result


# ============================================================================
# TensorNetwork
# ============================================================================

@dataclass
class TensorNetwork:
    tensors: Dict[str, np.ndarray] = field(default_factory=dict)
    connections: List[Tuple[str, str, int, int]] = field(default_factory=list)  
    # (name1, name2, axis_in_name1, axis_in_name2)

    def add_tensor(self, name: str, tensor: np.ndarray):
        self.tensors[name] = tensor

    def connect(self, name1: str, name2: str, axis1: int, axis2: int):
        self.connections.append((name1, name2, axis1, axis2))

    def contract(self) -> np.ndarray:
        if not self.tensors:
            return np.array(1.0)
        if len(self.tensors) == 1:
            return list(self.tensors.values())[0]
        try:
            import opt_einsum as oe
            # Build unique axis labels per tensor
            labels = {}
            counter = 0
            for name in self.tensors:
                labels[name] = [chr(ord('a') + (counter + i) % 26) for i in range(self.tensors[name].ndim)]
                counter += self.tensors[name].ndim
            # Apply connections: enforce shared labels for connected axes
            for n1, n2, a1, a2 in self.connections:
                shared = labels[n1][a1]
                labels[n2][a2] = shared
            # Build einsum string
            operands = list(self.tensors.values())
            input_str = ','.join(''.join(labels[name]) for name in self.tensors)
            output_str = ''  # full contraction to scalar
            einsum_str = f"{input_str}->{output_str}"
            result = oe.contract(einsum_str, *operands)
            return result
        except ImportError:
            # Fallback: sequential pairwise contraction (naive)
            names = list(self.tensors.keys())
            result = self.tensors[names[0]]
            for name in names[1:]:
                result = np.tensordot(result, self.tensors[name], axes=0)
            return result