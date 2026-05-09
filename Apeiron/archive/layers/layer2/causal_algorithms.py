"""
CAUSAL ALGORITHMS – ULTIMATE IMPLEMENTATION
============================================
This module provides advanced causal discovery algorithms beyond the basic PC/FCI/LiNGAM.
It now serves as a wrapper around causal_discovery.py for backward compatibility,
adding additional run_* methods and including GIN and CDNOD algorithms.

All algorithms degrade gracefully if required libraries are missing.
Results are returned as NetworkX DiGraph objects for seamless integration with Layer 2.
"""

import logging
import warnings
from typing import Optional, List, Dict, Any, Tuple, Union
import numpy as np

# Optional libraries
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# Try to import the comprehensive CausalDiscovery from causal_discovery
try:
    from .causal_discovery import CausalDiscovery as _BaseCausalDiscovery
    HAS_CAUSAL_DISCOVERY = True
except ImportError:
    HAS_CAUSAL_DISCOVERY = False
    # Define a placeholder that will raise an error on use
    class _BaseCausalDiscovery:
        def __init__(self, *args, **kwargs):
            raise ImportError("causal_discovery module not available. Please install causal-learn, lingam, etc.")

logger = logging.getLogger(__name__)


class CausalDiscovery(_BaseCausalDiscovery):
    """
    Advanced causal discovery with multiple algorithms.
    This class extends the base from causal_discovery.py with backward-compatible
    run_* methods and additional algorithms (GIN, CDNOD) exposed via run_* wrappers.
    """

    def __init__(self, data: np.ndarray, variable_names: Optional[List[str]] = None):
        super().__init__(data, variable_names)

    # ------------------------------------------------------------------------
    # Backward-compatible method names
    # ------------------------------------------------------------------------
    def run_ges(self, score_func: str = 'local_score_BIC', maxP: int = None,
                parameters: Optional[Dict] = None) -> nx.DiGraph:
        """Backward-compatible alias for ges()."""
        return self.ges(score_func, maxP, parameters)

    def run_cam(self, score_func: str = 'r2', alpha: float = 0.05,
                cutoff: int = 3, numB: int = 100, use_sklearn: bool = True) -> nx.DiGraph:
        """Backward-compatible alias for cam()."""
        return self.cam(score_func, alpha, cutoff, numB, use_sklearn)

    def run_lingam(self, method: str = 'ICALiNGAM', **kwargs) -> nx.DiGraph:
        """Backward-compatible alias for lingam()."""
        return self.lingam(method, **kwargs)

    def run_notears(self, lambda1: float = 0.1, loss_type: str = 'l2', max_iter: int = 100,
                    h_tol: float = 1e-8, rho_max: float = 1e+16, w_threshold: float = 0.3,
                    nonlinear: bool = False, **kwargs) -> nx.DiGraph:
        """Backward-compatible alias for notears()."""
        return self.notears(lambda1, loss_type, max_iter, h_tol, rho_max, w_threshold, nonlinear, **kwargs)

    # ------------------------------------------------------------------------
    # Additional algorithms (GIN, CDNOD) exposed with run_* prefix
    # ------------------------------------------------------------------------
    def run_gin(self, indep_test: str = 'kernel', alpha: float = 0.05, **kwargs) -> nx.DiGraph:
        """
        Run GIN (Generalized Independent Noise) algorithm.
        Requires causal-learn.
        """
        return self.gin(indep_test, alpha, **kwargs)

    def run_cdnod(self, alpha: float = 0.05, indep_test: str = 'fisherz', c_indep_test: str = 'fisherz',
                  background_knowledge=None, **kwargs) -> nx.DiGraph:
        """
        Run CDNOD (Causal Discovery from Nonstationary/heterogeneous Data).
        Requires the index of the domain variable (C) to be passed in kwargs.
        """
        return self.cdnod(alpha, indep_test, c_indep_test, background_knowledge, **kwargs)

    # ------------------------------------------------------------------------
    # Static methods (delegated to base)
    # ------------------------------------------------------------------------
    @staticmethod
    def generate_linear_gaussian(n_samples: int, n_vars: int, degree: int = 2,
                                  seed: int = 42, noise_scale: float = 0.1) -> Tuple[np.ndarray, nx.DiGraph]:
        return _BaseCausalDiscovery.generate_linear_gaussian(n_samples, n_vars, degree, seed, noise_scale)


