#!/usr/bin/env python3
"""
profile_cluster1.py
===================
Profiling van Cluster I:
  1) Atoomtesten (47 observables) – runtime + geheugen
  2) Clusteringpipeline (alle datasets) – runtime + geheugen
  3) Hardware‑informatie (CPU, RAM, OS, Python)
Resultaten worden getoond en opgeslagen in profile_cluster1_results.json.

Gebruik:  python profile_cluster1.py
"""

import time
import tracemalloc
import sys
import os
import json
import platform

# Optioneel: psutil voor betere hardware-info
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False

# ------------------------------------------------------------
# 0. Pad naar de package root toevoegen
# ------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
# Het script staat in de package-root (apeiron/apeiron/), dus sys.path hoeft alleen de ouder te bevatten als we willen dat "apeiron" vindbaar is.
# We voegen de huidige map toe voor de zekerheid, maar de import werkt via absolute package import.
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from experiment.run_all_experiments import DATASETS, load_data, run_method

from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable, ObservabilityType,
    boolean_atomicity, info_atomicity,
    decomposition_boolean_atomicity, decomposition_measure_atomicity
)


# ------------------------------------------------------------
# 1. Hardware-info
# ------------------------------------------------------------
def get_hardware_info():
    info = {
        "cpu": platform.processor() or "Unknown",
        "os": platform.platform(),
        "python_version": platform.python_version(),
    }
    if HAVE_PSUTIL:
        info["cpu_cores_physical"] = psutil.cpu_count(logical=False)
        info["cpu_cores_logical"] = psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        info["ram_total_gb"] = round(mem.total / (1024**3), 1)
    else:
        info["cpu_cores_physical"] = os.cpu_count()
        info["ram_total_gb"] = "unknown (install psutil)"
    return info


# ------------------------------------------------------------
# 2. Atomiciteitstests (47 observables)
# ------------------------------------------------------------
def benchmark_atomicity():
    """
    Voer de atomiciteitstests uit op een verzameling van 47 observables.
    Retourneer (runtime_sec, peak_memory_mb).
    """
    # Representatieve set
    observables = [
        (1, ObservabilityType.DISCRETE),
        (42, ObservabilityType.DISCRETE),
        (2, ObservabilityType.DISCRETE),
        (7, ObservabilityType.DISCRETE),
        (13, ObservabilityType.DISCRETE),
        (0, ObservabilityType.DISCRETE),
        (True, ObservabilityType.DISCRETE),
        (False, ObservabilityType.DISCRETE),
        ({1}, ObservabilityType.DISCRETE),
        ({1, 2, 3}, ObservabilityType.DISCRETE),
        ({'a', 'b', 'c'}, ObservabilityType.DISCRETE),
        (set(), ObservabilityType.DISCRETE),
        ("1" * 200, ObservabilityType.RELATIONAL),
        ("Apeiron", ObservabilityType.RELATIONAL),
        ("abcabcabc", ObservabilityType.RELATIONAL),
        ("x" * 500, ObservabilityType.RELATIONAL),
        ("", ObservabilityType.RELATIONAL),
        ([1.0, 0.0, 0.0], ObservabilityType.CONTINUOUS),
        ([0.5, 0.5, 0.5], ObservabilityType.CONTINUOUS),
        ([0.0, 0.0, 0.0], ObservabilityType.CONTINUOUS),
        ([1.0], ObservabilityType.CONTINUOUS),
        ([2.5, -1.2, 3.3, 1.1], ObservabilityType.CONTINUOUS),
        ([1e-10, 2e-10], ObservabilityType.CONTINUOUS),
        ([[1, 0], [0, 1]], ObservabilityType.TOPOLOGICAL),
        ([[1, 2], [3, 4]], ObservabilityType.TOPOLOGICAL),
        ([[0, 1], [1, 0]], ObservabilityType.TOPOLOGICAL),
        (3 + 4j, ObservabilityType.QUANTUM),
        (1 + 0j, ObservabilityType.QUANTUM),
        (0 + 1j, ObservabilityType.QUANTUM),
    ]
    # Aanvullen tot 47
    for i in range(17):
        observables.append((i * 7 + 1, ObservabilityType.DISCRETE))
    observables = observables[:47]

    print("=== Atomicity benchmark (47 observables) ===")
    tracemalloc.start()
    start = time.perf_counter()
    for value, otype in observables:
        obs = UltimateObservable(id="bench", value=value, observability_type=otype)
        boolean_atomicity(obs)
        decomposition_boolean_atomicity(obs)
        decomposition_measure_atomicity(obs)
        info_atomicity(obs)
    end = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    runtime = end - start
    mem_mb = peak / (1024 * 1024)
    print(f"Runtime: {runtime:.2f} s  Peak memory: {mem_mb:.1f} MB\n")
    return runtime, mem_mb


# ------------------------------------------------------------
# 3. Clusteringpipeline (alle datasets)
# ------------------------------------------------------------
def benchmark_clustering():
    """
    Voer de volledige clusteringpijplijn uit en meet runtime + peak memory.
    Retourneer (runtime_sec, peak_memory_mb).
    """
    print("=== Clustering pipeline (alle datasets) ===")
    tracemalloc.start()
    start = time.perf_counter()
    for name, cfg in DATASETS.items():
        X, y = load_data(name, cfg)
        _ = run_method(X, y, method='kmeans')
        _ = run_method(X, y, method='spectral')
        _ = run_method(X, y, method='apeiron')
    end = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    runtime = end - start
    mem_mb = peak / (1024 * 1024)
    print(f"Runtime: {runtime:.2f} s  Peak memory: {mem_mb:.1f} MB\n")
    return runtime, mem_mb


# ------------------------------------------------------------
# 4. Hoofdprogramma
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Profiling APEIRON Cluster I ...\n")

    hw_info = get_hardware_info()
    print("Hardware-omgeving:")
    for k, v in hw_info.items():
        print(f"  {k}: {v}")
    print()

    t1, m1 = benchmark_atomicity()
    t2, m2 = benchmark_clustering()

    print("=== Samenvatting ===")
    print(f"Atomicity (47 obs) : {t1:.2f} s, {m1:.1f} MB")
    print(f"Clustering (5 ds)  : {t2:.2f} s, {m2:.1f} MB")

    results = {
        "atomicity_47obs": {
            "runtime_s": round(t1, 2),
            "peak_memory_mb": round(m1, 1)
        },
        "clustering_pipeline": {
            "runtime_s": round(t2, 2),
            "peak_memory_mb": round(m2, 1)
        },
        "hardware": hw_info
    }

    with open("profile_cluster1_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResultaten opgeslagen in profile_cluster1_results.json")