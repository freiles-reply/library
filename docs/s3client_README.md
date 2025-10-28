# s3client

## 📦 Installazione Dipendenze

### Dipendenze Python richieste:
- **boto3**: `pip install boto3`
- **tkinter**: 
  - Linux: `sudo apt-get install python3-tk`
  - macOS: Incluso in Python standard
  - Windows: Incluso in Python standard
- **aws CLI**: 
  - Linux: `sudo apt install awscli`
  - macOS: `brew install awscli`
  - Windows: Scarica da AWS

### Dipendenza per AWS SSO:
- **aws-sso-credential-manager**: Richiesto per l'autenticazione SSO
  - Il setup automatico ti guiderà alla configurazione
  - Supporta selezione manuale della cartella tramite dialog

## ⚠️ Dipendenze dismesse:
- **aws-adfs**: Non più supportato

## 🚀 Primo Utilizzo

La libreria si configura automaticamente al primo import:

```python
from library.mylib import getTempCredentials
```

Se necessario, il sistema ti guiderà attraverso:
1. 🔍 **Auto-discovery** di aws-sso-credential-manager
2. 📁 **Selezione manuale** tramite dialog (se auto-discovery fallisce)
3. ✅ **Configurazione automatica** del file .env

## 📋 Setup Manuale (Opzionale)

```bash
python3 -m library.setup_aws_sso
```