# ============================================================================
# Command-line demo (updated)
# ============================================================================

def demo():
    """Run a simple demonstration of causal discovery algorithms."""
    print("="*80)
    print("CAUSAL ALGORITHMS DEMO")
    print("="*80)

    # Generate synthetic data
    print("\nGenerating synthetic linear Gaussian data...")
    data, true_graph = CausalDiscovery.generate_linear_gaussian(n_samples=1000, n_vars=5, degree=2)
    print(f"True graph edges: {list(true_graph.edges())}")

    cd = CausalDiscovery(data, variable_names=[f"X{i}" for i in range(5)])

    # Run GES (if available)
    if HAS_CAUSAL_DISCOVERY:
        print("\n--- GES ---")
        try:
            ges_graph = cd.run_ges()
            print(f"Estimated edges: {list(ges_graph.edges())}")
            eval = cd.evaluate(ges_graph, true_graph)
            print(f"SHD: {eval['shd']}, F1 (skeleton): {eval['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"GES failed: {e}")

    # Run CAM (if available)
    if HAS_CAUSAL_DISCOVERY:
        print("\n--- CAM ---")
        try:
            cam_graph = cd.run_cam()
            print(f"Estimated edges: {list(cam_graph.edges())}")
            eval = cd.evaluate(cam_graph, true_graph)
            print(f"SHD: {eval['shd']}, F1 (skeleton): {eval['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"CAM failed: {e}")

    # Run LiNGAM (if available)
    if HAS_CAUSAL_DISCOVERY:
        print("\n--- LiNGAM (ICALiNGAM) ---")
        try:
            lingam_graph = cd.run_lingam(method='ICALiNGAM')
            print(f"Estimated edges: {list(lingam_graph.edges())}")
            eval = cd.evaluate(lingam_graph, true_graph)
            print(f"SHD: {eval['shd']}, F1 (skeleton): {eval['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"LiNGAM failed: {e}")

    # Run NOTEARS
    print("\n--- NOTEARS ---")
    try:
        notears_graph = cd.run_notears(w_threshold=0.3)
        print(f"Estimated edges: {list(notears_graph.edges())}")
        eval = cd.evaluate(notears_graph, true_graph)
        print(f"SHD: {eval['shd']}, F1 (skeleton): {eval['skeleton_f1']:.3f}")
    except Exception as e:
        print(f"NOTEARS failed: {e}")

    # Run GIN (if available)
    if HAS_CAUSAL_DISCOVERY:
        print("\n--- GIN ---")
        try:
            gin_graph = cd.run_gin()
            print(f"Estimated edges: {list(gin_graph.edges())}")
            eval = cd.evaluate(gin_graph, true_graph)
            print(f"SHD: {eval['shd']}, F1 (skeleton): {eval['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"GIN failed: {e}")

    # Run CDNOD (requires C parameter – here we use a dummy)
    if HAS_CAUSAL_DISCOVERY:
        print("\n--- CDNOD (with dummy C) ---")
        try:
            # For CDNOD, we need to specify the index of the domain variable.
            # Here we assume the last variable is the domain indicator (just for demo).
            # In practice, you would provide the correct C.
            cdnod_graph = cd.run_cdnod(C=data.shape[1]-1, alpha=0.05)
            print(f"Estimated edges: {list(cdnod_graph.edges())}")
            eval = cd.evaluate(cdnod_graph, true_graph)
            print(f"SHD: {eval['shd']}, F1 (skeleton): {eval['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"CDNOD failed: {e}")


if __name__ == "__main__":
    demo()