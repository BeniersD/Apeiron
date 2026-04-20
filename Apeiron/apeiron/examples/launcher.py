#!/usr/bin/env python3
"""
NEXUS ULTIMATE V12 - UNIVERSELE HARDWARE LAUNCHER
Detecteert automatisch de beste beschikbare hardware!
Gebruikt centrale hardware factory voor consistente detectie.
"""

import subprocess
import os
import sys
import time
import webbrowser
import argparse
import asyncio
import logging
from typing import Dict, List, Optional

# V12 imports
from apeiron import start_v12, OceanicNexusV12

# Hardware factory (optioneel)
try:
    from hardware_factory import get_best_backend as hw_get_best_backend, get_hardware_factory
    from hardware_config import load_hardware_config
    from hardware_exceptions import HardwareError
    HARDWARE_FACTORY_AVAILABLE = True
except ImportError:
    HARDWARE_FACTORY_AVAILABLE = False
    print("⚠️ hardware_factory niet gevonden, gebruik eigen hardware detectie")

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger('Launcher')


# ====================================================================
# HARDWARE DETECTIE (met factory indien beschikbaar)
# ====================================================================

def detect_hardware():
    """Detecteer beschikbare hardware backends."""
    # Gebruik hardware factory indien beschikbaar
    if HARDWARE_FACTORY_AVAILABLE:
        try:
            factory = get_hardware_factory()
            available = factory.list_available()
            
            hardware = {
                'cpu': 'cpu' in available,
                'cuda': 'cuda' in available,
                'fpga': 'fpga' in available,
                'quantum': 'quantum' in available,
                'neuromorphic': False  # Wordt apart gecheckt
            }
            
            # Check neuromorphic apart
            try:
                import nxsdk
                hardware['neuromorphic'] = True
            except:
                pass
            
            return hardware
        except Exception as e:
            logger.warning(f"Hardware factory error: {e}")
    
    # Fallback naar eigen detectie
    hardware = {
        'cpu': True,  # CPU is altijd beschikbaar
        'cuda': False,
        'fpga': False,
        'quantum': False,
        'neuromorphic': False
    }
    
    # Check CUDA (GPU)
    try:
        import torch
        hardware['cuda'] = torch.cuda.is_available()
        if hardware['cuda']:
            logger.info(f"✅ CUDA beschikbaar: {torch.cuda.get_device_name(0)}")
    except:
        pass
    
    # Check FPGA (via PYNQ)
    try:
        import pynq
        hardware['fpga'] = True
        logger.info("✅ FPGA beschikbaar (PYNQ)")
    except:
        pass
    
    # Check Quantum (via Qiskit)
    try:
        import qiskit
        hardware['quantum'] = True
        logger.info("✅ Quantum beschikbaar (Qiskit)")
    except:
        pass
    
    # Check Neuromorphic (via NXSDK)
    try:
        import nxsdk
        hardware['neuromorphic'] = True
        logger.info("✅ Neuromorphic beschikbaar (NXSDK)")
    except:
        pass
    
    return hardware

def get_best_backend(hardware):
    """Kies de beste beschikbare backend."""
    # Gebruik hardware factory indien beschikbaar
    if HARDWARE_FACTORY_AVAILABLE:
        try:
            factory = get_hardware_factory()
            backend = factory.get_best_backend()
            return backend.__class__.__name__.lower().replace('backend', '')
        except Exception as e:
            logger.warning(f"Factory backend selectie error: {e}")
    
    # Fallback naar eigen prioriteit
    priority = ['quantum', 'fpga', 'neuromorphic', 'cuda', 'cpu']
    
    for backend in priority:
        if hardware.get(backend, False):
            return backend
    
    return 'cpu'

