#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
categorical_verification.py – Genuine Apeiron Category Verification (v2)
==========================================================================
Fix: morphism‑counting now recognises that the identity morphism of an
object is unique, irrespective of how many atomicity frameworks it comes
from.  The zero‑object test therefore correctly reports the theoretical
predictions.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import hashlib
import time

# ---- 1. Path & imports ---------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
from apeiron.layers.layer01_foundational.decomposition import (
    DECOMPOSITION_OPERATORS,
    is_atomic_by_operator,
)

# ---- 2. Helpers -----------------------------------------------------------

def make_id(raw_value: Any) -> str:
    rep = repr(raw_value)
    h = hashlib.md5(rep.encode()).hexdigest()[:8]
    return f"part_{h}"

def observable_from_value(value: Any, obs_id: str = None) -> UltimateObservable:
    if isinstance(value, (int, float, bool)):
        t = ObservabilityType.DISCRETE
    elif isinstance(value, (set, frozenset)):
        t = ObservabilityType.DISCRETE
    elif isinstance(value, str):
        t = ObservabilityType.RELATIONAL
    elif isinstance(value, list):
        t = ObservabilityType.CONTINUOUS
    else:
        t = ObservabilityType.RELATIONAL
    return UltimateObservable(id=obs_id or make_id(value), value=value,
                              observability_type=t)

def flatten_parts(parts: List[Any]) -> Set[Any]:
    result = set()
    for p in parts:
        if isinstance(p, (list, tuple, set, frozenset)):
            result.update(flatten_parts(list(p)))
        else:
            result.add(p)
    return result

# ---- 3. Category and closure ----------------------------------------------

FRAMEWORKS = ["boolean", "measure", "categorical", "information"]

def closure_of(seed: UltimateObservable) -> Dict[str, UltimateObservable]:
    worklist = [seed]
    objects = {seed.id: seed}
    while worklist:
        obs = worklist.pop()
        for fw in FRAMEWORKS:
            op = DECOMPOSITION_OPERATORS.get(fw)
            if op is None:
                continue
            if is_atomic_by_operator(obs.value, fw):
                continue
            parts = op.decompose(obs.value)
            for v in flatten_parts(parts):
                if v is None:
                    continue
                nid = make_id(v)
                if nid not in objects:
                    new_obs = observable_from_value(v, obs_id=nid)
                    objects[nid] = new_obs
                    worklist.append(new_obs)
    return objects

def has_non_identity_morphism(source: UltimateObservable,
                              target: UltimateObservable,
                              fw: str) -> bool:
    """True iff a non‑identity morphism exists from source to target via fw."""
    if source.id == target.id:
        return False                     # identity is handled separately
    op = DECOMPOSITION_OPERATORS.get(fw)
    if op is None:
        return False
    parts = op.decompose(source.value)
    flat = flatten_parts(parts)
    return target.value in flat

def count_morphisms(source: UltimateObservable, target: UltimateObservable) -> int:
    """
    Return 1 if exactly one morphism (possibly identity) exists, 0 or >1 otherwise.
    Identity counts exactly once, regardless of how many frameworks make the
    object atomic.
    """
    # Check identity
    if source.id == target.id:
        # identity exists iff source is atomic in AT LEAST ONE framework
        if any(is_atomic_by_operator(source.value, fw) for fw in FRAMEWORKS):
            # but there must be NO non‑identity paths to the same object
            for fw in FRAMEWORKS:
                if has_non_identity_morphism(source, target, fw):
                    return 2               # two distinct morphisms — not allowed
            return 1                       # exactly the identity
        return 0

    # non‑identity case
    count = 0
    for fw in FRAMEWORKS:
        if has_non_identity_morphism(source, target, fw):
            count += 1
    return count

def is_separated_in_closure(seed: UltimateObservable) -> bool:
    obs_dict = closure_of(seed)
    obs_list = list(obs_dict.values())
    # must have NO morphism from seed to any other object
    for target in obs_list:
        if target.id == seed.id:
            continue
        if count_morphisms(seed, target) > 0:
            return False
    return True


# ---- 4. Test observables and table ----------------------------------------

def test_observables() -> List[UltimateObservable]:
    import random, string
    obs = []
    obs.append(UltimateObservable(id="o1", value=1,
                                  observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="o_set_2", value={1,2},
                                  observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="o_prime_7", value=7,
                                  observability_type=ObservabilityType.DISCRETE))
    random.seed(42)
    rnd = ''.join(random.choices(string.ascii_letters + string.digits, k=200))
    obs.append(UltimateObservable(id="o_random_str", value=rnd,
                                  observability_type=ObservabilityType.RELATIONAL))
    return obs

def benchmark_overhead(observables, iterations=100):
    """Meet de gemiddelde verificatietijd per observable (ms)."""
    results = []
    for obs in observables:
        start = time.perf_counter()
        for _ in range(iterations):
            _ = is_separated_in_closure(obs)
        elapsed = (time.perf_counter() - start) / iterations * 1000  # ms
        results.append((obs.id, elapsed))
    # wegschrijven
    with open("tables/overhead_benchmark.txt", "w", encoding="utf-8") as f:
        for obs_id, t in results:
            f.write(f"{obs_id}: {t:.2f} ms\n")
    print("Benchmark geschreven naar tables/overhead_benchmark.txt")
    for obs_id, t in results:
        print(f"  {obs_id}: {t:.2f} ms")
    return results

def main():
    observables = test_observables()
    for o in observables:
        o._compute_atomicities()

    lines = [
        r"\begin{tabular}{l c c c c c}",
        r"\toprule",
        r"\textbf{Observable} & \textbf{Boolean} & \textbf{Measure} & \textbf{Category} & \textbf{Information} & \textbf{Separated?} \\"
        r"\midrule"
    ]

    for obs in observables:
        scores = ["1" if is_atomic_by_operator(obs.value, fw) else "0"
                  for fw in FRAMEWORKS]
        is_zero = is_separated_in_closure(obs)
        zero_sym = r"$\checkmark$" if is_zero else r"$\times$"
        lines.append(
            f"  {obs.id} & {scores[0]} & {scores[1]} & {scores[2]} & {scores[3]} & {zero_sym} \\\\"
        )

    lines.extend([r"\bottomrule", r"\end{tabular}"])

    bench = benchmark_overhead(observables, iterations=200)

    out_dir = Path("tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "cat_verification_table.tex", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("✅ tables/cat_verification_table.tex written")
    print("\n".join(lines))

if __name__ == "__main__":
    main()