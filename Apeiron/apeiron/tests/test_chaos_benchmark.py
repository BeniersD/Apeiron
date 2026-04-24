"""
Competitive benchmark: Apeiron predictive warning vs. reactive threshold.

Uses a slowly increasing linear error signal (0.1 → 1.5 over 200 points).
- Reactive detector fires when value > 1.0.
- Apeiron extrapolates the trend and warns earlier.
Predictive warnings are silenced.
"""

import asyncio, logging
import numpy as np
import json

# Silence predictive warnings
logging.getLogger('chaos_detection').setLevel(logging.ERROR)

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))
from chaos_detection import ChaosDetector, ChaosConfig, SafetyLevel

N_POINTS = 200
SLOPE = (1.5 - 0.1) / N_POINTS      # 0.1 → 1.5
REACTIVE_THRESHOLD = 1.0
EPSILON_THRESHOLD = 0.7             # Apeiron threshold
PREDICTION_HORIZON = 10
NOISE = 0.02

def generate_linear_series():
    base = np.linspace(0.1, 1.5, N_POINTS)
    noise = np.random.normal(0, NOISE, N_POINTS)
    return base + noise

async def main():
    series = generate_linear_series()

    # Reactive detector
    reactive_idx = None
    for i, val in enumerate(series):
        if val > REACTIVE_THRESHOLD:
            reactive_idx = i
            break

    # Apeiron detector
    config = ChaosConfig(
        auto_intervene=False,
        emergency_shutdown=False,
        circuit_breaker_failures=1_000_000,
        circuit_breaker_timeout=0.0,
        prediction_horizon=PREDICTION_HORIZON,
        epsilon_threshold=EPSILON_THRESHOLD
    )
    detector = ChaosDetector(config=config)

    apeiron_idx = None
    for i, val in enumerate(series):
        metrics = {"error": float(val), "coherence": 0.9, "complexity": 0.5}
        await detector.run_safety_checks(metrics)
        if apeiron_idx is None and detector.current_safety_level.value > 1:  # CAUTION of hoger
            apeiron_idx = i

    # Report
    print("--- RESULTS (linearly increasing error) ---")
    print(f"Reactive threshold:        {REACTIVE_THRESHOLD}")
    print(f"Apeiron epsilon threshold: {EPSILON_THRESHOLD}")
    print(f"Reactive detector fired at point: {reactive_idx}")
    print(f"Apeiron detector fired at point:   {apeiron_idx}")

    if apeiron_idx is not None and reactive_idx is not None:
        lead = reactive_idx - apeiron_idx
        print(f"Apeiron lead time: {lead} points (positive = earlier)")
    elif apeiron_idx is not None:
        print("Apeiron was the only detector to fire.")
    else:
        print("Neither detector fired.")

    # Save data
    with open("chaos_benchmark_results.json", "w") as f:
        json.dump({
            "series": series.tolist(),
            "reactive_idx": reactive_idx,
            "apeiron_idx": apeiron_idx
        }, f, indent=2)
    print("Saved to chaos_benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())