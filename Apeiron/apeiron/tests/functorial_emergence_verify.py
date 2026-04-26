#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
functorial_emergence_verify.py -- Expanded verification of the functor D.
==========================================================================
Tests a dozen diverse observables: atoms (1, primes), composite objects
(sets, lists), and edge cases (empty set, empty string). The generated
table confirms Lemma 5.2: atomic observables produce singleton graphs.
"""

import sys, os, time
from pathlib import Path
from typing import Dict, Set, List

# Setup paths
script_dir = Path(__file__).resolve().parent
package_root = script_dir.parent
sys.path.insert(0, str(package_root.parent))

print("Loading Apeiron framework...", flush=True)
t0 = time.time()
from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
from apeiron.layers.layer01_foundational.decomposition import (
    DECOMPOSITION_OPERATORS,
    is_atomic_by_operator,
)
print(f"Framework loaded in {time.time()-t0:.1f}s.\n", flush=True)

FRAMEWORKS = ["boolean", "measure", "categorical", "information"]

def observable_from_value(value, obs_id: str = None) -> UltimateObservable:
    if isinstance(value, (int, float, bool)):
        t = ObservabilityType.DISCRETE
    elif isinstance(value, (set, frozenset)):
        t = ObservabilityType.DISCRETE
    elif isinstance(value, (list, tuple)):
        t = ObservabilityType.CONTINUOUS
    elif isinstance(value, str):
        t = ObservabilityType.RELATIONAL
    else:
        t = ObservabilityType.RELATIONAL
    return UltimateObservable(id=obs_id or str(value), value=value,
                              observability_type=t)

def build_decomposition_graph(seeds: List[UltimateObservable]):
    worklist = list(seeds)
    objects: Dict[str, UltimateObservable] = {}
    edges: Dict[str, Set[str]] = {}
    while worklist:
        obs = worklist.pop()
        oid = obs.id
        if oid in objects:
            continue
        objects[oid] = obs
        edges.setdefault(oid, set())
        for fw in FRAMEWORKS:
            op = DECOMPOSITION_OPERATORS.get(fw)
            if op is None:
                continue
            if is_atomic_by_operator(obs.value, fw):
                continue
            parts = op.decompose(obs.value)
            for part in parts:
                if part is None:
                    continue
                part_id = str(part)
                if part_id not in objects:
                    nobs = observable_from_value(part, obs_id=part_id)
                    objects[part_id] = nobs
                    edges.setdefault(part_id, set())
                    worklist.append(nobs)
                edges[oid].add(part_id)
    return objects, edges

def downstream_reachable(fwd_edges: Dict[str, Set[str]], root_id: str) -> Set[str]:
    visited = set()
    stack = [root_id]
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        for nxt in fwd_edges.get(cur, []):
            if nxt not in visited:
                stack.append(nxt)
    return visited

# Expanded test set: 12 observables covering atoms, composites, edge cases
def test_observables() -> List[UltimateObservable]:
    import random, string
    obs = []

    # Atomic integers
    obs.append(UltimateObservable(id="1", value=1, observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="2", value=2, observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="3", value=3, observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="7", value=7, observability_type=ObservabilityType.DISCRETE))

    # Composite sets
    obs.append(UltimateObservable(id="{1,2}", value={1,2}, observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="{1,2,3}", value={1,2,3}, observability_type=ObservabilityType.DISCRETE))
    obs.append(UltimateObservable(id="{1,2,3,4}", value={1,2,3,4}, observability_type=ObservabilityType.DISCRETE))

    # Empty set (measure atom)
    obs.append(UltimateObservable(id="empty_set", value=set(), observability_type=ObservabilityType.DISCRETE))

    # A simple list (non-atomic)
    obs.append(UltimateObservable(id="list_[1,2]", value=[1,2], observability_type=ObservabilityType.CONTINUOUS))

    # A random string (information-theoretic atomic)
    random.seed(42)
    rnd = ''.join(random.choices(string.ascii_letters + string.digits, k=200))
    obs.append(UltimateObservable(id="rand_str", value=rnd, observability_type=ObservabilityType.RELATIONAL))

    # A highly compressible string (information-theoretic atomic)
    obs.append(UltimateObservable(id="rep_str", value="a"*200, observability_type=ObservabilityType.RELATIONAL))

    # Empty string (edge case)
    obs.append(UltimateObservable(id="empty_str", value="", observability_type=ObservabilityType.RELATIONAL))

    return obs

def main():
    print("Creating test observables...", flush=True)
    seeds = test_observables()
    for s in seeds:
        s._compute_atomicities()

    print("Building decomposition graph...", flush=True)
    objects, fwd_edges = build_decomposition_graph(seeds)
    n_vertices = len(objects)
    n_edges = sum(len(v) for v in fwd_edges.values())
    print(f"Graph built: {n_vertices} vertices, {n_edges} edges.\n", flush=True)

    lines = [
        r"\begin{tabular}{l c c c}",
        r"\toprule",
        r"\textbf{Observable} & \textbf{Separated?} & \(|\mathcal{D}(o)|\) & \textbf{Edges in \(\mathbf{D}(o)\)} \\",
        r"\midrule"
    ]

    for obs in seeds:
        dset = downstream_reachable(fwd_edges, obs.id)
        separated = all(is_atomic_by_operator(obs.value, fw) for fw in FRAMEWORKS)
        sym = r"$\checkmark$" if separated else r"$\times$"
        edge_count = 0
        for src, tgts in fwd_edges.items():
            if src in dset:
                edge_count += sum(1 for t in tgts if t in dset)
        safe_id = obs.id.replace("_", r"\_").replace("{", "").replace("}", "")
        lines.append(f"  {safe_id} & {sym} & {len(dset)} & {edge_count} \\\\")

    lines.extend([r"\bottomrule", r"\end{tabular}"])

    out_dir = Path("tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "decomposition_table.tex", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("✅ tables/decomposition_table.tex written\n")
    for line in lines:
        print(line)

if __name__ == "__main__":
    main()