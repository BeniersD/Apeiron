import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("Step 1: path configured", flush=True)

print("Step 2: importing irreducible_unit...", flush=True)
from apeiron.layers.layer01_foundational.irreducible_unit import UltimateObservable
print("Step 2: done", flush=True)