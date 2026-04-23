# -*- coding: utf-8 -*-
import sys, json, logging
from pathlib import Path

logging.getLogger("apeiron").setLevel(logging.ERROR)

# project root toevoegen
project_root = Path(__file__).resolve().parent
while not (project_root / "apeiron").exists():
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
from apeiron.layers.layer01_foundational.self_proving import (
    add_self_proving_capability,
    TheoremProverType,
)

# ------------------------------------------------------------
# 1. Observables en provers
# ------------------------------------------------------------
obs = UltimateObservable(
    id="one",
    value=1,
    observability_type=ObservabilityType.DISCRETE,
)
obs._compute_atomicities()
prover = add_self_proving_capability(obs)

provers = [TheoremProverType.SYMPY]
if __import__("importlib").util.find_spec("z3"):
    provers.append(TheoremProverType.Z3)
if Path(r"C:\Users\DIAG_LP\.elan\bin\lean.exe").exists():
    provers.append(TheoremProverType.LEAN)
if Path(r"C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe").exists():
    provers.append(TheoremProverType.COQ)

print(f"Actieve provers: {[p.value for p in provers]}")

# ------------------------------------------------------------
# 2. Verificatie Boolean atomicity
# ------------------------------------------------------------
if TheoremProverType.Z3 in provers:
    try:
        formula = prover.theorem_generator.generate_z3_formula(obs, "boolean")
        print("Z3 formula:", formula)
        import z3
        s = z3.Solver()
        s.add(z3.Not(formula))
        print("Z3 check:", s.check())
    except Exception as e:
        print("Z3 error:", e)

proof = prover.prove_atomicity("boolean", provers=provers, timeout_ms=30000)
cert = proof.to_certificate()
print(cert)

# Opslaan als JSON
with open("true_certificate_boolean.json", "w", encoding="utf-8") as f:
    f.write(cert)
print("✅ Echt certificaat opgeslagen als true_certificate_boolean.json")