"""
NEXUS ULTIMATE V6.5 - OCEANISCHE LAUNCHER
================================================================================================
Deze launcher start de V5 Nexus, maar transformeert hem naar oceanisch.
Je bestaande V5 code blijft 100% hetzelfde werken!
================================================================================================
"""

import subprocess
import os
import sys
import time
import webbrowser
from nexus_ultimate_v65_integratie import transformeer_v5_naar_oceanisch

# ====================================================================
# OCEANISCHE NEXUS WRAPPER
# ====================================================================

class OceanicNexusLauncher:
    """
    Deze klasse start V5 en transformeert hem naar oceanisch.
    Het behoudt alle functionaliteit van de originele launcher.
    """
    
    def __init__(self):
        self.nexus_process = None
        self.oceanic_nexus = None
        
    def start_nexus(self):
        """Start V5 en transformeer naar oceanisch."""
        print("\n" + "="*80)
        print("🌊 OCEANISCHE NEXUS V6.5 STARTEN")
        print("="*80)
        
        # Importeer V5 (dit gebeurt nu, niet bij module laden)
        from nexus_ultimate_v5 import NexusUltimateV5
        
        # Start V5
        print("🚀 V5 Nexus starten...")
        nexus = NexusUltimateV5()
        
        # Transformeer naar oceanisch (ZONDER code te veranderen!)
        print("🌊 Transformeren naar oceanische architectuur...")
        self.oceanic_nexus = transformeer_v5_naar_oceanisch(nexus)
        
        print("✅ Oceanische transformatie voltooid!")
        print("   V5 denkt nog steeds in cycli, maar stroomt nu continu")
        print("="*80)
        
        return self.oceanic_nexus
    
    def run(self):
        """Start de oceanische nexus in een apart proces."""
        import multiprocessing
        
        def run_nexus():
            nexus = self.start_nexus()
            nexus.start_autonomous_evolution()
        
        self.nexus_process = multiprocessing.Process(target=run_nexus)
        self.nexus_process.start()
        
        return self.nexus_process


# ====================================================================
# GEWIJZIGDE MAIN.PY FUNCTIES (alleen voor optie 1 en 2)
# ====================================================================

def start_oceanic_nexus():
    """Start de oceanische Nexus in plaats van V5."""
    print("\n🌊 Oceanische Nexus V6.5 starten...")
    
    # Gebruik de nieuwe launcher
    launcher = OceanicNexusLauncher()
    process = launcher.start_nexus()
    
    print("\n✅ Oceanische Nexus gestart!")
    print("   🌊 Continue stroming actief")
    print("   🔄 Cycli zijn momentopnames")
    print("   📊 Dashboard werkt hetzelfde")
    
    return process


def start_oceanic_dashboard():
    """Start dashboard (identiek aan V5)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Exact dezelfde code als in main.py
    batch = start_proces(
        script_dir, 
        "nexus_ultimate_dashboard_v2.py", 
        "Nexus Dashboard V6.5", 
        "streamlit run nexus_ultimate_dashboard_v2.py",
        is_streamlit=True,
        poort=8502
    )
    
    print("📊 Oceanisch dashboard gestart op poort 8502")
    return batch


def start_oceanic_web():
    """Start web interface (identiek aan V5)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Exact dezelfde code als in main.py
    batch = start_proces(
        script_dir, 
        "nexus_web_interface.py", 
        "Nexus Web Interface V6.5", 
        "streamlit run nexus_web_interface.py",
        is_streamlit=True,
        poort=8501
    )
    
    print("🌐 Oceanische web interface gestart op poort 8501")
    return batch


# ====================================================================
# KOPIE VAN JOUW BESTAANDE FUNCTIES (identiek)
# ====================================================================

def toon_menu():
    """Toon het hoofdmenu - identiek aan V5"""
    print("\n" + "=" * 60)
    print("  🚀 NEXUS ULTIMATE V6.5 - OCEANISCHE LAUNCHER")
    print("=" * 60)
    print("\nKies een optie:")
    print("1. 🚀 Start ALLES (Oceanisch Nexus + Dashboard + Web)")
    print("2. 🧠 Alleen Oceanisch Nexus (continu stromend)")
    print("3. 📊 Alleen Dashboard (werkt met beide)")
    print("4. 🌐 Alleen Web Interface")
    print("5. 📋 Toon status")
    print("6. 🛑 Stop alle processen")
    print("7. 🚪 Afsluiten")
    print("-" * 60)
    return input("Jouw keuze (1-7): ").strip()


