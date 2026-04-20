﻿# main.py - NEXUS ULTIMATE V9.1 LAUNCHER MET MENU
import subprocess
import os
import sys
import time
import webbrowser
from nexus_ultimate_v9_1_1 import start_v9

# ====================================================================
# VISUAL STUDIO DETECTIE
# ====================================================================

# Check of we in Visual Studio draaien
# if 'visualstudio' in sys.executable.lower() or 'vs' in sys.executable.lower():
#    print("=" * 60)
#    print("⚠️ LET OP: Je draait in Visual Studio!")
#     print("Het menu werkt niet goed in de VS output console.")
#     print("\nOpties:")
#     print("1. Open een gewone Command Prompt en type: python main.py")
#     print("2. Druk op CTRL+C om te stoppen en start opnieuw in cmd")
#     print("=" * 60)
#     input("\nDruk op Enter om toch door te gaan (maar menu werkt niet)...")

# ====================================================================
# FUNCTIES
# ====================================================================
def toon_menu():
    """Toon het hoofdmenu"""
    print("\n" + "=" * 60)
    print("  🚀 NEXUS ULTIMATE V9.1 - LAUNCHER")
    print("=" * 60)
    print("\nKies een optie:")
    print("1. 🚀 Start ALLES (Nexus + Dashboard + Web Interface)")
    print("2. 🧠 Alleen Nexus (AI Core)")
    print("3. 📊 Alleen Dashboard (Streamlit Stats)")
    print("4. 🌐 Alleen Web Interface (Artikel overzicht + Prompts)")
    print("5. 📋 Toon status van draaiende processen")
    print("6. 🛑 Stop alle processen")
    print("7. 🌊 Oceanische Nexus (continu stromend)")
    print("8. 🚪 Afsluiten")
    print("-" * 60)
    return input("Jouw keuze (1-8): ").strip()

