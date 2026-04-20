# -*- coding: utf-8 -*-
"""
conftest.py -- Layer 1 test configuration (v3.1)

Pytest configuration for Layer 1 test suite.

This file provides:
- Warning filters for benign sklearn/scipy messages.
- Fixtures for core Layer 1 objects (MetaSpecification, UltimateObservable, etc.).
- Fixtures for new core components (EventBus, LayerConfig).
- Automatic cleanup of async resources.
- Custom markers for test categorization.

Purpose
-------
Suppresses well-known, benign sklearn warnings that arise from spectral
embedding on small relational graphs:

1. UserWarning: Graph is not fully connected
   Raised by sklearn.manifold.SpectralEmbedding when the relational graph
   has disconnected components.  update_embedding() already handles this
   via the largest-connected-component fallback, so the warning is cosmetic.

2. RuntimeWarning: k >= N for N * N square matrix
   Raised when scipy.sparse.linalg.eigsh falls back to scipy.linalg.eigh
   for small dense matrices.  Our implementation requires at least 3 nodes
   (n_components = N-1), but scipy still emits the warning on some platforms.

Both conditions are theoretically harmless.  They are suppressed at the
pytest level here as a defensive measure, in addition to the internal
warnings.catch_warnings() guards inside update_embedding().

Usage:
    pytest unit/                          # run unit tests only
    pytest experiments/                   # run experiment scripts
    pytest -m "not slow"                  # exclude slow integration tests
"""
import asyncio
import warnings
from typing import AsyncGenerator, Generator, Optional

import numpy as np
import pytest

# ============================================================================
# Pytest configuration
# ============================================================================

def pytest_configure(config):
    """Register custom warning filters and markers."""
    # Warning filters (as before)
    warnings.filterwarnings(
        "ignore",
        message=".*Graph is not fully connected.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*k >= N for N.*",
        category=RuntimeWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Attempting to use scipy.linalg.eigh.*",
        category=RuntimeWarning,
    )

    # Custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: integration tests requiring multiple components")
    config.addinivalue_line("markers", "hardware: tests that require specific hardware backends")
    config.addinivalue_line("markers", "experimental: experimental tests that may be unstable")


# ============================================================================
# Core Layer 1 fixtures
# ============================================================================

@pytest.fixture
def default_meta_spec():
    """Return a fresh default MetaSpecification."""
    from apeiron.layers.layer01_foundational.meta_spec import MetaSpecification
    return MetaSpecification()


@pytest.fixture
def custom_meta_spec():
    """Return a MetaSpecification that can be mutated per test."""
    from apeiron.layers.layer01_foundational.meta_spec import MetaSpecification
    return MetaSpecification()


@pytest.fixture
def simple_observable():
    """Return a basic UltimateObservable (integer 1)."""
    from apeiron.layers.layer01_foundational.irreducible_unit import (
        UltimateObservable,
        ObservabilityType,
    )
    return UltimateObservable(
        id="test_obs",
        value=1,
        observability_type=ObservabilityType.DISCRETE,
    )


@pytest.fixture
def observable_factory():
    """Factory fixture to create UltimateObservable with custom parameters."""
    from apeiron.layers.layer01_foundational.irreducible_unit import (
        UltimateObservable,
        ObservabilityType,
    )
    def _make(obs_id="test", value=42, obs_type=ObservabilityType.DISCRETE, **kwargs):
        return UltimateObservable(
            id=obs_id,
            value=value,
            observability_type=obs_type,
            **kwargs
        )
    return _make


@pytest.fixture
def layer1_observables():
    """Return a fresh Layer1_Observables registry."""
    from apeiron.layers.layer01_foundational.observables import Layer1_Observables
    return Layer1_Observables()


@pytest.fixture
def density_field():
    """Return an empty DensityField."""
    from apeiron.layers.layer01_foundational.density_field import DensityField
    return DensityField()


