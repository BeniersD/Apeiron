#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
save_proofs.py -- Export generated Lean/Coq proofs for manual inspection
=======================================================================
Creates .lean and .v files for a few key observables so that the generated
proof scripts can be reviewed (and, if desired, compiled) offline.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
from apeiron.layers.layer01_foundational.self_proving import add_self_proving_capability


def save_proofs(value, filename_prefix):
    obs = UltimateObservable(
        id="test", value=value,
        observability_type=ObservabilityType.DISCRETE
    )
    prover = add_self_proving_capability(obs)

    lean_code = prover._generate_lean_proof("boolean")
    coq_code = prover._generate_coq_proof("boolean")

    lean_file = f"{filename_prefix}_lean.lean"
    coq_file  = f"{filename_prefix}_coq.v"

    with open(lean_file, "w", encoding="utf-8") as f:
        f.write(lean_code)
    with open(coq_file, "w", encoding="utf-8") as f:
        f.write(coq_code)

    print(f"Generated {lean_file} and {coq_file}")


def main():
    print("=== Saving generated Lean/Coq proofs ===\n")
    save_proofs(1,                      "proof_one")
    save_proofs(2,                      "proof_prime2")
    save_proofs(6,                      "proof_composite6")
    save_proofs(frozenset({1}),         "proof_singleton_set")
    save_proofs(frozenset({1, 2}),      "proof_pair_set")
    print("\nDone. Inspect the .lean and .v files manually.")


if __name__ == "__main__":
    main()