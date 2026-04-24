"""
Generate the "Safe Operating Area" dataset.

Varies complexity (c) and energy budget (e) over a grid, computes a stability
index (1 − λ) using the ChaosDetector's Lyapunov estimator, and saves the data
to a CSV file for pgfplots.
"""

import sys
import os
import numpy as np
import csv
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.chaos_detection import ChaosDetector, ChaosConfig

def simulate_epsilon(complexity, energy):
    """Synthetic error‑epsilon influenced by complexity and energy."""
    base = complexity * 0.3 + 0.05
    noise = np.random.normal(0, 0.1 * complexity, 50)
    scale = max(0.0, 1.0 - 0.005 * energy)
    return base + scale * noise

async def compute_stability(complexity, energy, detector):
    epsilon_series = simulate_epsilon(complexity, energy)
    # Reset detector state for each test
    detector.epsilon_history.clear()
    detector.coherence_history.clear()
    detector.complexity_history.clear()
    detector.epsilon = 0.0
    for val in epsilon_series:
        metrics = {'error': val, 'coherence': 0.9, 'complexity': complexity}
        await detector.run_safety_checks(metrics)
    return max(0.0, min(1.0, 1.0 - detector.lyapunov_exponent))

async def populate_grid():
    config = ChaosConfig(
        auto_intervene=False,
        emergency_shutdown=False,
        circuit_breaker_failures=1_000_000,
        circuit_breaker_timeout=0.0,
        prediction_horizon=0
    )
    detector = ChaosDetector(config=config)
    complexities = np.linspace(0, 1, 20)
    energies = np.linspace(1, 100, 20)
    rows = []
    for c in complexities:
        for e in energies:
            stab = await compute_stability(c, e, detector)
            rows.append([c, e, stab])
    return rows

def main():
    rows = asyncio.run(populate_grid())
    with open('safe_area_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['complexity', 'energy', 'stability'])
        writer.writerows(rows)
    print(f"Safe area data written to safe_area_data.csv ({len(rows)} points)")

if __name__ == "__main__":
    main()