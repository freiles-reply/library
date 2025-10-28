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
    """Crea un file .env nella directory del progetto (root del repository).

    Cerca una directory root ragionevole (quella che contiene `library/` o `src/`).
    """
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent

    potential_roots = [
        script_dir,
        current_dir,
        script_dir.parent,
        current_dir.parent,
    ]

    project_root = None
    for root in potential_roots:
        if (root / 'library').exists() or (root / 'src').exists():
            project_root = root
            break

    if not project_root:
        project_root = script_dir

    env_file_path = project_root / '.env'

    with open(env_file_path, 'w') as f:
        f.write('# AWS SSO Credential Manager Configuration\n')
        f.write('# Generato automaticamente da setup_aws_sso.py\n')
        f.write(f'AWS_SSO_CREDENTIAL_MANAGER_PATH={aws_sso_path}\n')

    print(f"✅ File .env creato in: {env_file_path}")
    print(f"📂 Directory del progetto: {project_root}")
    return str(env_file_path)


def setup_environment_variable(aws_sso_path, permanent=True):
    """Imposta la variabile d'ambiente; se permanent=True, aggiunge al profilo shell dell'utente."""
    home = Path.home()
    if permanent:
        shell_files = [home / '.zshrc', home / '.bashrc', home / '.bash_profile', home / '.profile']
        shell_file = None
        for file in shell_files:
            if file.exists():
                shell_file = file
                break
        if not shell_file:
            shell_file = home / '.profile'
        with open(shell_file, 'a') as f:
            f.write('\n# AWS SSO Credential Manager Path\n')
            f.write(f'export AWS_SSO_CREDENTIAL_MANAGER_PATH="{aws_sso_path}"\n')
        print(f"✅ Variabile d'ambiente aggiunta a {shell_file}")
        print(f"🔄 Riavvia il terminale o esegui: source {shell_file}")
    else:
        os.environ['AWS_SSO_CREDENTIAL_MANAGER_PATH'] = aws_sso_path
        print("✅ Variabile d'ambiente impostata per questa sessione")

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
        print("ℹ️ aws-sso-credential-manager non trovato automaticamente.")
        print()
        print("Opzioni disponibili:")
        print("  1) Seleziona manualmente la cartella (GUI, se disponibile)")
        print("  2) Inserisci manualmente il path via input")
        print("  3) Annulla setup")
        print()

        choice = input("Scelta (1-3): ").strip()

        if choice == '1':
            print("� Apertura dialog per selezione manuale...")
            manual_path = select_aws_sso_path_manually()
            if manual_path:
                print(f"✅ Cartella selezionata: {manual_path}")
                aws_sso_path = manual_path
            else:
                print("❌ Selezione manuale fallita o annullata.")
                return False
        elif choice == '2':
            user_path = input("Inserisci il path completo di aws-sso-credential-manager: ").strip()
            if user_path:
                aws_sso_path = str(Path(user_path).expanduser().resolve())
            else:
                print("❌ Path non fornito. Setup annullato.")
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

            # Offri opzioni di configurazione: variabile permanente, sessione, o .env
            print()
            print("Scegli come configurare il path:")
            print("  1) Variabile d'ambiente permanente (aggiunta al profilo shell dell'utente)")
            print("  2) Solo per questa sessione")
            print("  3) Crea/aggiorna file .env nella root del progetto (raccomandato per submodule)")
            print()
            cfg_choice = input("Scelta (1-3): ").strip()

            if cfg_choice == '1':
                setup_environment_variable(aws_sso_path, permanent=True)
            elif cfg_choice == '2':
                setup_environment_variable(aws_sso_path, permanent=False)
            else:
                env_file_result = create_env_file(aws_sso_path)
                print(f"✅ File .env aggiornato in: {env_file_result}")

            print("🎉 Setup completato con successo!")
            print()
            print("📋 La libreria riproverà automaticamente a caricare il modulo.")
            return True
        except Exception as e:
            print(f"❌ Errore durante la configurazione: {e}")
            return False
    
    return False

if __name__ == "__main__":
    success = run_setup()
    if not success:
        print("⚠️ Setup non completato. La libreria non potrà utilizzare AWS SSO.")
        sys.exit(1)

