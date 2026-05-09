# test_imports.py
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("DEBUG: sys.path configured", flush=True)

try:
    from apeiron.layers.layer01_foundational.irreducible_unit import (
        UltimateObservable,
        ObservabilityType,
    )
    print("DEBUG: imported irreducible_unit", flush=True)
except Exception as e:
    print(f"ERROR importing irreducible_unit: {e}", flush=True)

try:
    from apeiron.layers.layer01_foundational.self_proving import (
        TheoremProverType,
        add_self_proving_capability,
    )
    print("DEBUG: imported self_proving", flush=True)
except Exception as e:
    print(f"ERROR importing self_proving: {e}", flush=True)

# Test prover discovery
provers = []
try:
    import sympy
    provers.append('sympy')
    print("DEBUG: sympy available", flush=True)
except ImportError:
    print("DEBUG: sympy not available", flush=True)

try:
    import z3
    provers.append('z3')
    print("DEBUG: z3 available", flush=True)
except ImportError:
    print("DEBUG: z3 not available", flush=True)

from apeiron.layers.layer01_foundational.self_proving import LEAN_AVAILABLE, COQ_AVAILABLE
if LEAN_AVAILABLE:
    provers.append('lean')
    print("DEBUG: lean available", flush=True)
if COQ_AVAILABLE:
    provers.append('coq')
    print("DEBUG: coq available", flush=True)

print(f"DEBUG: provers = {provers}", flush=True)

# Test een minimale prover run
try:
    obs = UltimateObservable(id='test', value=1, observability_type=ObservabilityType.DISCRETE)
    obs._compute_atomicities()
    prover = add_self_proving_capability(obs)
    proof = prover.prove_atomicity('boolean', provers=[TheoremProverType.SYMPY] if 'sympy' in provers else [], timeout_ms=2000)
    print(f"DEBUG: proof status = {proof.status if proof else 'None'}", flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERROR in minimal test: {e}", flush=True)