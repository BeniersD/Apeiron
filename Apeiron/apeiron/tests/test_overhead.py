"""
Overhead benchmark – realistic micro‑workload (numpy dot product),
tested across multiple payload sizes to show scalability.

Configuration:
  - Vector dimensions: 32, 128, 512, 2048
  - Number of events per run: 500
  - Repetitions per configuration: 10

Output:
  - Console: table with mean ± std overhead (ms and µs/event)
  - JSON file: overhead_results.json
"""

import asyncio
import time
import sys
import os
import json
import numpy as np
from dataclasses import dataclass, asdict

# Import directly to avoid loading the full Apeiron framework
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))
from event_bus import EventBus, EventBusConfig

# ----------------------------------------------------------------------
# Configurable parameters
# ----------------------------------------------------------------------
VEC_SIZES = [32, 128, 512, 2048]   # vector dimensions to test
N_EVENTS = 500                     # events per repetition
N_RUNS = 10                        # repetitions per configuration

# ----------------------------------------------------------------------
# Helper to run one configuration
# ----------------------------------------------------------------------
async def measure_bus_workload(vec_size: int) -> float:
    """Process N_EVENTS events through the EventBus, each computing a dot product.
       Returns elapsed time in milliseconds."""
    # Generate fresh vectors for this run to keep work constant
    a = np.random.rand(N_EVENTS, vec_size).astype(np.float32)
    b = np.random.rand(N_EVENTS, vec_size).astype(np.float32)
    results = np.empty(N_EVENTS, dtype=np.float32)

    bus = EventBus(EventBusConfig(enable_persistence=False, max_queue_size=10_000))
    received = 0

    async def handler(event):
        nonlocal received
        idx = event.data["idx"]
        results[idx] = np.dot(a[idx], b[idx])
        received += 1

    bus.subscribe("work", handler)
    await bus.start()

    t0 = time.perf_counter()
    for i in range(N_EVENTS):
        await bus.emit("work", {"idx": i}, source="bench")
    t1 = time.perf_counter()
    await bus.stop()
    return (t1 - t0) * 1000   # ms


def direct_workload(vec_size: int) -> float:
    """Same dot‑product work, called directly without EventBus.
       Returns elapsed time in milliseconds."""
    a = np.random.rand(N_EVENTS, vec_size).astype(np.float32)
    b = np.random.rand(N_EVENTS, vec_size).astype(np.float32)
    results = np.empty(N_EVENTS, dtype=np.float32)

    t0 = time.perf_counter()
    for i in range(N_EVENTS):
        results[i] = np.dot(a[i], b[i])
    t1 = time.perf_counter()
    return (t1 - t0) * 1000   # ms


# ----------------------------------------------------------------------
# Main benchmark loop
# ----------------------------------------------------------------------
@dataclass
class ResultEntry:
    vec_size: int
    n_events: int
    direct_mean_ms: float
    direct_std_ms: float
    bus_mean_ms: float
    bus_std_ms: float
    overhead_mean_pct: float
    overhead_std_pct: float
    overhead_per_event_us: float

def main():
    print(f"Running overhead benchmark across vector sizes {VEC_SIZES}...")
    all_results = []

    for vs in VEC_SIZES:
        direct_times = []
        bus_times = []

        for run in range(N_RUNS):
            dt = direct_workload(vs)
            bt = asyncio.run(measure_bus_workload(vs))
            direct_times.append(dt)
            bus_times.append(bt)
            overhead_pct = (bt - dt) / dt * 100 if dt > 0 else float('inf')
            print(f"  size {vs:4d} run {run+1:2d}: direct {dt:.3f} ms, bus {bt:.3f} ms, overhead {overhead_pct:.1f}%")

        d_mean = np.mean(direct_times)
        d_std  = np.std(direct_times)
        b_mean = np.mean(bus_times)
        b_std  = np.std(bus_times)
        overheads = [(b - d) / d * 100 for b, d in zip(bus_times, direct_times) if d > 0]
        o_mean = np.mean(overheads)
        o_std  = np.std(overheads)
        per_event_us = (b_mean - d_mean) / N_EVENTS * 1000

        entry = ResultEntry(
            vec_size=vs,
            n_events=N_EVENTS,
            direct_mean_ms=d_mean,
            direct_std_ms=d_std,
            bus_mean_ms=b_mean,
            bus_std_ms=b_std,
            overhead_mean_pct=o_mean,
            overhead_std_pct=o_std,
            overhead_per_event_us=per_event_us
        )
        all_results.append(entry)

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'Size':>6}  {'Direct ms':>12}  {'Bus ms':>12}  {'Overhead %':>12}  {'µs/event':>10}")
    print("-" * 90)
    for e in all_results:
        print(f"{e.vec_size:>6}  {e.direct_mean_ms:>8.3f} ± {e.direct_std_ms:.3f}  "
              f"{e.bus_mean_ms:>8.3f} ± {e.bus_std_ms:.3f}  "
              f"{e.overhead_mean_pct:>7.1f} ± {e.overhead_std_pct:.1f}  "
              f"{e.overhead_per_event_us:>10.2f}")

    # Save to JSON
    output = [asdict(e) for e in all_results]
    with open("overhead_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nResults saved to overhead_results.json")

if __name__ == "__main__":
    main()