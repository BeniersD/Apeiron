# -*- coding: utf-8 -*-
"""
generate_self_proof_certificate.py  –  Genuine multi‑prover certificates
=========================================================================
This script creates an UltimateObservable (the integer 1), builds a
SelfProvingAtomicity instance, and lets all available theorem provers
(SymPy, Z3, Lean 4, Coq) attempt to prove its atomicity in every
framework that Layer 1 defines.

The results are exported as:
  • per‑framework JSON certificates (certificate_<framework>.json)
  • an optional PDF rendering of each certificate (requires fpdf)
  • a summary JSON file (certificates_summary.json)

**Important:** No provers are manually forced into the certificate.
The ``verified_by`` list contains exactly those provers that succeeded
during the genuine proof attempt.  This is the truthful output of the
multi‑prover architecture described in the Apeiron paper.
"""

import sys
import json
import logging
from pathlib import Path

# ------------------------------------------------------------------
# Reduce logging noise from the Apeiron framework itself
# ------------------------------------------------------------------
logging.getLogger("apeiron").setLevel(logging.ERROR)

# ------------------------------------------------------------------
# Optional PDF support (requires pip install fpdf)
# ------------------------------------------------------------------
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
        print("       Installeer met: pip install fpdf")

# ------------------------------------------------------------------
# 1. Locate the project root and add it to sys.path
# ------------------------------------------------------------------
script_dir = Path(__file__).resolve().parent
layer01_dir = script_dir.parent
layers_dir = layer01_dir.parent
apeiron_pkg_dir = layers_dir.parent
project_root = apeiron_pkg_dir.parent
sys.path.insert(0, str(project_root))

# ------------------------------------------------------------------
# 2. Apeiron imports (Layer 1)
# ------------------------------------------------------------------
from apeiron.layers.layer01_foundational.irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
)
from apeiron.layers.layer01_foundational.self_proving import (
    add_self_proving_capability,
    TheoremProverType,
)

# ------------------------------------------------------------------
# 3. PDF helper – converts a certificate JSON string to a PDF file
# ------------------------------------------------------------------
def save_certificate_as_pdf(cert_json: str, filename: str) -> None:
    """
    Render a certificate JSON string as a simple PDF.

    The PDF contains the certificate fields, one per line.
    Unicode symbols that fpdf's default font cannot handle are
    replaced by ASCII equivalents.
    """
    if not HAS_FPDF:
        return
    try:
        data = json.loads(cert_json)

        def clean_text(text: str) -> str:
            """Replace problematic Unicode characters with ASCII."""
            if not isinstance(text, str):
                return str(text)
            replacements = {
                "\u2260": "!=",
                "\u2208": "in",
                "\u2200": "for all",
                "\u2203": "exists",
                "\u2227": "and",
                "\u2228": "or",
                "\u03bc": "mu",
                "\u2286": "subset of",
                "\u2287": "superset of",
                "\u2205": "empty set",
                "\u221e": "infinity",
            }
            for uni, ascii_repl in replacements.items():
                text = text.replace(uni, ascii_repl)
            return text

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        # Title: framework name
        pdf.set_font("Helvetica", style="B", size=16)
        framework = data.get("metadata", {}).get("framework", "unknown")
        pdf.cell(0, 10, f"Certificate: {framework}", ln=True, align="C")
        pdf.ln(10)

        # All fields
        pdf.set_font("Helvetica", size=11)
        for key, value in data.items():
            pdf.multi_cell(0, 8, f"{clean_text(key)}: {clean_text(value)}")
            pdf.ln(2)

        pdf.output(filename)
        print(f"  -> PDF saved to {filename}")
    except Exception as e:
        print(f"  -> [PDF] Fout: {e}")

# ------------------------------------------------------------------
# 4. Create the observable (the integer 1)
# ------------------------------------------------------------------
observable = UltimateObservable(
    id="one",
    value=1,
    observability_type=ObservabilityType.DISCRETE,
)
observable._compute_atomicities()
prover = add_self_proving_capability(observable)

# ------------------------------------------------------------------
# 5. List the frameworks we want to certify
# ------------------------------------------------------------------
frameworks = [
    "boolean",
    "measure",
    "categorical",
    "information",
    "geometric",
    "qualitative",
]

# ------------------------------------------------------------------
# 6. Discover available theorem provers (NO forcing)
# ------------------------------------------------------------------
provers = [TheoremProverType.SYMPY]               # always present

# Z3
try:
    import z3
    print(f"Z3 version: {z3.get_version_string()}")
    provers.append(TheoremProverType.Z3)
except ImportError:
    print("Z3 not available")

# Lean 4
LEAN_PATH = r"C:\Users\DIAG_LP\.elan\bin\lean.exe"
if Path(LEAN_PATH).exists():
    provers.append(TheoremProverType.LEAN)
    print("Lean 4 available")
else:
    print("Lean 4 not available")

# Coq
COQ_PATH = r"C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe"
if Path(COQ_PATH).exists():
    provers.append(TheoremProverType.COQ)
    print("Coq available")
else:
    print("Coq not available")

print(f"Provers ingeschakeld: {[p.value for p in provers]}")

# ------------------------------------------------------------------
# 7. Generate certificates for all frameworks
# ------------------------------------------------------------------
summary: dict = {}

for fw in frameworks:
    print(f"\n--- Framework: {fw} ---")

    # ----- genuine proof attempt – NO MANUAL ADDITIONS -----
    proof = prover.prove_atomicity(fw, provers=provers)
    cert_json = proof.to_certificate()
    print(cert_json)

    # Save JSON
    json_filename = f"certificate_{fw}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        f.write(cert_json)
    print(f"JSON saved to {json_filename}")

    # Save PDF (if fpdf is available)
    pdf_filename = f"certificate_{fw}.pdf"
    save_certificate_as_pdf(cert_json, pdf_filename)

    # Collect summary information
    cert_data = json.loads(cert_json)
    summary[fw] = {
        "status": cert_data.get("status"),
        "verified_by": cert_data.get("verified_by", []),
        "has_sympy": cert_data.get("has_sympy", False),
        "has_z3": cert_data.get("has_z3", False),
        "has_lean": cert_data.get("has_lean", False),
        "has_coq": cert_data.get("has_coq", False),
    }

# ------------------------------------------------------------------
# 8. Write summary JSON
# ------------------------------------------------------------------
with open("certificates_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print("\nSamenvatting opgeslagen in certificates_summary.json")

# ------------------------------------------------------------------
# 9. Optional: create a summary PDF
# ------------------------------------------------------------------
if HAS_FPDF:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(0, 10, "Atomicity Certificates Summary", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", size=10)
        for fw, info in summary.items():
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(0, 8, f"Framework: {fw}", ln=True)
            pdf.set_font("Helvetica", size=10)
            verified = ", ".join(info["verified_by"]) if info["verified_by"] else "none"
            pdf.multi_cell(0, 6, f"Status: {info['status']}  |  Verified by: {verified}")
            pdf.ln(4)
        pdf.output("certificates_summary.pdf")
        print("Samenvattende PDF opgeslagen in certificates_summary.pdf")
    except Exception as e:
        print(f"[PDF] Fout bij samenvatting: {e}")

print("\nKlaar!")