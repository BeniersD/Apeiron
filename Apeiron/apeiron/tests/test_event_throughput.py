"""
Benchmark: EventBus throughput under varying payload sizes.

Measures events/s for payloads of 128 B, 1 kB, and 16 kB using the
in‑memory backend. Outputs a compact table suitable for the paper.
"""

import asyncio
import time
import sys
import os
import asyncio, time, sys, os, logging
logging.basicConfig(level=logging.DEBUG)

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.event_bus import EventBus, EventBusConfig

async def throughput_test(payload_size, n_events=5000):  # kleiner voor test
    bus = EventBus(EventBusConfig(enable_persistence=False))
    received = 0
    async def counter(event):
        nonlocal received
        received += 1
    bus.subscribe("test", counter)

    start = time.perf_counter()
    for _ in range(n_events):
        await bus.emit("test", {"data": "x" * payload_size}, source="bench")
    elapsed = time.perf_counter() - start
    return n_events / elapsed

async def main():
    print("Start throughput test...")
    for size in [128, 1024, 16384]:
        t = await throughput_test(size)
        label = f"{size} B" if size < 1024 else f"{size//1024} kB"
        print(f"{label}\t{t:.0f} events/s")
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())