# Kopie van jouw bestaande functies
def check_bestanden(script_dir):
    """Controleer of alle benodigde bestanden bestaan - identiek"""
    bestanden = {
        "nexus_ultimate_v5.py": "🧠 Nexus Core (V5)",
        "nexus_ultimate_dashboard_v2.py": "📊 Dashboard",
        "nexus_web_interface.py": "🌐 Web Interface",
        "nexus_ultimate_v65_integratie.py": "🌊 Oceanische integratie"
    }
    
    alle_aanwezig = True
    print("\n📁 Controleren op bestanden:")
    
    for bestand, naam in bestanden.items():
        if os.path.exists(bestand):
            print(f"  ✅ {naam}: {bestand}")
        else:
            print(f"  ❌ {naam}: {bestand} (NIET GEVONDEN!)")
            alle_aanwezig = False
    
    return alle_aanwezig


def maak_batch_bestand(script_dir, bestand, titel, commando, is_streamlit=False):
    """IDENTIEK aan jouw functie"""
    batch_naam = f"_start_{bestand.replace('.py', '')}.bat"
    
    if is_streamlit:
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
    """IDENTIEK aan jouw functie"""
    print(f"\n[{titel}] Starten in nieuw venster...")
    
    if is_streamlit and poort != 8501:
        commando = f"{commando} --server.port {poort}"
    
    batch = maak_batch_bestand(script_dir, bestand, titel, commando, is_streamlit)
    subprocess.Popen(['cmd', '/c', 'start', batch], shell=True)
    print(f"[{titel}] Gestart op poort {poort if is_streamlit else 'nvt'}")
    return batch


def toon_status(processen):
    """IDENTIEK aan jouw functie"""
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
    """IDENTIEK aan jouw functie"""
    print("\n" + "=" * 60)
    print("🛑 STOPPEN VAN PROCESSEN")
    print("=" * 60)
    
    for naam, batch in processen.items():
        if batch and os.path.exists(batch):
            print(f"  ⏳ {naam} wordt gestopt...")
            try:
                os.system(f'taskkill /f /im cmd.exe /fi "WINDOWTITLE eq {naam}"')
            except:
                pass
    
    print("\n✅ Stopcommando's verzonden. Sluit eventuele resterende vensters handmatig.")


def cleanup_batches(batch_files):
    """IDENTIEK aan jouw functie"""
    print("\n🧹 Opruimen van batch bestanden...")
    for batch in batch_files:
        if batch and os.path.exists(batch):
            try:
                os.remove(batch)
                print(f"  ✓ {batch} verwijderd")
            except:
                print(f"  ⚠️ Kon {batch} niet verwijderen")


