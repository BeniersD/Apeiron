"""
Performance and overhead tests for Apeiron Core components.
"""

import asyncio, time, os, sys, pytest, numpy as np
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.event_bus import EventBus, EventBusConfig
from core.adaptive_thresholds import AdaptiveThresholds, ThresholdConfig
from core.chaos_detection import ChaosDetector, ChaosConfig
from core.thermodynamic_cost import ThermodynamicCost, CostConfig


def test_event_bus_throughput_1sub():
    N = 20_000
    async def run():
        bus = EventBus(EventBusConfig(enable_persistence=False))
        received = 0
        async def handler(event):
            nonlocal received
            received += 1
        bus.subscribe("test", handler)
        t0 = time.perf_counter()
        for _ in range(N):
            await bus.emit("test", {"data": "x"*128}, source="perf")
        t1 = time.perf_counter()
        tps = N / (t1 - t0)
        assert tps > 10_000
    asyncio.run(run())


def test_event_bus_overhead():
    N = 2_000
    async def bus_work():
        bus = EventBus(EventBusConfig(enable_persistence=False, max_queue_size=50_000))
        received = 0
        async def handler(event):
            nonlocal received
            received += 1
        bus.subscribe("test", handler)
        await bus.start()
        t0 = time.perf_counter()
        for _ in range(N):
            await bus.emit("test", {"x": 1}, source="perf")
        t1 = time.perf_counter()
        await bus.stop()
        return (t1 - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(N):
        pass
    t1 = time.perf_counter()
    baseline_ms = (t1 - t0) * 1000
    bus_ms = asyncio.run(bus_work())
    overhead = (bus_ms - baseline_ms) / baseline_ms * 100 if baseline_ms > 0 else 0
    # The bus adds some overhead, but it should be reasonable (< 10000% of a bare loop)
    assert overhead < 10000  # ensure we are not in infinite loop


def test_adaptive_thresholds_update_speed():
    provider = MagicMock()
    provider.get_current_complexity.return_value = 0.5
    provider.get_unresolved_gaps.return_value = []
    th = AdaptiveThresholds(provider)
    async def run():
        for _ in range(1000):
            await th.update(force=True)
    t0 = time.perf_counter()
    asyncio.run(run())
    assert time.perf_counter() - t0 < 2.0


def test_chaos_detector_latency_1000_cycles():
    detector = ChaosDetector(ChaosConfig())
    async def loop():
        for i in range(1000):
            metrics = {"error": 0.1 + 0.01 * (i % 50), "coherence": 0.9, "complexity": 0.5}
            await detector.run_safety_checks(metrics)
    t0 = time.perf_counter()
    asyncio.run(loop())
    assert time.perf_counter() - t0 < 1.0


def test_thermodynamic_cost_evaluation_speed():
    cost = ThermodynamicCost(CostConfig(enable_co2_tracking=False, enable_predictive=False))
    cost.monitor.measure = MagicMock(return_value=cost.monitor.measure().__class__(
        timestamp=time.time(), power_watts=50, energy_joules=0.1, source="UNKNOWN"))
    async def evaluate():
        for i in range(1000):
            await cost.evaluate(f"struct_{i}", 0.001, 0.5)
    t0 = time.perf_counter()
    asyncio.run(evaluate())
    assert time.perf_counter() - t0 < 2.0


def test_chaos_detector_false_positive_rate():
    from scipy.signal import medfilt
    np.random.seed(42)
    series = np.random.normal(0.1, 0.02, 1000)
    series[200:210] = 0.3
    series_filt = medfilt(series, kernel_size=5)
    config = ChaosConfig(auto_intervene=False, emergency_shutdown=False,
                         circuit_breaker_failures=1_000_000, circuit_breaker_timeout=0.0,
                         epsilon_threshold=0.4)
    detector = ChaosDetector(config)
    alarms = 0
    loop = asyncio.new_event_loop()
    try:
        for val in series_filt:
            metrics = {"error": float(val), "coherence": 0.95, "complexity": 0.3}
            loop.run_until_complete(detector.run_safety_checks(metrics))
            if detector.current_safety_level.value > 1:
                alarms += 1
    finally:
        loop.close()
    assert alarms < 50