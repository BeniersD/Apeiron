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

    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "hardware: tests that require specific hardware")
    config.addinivalue_line("markers", "experimental: experimental tests")


# ============================================================================
# Session-scoped fixtures (aangemaakt één keer per testsessie)
# ============================================================================

@pytest.fixture(scope="session")
def default_meta_spec():
    """Session-scoped default MetaSpecification - gedeeld door alle tests."""
    from apeiron.layers.layer01_foundational.meta_spec import MetaSpecification
    return MetaSpecification()


@pytest.fixture(scope="session")
def layer1_observables():
    """Session-scoped Layer1_Observables registry."""
    from apeiron.layers.layer01_foundational.observables import Layer1_Observables
    return Layer1_Observables()


# ============================================================================
# Function-scoped fixtures (vers per test)
# ============================================================================

@pytest.fixture
def fresh_meta_spec():
    """Een verse MetaSpecification per test - gebruik als je de spec wilt muteren."""
    from apeiron.layers.layer01_foundational.meta_spec import MetaSpecification
    return MetaSpecification()


@pytest.fixture
def custom_meta_spec():
    """Alias voor fresh_meta_spec (backwards compatibel)."""
    from apeiron.layers.layer01_foundational.meta_spec import MetaSpecification
    return MetaSpecification()


@pytest.fixture
def simple_observable():
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
def density_field():
    from apeiron.layers.layer01_foundational.density_field import DensityField
    return DensityField()


@pytest.fixture
def evolutionary_loop(fresh_meta_spec):
    from apeiron.layers.layer01_foundational.discovery import EvolutionaryFeedbackLoop
    return EvolutionaryFeedbackLoop(fresh_meta_spec)


# ============================================================================
# Core framework fixtures
# ============================================================================

@pytest.fixture
def event_bus():
    from apeiron.core.event_bus import EventBus, EventBusConfig
    config = EventBusConfig(
        node_id="test_node",
        enable_persistence=False,
        enable_distributed=False,
    )
    return EventBus(config)


@pytest.fixture
async def running_event_bus(event_bus) -> AsyncGenerator:
    event_bus.start()
    yield event_bus
    await event_bus.stop()


@pytest.fixture
def layer_config():
    from apeiron.core.base import LayerConfig, LayerType
    return LayerConfig(
        layer_id="test_layer",
        layer_type=LayerType.FOUNDATIONAL,
    )


@pytest.fixture
def mock_hardware_backend():
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.initialize.return_value = True
    mock.process.return_value = "mock_result"
    mock.get_info.return_value = {"name": "MockBackend"}
    return mock


# ============================================================================
# Asyncio
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Data fixtures
# ============================================================================

@pytest.fixture(scope="session")
def synthetic_two_groups():
    rng = np.random.default_rng(42)
    n_samples, n_features = 200, 64
    X = np.zeros((n_samples, n_features))
    X[:100, :32] = rng.random((100, 32)) * 0.8 + 0.1
    X[100:, 32:] = rng.random((100, 32)) * 0.8 + 0.1
    y = np.array([0] * 100 + [1] * 100)
    return X, y


@pytest.fixture(scope="session")
def coactivation_matrix(synthetic_two_groups):
    X, _ = synthetic_two_groups
    corr = np.corrcoef(X.T)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 0)
    corr[corr < 0] = 0
    return corr


# ============================================================================
# Hardware fixtures
# ============================================================================

@pytest.fixture
def cpu_backend():
    try:
        from apeiron.hardware.backends import CPUBackend
        backend = CPUBackend()
        backend.initialize({})
        return backend
    except ImportError:
        pytest.skip("Hardware module not available")


@pytest.fixture
def hardware_factory():
    try:
        from apeiron.hardware.factory import HardwareFactory
        return HardwareFactory()
    except ImportError:
        pytest.skip("Hardware factory not available")


# ============================================================================
# Self-proving fixtures
# ============================================================================

@pytest.fixture
def self_proving_observable():
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
    try:
        import sympy
        return True
    except ImportError:
        return False


@pytest.fixture
def has_z3():
    try:
        import z3
        return True
    except ImportError:
        return False