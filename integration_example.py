#!/usr/bin/env python3
"""
Script di esempio per l'integrazione della libreria mylib come submodule

Questo script mostra come integrare la libreria in qualsiasi progetto Python.
"""

import sys
import os

# Aggiungi la directory della libreria al Python path
# Questo permette di importare mylib da qualsiasi progetto che abbia library come submodule
library_path = os.path.join(os.path.dirname(__file__), 'library')
if library_path not in sys.path:
    sys.path.insert(0, library_path)

def main():
    """Esempio di utilizzo della libreria mylib"""
    
    print("🚀 Test integrazione libreria mylib")
    print("=" * 50)
    
    try:
        # Import della libreria
        # La libreria si auto-configura al primo import
        import mylib
        
        print("✅ Libreria mylib importata con successo!")
        
        # Test delle funzioni base
        print("\n📋 Test funzioni disponibili:")
        
        # Test di configurazione
        if hasattr(mylib, '_USE_SSO'):
            if mylib._USE_SSO:
                print("✅ AWS SSO Credential Manager: DISPONIBILE")
            else:
                print("⚠️  AWS SSO Credential Manager: NON DISPONIBILE")
        
        # Test UUID
        uuid = mylib.generateUUID()
        print(f"✅ UUID generato: {uuid}")
        
        # Test creazione cartella data
        from datetime import datetime
        date_folder = mylib.create_date_folder(datetime.now())
        print(f"✅ Cartella data: {date_folder}")
        
        # Test rilevamento WSL
        wsl_status = mylib.is_wsl()
        if wsl_status:
            print(f"✅ WSL rilevato (versione {wsl_status})")
        else:
            print("✅ Sistema non-WSL")
        
        print("\n🎉 Test completato con successo!")
        print("📚 La libreria è pronta per l'uso nel tuo progetto")
        
    except ImportError as e:
        print(f"❌ Errore import libreria: {e}")
        print("\n💡 Soluzioni possibili:")
        print("1. Verifica che la directory 'library' sia presente")
        print("2. Controlla che library contenga mylib.py")
        print("3. Esegui: git submodule update --init --recursive")
        return False
    
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