@pytest.fixture
def evolutionary_loop(default_meta_spec):
    """Return an EvolutionaryFeedbackLoop with default MetaSpec."""
    from apeiron.layers.layer01_foundational.discovery import EvolutionaryFeedbackLoop
    return EvolutionaryFeedbackLoop(default_meta_spec)


# ============================================================================
# Core framework fixtures (new core modules)
# ============================================================================

@pytest.fixture
def event_bus():
    """Return a fresh EventBus instance (memory backend, no persistence)."""
    from apeiron.core.event_bus import EventBus, EventBusConfig
    config = EventBusConfig(
        node_id="test_node",
        enable_persistence=False,
        enable_distributed=False,
    )
    return EventBus(config)


@pytest.fixture
async def running_event_bus(event_bus) -> AsyncGenerator:
    """Return an EventBus that is already started (and stopped after test)."""
    event_bus.start()
    yield event_bus
    await event_bus.stop()


@pytest.fixture
def layer_config():
    """Return a default LayerConfig for testing."""
    from apeiron.core.base import LayerConfig, LayerType
    return LayerConfig(
        layer_id="test_layer",
        layer_type=LayerType.FOUNDATIONAL,
    )


@pytest.fixture
def mock_hardware_backend():
    """Mock a hardware backend that always returns success."""
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.initialize.return_value = True
    mock.process.return_value = "mock_result"
    mock.get_info.return_value = {"name": "MockBackend"}
    return mock


# ============================================================================
# Asyncio fixtures & event loop management
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# @pytest.fixture(autouse=True)
# async def cleanup_async_tasks():
#     """Automatically cancel pending tasks after each async test."""
#     yield
#     tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in tasks:
#         task.cancel()
#     if tasks:
#         await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================================
# Data fixtures for experiments
# ============================================================================

@pytest.fixture
def synthetic_two_groups():
    """Generate synthetic dataset: 200 samples, 64 features, two perfectly separated groups."""
    rng = np.random.default_rng(42)
    n_samples, n_features = 200, 64
    X = np.zeros((n_samples, n_features))
    X[:100, :32] = rng.random((100, 32)) * 0.8 + 0.1
    X[100:, 32:] = rng.random((100, 32)) * 0.8 + 0.1
    y = np.array([0] * 100 + [1] * 100)
    return X, y


@pytest.fixture
def coactivation_matrix(synthetic_two_groups):
    """Build co-activation matrix from synthetic data."""
    X, _ = synthetic_two_groups
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    return corr


# ============================================================================
# Hardware-related fixtures (optional, skipped if not available)
# ============================================================================

@pytest.fixture
def cpu_backend():
    """Return an initialized CPU backend."""
    try:
        from apeiron.hardware.backends import CPUBackend
        backend = CPUBackend()
        backend.initialize({})
        return backend
    except ImportError:
        pytest.skip("Hardware module not available")


@pytest.fixture
def hardware_factory():
    """Return a HardwareFactory instance."""
    try:
        from apeiron.hardware.factory import HardwareFactory
        return HardwareFactory()
    except ImportError:
        pytest.skip("Hardware factory not available")


# ============================================================================
# Self-proving fixtures (Z3, SymPy)
# ============================================================================

@pytest.fixture
def self_proving_observable():
    """Return an UltimateObservable with self-proving capability added."""
    from apeiron.layers.layer01_foundational.irreducible_unit import (
        UltimateObservable,
        ObservabilityType,
    )
    from apeiron.layers.layer01_foundational.self_proving import add_self_proving_capability

    obs = UltimateObservable(
        id="provable",
        value=1,
        observability_type=ObservabilityType.DISCRETE,
    )
    obs._compute_atomicities()
    prover = add_self_proving_capability(obs)
    return obs, prover


@pytest.fixture
def has_sympy():
    """Check if SymPy is available."""
    try:
        import sympy
        return True
    except ImportError:
        return False


@pytest.fixture
def has_z3():
    """Check if Z3 is available."""
    try:
        import z3
        return True
    except ImportError:
        return False