#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_z3_claims.py  –  Direct verification of Z3 Boolean atomicity
==================================================================
Runs the Z3 prover outside the Apeiron pipeline to confirm it
correctly classifies primes/composites and sets as atomic/non‑atomic.
"""

import sys
from pathlib import Path

# Add project root to sys.path (same method as benchmark_atomicity.py)
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apeiron.layers.layer01_foundational.self_proving import AtomicityTheoremGenerator
from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
import z3


def check_z3_boolean(value, expected_is_atom):
    obs = UltimateObservable(
        id="verify", value=value,
        observability_type=ObservabilityType.DISCRETE
    )
    gen = AtomicityTheoremGenerator()
    formula = gen.generate_z3_formula(obs, "boolean")
    solver = z3.Solver()
    solver.add(z3.Not(formula))
    result = solver.check()
    is_atom = (result == z3.unsat)

    status = "✅" if is_atom == expected_is_atom else "❌"
    print(f"{status} Z3 Boolean for {value!r}: atom={is_atom} (expected {expected_is_atom})")
    return is_atom == expected_is_atom


def main():
    print("=== Verifying Z3 Boolean atomicity ===\n")
    all_passed = True

    # Primes
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    for p in primes:
        if not check_z3_boolean(p, True):
            all_passed = False

    # Composites
    composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18]
    for c in composites:
        if not check_z3_boolean(c, False):
            all_passed = False

    # Sets
    if not check_z3_boolean(frozenset({1}), True):
        all_passed = False
    if not check_z3_boolean(frozenset({1, 2}), False):
        all_passed = False

    print("\n" + ("🎉 All Z3 claims passed." if all_passed else "❌ Some Z3 claims failed!"))
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()