def toon_hardware_status(hardware, gekozen):
    """Toon hardware status in een mooi formaat."""
    print("\n" + "=" * 60)
    print("🔍 HARDWARE DETECTIE")
    print("=" * 60)
    
    for backend, beschikbaar in hardware.items():
        if beschikbaar:
            if backend == gekozen:
                print(f"  ✅ {backend.upper():12} ✓ GEKOZEN")
            else:
                print(f"  ✅ {backend.upper():12} - Beschikbaar")
        else:
            print(f"  ❌ {backend.upper():12} - Niet beschikbaar")
    
    print("-" * 60)
    
    # Toon specifieke voordelen
    voordelen = {
        'fpga': [
            "⚡ ECHTE PARALLELLITEIT - Alle stromingen tegelijk!",
            "🌊 Continue velden in hardware - geen discretisatie!"
        ],
        'quantum': [
            "🌀 ECHTE SUPERPOSITIE - Alle mogelijkheden bestaan tegelijk!",
            "⚛️ Tijdloze berekeningen - geen klokcycli!"
        ],
        'neuromorphic': [
            "🧠 NEUROMORPHISCH - Event-driven, geen klok!",
            "⚡ Energiezuinig - 1000x efficiënter dan CPU!"
        ],
        'cuda': [
            "🎯 GPU VERSNELLING - 100x sneller dan CPU!",
            "📊 Massief parallel - perfect voor matrix operaties!"
        ],
        'cpu': [
            "💻 CPU SIMULATIE - Werkt overal, maar traagste optie",
            "⚠️ Voor echte tijdloosheid: FPGA of Quantum aanbevolen"
        ]
    }
    
    for voordeel in voordelen.get(gekozen, voordelen['cpu']):
        print(voordeel)
    
    # Toon factory status
    if HARDWARE_FACTORY_AVAILABLE:
        print("-" * 60)
        print("🔧 Hardware Factory actief")
    
    print("=" * 60)


# ====================================================================
# FUNCTIES
# ====================================================================

def toon_menu():
    """Toon het hoofdmenu."""
    print("\n" + "=" * 60)
    print("  🚀 NEXUS ULTIMATE V12 - UNIVERSELE LAUNCHER")
    print("=" * 60)
    print("\nKies een optie:")
    print("1. 🚀 Start ALLES (Nexus + Dashboard)")
    print("2. 🧠 Alleen Nexus (AI Core)")
    print("3. 📊 Alleen Dashboard (Streamlit Stats)")
    print("4. 🧪 Test modus (5 cycles blind exploration)")
    print("5. 📋 Toon status van draaiende processen")
    print("6. 🛑 Stop alle processen")
    print("7. 🌌 Blind-Exploratie V12 (normaal)")
    print("8. 🚪 Afsluiten")
    print("-" * 60)
    return input("Jouw keuze (1-8): ").strip()

def check_bestanden(script_dir):
    """Controleer of alle benodigde bestanden bestaan."""
    bestanden = {
        "apeiron_v12.py": "🧠 Apeiron Core V12.0",
        "apeiron_ultimate_dashboard_v4.py": "📊 Dashboard V4",
    }
    
    # Optionele bestanden (waarschuwen maar niet stoppen)
    optioneel = {
        "hardware_factory.py": "🔧 Hardware Factory",
        "hardware_config.py": "⚙️ Hardware Config",
        "hardware_exceptions.py": "⚠️ Hardware Exceptions",
        "resonance_scout.py": "🔍 Resonance Scout",
        "chaos_detection.py": "🛡️ Chaos Detection"
    }
    
    alle_aanwezig = True
    print("\n📁 Controleren op bestanden:")
    
    # Verplichte bestanden
    for bestand, naam in bestanden.items():
        if os.path.exists(bestand):
            print(f"  ✅ {naam}: {bestand}")
        else:
            print(f"  ❌ {naam}: {bestand} (NIET GEVONDEN!)")
            alle_aanwezig = False
    
    # Optionele bestanden
    for bestand, naam in optioneel.items():
        if os.path.exists(bestand):
            print(f"  ✅ {naam}: {bestand} (optioneel)")
        else:
            print(f"  ⚠️ {naam}: {bestand} (niet gevonden, optioneel)")
    
    return alle_aanwezig

