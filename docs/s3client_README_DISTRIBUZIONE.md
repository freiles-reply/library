# Guida alla Distribuzione - s3client

Questa guida spiega come distribuire e configurare la libreria `s3client` con supporto AWS SSO automatico.

## ✨ **Caratteristiche Principali**

- **✅ Setup Automatico**: Configurazione automatica di AWS SSO al primo utilizzo
- **🔍 Auto-Discovery**: Ricerca automatica di aws-sso-credential-manager in percorsi comuni
- **📄 File .env**: Configurazione locale tramite file .env
- **🎯 Zero Configurazione**: Funziona out-of-the-box nella maggior parte dei casi

## 📦 **Installazione e Primo Utilizzo**

### 1. **Setup Automatico (Raccomandato)**

Al primo import della libreria, se `aws-sso-credential-manager` non è disponibile, verrà automaticamente proposto il setup:

```python
from library.mylib import getTempCredentials
```

Se aws-sso-credential-manager è presente ma non configurato, il sistema:
1. 🔍 Cerca automaticamente il tool in percorsi comuni
2. 💬 Chiede conferma del path trovato
3. ✅ Crea automaticamente il file `.env` 
4. 🎯 Rende disponibile AWS SSO

## 🛠️ **Per lo Sviluppatore (Chi Distribuisce)**

### **Come Preparare la Distribuzione**

1. **Copia i file necessari**:
   ```
   cartella_distribuzione/
   ├── library/
   │   └── mylib.py (senza path hardcoded!)
   ├── setup_aws_sso.py
   ├── setup_aws_sso.sh  
   └── README_DISTRIBUZIONE.md (questo file)
   ```

2. **Fornisci istruzioni chiare**:
   - Includi questo README
   - Specifica dove l'utente può trovare aws-sso-credential-manager
   - Fornisci esempi di path comuni per il sistema target

## 🔍 **Risoluzione Problemi**

### **"AWS SSO Credential Manager non trovato"**
1. Verifica che aws-sso-credential-manager sia installato
2. Controlla che il path sia corretto
3. Esegui lo script di setup: `python3 setup_aws_sso.py`

### **"Import credential_manager non riuscito"**
1. Verifica che il path punti alla directory corretta
2. Controlla che il file `credential_manager.py` esista nel path specificato

## ⚡ **Quick Start per l'Utente**

```bash
# 1. Scarica/ricevi i file della libreria
# 2. Esegui setup automatico:
python3 setup_aws_sso.py

# 3. Testa:
python3 -c "from library.mylib import getTempCredentials; print('✅ Configurazione OK!')"
```
