# Quick Reference - MyLib Submodule Integration

## Repository URL
```
git@github-reply:freiles-reply/library.git
```

## Comandi di Integrazione Rapida

### Aggiungi come submodule
```bash
git submodule add git@github-reply:freiles-reply/library.git library
git submodule update --init --recursive
```

### Aggiorna submodule
```bash
git submodule update --remote library
git add library
git commit -m "Update library submodule"
```

### Clone con submodules
```bash
git clone --recursive <URL_TUO_PROGETTO>
```

### Se hai già clonato senza --recursive
```bash
git submodule update --init --recursive
```

## Test di Integrazione

### Codice minimo per testare
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'library'))
import mylib
print("✅ MyLib integrata con successo!")
```

### Script di test completo
```bash
cd library
python3 integration_example.py
```

## Versioni Disponibili

- **v2.0.0**: Release completa con auto-configurazione AWS SSO
- **main**: Ultima versione di sviluppo

## Note
- La library è autosufficiente e si auto-configura
- Include AWS SSO Credential Manager integration
- Supporta GUI per configurazione manuale
- Compatible con tutti i progetti esistenti (s3client, awspm, dynamoClient)