# ====================================================================
# NIEUWE MAIN (gebaseerd op jouw main.py, maar oceanisch)
# ====================================================================

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Toon menu (aangepast voor V6.5)
    keuze = toon_menu()
    
    # Controleer bestanden
    if keuze not in ["5", "6", "7"] and not check_bestanden(script_dir):
        print("\n❌ Niet alle benodigde bestanden zijn aanwezig!")
        input("\nDruk op Enter om te stoppen...")
        return
    
    # Dictionary om processen bij te houden
    gestarte_processen = {}
    batch_bestanden = []
    
    if keuze == "1":  # Start ALLES (Oceanisch)
        print("\n🚀 Alles oceanisch starten...")
        
        # ⭐ Start OCEANISCHE Nexus (ipv V5)
        print("\n🌊 Oceanische Nexus starten in huidig venster...")
        print("   (Dit venster wordt nu de oceanische Nexus)")
        print("   Nieuwe vensters voor dashboard en web interface\n")
        
        # Start oceanische nexus in dit venster
        launcher = OceanicNexusLauncher()
        nexus = launcher.start_nexus()
        
        # Start in een aparte thread zodat we verder kunnen
        import threading
        nexus_thread = threading.Thread(target=nexus.start_autonomous_evolution)
        nexus_thread.daemon = True
        nexus_thread.start()
        
        gestarte_processen["Oceanische Nexus"] = "in dit venster"
        
        # Wacht 5 seconden
        print("\n⏳ Wachten 5 seconden...")
        time.sleep(5)
        
        # Start Dashboard (identiek aan V5)
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_dashboard_v2.py", 
            "Nexus Dashboard (Oceanisch)", 
            "streamlit run nexus_ultimate_dashboard_v2.py",
            is_streamlit=True,
            poort=8502
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        # Wacht 3 seconden
        print("\n⏳ Wachten 3 seconden...")
        time.sleep(3)
        
        # Start Web Interface (identiek aan V5)
        batch = start_proces(
            script_dir, 
            "nexus_web_interface.py", 
            "Nexus Web Interface (Oceanisch)", 
            "streamlit run nexus_web_interface.py",
            is_streamlit=True,
            poort=8501
        )
        gestarte_processen["Web Interface"] = batch
        batch_bestanden.append(batch)
        
        # Open browser
        print("\n🌐 Openen van web interface in browser...")
        time.sleep(5)
        webbrowser.open("http://localhost:8501")
        
        print("\n" + "=" * 60)
        print("✅ OCEANISCH SYSTEEM GESTART!")
        print("=" * 60)
        print("\n📌 Je hebt nu:")
        print("   1. 🌊 Oceanische Nexus - continu stromend (dit venster)")
        print("   2. 📊 Dashboard - http://localhost:8502")
        print("   3. 🌐 Web Interface - http://localhost:8501")
        print("\n💡 De Nexus DENKT dat het cycli draait, maar het STROOMT continu!")
        
        # Houd dit venster open
        print("\n" + "-" * 60)
        print("⚠️  Druk op Ctrl+C om de oceanische Nexus te stoppen.")
        print("   De andere vensters kun je apart sluiten.")
        
        try:
            # Houd de main thread actief
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Oceanische Nexus gestopt.")
        
    elif keuze == "2":  # Alleen Oceanische Nexus
        print("\n🌊 Alleen Oceanische Nexus starten...")
        
        launcher = OceanicNexusLauncher()
        nexus = launcher.start_nexus()
        
        print("\n✅ Oceanische Nexus gestart in dit venster!")
        print("   Het systeem stroomt continu...")
        print("   Druk op Ctrl+C om te stoppen")
        
        try:
            nexus.start_autonomous_evolution()
        except KeyboardInterrupt:
            print("\n\n👋 Oceanische Nexus gestopt.")
        
    elif keuze == "3":  # Alleen Dashboard (identiek aan V5)
        print("\n📊 Alleen Dashboard starten...")
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_dashboard_v2.py", 
            "Nexus Dashboard", 
            "streamlit run nexus_ultimate_dashboard_v2.py",
            is_streamlit=True,
            poort=8501
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        print("\n✅ Dashboard gestart!")
        print("🌐 http://localhost:8501")
        print("\n💡 Dit dashboard werkt met ZOWEL V5 als V6.5!")
        
    elif keuze == "4":  # Alleen Web Interface (identiek)
        print("\n🌐 Alleen Web Interface starten...")
        batch = start_proces(
            script_dir, 
            "nexus_web_interface.py", 
            "Nexus Web Interface", 
            "streamlit run nexus_web_interface.py",
            is_streamlit=True
        )
        gestarte_processen["Web Interface"] = batch
        batch_bestanden.append(batch)
        
        print("\n✅ Web Interface gestart!")
        print("🌐 http://localhost:8501")
        
        time.sleep(3)
        webbrowser.open("http://localhost:8501")
        
    elif keuze == "5":  # Toon status
        toon_status(gestarte_processen)
        
    elif keuze == "6":  # Stop processen
        stop_processen(gestarte_processen)
        
    elif keuze == "7":  # Afsluiten
        print("\n👋 Tot ziens!")
        return
        
    else:
        print("\n❌ Ongeldige keuze.")
    
    # Cleanup batch files (optioneel)
    if gestarte_processen and batch_bestanden:
        print("\nWil je de batch bestanden opruimen? (j/n): ", end="")
        cleanup = input().lower().strip()
        if cleanup == 'j':
            cleanup_batches(batch_bestanden)
        else:
            print("Batch bestanden blijven behouden.")


if __name__ == "__main__":
    main()