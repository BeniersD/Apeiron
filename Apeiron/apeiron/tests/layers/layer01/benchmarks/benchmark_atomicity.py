#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
benchmark_atomicity.py  –  Multi‑Prover Scalability Benchmark (updated)
======================================================================
Evaluates the Apeiron Layer 1 formal verification pipeline by running
the configured theorem provers (SymPy, Z3, Lean 4, Coq) on a diverse
suite of test observables: prime numbers, composite numbers, finite sets,
and repetitive strings.  For each observable and for each atomicity
framework, the script records whether each prover succeeded, failed,
or timed out, together with the execution time in milliseconds.

Outputs
-------
• ``benchmark_results.csv`` : full raw data for all tested observables.
• ``benchmark_table.tex``   : LaTeX table excerpt with proof times and
  one‑letter status codes (S=success, F=fail, T=timeout).

The script uses a thread pool to parallelise framework‑level verification
and respects the configured timeout (default 5000 ms per prover).

Requirements
------------
- ``apeiron`` package (Layer 1) with the corrected ``self_proving.py``.
- Optional: ``sympy``, ``z3``, ``lean``, ``coq`` executables.
"""

import sys
import time
import csv
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# 1.  Make the project root importable
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ---------------------------------------------------------------------------
# 2.  Apeiron imports
# ---------------------------------------------------------------------------
from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
from apeiron.layers.layer01_foundational.self_proving import (
    TheoremProverType,
    add_self_proving_capability,
)

# ---------------------------------------------------------------------------
# 3.  Prover discovery
# ---------------------------------------------------------------------------
def discover_provers() -> List[TheoremProverType]:
    """
    Return a list of ``TheoremProverType`` values for which the required
    Python library (SymPy, Z3) or external compiler (Lean 4, Coq) is
    available on this machine.
    """
    provers: List[TheoremProverType] = [TheoremProverType.SYMPY]   # always present

    try:
        import z3                                                      # noqa: F401
        provers.append(TheoremProverType.Z3)
    except ImportError:
        pass

    from apeiron.layers.layer01_foundational.self_proving import (
        LEAN_AVAILABLE,
        COQ_AVAILABLE,
    )
    if LEAN_AVAILABLE:
        provers.append(TheoremProverType.LEAN)
    if COQ_AVAILABLE:
        provers.append(TheoremProverType.COQ)

    return provers


# ---------------------------------------------------------------------------
# 4.  Test case generators
# ---------------------------------------------------------------------------
def generate_prime_numbers(count: int) -> List[int]:
    """Return the first *count* prime numbers."""
    primes: List[int] = []
    candidate: int = 2
    while len(primes) < count:
        is_prime = True
        for p in primes:
            if p * p > candidate:
                break
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes


def generate_composite_numbers(count: int) -> List[int]:
    """Return *count* composite numbers, each the product of two consecutive primes."""
    primes = generate_prime_numbers(count + 1)
    return [primes[i] * primes[i - 1] for i in range(1, count + 1)]


def generate_sets(max_size: int) -> List[frozenset]:
    """Return frozensets of sizes 1 .. *max_size*."""
    return [frozenset(range(size)) for size in range(1, max_size + 1)]


def generate_strings(lengths: List[int]) -> List[str]:
    """Return random ASCII strings of the given lengths."""
    import random
    import string
    random.seed(42)          # deterministic across runs
    return [
        "".join(random.choices(string.ascii_letters + string.digits, k=length))
        for length in lengths
    ]


# ---------------------------------------------------------------------------
# 5.  Benchmark runner
# ---------------------------------------------------------------------------
def benchmark_observable(
    obs: UltimateObservable,
    provers: List[TheoremProverType],
    frameworks: List[str],
    timeout_ms: int = 10000,
) -> Dict[str, Any]:
    """
    Run every *prover* on every *framework* for a single observable.

    Returns a dictionary with keys ``observable_id``, ``observable_type``,
    ``value_summary``, and then for each framework a sub‑dict mapping
    prover name to ``{'status': ..., 'time_ms': ..., 'verified_by': ...}``.

    Frameworks are executed in parallel using a thread pool.
    """
    obs._compute_atomicities()

    result: Dict[str, Any] = {
        "observable_id": obs.id,
        "observable_type": obs.observability_type.value,
        "value_summary": repr(obs.value)[:50],
    }

    def prove_one_framework(fw: str) -> Tuple[str, Dict[str, Dict]]:
        """Prove atomicity in *fw* with all provers (sequential)."""
        prover = add_self_proving_capability(obs)
        prover.clear_cache()                            # fresh state
        fw_results: Dict[str, Dict] = {}

        for prv in provers:
            start = time.perf_counter()
            try:
                proof = prover.prove_atomicity(
                    fw, provers=[prv], timeout_ms=timeout_ms, use_cache=False
                )
                elapsed = time.perf_counter() - start
                status = "success" if proof.is_verified() else "failed"
                fw_results[prv.value] = {
                    "status": status,
                    "time_ms": elapsed * 1000.0,
                    "verified_by": proof.verified_by if proof else [],
                }
            except Exception as exc:
                elapsed = time.perf_counter() - start
                fw_results[prv.value] = {
                    "status": f"error: {exc}",
                    "time_ms": elapsed * 1000.0,
                    "verified_by": [],
                }
            if elapsed > timeout_ms / 1000:
                fw_results[prv.value]["status"] = "timeout"

        return fw, fw_results

    # Parallelise over frameworks
    with ThreadPoolExecutor(max_workers=min(len(frameworks), 8)) as executor:
        futures = {
            executor.submit(prove_one_framework, fw): fw for fw in frameworks
        }
        for future in as_completed(futures):
            fw, res = future.result()
            result[fw] = res

    return result


# ---------------------------------------------------------------------------
# 6.  Main program
# ---------------------------------------------------------------------------
def main() -> None:
    """Execute the benchmark and write CSV + LaTeX table."""

    print("Apeiron Multi‑Prover Benchmark")
    print("=" * 60)

    output_csv = "benchmark_results.csv"
    output_tex = "benchmark_table.tex"

    # Detect available provers
    provers = discover_provers()
    print(f"Provers: {[p.value for p in provers]}")

    # Frameworks to test
    frameworks = ["boolean", "measure", "category", "info"]

    # Build test suite
    observables: List[UltimateObservable] = []

    for i, p in enumerate(generate_prime_numbers(20)):
        observables.append(
            UltimateObservable(
                id=f"prime_{i}", value=p,
                observability_type=ObservabilityType.DISCRETE,
            )
        )

    for i, c in enumerate(generate_composite_numbers(10)):
        observables.append(
            UltimateObservable(
                id=f"composite_{i}", value=c,
                observability_type=ObservabilityType.DISCRETE,
            )
        )

    for s in generate_sets(10):
        observables.append(
            UltimateObservable(
                id=f"set_{len(s)}", value=s,
                observability_type=ObservabilityType.DISCRETE,
            )
        )

    lengths = [10, 50, 100, 500, 1000, 5000, 10000]
    for length in lengths:
        observables.append(
            UltimateObservable(
                id=f"rep_string_{length}", value="a" * length,
                observability_type=ObservabilityType.RELATIONAL,
            )
        )

    print(f"Test suite contains {len(observables)} observables.\n")

    # Run benchmarks
    results: List[Dict[str, Any]] = []
    for obs in observables:
        print(f"Benchmarking {obs.id} ({obs.observability_type.value}) ...")
        res = benchmark_observable(obs, provers, frameworks, timeout_ms=5000)
        results.append(res)

    # ------------------------------------------------------------------
    # 7.  CSV export
    # ------------------------------------------------------------------
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["observable_id", "observable_type", "value_summary"]
        for fw in frameworks:
            for prv in provers:
                fieldnames.append(f"{fw}_{prv.value}_status")
                fieldnames.append(f"{fw}_{prv.value}_time_ms")
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {
                "observable_id": r["observable_id"],
                "observable_type": r["observable_type"],
                "value_summary": r["value_summary"],
            }
            for fw in frameworks:
                for prv in provers:
                    data = r[fw].get(prv.value, {})
                    row[f"{fw}_{prv.value}_status"] = data.get("status", "N/A")
                    row[f"{fw}_{prv.value}_time_ms"] = data.get("time_ms", 0)
            writer.writerow(row)
    print(f"\nFull results written to {output_csv}")

    # ------------------------------------------------------------------
    # 8.  LaTeX table (excerpt, now with all 4 provers)
    # ------------------------------------------------------------------
    provers_for_table = ["sympy", "z3", "lean", "coq"]
    with open(output_tex, "w", encoding="utf-8") as texfile:
        texfile.write(r"""
\begin{table}[htbp]
\centering
\caption{Multi‑prover benchmark: proof times (ms) and status for selected observables.
         S=success, F=failed, T=timeout.}
\label{tab:benchmark}
\begin{tabular}{l c c c c c}
\toprule
\textbf{Observable} & \textbf{Framework} & \textbf{SymPy} & \textbf{Z3} & \textbf{Lean} & \textbf{Coq} \\
\midrule
"""
        )
        for r in results[:5]:
            for fw in frameworks:
                cells = []
                for p in provers_for_table:
                    t = r[fw].get(p, {}).get("time_ms", "N/A")
                    s = r[fw].get(p, {}).get("status", "?")[0].upper()  # first letter
                    if isinstance(t, (int, float)) and t < 5000:
                        cells.append(f"{t:.1f} {s}")
                    else:
                        cells.append("T" if s == "T" else "F")
                texfile.write(
                    f"{r['observable_id']} & {fw} & "
                    + " & ".join(cells) + r" \\"
                    + "\n"
                )
        texfile.write(r"""
\bottomrule
\end{tabular}
\end{table}
""")
    print(f"LaTeX table excerpt written to {output_tex}")


if __name__ == "__main__":
    main()