#!/usr/bin/env python3
"""
Split seventeen_layers_framework.py and layers_11_to_17.py into separate layer files.
Searches for source files in current directory and in layers/ subdirectory.
Run this script from the apeiron/ directory.
"""

import os
import re
from pathlib import Path

# ====================================================================
# CONFIGURATIE
# ====================================================================
BASE_DIR = Path(".")

# Mapping: (bronbestand, klasse_naam) -> (doelmap, doelbestand)
CLASS_MAPPING = {
    # Uit seventeen_layers_framework.py
    ("seventeen_layers_framework.py", "Layer1_Observables"):      ("layers/layer01_foundational", "observables.py"),
    ("seventeen_layers_framework.py", "Layer2_Relations"):        ("layers/layer02_relational", "relations.py"),
    ("seventeen_layers_framework.py", "Layer3_Functions"):        ("layers/layer03_functional", "functions.py"),
    ("seventeen_layers_framework.py", "Layer4_Dynamics"):         ("layers/layer04_dynamics", "dynamics.py"),
    ("seventeen_layers_framework.py", "Layer5_Optimization"):     ("layers/layer05_optimization", "optimization.py"),
    ("seventeen_layers_framework.py", "Layer6_MetaLearning"):     ("layers/layer06_metalearning", "meta_learning.py"),
    ("seventeen_layers_framework.py", "Layer7_SelfAwareness"):    ("layers/layer07_selfawareness", "self_awareness.py"),
    ("seventeen_layers_framework.py", "GlobalSynthesis"):         ("layers/layer07_selfawareness", "synthesis.py"),
    ("seventeen_layers_framework.py", "Layer9_OntologicalCreation"): ("layers/layer09_ontological", "ontological_creation.py"),
    ("seventeen_layers_framework.py", "Layer10_EmergentComplexity"): ("layers/layer10_complexity", "emergent_complexity.py"),
    ("seventeen_layers_framework.py", "IntegratedHigherLayers"):  ("core", "higher_layers_wrapper.py"),
    ("seventeen_layers_framework.py", "SeventeenLayerFramework"): ("core", "framework.py"),

    # Uit layers_11_to_17.py
    ("layers_11_to_17.py", "Layer11_MetaContextualization"):      ("layers/layer11_context", "meta_contextualization.py"),
    ("layers_11_to_17.py", "Layer12_Reconciliation"):             ("layers/layer12_reconciliation", "reconciliation.py"),
    ("layers_11_to_17.py", "Layer13_Ontogenesis"):                ("layers/layer13_ontogenesis", "ontogenesis.py"),
    ("layers_11_to_17.py", "Layer14_Worldbuilding"):              ("layers/layer14_worldbuilding", "worldbuilding.py"),
    ("layers_11_to_17.py", "Layer15_EthicalConvergence"):         ("layers/layer15_responsible", "ethical_convergence.py"),
    ("layers_11_to_17.py", "DynamischeStromingenManager"):        ("layers/layer16_transcendence", "dynamic_flows.py"),
    ("layers_11_to_17.py", "AbsoluteIntegratie"):                 ("layers/layer17_absolute", "absolute_integration.py"),

    # Dataclasses
    ("layers_11_to_17.py", "Ontology"):                           ("layers/layer12_reconciliation", "ontology.py"),
    ("layers_11_to_17.py", "NovelStructure"):                     ("layers/layer13_ontogenesis", "novel_structure.py"),
    ("layers_11_to_17.py", "SimulatedWorld"):                     ("layers/layer14_worldbuilding", "simulated_world.py"),
}

# ====================================================================
# HULPFUNCTIES
# ====================================================================
def find_source_file(filename: str) -> Path:
    """Zoek naar het bronbestand in de huidige map of in de submap layers/."""
    candidates = [
        BASE_DIR / filename,
        BASE_DIR / "layers" / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None

def extract_class_code(filepath: Path, class_name: str) -> str:
    """Haal de volledige code van een klasse uit een bestand."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Zoek de class-definitie (inclusief docstring en methodes)
    pattern = rf"class {class_name}[\s\S]*?(?=\nclass |\Z)"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        raise ValueError(f"Klasse {class_name} niet gevonden in {filepath}")

    class_code = match.group(0)

    # Haal imports bovenaan het bestand op (vereenvoudigd)
    imports = re.findall(r"^(from|import) .*$", content, re.MULTILINE)
    import_block = "\n".join(imports) + "\n\n" if imports else ""

    return import_block + class_code

def write_class_to_file(class_code: str, target_path: Path):
    """Schrijf de klassecode naar het doelbestand, overschrijf eventueel."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(class_code)
    print(f"✅ {target_path}")

# ====================================================================
# HOOFDPROGRAMMA
# ====================================================================
def main():
    any_processed = False
    for (src_file, class_name), (target_dir, target_file) in CLASS_MAPPING.items():
        src_path = find_source_file(src_file)
        if src_path is None:
            print(f"⚠️ {src_file} niet gevonden in . of layers/, sla over.")
            continue

        target_path = BASE_DIR / target_dir / target_file

        try:
            code = extract_class_code(src_path, class_name)
            write_class_to_file(code, target_path)
            any_processed = True
        except ValueError as e:
            print(e)

    if any_processed:
        print("\n🎉 Splitsing voltooid! Controleer of alle bestanden goed zijn gevuld.")
        print("Vergeet niet de imports in de rest van het project aan te passen naar de nieuwe paden.")
    else:
        print("\n❌ Geen bestanden verwerkt. Controleer of de bronbestanden bestaan.")

if __name__ == "__main__":
    main()