def check_bestanden(script_dir):
    """Controleer of alle benodigde bestanden bestaan"""
    bestanden = {
        "nexus_ultimate_v9_1.py": "🧠 Nexus Core V9.1",
        "nexus_ultimate_dashboard_v4.py": "📊 Dashboard V4",
        "nexus_web_interface.py": "🌐 Web Interface"
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
    """Maak een batch bestand aan voor een proces"""
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
    """Start een proces in een nieuw venster met optionele poort"""
    print(f"\n[{titel}] Starten in nieuw venster...")
    
    # Voeg poort toe voor streamlit apps
    if is_streamlit and poort != 8501:
        commando = f"{commando} --server.port {poort}"
    
    batch = maak_batch_bestand(script_dir, bestand, titel, commando, is_streamlit)
    subprocess.Popen(['cmd', '/c', 'start', batch], shell=True)
    print(f"[{titel}] Gestart op poort {poort if is_streamlit else 'nvt'}")
    return batch

def toon_status(processen):
    """Toon status van alle processen"""
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
    """Stop alle processen (voor zover mogelijk)"""
    print("\n" + "=" * 60)
    print("🛑 STOPPEN VAN PROCESSEN")
    print("=" * 60)
    
    for naam, batch in processen.items():
        if batch and os.path.exists(batch):
            print(f"  ⏳ {naam} wordt gestopt...")
            # Probeer het batch venster te sluiten (werkt niet altijd)
            try:
                os.system(f'taskkill /f /im cmd.exe /fi "WINDOWTITLE eq {naam}"')
            except:
                pass
    
    print("\n✅ Stopcommando's verzonden. Sluit eventuele resterende vensters handmatig.")

def cleanup_batches(batch_files):
    """Verwijder tijdelijke batch files"""
    print("\n🧹 Opruimen van batch bestanden...")
    for batch in batch_files:
        if batch and os.path.exists(batch):
            try:
                os.remove(batch)
                print(f"  ✓ {batch} verwijderd")
            except:
                print(f"  ⚠️ Kon {batch} niet verwijderen")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
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
        
        # Start Nexus (geen poort nodig)
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_v9_1.py", 
            "Nexus Ultimate V9.1", 
            "python nexus_ultimate_v9_1.py"
        )
        gestarte_processen["Nexus"] = batch
        batch_bestanden.append(batch)
        
        # Wacht 5 seconden
        print("\n⏳ Wachten 5 seconden...")
        time.sleep(5)
        
        # Start Dashboard op poort 8502
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_dashboard_v4.py", 
            "Nexus Dashboard V4", 
            "streamlit run nexus_ultimate_dashboard_v4.py",
            is_streamlit=True,
            poort=8502  # 🔥 Andere poort!
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        # Wacht 3 seconden
        print("\n⏳ Wachten 3 seconden...")
        time.sleep(3)
        
        # Start Web Interface op poort 8501 (standaard)
        batch = start_proces(
            script_dir, 
            "nexus_web_interface.py", 
            "Nexus Web Interface", 
            "streamlit run nexus_web_interface.py",
            is_streamlit=True,
            poort=8501  # Standaard poort voor web interface
        )
        gestarte_processen["Web Interface"] = batch
        batch_bestanden.append(batch)
        
        # Open automatisch de web interface in browser
        print("\n🌐 Openen van web interface in browser...")
        time.sleep(5)
        webbrowser.open("http://localhost:8501")
        
        print("\n" + "=" * 60)
        print("✅ ALLES GESTART!")
        print("=" * 60)
        print("\n📌 Je hebt nu:")
        print("   1. 🧠 Nexus venster - voor AI chat")
        print("   2. 📊 Dashboard venster - http://localhost:8502")
        print("   3. 🌐 Web Interface - http://localhost:8501")
        
    elif keuze == "2":  # Alleen Nexus
        print("\n🧠 Alleen Nexus starten...")
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_v9_1.py", 
            "Nexus Ultimate V9.1", 
            "python nexus_ultimate_v9_1.py"
        )
        gestarte_processen["Nexus"] = batch
        batch_bestanden.append(batch)
        
        print("\n✅ Nexus gestart in nieuw venster!")
        print("📝 Je kunt nu input geven in dat venster")
        
    elif keuze == "3":  # Alleen Dashboard
        print("\n📊 Alleen Dashboard starten...")
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_dashboard_v4.py", 
            "Nexus Dashboard V4", 
            "streamlit run nexus_ultimate_dashboard_v4.py",
            is_streamlit=True,
            poort=8501  # Of 8502 als je wilt
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        print("\n✅ Dashboard gestart in nieuw venster!")
        print("🌐 http://localhost:8501")
        
    elif keuze == "4":  # Alleen Web Interface
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
        
        print("\n✅ Web Interface gestart in nieuw venster!")
        print("🌐 http://localhost:8501")
        print("\n💡 Deze interface toont:")
        print("   - 📚 Alle geladen artikelen (real-time)")
        print("   - 💬 Interactieve prompts om het systeem te testen")
        print("   - 📊 Live statistieken")
        
        # Open automatisch de browser
        time.sleep(3)
        webbrowser.open("http://localhost:8501")
        
    elif keuze == "5":  # Toon status
        if 'gestarte_processen' not in locals():
            gestarte_processen = {}
        toon_status(gestarte_processen)
        
    elif keuze == "6":  # Stop processen
        if 'gestarte_processen' not in locals():
            gestarte_processen = {}
        stop_processen(gestarte_processen)

    elif keuze == "7":  # Oceanische Nexus
        print("\n🌊 Oceanische Nexus V9.1 starten...")
        start_v9()
        return

    elif keuze == "8":  # Afsluiten
        print("\n👋 Tot ziens!")
        return
        
    else:
        print("\n❌ Ongeldige keuze. Start alles als standaard...")
        # Default: start alles
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_v9_1.py", 
            "Nexus Ultimate V9.1", 
            "python nexus_ultimate_v9_1.py"
        )
        gestarte_processen["Nexus"] = batch
        batch_bestanden.append(batch)
        
        time.sleep(5)
        
        batch = start_proces(
            script_dir, 
            "nexus_ultimate_dashboard_v4.py", 
            "Nexus Dashboard V4", 
            "streamlit run nexus_ultimate_dashboard_v4.py",
            is_streamlit=True
        )
        gestarte_processen["Dashboard"] = batch
        batch_bestanden.append(batch)
        
        time.sleep(3)
        
        batch = start_proces(
            script_dir, 
            "nexus_web_interface.py", 
            "Nexus Web Interface", 
            "streamlit run nexus_web_interface.py",
            is_streamlit=True
        )
        gestarte_processen["Web Interface"] = batch
        batch_bestanden.append(batch)
        
        time.sleep(5)
        webbrowser.open("http://localhost:8501")
    
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
    main()