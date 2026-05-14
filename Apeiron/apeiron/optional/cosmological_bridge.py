#!/usr/bin/env python3
"""
Cosmological Bridge – From Hypergraph Topology to Cosmological Parameters
==========================================================================
Optional module for Layer 2.

Interprets the hypergraph as a discrete analogue of an FLRW spacetime.
Topological invariants (Betti numbers, sheaf cohomology, spectral dimension)
are mapped to cosmological observables: Hubble constant, density parameters,
and the cosmological constant. This provides the bridge from Layer 2
(Relational Hypergraph) to Layers 14‑17 (Cosmological Emergence).

Mathematical Foundation
-----------------------
A hypergraph H can be seen as a causal set (discrete spacetime) if
directed edges represent causal precedence. The spectral dimension d_s
is computed from the heat kernel trace K(t) = Σ_i exp(-λ_i t) of the
Laplacian: d_s = -2 d log K / d log t. For a 4‑dimensional FLRW universe,
d_s → 4 for small t.

The Hubble expansion rate H(z) corresponds to the rate of vertex addition
per unit redshift. The cosmological constant Λ is identified with the
vacuum energy density computed from the TQFT partition function:
Λ = - (2/V) ln Z, where V is the "volume" (number of vertices).

The density parameters Ω_i are estimated from the proportions of
hyperedges of different types (matter, radiation, dark energy) classified
by their topological persistence.

References
----------
.. [1] Beniers, D. "17 Layers AI Model" – Layer 14‑17 (2025)
.. [2] Sorkin, R.D. "Causal Sets: Discrete Gravity" (2003)
.. [3] Connes, A. "Noncommutative Geometry" (1994)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import warnings

try:
    from scipy.optimize import curve_fit
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class CosmologicalParameters:
    """
    Cosmological parameters estimated from a hypergraph.

    Attributes:
        Hubble_constant: estimated expansion rate (km/s/Mpc).
        matter_density: Ω_m.
        radiation_density: Ω_r.
        dark_energy_density: Ω_Λ.
        cosmological_constant: Λ in natural units.
        spectral_dimension: spectral dimension of the hypergraph.
        spatial_curvature: Ω_k = 1 - Ω_total.
        num_vertices: number of vertices (proxy for volume).
        timestamp: time of estimation.
    """
    Hubble_constant: float = 70.0
    matter_density: float = 0.3
    radiation_density: float = 0.0
    dark_energy_density: float = 0.7
    cosmological_constant: float = 1e-122
    spectral_dimension: float = 4.0
    spatial_curvature: float = 0.0
    num_vertices: int = 0
    timestamp: float = 0.0


class CosmologicalBridge:
    """
    Bridge between hypergraph topology and cosmology.

    Parameters
    ----------
    hypergraph : Hypergraph
        The knowledge hypergraph representing the observable universe.
    """

    def __init__(self, hypergraph):
        self.hypergraph = hypergraph
        self._params = None

    # ------------------------------------------------------------------
    # Spectral dimension (heat kernel trace)
    # ------------------------------------------------------------------
    def spectral_dimension(self, t_min: float = 0.1, t_max: float = 10.0, n_points: int = 20) -> float:
        """
        Compute the spectral dimension d_s from the heat kernel trace K(t).

        Returns the average spectral dimension over the time interval.
        """
        # Build Laplacian (0‑Laplacian for simplicity)
        try:
            L = self.hypergraph.hodge_laplacian(dim=0)
        except Exception:
            # Fallback: degree-normalised adjacency Laplacian
            adj = np.zeros((len(self.hypergraph.vertices), len(self.hypergraph.vertices)))
            vertex_list = list(self.hypergraph.vertices)
            idx = {v: i for i, v in enumerate(vertex_list)}
            for edge in self.hypergraph.hyperedges.values():
                for v1, v2 in combinations(edge, 2):
                    i, j = idx[v1], idx[v2]
                    adj[i, j] = adj[j, i] = 1
            deg = adj.sum(axis=1)
            deg_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
            L = np.eye(len(vertex_list)) - deg_inv_sqrt[:, None] * adj * deg_inv_sqrt[None, :]

        eigenvalues = np.linalg.eigvalsh(L)
        eigenvalues = eigenvalues[eigenvalues > 0]

        ts = np.logspace(np.log10(t_min), np.log10(t_max), n_points)
        log_K = []
        for t in ts:
            K_t = np.sum(np.exp(-eigenvalues * t))
            log_K.append(np.log(max(K_t, 1e-300)))

        log_K = np.array(log_K)
        log_t = np.log(ts)

        # d_s = -2 d(log K) / d(log t)
        if HAS_SCIPY and len(ts) >= 4:
            # Fit a quadratic and take derivative at the midpoint
            coeffs = np.polyfit(log_t, log_K, 2)
            midpoint = np.median(log_t)
            deriv = 2 * coeffs[0] * midpoint + coeffs[1]
            return float(-2 * deriv)
        else:
            # Finite difference
            d_log_K = np.diff(log_K)
            d_log_t = np.diff(log_t)
            deriv = d_log_K / d_log_t
            return float(-2 * np.median(deriv))

    # ------------------------------------------------------------------
    # Hubble constant (vertex growth rate)
    # ------------------------------------------------------------------
    def estimate_hubble_constant(self, time_interval: float = 1.0) -> float:
        """
        Estimate H₀ from the growth rate of vertices.
        H = (1/V) dV/dt ≈ (1/N) ΔN / Δt.
        Since we have a static snapshot, we approximate by counting
        hyperedges as proxy for expansion history.
        """
        n_vertices = len(self.hypergraph.vertices)
        n_hyperedges = len(self.hypergraph.hyperedges)
        if n_vertices == 0 or time_interval <= 0:
            return 70.0  # default
        # Heuristic: more hyperedges per vertex → faster expansion
        expansion_rate = n_hyperedges / max(n_vertices, 1)
        return float(70.0 * expansion_rate)

    # ------------------------------------------------------------------
    # Density parameters (from topological persistence)
    # ------------------------------------------------------------------
    def estimate_density_parameters(self) -> Tuple[float, float, float]:
        """
        Estimate Ω_m, Ω_r, Ω_Λ from the persistence of hyperedges.
        Long-lived hyperedges → matter, short-lived → radiation,
        newly appearing → dark energy.
        """
        try:
            persistent = self.hypergraph.persistent_homology()
            diagrams = persistent.get('diagrams', {})
            # Count features by lifespan
            short = 0
            medium = 0
            long_lived = 0
            for dim, intervals in diagrams.items():
                for birth, death in intervals:
                    lifespan = death - birth if death < float('inf') else 1e10
                    if lifespan < 0.5:
                        short += 1
                    elif lifespan < 10:
                        medium += 1
                    else:
                        long_lived += 1
            total = max(short + medium + long_lived, 1)
            omega_r = short / total
            omega_m = medium / total
            omega_L = long_lived / total
            return omega_m, omega_r, omega_L
        except Exception:
            # Fallback: heuristics
            n_vertices = len(self.hypergraph.vertices)
            n_edges = len(self.hypergraph.hyperedges)
            if n_vertices == 0:
                return 0.3, 0.0, 0.7
            omega_m = 0.3 * n_edges / max(n_vertices, 1)
            omega_L = 0.7
            omega_r = 0.0
            return omega_m, omega_r, omega_L

    # ------------------------------------------------------------------
    # Cosmological constant from TQFT partition function
    # ------------------------------------------------------------------
    def estimate_cosmological_constant(self) -> float:
        """
        Λ = - (2 / V) ln Z, where V = number of vertices, Z = TQFT
        partition function.
        """
        V = max(len(self.hypergraph.vertices), 1)
        try:
            from apeiron.layers.layer02_relational.quantum_topology import HypergraphTQFT
            tqft = HypergraphTQFT(self.hypergraph)
            Z = tqft.partition_function()
        except ImportError:
            # Fallback: use Euler characteristic
            chi = len(self.hypergraph.vertices) - len(self.hypergraph.hyperedges)
            Z = np.exp(-abs(chi))
        if Z <= 0:
            Z = 1e-300
        Lambda = - (2.0 / V) * np.log(Z)
        return float(Lambda)

    # ------------------------------------------------------------------
    # Full cosmological analysis
    # ------------------------------------------------------------------
    def compute_cosmology(self) -> CosmologicalParameters:
        """
        Run all estimators and return a CosmologicalParameters dataclass.
        """
        d_s = self.spectral_dimension()
        H0 = self.estimate_hubble_constant()
        omega_m, omega_r, omega_L = self.estimate_density_parameters()
        Lambda = self.estimate_cosmological_constant()
        omega_k = 1.0 - (omega_m + omega_r + omega_L)

        self._params = CosmologicalParameters(
            Hubble_constant=H0,
            matter_density=omega_m,
            radiation_density=omega_r,
            dark_energy_density=omega_L,
            cosmological_constant=Lambda,
            spectral_dimension=d_s,
            spatial_curvature=omega_k,
            num_vertices=len(self.hypergraph.vertices),
            timestamp=np.datetime64('now').astype(float),
        )
        return self._params


# ============================================================================
# Factory
# ============================================================================

def hypergraph_to_cosmology(hypergraph) -> CosmologicalParameters:
    """
    Convenience function: compute cosmological parameters from a hypergraph.
    """
    bridge = CosmologicalBridge(hypergraph)
    return bridge.compute_cosmology()


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)