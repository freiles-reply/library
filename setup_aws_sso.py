#!/usr/bin/env python3
"""
🔧 Setup automatico per AWS SSO Credential Manager
==================================================

Script integrato nella libreria per configurare automaticamente il path di 
aws-sso-credential-manager tramite file .env quando il modulo credential_manager 
non è disponibile.
"""

import os
import sys
from pathlib import Path

def find_aws_sso_path():
    """Trova automaticamente il path di aws-sso-credential-manager"""
    common_paths = [
        "./aws-sso-credential-manager",
        "../aws-sso-credential-manager", 
        "../../aws-sso-credential-manager",  # Due livelli sopra per directory library
        "~/tools/aws-sso-credential-manager",
        "~/aws-sso-credential-manager",
        "/opt/aws-sso-credential-manager",
        "/usr/local/bin/aws-sso-credential-manager",
    ]
    
    for path_str in common_paths:
        path = Path(path_str).expanduser().resolve()
        if path.exists():
            return str(path)
    return None

def select_aws_sso_path_manually():
    """Apre una dialog per selezionare manualmente la cartella aws-sso-credential-manager"""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        
        # Crea una finestra principale nascosta
        root = tk.Tk()
        root.withdraw()
        
        # Mostra un messaggio informativo
        messagebox.showinfo(
            "Selezione Manuale",
            "Seleziona la cartella 'aws-sso-credential-manager'\n\n"
            "La cartella deve contenere il file 'credential_manager.py'"
        )
        
        # Apre la dialog per selezionare la directory
        selected_path = filedialog.askdirectory(
            title="Seleziona la cartella aws-sso-credential-manager",
            mustexist=True
        )
        
        # Chiudi la finestra principale
        root.destroy()
        
        if selected_path:
            # Verifica che la cartella contenga credential_manager.py
            credential_manager_file = Path(selected_path) / "credential_manager.py"
            if credential_manager_file.exists():
                return selected_path
            else:
                print(f"❌ La cartella selezionata non contiene 'credential_manager.py'")
                print(f"   Path: {selected_path}")
                return None
        else:
            print("❌ Nessuna cartella selezionata")
            return None
            
    except ImportError:
        print("❌ tkinter non disponibile per la selezione manuale")
        print("💡 Installa tkinter: sudo apt-get install python3-tk (Linux) o usa Homebrew (Mac)")
        return None
    except Exception as e:
        print(f"❌ Errore durante la selezione manuale: {e}")
        return None

def create_env_file(aws_sso_path):
    """Crea un file .env nella directory del progetto (root del repository)"""
    # Determina la directory root del progetto partendo dalla directory della libreria
    library_dir = Path(__file__).parent
    project_root = library_dir.parent  # La directory padre di library/
    
    env_file_path = project_root / '.env'
    
    with open(env_file_path, 'w') as f:
        f.write('# AWS SSO Credential Manager Configuration\n')
        f.write('# Generato automaticamente da setup_aws_sso.py\n')
        f.write(f'AWS_SSO_CREDENTIAL_MANAGER_PATH={aws_sso_path}\n')
    
    return str(env_file_path)

def run_setup():
    """Esegue il setup automatico e restituisce True se completato con successo"""
    print("🚀 Setup automatico AWS SSO Credential Manager")
    print("=" * 50)
    print()
    
    # Controlla se esiste già un file .env e se il path è valido
    library_dir = Path(__file__).parent
    project_root = library_dir.parent
    env_file_path = project_root / '.env'
    
    current_configured_path = None
    if env_file_path.exists():
        try:
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == 'AWS_SSO_CREDENTIAL_MANAGER_PATH':
                            current_configured_path = value.strip()
                            break
        except Exception:
            pass
    
    if current_configured_path:
        print(f"📄 Configurazione esistente trovata: {current_configured_path}")
        if not Path(current_configured_path).exists():
            print("❌ Il path configurato non esiste più!")
            print("🔧 Riconfigurazione necessaria...")
        else:
            credential_manager_file = Path(current_configured_path) / "credential_manager.py"
            if not credential_manager_file.exists():
                print("❌ Il path configurato non contiene 'credential_manager.py'!")
                print("🔧 Riconfigurazione necessaria...")
            else:
                print("✅ La configurazione esistente sembra valida.")
                reconfigure = input("Vuoi riconfigurare comunque? (y/n): ").strip().lower()
                if reconfigure not in ['y', 'yes', 'si', 's']:
                    print("ℹ️ Mantenendo la configurazione esistente.")
                    return True
        print()
    
    # Prova ricerca automatica
    print("🔍 Ricerca automatica di aws-sso-credential-manager...")
    auto_path = find_aws_sso_path()
    
    aws_sso_path = None
    
    if auto_path:
        print(f"✅ Trovato automaticamente: {auto_path}")
        response = input("Usare questo path? (y/n): ").strip().lower()
        
        if response in ['y', 'yes', 'si', 's']:
            aws_sso_path = auto_path
        else:
            print("❌ Path automatico rifiutato.")
    
    # Se non trovato automaticamente o rifiutato dall'utente
    if not aws_sso_path:
        print("❌ aws-sso-credential-manager non trovato automaticamente.")
        print()
        print("💡 Opzioni disponibili:")
        print("   1. Seleziona manualmente la cartella (tramite dialog)")
        print("   2. Installa aws-sso-credential-manager nella directory del progetto")
        print("   3. Installa aws-sso-credential-manager in ~/tools/")
        print("   4. Imposta manualmente la variabile d'ambiente AWS_SSO_CREDENTIAL_MANAGER_PATH")
        print()
        
        choice = input("Vuoi selezionare manualmente la cartella? (y/n): ").strip().lower()
        
        if choice in ['y', 'yes', 'si', 's']:
            print("� Apertura dialog per selezione manuale...")
            manual_path = select_aws_sso_path_manually()
            
            if manual_path:
                print(f"✅ Cartella selezionata: {manual_path}")
                aws_sso_path = manual_path
            else:
                print("❌ Selezione manuale fallita o annullata.")
                return False
        else:
            print("❌ Setup annullato dall'utente.")
            return False
    
    # Se abbiamo un path valido, crea il file .env
    if aws_sso_path:
        # Verifica finale che il path sia valido
        credential_manager_file = Path(aws_sso_path) / "credential_manager.py"
        if not credential_manager_file.exists():
            print("❌ Errore: Il path non contiene 'credential_manager.py'")
            print(f"   Path verificato: {aws_sso_path}")
            print("💡 Assicurati che la cartella contenga il file credential_manager.py")
            return False
        
        try:
            # Se stiamo riconfigurando, informa l'utente
            if env_file_path.exists():
                print("🔄 Aggiornamento file .env esistente...")
            else:
                print("📄 Creazione nuovo file .env...")
                
            env_file_result = create_env_file(aws_sso_path)
            print(f"✅ File .env aggiornato in: {env_file_result}")
            print("🎉 Setup completato con successo!")
            print()
            print("📋 La libreria riproverà automaticamente a caricare il modulo.")
            return True
        except Exception as e:
            print(f"❌ Errore durante la creazione del file .env: {e}")
            return False
    
    return False

if __name__ == "__main__":
    success = run_setup()
    if not success:
        print("⚠️ Setup non completato. La libreria non potrà utilizzare AWS SSO.")
        sys.exit(1)

