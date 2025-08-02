# Changelog - MyLib

Tutte le modifiche notevoli a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-08-03

### Aggiunto
- **Auto-configurazione AWS SSO**: Setup automatico con ricerca dinamica del credential manager
- **Gestione dinamica .env**: Ricerca automatica del file .env nelle directory padre
- **Auto-riparazione**: Rilevamento e correzione automatica di configurazioni non valide
- **GUI per selezione manuale**: Dialog tkinter per selezione cartella se setup automatico fallisce
- **Ricaricamento in tempo reale**: Aggiornamento configurazione senza riavvio programma
- **Import dinamico robusto**: Multipli metodi di import per il modulo setup_aws_sso
- **Pulizia cache moduli**: Rimozione forzata dalla cache per reimport pulito
- **Validazione path**: Controllo automatico della validità dei path configurati
- **Sistema di fallback**: Logica progressiva da automatico a manuale a errore

### Modificato
- **Gestione credenziali**: Migrazione da path hardcoded a configurazione dinamica
- **Import credential_manager**: Da import statico a import dinamico con gestione errori
- **Struttura package**: Aggiunto __init__.py per uso come submodule
- **Documentazione**: README completo per integrazione come submodule

### Rimosso
- **Path hardcoded**: Eliminato path fisso per aws-sso-credential-manager
- **Dipendenza rigida**: Rimossa dipendenza obbligatoria da credential_manager

### Corretto
- **UX seamless**: Risolto problema di riavvio programma dopo setup
- **Gestione errori**: Migliorata gestione errori durante import e configurazione
- **Compatibilità import**: Risolti problemi di import relativo vs assoluto

## [1.0.0] - 2025-07-XX

### Aggiunto
- Versione iniziale con funzionalità base
- Gestione credenziali AWS con path hardcoded
- Funzioni utility per S3 e DynamoDB
- Supporto per operazioni ENEL

### Note di Migrazione da 1.0.0 a 2.0.0

#### Breaking Changes
- Il path hardcoded per aws-sso-credential-manager è stato rimosso
- È richiesta la configurazione tramite file .env o setup automatico

#### Migrazione Consigliata
1. Aggiorna tutti i progetti per utilizzare la library come submodule
2. Esegui il setup automatico al primo utilizzo
3. Verifica che il file .env sia creato correttamente
4. Testa l'import in ogni progetto

#### Benefici dell'Aggiornamento
- Configurazione automatica e dinamica
- Nessun path hardcoded da mantenere
- Setup guidato per nuovi utenti
- Maggiore flessibilità nell'installazione
- Auto-riparazione di configurazioni corrotte