def maak_batch_bestand(script_dir, bestand, titel, commando, is_streamlit=False):
    """Maak een batch bestand aan voor een proces."""
    batch_naam = f"_start_{bestand.replace('.py', '')}.bat"
    
    if is_streamlit:
        # Extraheer poort uit commando voor weergave
        poort = "8501"
        if "--server.port" in commando:
            poort = commando.split("--server.port")[-1].strip().split()[0]
        
        content = f"""@echo off
title {titel}
cd /d "{script_dir}"
echo ========================================
echo    {titel}
echo ========================================
echo.
echo {commando} wordt gestart...
echo.
echo Even geduld, streamlit moet opstarten...
echo.
echo Je zult straks een browser zien openen met:
echo http://localhost:{poort}
echo.
echo ========================================
{commando}
echo.
echo ========================================
echo {titel} is gestopt.
pause
"""
    else:
        content = f"""@echo off
title {titel}
cd /d "{script_dir}"
echo ========================================
echo    {titel}
echo ========================================
echo.
echo Je kunt nu input geven in dit venster!
echo.
{commando}
echo.
echo ========================================
echo {titel} is gestopt.
pause
"""
    
    with open(batch_naam, "w", encoding='ascii', errors='ignore') as f:
        f.write(content)
    
    return batch_naam

def start_proces(script_dir, bestand, titel, commando, is_streamlit=False, poort=8501):
    """Start een proces in een nieuw venster met optionele poort."""
    print(f"\n[{titel}] Starten in nieuw venster...")
    
    # Voeg poort toe voor streamlit apps
    if is_streamlit and poort != 8501:
        commando = f"{commando} --server.port {poort}"
    
    batch = maak_batch_bestand(script_dir, bestand, titel, commando, is_streamlit)
    subprocess.Popen(['cmd', '/c', 'start', batch], shell=True)
    print(f"[{titel}] Gestart op poort {poort if is_streamlit else 'nvt'}")
    return batch

def toon_status(processen):
    """Toon status van alle processen."""
    print("\n" + "=" * 60)
    print("📋 STATUS VAN DRAAIENDE PROCESSEN")
    print("=" * 60)
    
    if not processen:
        print("\nGeen processen gestart via deze sessie.")
        return
    
    for naam, batch in processen.items():
        if batch and os.path.exists(batch):
            print(f"  ✅ {naam}: gestart (batch: {batch})")
        else:
            print(f"  ❌ {naam}: niet gestart")
    
    print("\n💡 Tip: Gebruik Taakbeheer om processen handmatig te stoppen")

def stop_processen(processen):
    """Stop alle processen (voor zover mogelijk)."""
    print("\n" + "=" * 60)
    print("🛑 STOPPEN VAN PROCESSEN")
    print("=" * 60)
    
    for naam, batch in processen.items():
        if batch and os.path.exists(batch):
            print(f"  ⏳ {naam} wordt gestopt...")
            # Probeer het batch venster te sluiten
            try:
                os.system(f'taskkill /f /im cmd.exe /fi "WINDOWTITLE eq {naam}"')
            except:
                pass
    
    print("\n✅ Stopcommando's verzonden. Sluit eventuele resterende vensters handmatig.")

def cleanup_batches(batch_files):
    """Verwijder tijdelijke batch files."""
    print("\n🧹 Opruimen van batch bestanden...")
    for batch in batch_files:
        if batch and os.path.exists(batch):
            try:
                os.remove(batch)
                print(f"  ✓ {batch} verwijderd")
            except:
                print(f"  ⚠️ Kon {batch} niet verwijderen")


# ====================================================================
# TEST MODUS
# ====================================================================

