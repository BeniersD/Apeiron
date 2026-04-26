# -*- coding: utf-8 -*-
"""
generate_real_certificates.py  –  Real multi‑prover certificates (v2)
========================================================================
Now proves atomicity for two observables (integer 1, singleton set {1})
using the optimised prover with parallel execution, retries, and caching.
"""

import sys, json, logging
from pathlib import Path

logging.getLogger("apeiron").setLevel(logging.ERROR)

project_root = Path(__file__).resolve().parent
while not (project_root / "apeiron").exists():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable, ObservabilityType,
)
from apeiron.layers.layer01_foundational.self_proving import (
    add_self_proving_capability, TheoremProverType,
)

# Prover discovery (same as before)
provers = [TheoremProverType.SYMPY]
if __import__("importlib").util.find_spec("z3"):
    provers.append(TheoremProverType.Z3)
if Path(r"C:\Users\DIAG_LP\.elan\bin\lean.exe").exists():
    provers.append(TheoremProverType.LEAN)
if Path(r"C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe").exists():
    provers.append(TheoremProverType.COQ)
print(f"Actieve provers: {[p.value for p in provers]}")

# Helper functie
def prove_and_save(obs, label):
    prover = add_self_proving_capability(obs)
    for fw in ["boolean", "measure", "categorical"]:
        print(f"\n=== {label} / {fw} ===")
        proof = prover.prove_atomicity(fw, provers=provers, timeout_ms=15000, parallel=True)
        cert = proof.to_certificate()
        print(cert)
        with open(f"true_certificate_{label}_{fw}.json", "w", encoding="utf-8") as f:
            f.write(cert)
        print(f"✅ true_certificate_{label}_{fw}.json opgeslagen")

# Observable 1: integer 1
obs1 = UltimateObservable(id="one", value=1, observability_type=ObservabilityType.DISCRETE)
obs1._compute_atomicities()
prove_and_save(obs1, "integer1")

# Observable 2: singleton set {1}
obs2 = UltimateObservable(id="singleton_set", value={1}, observability_type=ObservabilityType.DISCRETE)
obs2._compute_atomicities()
prove_and_save(obs2, "set_singleton")