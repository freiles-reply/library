# MyLib - Libreria Universale AWS SSO

Libreria Python universale per la gestione di credenziali AWS SSO, operazioni S3, DynamoDB e utility comuni per i progetti ENEL.

## Caratteristiche

- ✅ **Auto-configurazione AWS SSO**: Setup automatico con ricerca dinamica del credential manager
- ✅ **GUI per selezione manuale**: Dialog per la selezione della cartella se necessario
- ✅ **Auto-riparazione**: Rilevamento e correzione automatica di configurazioni non valide
- ✅ **Gestione dinamica .env**: Ricerca e creazione automatica del file di configurazione
- ✅ **Ricaricamento in tempo reale**: Aggiornamento della configurazione senza riavvio
- ✅ **Compatibilità universale**: Funziona come submodule in tutti i progetti

## Installazione come Submodule

### 1. Aggiungi il submodule al tuo progetto

```bash
# Nella directory del tuo progetto
git submodule add <URL_REPOSITORY_LIBRARY> library
git submodule update --init --recursive
```

### 2. Usa la libreria nel tuo codice

```python
import sys
import os

# Aggiungi la library al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'library'))

# Importa la libreria
import mylib

# La libreria si auto-configura automaticamente
# Se AWS SSO Credential Manager non è configurato, si avvierà il setup automatico
```

## Configurazione Automatica

La libreria si auto-configura al primo import:

1. **Ricerca file .env**: Cerca il file di configurazione nella directory corrente e nelle directory padre
2. **Verifica path AWS SSO**: Controlla se il path configurato è valido
3. **Setup automatico**: Se necessario, avvia il setup per configurare AWS SSO Credential Manager
4. **GUI fallback**: Se il setup automatico fallisce, apre un dialog per la selezione manuale

## File di Configurazione (.env)

La libreria crea automaticamente un file `.env` con:

```
AWS_SSO_CREDENTIAL_MANAGER_PATH=/path/to/aws-sso-credential-manager
```

Il file viene cercato in:
- Directory corrente
- Directory della libreria
- Directory padre della libreria
- Directory padre dell'eseguibile

## Dipendenze

- Python 3.7+
- boto3
- tkinter (per GUI)
- configparser
- pathlib

## Utilizzo nei Progetti

### Per progetti S3Client

```python
import sys
sys.path.insert(0, 'library')
import mylib

# Usa le funzioni per S3
config = mylib.load_config('config.json')
envprefix = mylib.envSaveTempCredentials(config)
```

### Per progetti AWSPM

```python
import sys
sys.path.insert(0, 'library')
import mylib

# Usa le funzioni per gestione AWS
# La libreria fornisce tutte le utility necessarie
```

### Per progetti DynamoClient

```python
import sys
sys.path.insert(0, 'library')
import mylib

# Usa le funzioni per DynamoDB
items = mylib.get_dynamodb_items('table_name')
```

## Setup Manuale

Se necessario, puoi eseguire il setup manualmente:

```bash
# Dalla directory del progetto
python3 -m library.setup_aws_sso
```

## Aggiornamento del Submodule

```bash
# Aggiorna la libreria alla versione più recente
git submodule update --remote library

# Commit delle modifiche
git add library
git commit -m "Aggiornamento libreria mylib"
```

## Struttura Files

```
library/
├── __init__.py          # Configurazione package
├── mylib.py             # Libreria principale
├── setup_aws_sso.py     # Setup automatico AWS SSO
└── README.md            # Questa documentazione
```

## Funzioni Principali

### Gestione Credenziali AWS
- `envSaveTempCredentials()` - Gestione credenziali temporanee
- `getTempCredentials()` - Ottenimento credenziali SSO
- `getRoleArn()` - Estrazione ruolo ARN

### Utility S3
- `downloadFileFromS3()` - Download file da S3
- `uploadFileToS3()` - Upload file su S3
- `getFileListSortedByDate()` - Lista file S3 ordinati per data

### Utility DynamoDB
- `get_dynamodb_items()` - Recupero items da tabella
- `update_dynamodb_entry()` - Aggiornamento entry

### Utility Generali
- `load_config()` / `save_config()` - Gestione configurazioni JSON
- `create_date_folder()` - Creazione cartelle con data
- `generateUUID()` - Generazione UUID

## Troubleshooting

### Errore "credential_manager not found"
La libreria avvierà automaticamente il setup. Se continua a non funzionare:
1. Verifica che aws-sso-credential-manager sia installato
2. Esegui manualmente: `python3 -m library.setup_aws_sso`

### Errore "tkinter not available"
Su alcuni sistemi potrebbe essere necessario installare tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (dovrebbe essere già incluso)
# Windows (incluso con Python)
```

### File .env non trovato
La libreria crea automaticamente il file .env. Se hai problemi:
1. Controlla i permessi della directory
2. Esegui il setup manuale
3. Crea manualmente il file .env con il path corretto

## Supporto

Per problemi o domande, verifica:
1. La configurazione di aws-sso-credential-manager
2. I permessi della directory
3. La presenza di tutte le dipendenze
