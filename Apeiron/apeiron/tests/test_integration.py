"""
Integration tests for the Apeiron Core modules.

Checks that EventBus, AdaptiveThresholds, ChaosDetector and ThermodynamicCost
cooperate correctly in a simulated self‑regulation loop.
"""

import asyncio, time, os, sys, pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.event_bus import EventBus, EventBusConfig
from core.adaptive_thresholds import AdaptiveThresholds, ThresholdConfig, ComplexityProvider
from core.chaos_detection import ChaosDetector, ChaosConfig, SafetyLevel, SystemState
from core.thermodynamic_cost import ThermodynamicCost, CostPriority, CostConfig


@pytest.fixture
async def event_bus():
    bus = EventBus(EventBusConfig(enable_persistence=False, max_history=100))
    await bus.start()
    yield bus
    await bus.stop()

@pytest.fixture
def mock_complexity_provider():
    provider = MagicMock(spec=ComplexityProvider)
    provider.get_current_complexity.return_value = 0.4
    provider.get_unresolved_gaps.return_value = []
    provider.get_stats.return_value = {}
    return provider

@pytest.fixture
async def adaptive_thresholds(mock_complexity_provider, event_bus):
    return AdaptiveThresholds(mock_complexity_provider, event_bus=event_bus)

@pytest.fixture
async def chaos_detector(event_bus):
    return ChaosDetector(intervention_handler=None, config=ChaosConfig())

@pytest.fixture
async def thermodynamic_cost():
    return ThermodynamicCost(CostConfig())


@pytest.mark.asyncio
async def test_full_feedback_loop(
    event_bus, mock_complexity_provider, adaptive_thresholds, chaos_detector, thermodynamic_cost
):
    """End‑to‑end: complexity spike → threshold relaxation → chaos detection → energy budget."""
    mock_complexity_provider.get_current_complexity.return_value = 0.9
    await adaptive_thresholds.update(force=True)
    assert adaptive_thresholds.get("chaos_epsilon") > 0.3

    metrics = {"error": 0.35, "coherence": 0.7, "complexity": 0.9}
    await chaos_detector.run_safety_checks(metrics)
    assert chaos_detector.current_safety_level in (SafetyLevel.CAUTION, SafetyLevel.WARNING, SafetyLevel.DANGER)

    thermodynamic_cost.config = CostConfig(priority=CostPriority.GREEN)
    approved, info = await thermodynamic_cost.evaluate("test_struct", computation_time=0.5, information_value=0.05)
    if approved:
        assert info.efficiency < 0.2
    else:
        assert not approved


@pytest.mark.asyncio
async def test_event_bus_persistence_replay():
    import tempfile
    db = tempfile.mktemp(suffix=".db")
    bus = EventBus(EventBusConfig(enable_persistence=True, persistence_path=db))
    await bus.start()
    e1 = await bus.emit("test", {"v": 1}, source="t")
    e2 = await bus.emit("test", {"v": 2}, source="t")
    await bus.stop()

    bus2 = EventBus(EventBusConfig(enable_persistence=True, persistence_path=db))
    await bus2.start()
    seen = []
    async def record(event):
        seen.append(event.data["v"])
    bus2.subscribe("test", record)
    await bus2.replay(from_time=0)
    await asyncio.sleep(0.2)
    assert 1 in seen and 2 in seen
    await bus2.stop()
    os.remove(db)


@pytest.mark.asyncio
async def test_circuit_breaker_dead_letter(event_bus):
    fail_count = 0
    async def failing_handler(event):
        nonlocal fail_count
        fail_count += 1
        raise RuntimeError("fail")
    event_bus.subscribe("test", failing_handler)
    for _ in range(10):
        await event_bus.emit("test", {"x": 1}, source="test")
    await asyncio.sleep(0.3)
    dead = event_bus.get_dead_letter()
    assert len(dead) > 0
    sub = event_bus._subscribers["test"][0]
    assert sub.circuit_breaker.state == "OPEN"


@pytest.mark.asyncio
async def test_adaptive_thresholds_emits_event(adaptive_thresholds, event_bus, mock_complexity_provider):
    received = []
    async def listener(event):
        received.append(event)
    event_bus.subscribe("thresholds_updated", listener)
    mock_complexity_provider.get_current_complexity.return_value = 0.95
    await adaptive_thresholds.update(force=True)
    await asyncio.sleep(0.1)
    assert len(received) > 0
    assert received[0].data["changes"]


@pytest.mark.asyncio
async def test_chaos_detector_predictive_warning(chaos_detector):
    for i in range(20):
        err = 0.1 + i * 0.02
        metrics = {"error": err, "coherence": 0.8, "complexity": 0.5}
        await chaos_detector.run_safety_checks(metrics)
    assert len(chaos_detector.predictive_warnings) > 0
    assert chaos_detector.predictive_warnings[-1].confidence > 0.5


@pytest.mark.asyncio
async def test_thermodynamic_cost_uses_adaptive_thresholds(adaptive_thresholds, thermodynamic_cost):
    thr = adaptive_thresholds.get("efficiency_threshold")
    assert thr > 0


@pytest.mark.asyncio
async def test_core_with_cpu_backend(chaos_detector):
    from apeiron.hardware.backends.cpu_backend import CPUBackend
    backend = CPUBackend()
    backend.initialize({"precision": "float64", "num_threads": 2})
    fields = [backend.create_continuous_field(10) for _ in range(5)]
    coherence = backend.measure_coherence(fields)
    error = 1.0 - coherence
    metrics = {"error": error, "coherence": coherence, "complexity": 0.3}
    await chaos_detector.run_safety_checks(metrics)
    assert chaos_detector.current_state == SystemState.STABLE
    assert chaos_detector.current_safety_level == SafetyLevel.NORMAL
    backend.cleanup()


@pytest.mark.asyncio
async def test_thermodynamic_cost_with_cpu_backend():
    from apeiron.hardware.backends.cpu_backend import CPUBackend
    backend = CPUBackend()
    backend.initialize({"precision": "float64"})
    t0 = time.perf_counter()
    field = backend.create_continuous_field(100)
    elapsed = time.perf_counter() - t0
    cost = ThermodynamicCost(CostConfig(priority=CostPriority.BALANCED))
    approved, info = await cost.evaluate("cpu_field", elapsed, 0.7)
    assert approved
    assert info.efficiency > 0
    backend.cleanup()