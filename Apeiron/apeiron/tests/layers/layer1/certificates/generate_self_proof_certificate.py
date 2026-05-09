# -*- coding: utf-8 -*-
"""
generate_self_proof_certificate.py  –  Genuine multi‑prover certificates (v2)
===============================================================================
Creates two observables (integer 1 and singleton set {1}) and proves their
atomicity in all Layer 1 frameworks.  The new Lean/Coq generators are exercised
for measure and categorical on the singleton set.

Results are exported as JSON and PDF certificates, plus a summary.
"""

import sys
import json
import logging
from pathlib import Path

logging.getLogger("apeiron").setLevel(logging.ERROR)

# Optional PDF support
try:
    from fpdf import FPDF
    HAS_FPDF = True
    print("[OK] fpdf beschikbaar – PDF wordt gegenereerd.")
except ImportError:
    try:
        import fpdf as fpdf_module
        if hasattr(fpdf_module, "FPDF"):
            FPDF = fpdf_module.FPDF
        else:
            FPDF = fpdf_module
        HAS_FPDF = True
        print("[OK] fpdf beschikbaar (alternatieve import) – PDF wordt gegenereerd.")
    except ImportError:
        HAS_FPDF = False
        print("[INFO] fpdf niet geïnstalleerd – PDF-export overgeslagen.")

# 1. Locate project root
script_dir = Path(__file__).resolve().parent
layer01_dir = script_dir.parent
layers_dir = layer01_dir.parent
apeiron_pkg_dir = layers_dir.parent
project_root = apeiron_pkg_dir.parent
sys.path.insert(0, str(project_root))

from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable, ObservabilityType,
)
from apeiron.layers.layer01_foundational.self_proving import (
    add_self_proving_capability, TheoremProverType,
)

# 2. PDF helper
def save_certificate_as_pdf(cert_json: str, filename: str) -> None:
    if not HAS_FPDF:
        return
    try:
        data = json.loads(cert_json)
        def clean_text(text: str) -> str:
            if not isinstance(text, str):
                return str(text)
            replacements = {
                "\u2260": "!=", "\u2208": "in", "\u2200": "for all", "\u2203": "exists",
                "\u2227": "and", "\u2228": "or", "\u03bc": "mu",
                "\u2286": "subset of", "\u2287": "superset of", "\u2205": "empty set",
                "\u221e": "infinity",
            }
            for uni, ascii_repl in replacements.items():
                text = text.replace(uni, ascii_repl)
            return text
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.set_font("Helvetica", style="B", size=16)
        framework = data.get("metadata", {}).get("framework", "unknown")
        pdf.cell(0, 10, f"Certificate: {framework}", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", size=11)
        for key, value in data.items():
            pdf.multi_cell(0, 8, f"{clean_text(key)}: {clean_text(value)}")
            pdf.ln(2)
        pdf.output(filename)
        print(f"  -> PDF saved to {filename}")
    except Exception as e:
        print(f"  -> [PDF] Fout: {e}")

# 3. Prover discovery
provers = [TheoremProverType.SYMPY]
try:
    import z3
    print(f"Z3 version: {z3.get_version_string()}")
    provers.append(TheoremProverType.Z3)
except ImportError:
    print("Z3 not available")

LEAN_PATH = r"C:\Users\DIAG_LP\.elan\bin\lean.exe"
if Path(LEAN_PATH).exists():
    provers.append(TheoremProverType.LEAN)
    print("Lean 4 available")
else:
    print("Lean 4 not available")

COQ_PATH = r"C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe"
if Path(COQ_PATH).exists():
    provers.append(TheoremProverType.COQ)
    print("Coq available")
else:
    print("Coq not available")

print(f"Provers ingeschakeld: {[p.value for p in provers]}")

# 4. Frameworks
frameworks = ["boolean", "measure", "categorical", "information", "geometric", "qualitative"]

# 5. Prover functie voor één observable
def prove_observable(obs, label):
    """Run prover on all frameworks for the given observable, return summary dict."""
    prover = add_self_proving_capability(obs)
    summary = {}
    print(f"\n=== {label} ===")
    for fw in frameworks:
        print(f"\n--- Framework: {fw} ---")
        proof = prover.prove_atomicity(fw, provers=provers, timeout_ms=15000, parallel=True)
        cert_json = proof.to_certificate()
        print(cert_json)

        json_filename = f"certificate_{label}_{fw}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            f.write(cert_json)
        print(f"JSON saved to {json_filename}")

        pdf_filename = f"certificate_{label}_{fw}.pdf"
        save_certificate_as_pdf(cert_json, pdf_filename)

        cert_data = json.loads(cert_json)
        summary[f"{label}_{fw}"] = {
            "status": cert_data.get("status"),
            "verified_by": cert_data.get("verified_by", []),
            "has_sympy": cert_data.get("has_sympy", False),
            "has_z3": cert_data.get("has_z3", False),
            "has_lean": cert_data.get("has_lean", False),
            "has_coq": cert_data.get("has_coq", False),
        }
    return summary

# 6. Create observables
print("\n=== Observabelen aanmaken ===")
obs_one = UltimateObservable(id="one", value=1, observability_type=ObservabilityType.DISCRETE)
obs_one._compute_atomicities()

obs_set = UltimateObservable(id="singleton_set", value={1}, observability_type=ObservabilityType.DISCRETE)
obs_set._compute_atomicities()

# 7. Prove both
summary_all = {}
summary_all.update(prove_observable(obs_one, "integer1"))
summary_all.update(prove_observable(obs_set, "set_singleton"))

# 8. Write summary
with open("certificates_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary_all, f, indent=2)
print("\nSamenvatting opgeslagen in certificates_summary.json")

if HAS_FPDF:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(0, 10, "Atomicity Certificates Summary", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", size=10)
        for key, info in summary_all.items():
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(0, 8, f"{key}", ln=True)
            pdf.set_font("Helvetica", size=10)
            verified = ", ".join(info["verified_by"]) if info["verified_by"] else "none"
            pdf.multi_cell(0, 6, f"Status: {info['status']}  |  Verified by: {verified}")
            pdf.ln(4)
        pdf.output("certificates_summary.pdf")
        print("Samenvattende PDF opgeslagen in certificates_summary.pdf")
    except Exception as e:
        print(f"[PDF] Fout bij samenvatting: {e}")

print("\nKlaar!")