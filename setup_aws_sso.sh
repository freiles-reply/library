#!/bin/bash

# 🔧 Setup Script per AWS SSO Credential Manager (copiato da s3client)
# ================================================================

echo "🚀 Setup AWS SSO Credential Manager per mylib.py"
echo "=================================================="
echo

# Funzione per trovare automaticamente il path
find_aws_sso_path() {
    local paths=(
        "./aws-sso-credential-manager"
        "../aws-sso-credential-manager"
        "~/tools/aws-sso-credential-manager"
        "~/aws-sso-credential-manager"
        "/opt/aws-sso-credential-manager"
        "/usr/local/bin/aws-sso-credential-manager"
    )
    
    for path in "${paths[@]}"; do
        expanded_path=$(eval echo "$path")
        if [ -d "$expanded_path" ] || [ -f "$expanded_path" ]; then
            echo "$expanded_path"
            return 0
        fi
    done
    return 1
}

# Prova a trovare automaticamente il path
echo "🔍 Ricerca automatica di aws-sso-credential-manager..."
auto_path=$(find_aws_sso_path)

if [ -n "$auto_path" ]; then
    echo "✅ Trovato automaticamente: $auto_path"
    aws_sso_path="$auto_path"
    read -p "Usare questo path? (y/n): " confirm
    if [[ $confirm =~ ^[Nn]$ ]]; then
        aws_sso_path=""
    fi
fi

# Se non trovato automaticamente o utente ha rifiutato, chiedi manualmente
if [ -z "$aws_sso_path" ]; then
    echo "📁 Inserisci il path completo di aws-sso-credential-manager:"
    echo "   Esempi:"
    echo "   - /Users/tuoutente/tools/aws-sso-credential-manager"
    echo "   - /opt/aws-sso-credential-manager"
    echo "   - ./aws-sso-credential-manager"
    echo
    read -p "Path: " aws_sso_path
    
    # Espandi ~ se presente
    aws_sso_path=$(eval echo "$aws_sso_path")
fi

# Verifica che il path sia valido
if [ ! -d "$aws_sso_path" ] && [ ! -f "$aws_sso_path" ]; then
    echo "❌ Errore: Path non valido o non esistente: $aws_sso_path"
    echo "Verifica che aws-sso-credential-manager sia installato e accessibile."
    exit 1
fi

echo "✅ Path verificato: $aws_sso_path"

# Opzione 1: Imposta variabile d'ambiente permanentemente
echo
echo "🎯 Scegli come configurare il path:"
echo "1. Variabile d'ambiente permanente (raccomandato)"
echo "2. Solo per questa sessione"
echo "3. Crea file di configurazione locale"

read -p "Scelta (1-3): " choice

case $choice in
    1)
        # Determina il file di shell profile
        if [ -f "$HOME/.zshrc" ]; then
            shell_file="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            shell_file="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            shell_file="$HOME/.bash_profile"
        else
            shell_file="$HOME/.profile"
        fi
        
        echo "export AWS_SSO_CREDENTIAL_MANAGER_PATH=\"$aws_sso_path\"" >> "$shell_file"
        echo "✅ Variabile d'ambiente aggiunta a $shell_file"
        echo "🔄 Riavvia il terminale o esegui: source $shell_file"
        ;;
        
    2)
        export AWS_SSO_CREDENTIAL_MANAGER_PATH="$aws_sso_path"
        echo "✅ Variabile d'ambiente impostata per questa sessione"
        echo "💡 Per impostarla permanentemente, esegui:"
        echo "   export AWS_SSO_CREDENTIAL_MANAGER_PATH=\"$aws_sso_path\""
        ;;
        
    3)
        # Cerca una directory root ragionevole (quella che contiene 'library' o 'src')
        project_root=""
        if [ -d "./library" ]; then
            project_root="."
        elif [ -d "../library" ]; then
            project_root=".."
        elif [ -d "$(pwd)/library" ]; then
            project_root="$(pwd)"
        else
            project_root="."
        fi

        echo "AWS_SSO_CREDENTIAL_MANAGER_PATH=$aws_sso_path" > "$project_root/.env"
        echo "✅ File .env creato in: $project_root/.env"
        echo "💡 La libreria caricherà automaticamente questo file"
        ;;
        
    *)
        echo "❌ Scelta non valida"
        exit 1
        ;;
esac

echo
echo "🎉 Setup completato!"
echo "📋 Per testare la configurazione, esegui:"
echo "   python3 -c \"import os; print('Path:', os.environ.get('AWS_SSO_CREDENTIAL_MANAGER_PATH', 'Non impostato'))\""
echo
echo "📚 La libreria mylib.py ora dovrebbe funzionare correttamente!"