async def run_test_mode(cycles: int = 5):
    """Voer test modus uit."""
    print("\n" + "="*60)
    print("🧪 TEST MODUS V12")
    print("="*60)
    print(f"{cycles} cycles blind exploration met beperkte resolutie")
    print("\n🚀 Starten...")
    print("="*60)
    
    try:
        # Initialiseer Nexus met test configuratie
        nexus = OceanicNexusV12(
            db_path="./nexus_test_memory",
            config_path="config.yaml"
        )
        
        # Voer test exploratie uit
        for i in range(cycles):
            print(f"\n📊 Cycle {i+1}/{cycles}")
            
            # Simuleer blind exploration
            result = await nexus.blind_engine.quantum_scanner.scan_ruimte(resolutie=10)
            
            if result:
                print(f"   📡 {len(result)} pieken gedetecteerd")
            
            # Korte pauze
            await asyncio.sleep(1)
        
        print("\n✅ Test modus voltooid!")
        
    except Exception as e:
        print(f"\n❌ Fout in test modus: {e}")
    finally:
        if 'nexus' in locals():
            await nexus.stop_oceanic()


# ====================================================================
# MAIN
# ====================================================================

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Nexus Ultimate Hardware Launcher')
    parser.add_argument('--backend', choices=['auto', 'cpu', 'cuda', 'fpga', 'quantum', 'neuromorphic'],
                       default='auto', help='Kies specifieke hardware backend')
    parser.add_argument('--no-hardware-detect', action='store_true', 
                       help='Sla hardware detectie over')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Pad naar configuratie bestand')
    parser.add_argument('--version', action='store_true',
                       help='Toon versie informatie')
    args = parser.parse_args()
    
    if args.version:
        print("\n" + "="*60)
        print("NEXUS ULTIMATE V12.0")
        print("="*60)
        print("ResonanceScout - De AI ontdekt waar kennis ontbreekt!")
        print(f"Hardware Factory: {'✅' if HARDWARE_FACTORY_AVAILABLE else '❌'}")
        print(f"Python: {sys.version}")
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Hardware detectie (tenzij overgeslagen)
    gekozen_backend = None
    if not args.no_hardware_detect:
        hardware = detect_hardware()
        
        if args.backend == 'auto':
            gekozen_backend = get_best_backend(hardware)
        else:
            if hardware.get(args.backend, False):
                gekozen_backend = args.backend
                print(f"\n✨ Geforceerde backend: {args.backend.upper()}")
            else:
                print(f"\n⚠️  Backend {args.backend} niet beschikbaar!")
                gekozen_backend = get_best_backend(hardware)
                print(f"   Fallback naar: {gekozen_backend.upper()}")
        
        toon_hardware_status(hardware, gekozen_backend)
        
        # Sla backend keuze op voor Nexus
        os.environ['NEXUS_HARDWARE_BACKEND'] = gekozen_backend
        
        # Laad configuratie
        if os.path.exists(args.config):
            print(f"\n📋 Configuratie geladen: {args.config}")
    
    # Toon menu
    keuze = toon_menu()
    
    # Controleer bestanden (behalve voor afsluiten)
    if keuze not in ["5", "6", "8"] and not check_bestanden(script_dir):
        print("\n❌ Niet alle benodigde bestanden zijn aanwezig!")
        input("\nDruk op Enter om te stoppen...")
        return
    
    # Dictionary om bij te houden welke processen we gestart hebben
    gestarte_processen = {}
    batch_bestanden = []
    
    if keuze == "1":  # Start ALLES
        print("\n🚀 Alles starten...")
        
        # Start Nexus V12 (geen poort nodig)
        batch = start_proces(
            script_dir, 
            "apeiron_v12.py", 
            "Apeiron V12", 
            "python apeiron_v12.py"
        )
        gestarte_processen["Nexus"] = batch
        batch_bestanden.append(batch)
        
        # Wacht 5 seconden
        print("\n⏳ Wachten 5 seconden...")
        time.sleep(5)
        
        # Start Dashboard op poort 8502
        batch = start_proces(
            script_dir, 
            "apeiron_dashboard_v4.py", 
            "Apeiron Dashboard V4", 
            "streamlit run apeiron_dashboard_v4.py",
            is_streamlit=True,
            poort=8502
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        print("\n" + "=" * 60)
        print("✅ ALLES GESTART!")
        print("=" * 60)
        print("\n📌 Je hebt nu:")
        print("   1. 🧠 Nexus V12 venster - Blind Exploration!")
        print("   2. 📊 Dashboard venster - http://localhost:8502")
        
    elif keuze == "2":  # Alleen Nexus V12
        print("\n🧠 Alleen Nexus V12 starten...")
        batch = start_proces(
            script_dir, 
            "apeiron_v12.py", 
            "Apeiron V12", 
            "python apeiron_v12.py"
        )
        gestarte_processen["Nexus"] = batch
        batch_bestanden.append(batch)
        
        print("\n✅ Nexus V12 gestart in nieuw venster!")
        print("🌌 Blind Exploration mode - geen menselijke concepten!")
        
    elif keuze == "3":  # Alleen Dashboard
        print("\n📊 Alleen Dashboard starten...")
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_dashboard_v4.py", 
            "Nexus Dashboard V4", 
            "streamlit run nexus_ultimate_dashboard_v4.py",
            is_streamlit=True,
            poort=8501
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        print("\n✅ Dashboard gestart in nieuw venster!")
        print("🌐 http://localhost:8501")
        
    elif keuze == "4":  # Test modus
        asyncio.run(run_test_mode(cycles=5))
        
    elif keuze == "5":  # Toon status
        if 'gestarte_processen' not in locals():
            gestarte_processen = {}
        toon_status(gestarte_processen)
        
    elif keuze == "6":  # Stop processen
        if 'gestarte_processen' not in locals():
            gestarte_processen = {}
        stop_processen(gestarte_processen)

    elif keuze == "7":  # 🌌 BLIND EXPLORATION V12
        print("\n" + "="*60)
        print("🌌 BLIND-EXPLORATIE V12")
        print("="*60)
        print("Geen menselijke concepten zoals 'Biotech' of 'AI'!")
        print("De AI zoekt naar patronen in pure wiskundige ruis.")
        print("Nieuwe structuren krijgen IDs als STRUCT_PHI_772")
        print("\n🚀 Starten...")
        print("="*60)
    
        # Toon welke hardware wordt gebruikt
        if gekozen_backend:
            print(f"   Hardware backend: {gekozen_backend.upper()}")
        if HARDWARE_FACTORY_AVAILABLE:
            print("   🔧 Hardware Factory actief")
    
        # Start blind exploration
        start_v12("blind")
        return

    elif keuze == "8":  # Afsluiten
        print("\n👋 Tot ziens!")
        return
        
    else:
        print("\n❌ Ongeldige keuze.")
    
    # Toon samenvatting van gestarte processen
    if gestarte_processen:
        print("\n" + "-" * 60)
        print("📋 GESTARTE PROCESSEN:")
        for naam in gestarte_processen:
            print(f"  ✅ {naam}")
    
    # Houd hoofdvenster open
    print("\n" + "-" * 60)
    print("⚠️  Druk op Enter om dit venster te sluiten.")
    print("   De andere vensters blijven open draaien.")
    print("   Gebruik optie 6 in een nieuwe sessie om ze te stoppen.")
    input()
    
    # Optioneel: cleanup batch files
    if gestarte_processen:
        print("\nWil je de batch bestanden opruimen? (j/n): ", end="")
        cleanup = input().lower().strip()
        if cleanup == 'j':
            cleanup_batches(batch_bestanden)
        else:
            print("Batch bestanden blijven behouden.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programma onderbroken door gebruiker.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Onverwachte fout: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)