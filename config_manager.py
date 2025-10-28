import json
import os
from pathlib import Path


class ConfigManager:
    """Gestisce la configurazione per mylib.py (shared in library)"""
    
    def __init__(self, config_path=None):
        """Inizializza il configuration manager
        
        Args:
            config_path: Path al file di configurazione (opzionale)
        """
        if config_path is None:
            # Cerca il file di configurazione nella stessa directory di questo file
            current_dir = Path(__file__).parent
            config_path = current_dir / "mylib_config.json"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self):
        """Carica la configurazione dal file JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ File di configurazione non trovato: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"⚠️ Errore nel parsing del file di configurazione: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Restituisce la configurazione di default"""
        return {
            "paths": {
                "aws_sso_credential_manager": "/Users/francescofreiles/Library/CloudStorage/OneDrive-Personal/Devel/GIT/aws-sso-credential-manager",
                "aws_credentials_dir": ".aws",
                "aws_credentials_file": "credentials"
            },
            "aws": {
                "default_region": "eu-central-1",
                "account_id_length": 12,
                "min_account_id_length": 10
            },
            "timeouts": {
                "file_dialog_delay": 3,
                "sso_session_timeout": 120
            }
        }
    
    def get(self, key_path, default=None):
        """Ottiene un valore dalla configurazione usando una chiave con path
        
        Args:
            key_path: Chiave con path separato da punti (es. "aws.default_region")
            default: Valore di default se la chiave non esiste
            
        Returns:
            Il valore dalla configurazione o il default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value):
        """Imposta un valore nella configurazione
        
        Args:
            key_path: Chiave con path separato da punti
            value: Valore da impostare
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """Salva la configurazione corrente nel file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ Errore nel salvataggio della configurazione: {e}")
            return False
    
    def get_aws_sso_path(self):
        """Ottiene il path del AWS SSO Credential Manager"""
        return self.get('paths.aws_sso_credential_manager')
    
    def get_default_region(self):
        """Ottiene la regione AWS di default"""
        return self.get('aws.default_region')
    
    def get_timeout(self, timeout_type):
        """Ottiene un timeout specifico"""
        return self.get(f'timeouts.{timeout_type}', 5)
    
    def update_aws_sso_path(self, new_path):
        """Aggiorna il path del AWS SSO Credential Manager"""
        self.set('paths.aws_sso_credential_manager', new_path)
        return self.save()
    
    def update_region(self, new_region):
        """Aggiorna la regione di default"""
        self.set('aws.default_region', new_region)
        return self.save()


# Istanza globale del configuration manager
config = ConfigManager()
