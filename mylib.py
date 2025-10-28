#import requests
#import argparse
import configparser
import os
import re
import time
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import filedialog
import json
import boto3
import platform
import sys

# Import inquirer per menu interattivi (frecce)
try:
    import inquirer
    INQUIRER_AVAILABLE = True
except Exception:
    INQUIRER_AVAILABLE = False

# Funzione di utilità: ricerca file .env risalendo la gerarchia
def find_env_file():
    """Cerca il file .env partendo dalla directory corrente e risalendo fino alla directory padre"""
    current_dir = os.getcwd()
    search_dirs = [
        current_dir,
        os.path.dirname(__file__),
        os.path.dirname(os.path.dirname(__file__)),
    ]
    parent_dir = os.path.dirname(current_dir)
    if parent_dir != current_dir:
        search_dirs.append(parent_dir)

    for search_dir in search_dirs:
        env_file = os.path.join(search_dir, '.env')
        if os.path.exists(env_file):
            return env_file
    return None


# Carica variabili dal file .env (se presente)
env_file = find_env_file()
if env_file:
    try:
        print(f"📄 Caricamento configurazione da {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except Exception:
        # Non bloccare l'import se il .env è malformato
        pass

# Determina il path di aws-sso-credential-manager (variabile d'ambiente o percorsi comuni)
aws_sso_path = os.environ.get('AWS_SSO_CREDENTIAL_MANAGER_PATH')
if not aws_sso_path:
    common_paths = [
        "./aws-sso-credential-manager",
        "../aws-sso-credential-manager",
        "~/tools/aws-sso-credential-manager",
        "/opt/aws-sso-credential-manager",
        "/usr/local/bin/aws-sso-credential-manager",
    ]
    for path in common_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            aws_sso_path = expanded_path
            print(f"🔍 AWS SSO Credential Manager trovato in: {aws_sso_path}")
            break

    if not aws_sso_path:
        print("⚠️ AWS SSO Credential Manager non trovato.")
        print("💡 Imposta AWS_SSO_CREDENTIAL_MANAGER_PATH oppure crea un .env con il path")

if aws_sso_path and aws_sso_path not in sys.path:
    sys.path.insert(0, aws_sso_path)


# Importa direttamente la classe AWSCredentialManager, con fallback di setup automatico
try:
    from credential_manager import AWSCredentialManager
    _USE_SSO = True
    print("🎯 AWS SSO Credential Manager disponibile")
except ImportError as e:
    print(f"⚠️ AWS SSO non disponibile: {e}")
    _USE_SSO = False

    # Proviamo un setup automatico simile a quello usato in consumer che includono setup_aws_sso
    try:
        setup_aws_sso = None
        # Tentativi multipli di import per essere robusti
        try:
            from . import setup_aws_sso
        except Exception:
            try:
                import setup_aws_sso
            except Exception:
                # Import dinamico dal file presente nella stessa directory di questo modulo
                import importlib.util
                setup_file = os.path.join(os.path.dirname(__file__), 'setup_aws_sso.py')
                if os.path.exists(setup_file):
                    spec = importlib.util.spec_from_file_location('setup_aws_sso', setup_file)
                    setup_aws_sso = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(setup_aws_sso)

        if setup_aws_sso is None:
            raise ImportError('Impossibile importare setup_aws_sso')

        print('🔧 Tentativo di configurazione automatica di aws-sso-credential-manager...')
        setup_success = False
        try:
            setup_success = setup_aws_sso.run_setup()
        except Exception:
            # run_setup può non esistere o fallire; non blocchiamo l'import
            setup_success = False

        if setup_success:
            # Ricarica eventuale .env aggiornato
            env_file = find_env_file()
            if env_file:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'AWS_SSO_CREDENTIAL_MANAGER_PATH':
                                new_aws_sso_path = value.strip()
                                if os.path.exists(new_aws_sso_path):
                                    if aws_sso_path and aws_sso_path in sys.path:
                                        try:
                                            sys.path.remove(aws_sso_path)
                                        except Exception:
                                            pass
                                    if new_aws_sso_path not in sys.path:
                                        sys.path.insert(0, new_aws_sso_path)
                                    aws_sso_path = new_aws_sso_path

            # Riproviamo l'import
            try:
                if 'credential_manager' in sys.modules:
                    del sys.modules['credential_manager']
                from credential_manager import AWSCredentialManager
                _USE_SSO = True
                print('✅ AWS SSO Credential Manager ora disponibile!')
            except Exception:
                print('❌ Il modulo credential_manager non è ancora disponibile dopo il setup.')
    except Exception:
        # Non forziamo un'eccezione all'import del modulo library: semplicemente proseguiamo senza SSO
        _USE_SSO = False

def is_wsl(v: str = platform.uname().release) -> int:
    """
    detects if Python is running in WSL
    """
    if v.endswith("-Microsoft"):
        return 1
    elif v.endswith("microsoft-standard-WSL2"):
        return 2
    return 0

# Crea una cartella con il formato 'YYYYMMDD'
def create_date_folder(date):
    return date.strftime("%Y%m%d")

# Salva la configurazione in un file JSON
def save_config(config_var, config_file):
    with open(config_file, 'w') as config:
        json.dump(config_var, config, indent=4)

# Carica la configurazione da un file JSON
def load_config(config_json):
    if os.path.exists(config_json):
        with open(config_json, 'r') as config_file:
            return json.load(config_file)
    return None

# Splitta una stringa in una parte centrale e finale per mezzo di un separatore
def getStringParts(strng, sep):
    parts = re.split(f'[{sep}]', strng)
    centralPart = parts[1]
    finalPart = parts[-1]
    return centralPart, finalPart

# Genera il file delle credenziali Enel per aws
def saveCredentials(user, passwd, name=None):
    if name:
        print("Creo il file delle credenziali ENEL...")
        with open(name, 'w') as file:
            file.write("[default]\n")
            file.write(f"username = {user}\n")
            file.write(f"password = {passwd}\n")
    print("Salvo come variabili di ambiente le credenziali ENEL...")
    os.environ['username'] = user
    os.environ['password'] = passwd

# Ciclo attraverso tutti i file nella directory corrente ed elimina quelli più vecchi di un certo numero di secondi
def listAndDeleteFiles(file_pattern, secs, current_time):
    for filename in os.listdir():
        match = re.match(file_pattern, filename)
        if match:
            file_time = match.group(1)  # Estrai la data/ora dal nome del file
            file_datetime = datetime.strptime(file_time, "%Y%m%d%H%M")
            # Confronta la data/ora attuale con la data/ora del file + 1 ora
            if (file_datetime + timedelta(seconds=secs)) < current_time:
                os.remove(filename)
                print(f"\nFile '{filename}' rimosso.\n")

# Seleziona il path della home directory dove solitamente risiede la folder .aws che ospita le credenziali temporanee
def createHomeDirPath(name):
    if not os.path.exists(name):
        # Crea una finestra principale nascosta
        root = tk.Tk()
        root.withdraw()

        # Apre la finestra di dialogo per selezionare un percorso (in questo caso la home Dir)
        print("\nSELEZIONA LA TUA HOME DIRECTORY PER IL SALVATAGGIO DELLE CREDENZIALI (ES. windows: C:\\Users\\NomeUtente ; Linux/MacOS /home/NomeUtente)\n")
        time.sleep(3)
        homeDir = filedialog.askdirectory(title="Seleziona la tua Home Directory (ES. windows: C:\\Users\\NomeUtente ; Linux/MacOS /home/NomeUtente)")
        home = open(name, "w")
        home.write(homeDir)
        home.close()
    else:
        with open(name, "r") as home:
            homeDir = home.read()
    return homeDir

# Trova tutti i file nella directory corrente che iniziano con il prefisso del ruolo di default
def enumerateCredentialFiles(defaultRole):
    selected_file = None
    aws_access_key_id = None
    aws_secret_access_key = None
    aws_session_token = None
    aws_security_token = None
    file_list = [file for file in os.listdir() if file.startswith(defaultRole)]
    if file_list :
        # Stampa l'elenco numerato dei file
        print("\nElenco dei file disponibili:\n")
        for index, file_name in enumerate(file_list, start=1):
            print(f"{index}. {file_name}")

        # Chiedi all'utente di selezionare un numero
        choice = input("\nSeleziona un numero (0 per uscire): ")

        # Verifica la scelta dell'utente
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(file_list):
                selected_file = file_list[choice - 1]

                # Crea un oggetto ConfigParser
                projRoleCred = configparser.ConfigParser()

                # Leggi il file di configurazione
                projRoleCred.read(selected_file)

                # Estrai le chiavi e i valori dal file
                aws_access_key_id = projRoleCred['default']['aws_access_key_id']
                aws_secret_access_key = projRoleCred['default']['aws_secret_access_key']
                aws_session_token = projRoleCred['default']['aws_session_token']
                aws_security_token = projRoleCred['default']['aws_security_token']

                # Dividi il nome del file utilizzando l'underscore come separatore
                parts = selected_file.split('_')

                # Verifica se ci sono almeno due parti (prima e dopo l'underscore)
                if len(parts) >= 2:
                    # La parte prima dell'underscore è la prima parte
                    role_arn = parts[0]
                    #print(role_arn)

                    pattern = r'esol-ap\d+-\w+'
                    matches = re.findall(pattern, role_arn)
                    if matches:
                        project_name = matches[0].replace("-", "_")
                        #print(project_name)

                role = re.search(re.escape(project_name), role_arn)
                if role:
                    # Estrai il ruolo
                    roleName = role_arn[:role.start()]
                
                #if roleName.endswith("-"):
                #    roleName = roleName[:-1]
                #    #print(pureRoleName)
                return selected_file, aws_access_key_id, aws_secret_access_key, aws_session_token, aws_security_token
            
            elif choice == 0:
                print("\nHai scelto di proseguire senza utilizzare le credenziali già disponibili.\n")
                return None
            else:
                print("\nScelta non valida, si procederà con nuove credenziali temporanee.n")
                return None
        else:
            print("\nInput non valido. Si procederà con nuove credenziali temporanee.\n")
            return None
        
def envSaveTempCredentials(config, awsauth=None, roleName=None):
    rows = []

    basicRolePrefix = config["configuration"]["generic"]["role"]["value"]
    homeDirFileName = config["configuration"]["generic"]["homeDirFileName"]["value"]
    #credentialFile = config["configuration"]["generic"]["credentialFile"]["value"]
    defaultRole = config["configuration"]["generic"]["defaultRole"]["value"]

    user = config["enelCredentials"]["user"]
    passwd = config["enelCredentials"]["passwd"]

    if awsauth:
        saveCredentials(user, passwd, awsauth)
    else:
        saveCredentials(user, passwd)

    homeDir = createHomeDirPath(homeDirFileName)

    file_pattern = r"^"+basicRolePrefix+r".*_(\d{12})\..*$"
    print(f"\nPattern per la ricerca dei file: {file_pattern}\n")
    secs = float(config["configuration"]["timeToDelete"]["seconds"])
    current_time = datetime.now()

    listAndDeleteFiles(file_pattern, secs, current_time)

    # Stampa il percorso selezionato
    print("Percorso selezionato della home directory:", homeDir)
    if roleName is None:
        result = enumerateCredentialFiles(defaultRole)
    else:
        result = enumerateCredentialFiles(roleName)

    if result == None:
        print(f"Si procederà al prelievo delle credenziali temporanee modificando le variabili dell'ambiente scelto...\n")
        tempCredentials, role_arn = getTempCredentials(homeDir, config)
        
        # Per SSO, crea direttamente il selectedFile e salta saveTempCredentials
        if _USE_SSO:
            import time
            current_time = time.strftime("%Y%m%d%H%M")
            
            # Crea un nome file basato sul role_arn per compatibilità con extract_string
            if role_arn and role_arn.isdigit():
                # È un account ID, crea un nome progetto fittizio
                selectedFile = f"esol-ap-{role_arn}_{current_time}.txt"
            elif role_arn and 'esol' in role_arn:
                # Usa il role_arn che contiene 'esol'
                selectedFile = f"{role_arn}_{current_time}.txt"
            else:
                # Fallback generico
                selectedFile = f"esol-ap-unknown_{current_time}.txt"
            
            # Leggi le credenziali dal file AWS che abbiamo creato
            import configparser
            aws_config = configparser.ConfigParser()
            aws_config.read(tempCredentials)
            
            access_key = aws_config['default']['aws_access_key_id']
            secret_key = aws_config['default']['aws_secret_access_key']
            session_token = aws_config['default']['aws_session_token']
            security_token = aws_config['default']['aws_security_token']
        else:
            selectedFile = saveTempCredentials(tempCredentials, role_arn, rows)

            # Check if 'rows' has enough elements
            if len(rows) < 5:
                print("Errore: Le credenziali temporanee non sono state recuperate correttamente.")
                raise IndexError("Le credenziali temporanee non contengono tutti i valori necessari.")
            access_key = rows[1]
            secret_key = rows[2]
            session_token = rows[3]
            security_token = rows[4]
    else:
        try:
            selectedFile, access_key, secret_key, session_token, security_token = result
            print(f"File selezionato: {selectedFile}.\nAcquisisco le credenziali temporanee...")
            role_arn = getRoleArn(homeDir, config)
        except ValueError:
            print("Errore: Il risultato non contiene tutti i valori necessari.")
            raise

    envprefix = extract_string(selectedFile)

    config["awsCredentials"]["aws_access_key_id"] = access_key
    config["awsCredentials"]["aws_secret_access_key"] = secret_key
    config["awsCredentials"]["aws_session_token"] = session_token
    config["awsCredentials"]["aws_security_token"] = security_token

    print("Salvo le credenziali temporanee nelle relative variabili di ambiente...")
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    os.environ['AWS_SESSION_TOKEN'] = session_token
    os.environ['AWS_SECURITY_TOKEN'] = security_token
    os.environ['AWS_DEFAULT_REGION'] = 'eu-central-1'  # Region di default per ENEL
    print(envprefix)
    return envprefix

def filterFileList(objects, filter):
    # Specifica il filtro (esempio: file che contengono 'fjb' o cartelle che contengono 'CP')
    if filter is None:
        filter = input('\ninserisci il filtro desiderato: ')  # Sostituisci con il filtro desiderato

    # Filtra gli oggetti in base al filtro
    filtered_objects = [obj for obj in objects.get('Contents', []) if filter in obj['Key']]
    return filtered_objects

def getFileListSortedByDate(bucket, folderKey, subFolderKey, filter, num_days):
    if subFolderKey is not None:
        folderKey = f"{folderKey}/{subFolderKey}"
    
    # Crea un client S3
    s3 = boto3.client('s3')

    # Specifica il filtro (esempio: file che contengono 'fjb' o cartelle che contengono 'CP')
    #filter = str(input('\ninserisci il filtro desiderato: '))  # Sostituisci con il filtro desiderato
    Key=f"{folderKey}"

    print(f"{bucket}/{Key}")
    
    objects = s3.list_objects_v2(Bucket=bucket, Prefix=Key)
    filtered_objects = filterFileList(objects, filter)

#    print(objects)
#    filtered_objects = filterFileList(objects, Key)
#    filtered_objects = [obj for obj in objects.get('Contents', [])]
#    print(filtered_objects)

    # Chiedi all'utente il numero di giorni da considerare
    if num_days is None:    
        num_days = input("\nInserisci il numero di giorni precedenti ad oggi per cui visualizzare i file: ")

    if num_days.strip() == "":
        num_days = "10"
        print(f"\nVerranno visualizzati i file recenti risalenti agli ultimi {num_days} giorni...")

    num_days = int(num_days)

    # Calcola la data di num_days fa
    num_days_ago = datetime.now(timezone.utc) - timedelta(days=num_days)

    # Filtra e ordina gli oggetti in base alla data
    recent_objects = [obj for obj in filtered_objects if obj['LastModified'].replace(tzinfo=timezone.utc) >= num_days_ago]
        
    recent_objects.sort(key=lambda x: x['LastModified'], reverse=True)

    # Inizializza la variabile i a 0
    i = 0

    # Stampa l'elenco dei file recenti enumerati
    print(f"\nFile nella folder {folderKey} degli ultimi {num_days} giorni (dal più recente al più vecchio):\n")
    for obj in recent_objects:
        i += 1
        print(f"\n{i}. Nome: {obj['Key']}  Data di modifica: {obj['LastModified']}\n")
    return recent_objects, num_days, i

def getFileListSortedByCount(bucket, folderKey, subFolderKey, filter, num_files):
    if subFolderKey is not None:
        folderKey = f"{folderKey}/{subFolderKey}"
    #print(subFolderKey)

    # Crea un client S3
    s3 = boto3.client('s3')

    #filtered_objects = filterFileList(objects)
    # Specifica il filtro (esempio: file che contengono 'fjb' o cartelle che contengono 'CP')
    #filter = input('\ninserisci il filtro desiderato: ')  # Sostituisci con il filtro desiderato
    Key=f"{folderKey}"

    print(f"{bucket}/{Key}")

    objects = s3.list_objects_v2(Bucket=bucket, Prefix=Key)
    filtered_objects = filterFileList(objects, filter)

#    print(objects)
#    filtered_objects = filterFileList(objects, Key)
#    filtered_objects = [obj for obj in objects.get('Contents', [])]
#    print(filtered_objects)

    # Chiedi all'utente il numero di file da visualizzare
    if num_files is None:
        num_files = input("\nInserisci il numero di file da visualizzare: ")

    if num_files.strip() == "":
        num_files = 10  # Imposta un valore predefinito se l'utente non inserisce nulla
        print(f"\nVerranno visualizzati i primi {num_files} file...")

    num_files = int(num_files)

    # Ordina gli oggetti per data di modifica in ordine decrescente
    filtered_objects.sort(key=lambda x: x['LastModified'], reverse=True)

    # Prendi i primi "num_files" oggetti
    recent_objects = filtered_objects[:num_files]

    # Inizializza la variabile i a 0
    i = 0

    # Stampa l'elenco dei file recenti enumerati
    print(f"\nFile nella folder {folderKey} (primi {num_files} file per data di modifica):\n")
    for obj in recent_objects:
        i += 1
        print(f"\n{i}. Nome: {obj['Key']}  Data di modifica: {obj['LastModified']}\n")
    return recent_objects, num_files, i

def getEnumFileListSortedByDate(objects):
    # Chiedi all'utente quali file scaricare
    files = input("\nInserisci il/i numero/i del/dei file/s da elaborare [separati da virgola. (digitare ALL per selezionare tutti i files)]: ")

    if not files:
        print("\nNessun file selezionato.\n")
        exit(1)
    elif files == 'ALL':
        ans = input('\nAttenzione!!! saranno selezionati tutti i file, SEI SICURO DI VOLER PROSEGUIRE? (YES per accettare): ')
        if ans =='YES':
            files = list(range(1, len(objects) + 1))
            print(f'\nTutti i file verranno selezionati! {files}\n')
        else:
            print('\nNon è stata confermata la selezione di tutti i file il programma terminerà\n')
            exit(1)
    else:
        files = [int(num.strip()) for num in files.split(',') if num.strip().isdigit()]
    return files

def getFileNamesAndDates(files, objects, path_list, name_list, date_list):
    for file_number in files:
        if 1 <= file_number <= len(objects):
            selected_object = objects[file_number - 1]
            file_path = selected_object['Key']  # Ottieni tutto il path
            file_name = os.path.basename(selected_object['Key'])  # Ottieni solo il nome del file
            file_date = selected_object['LastModified']
            path_list.append(file_path)
            name_list.append(file_name)
            date_list.append(file_date)
        else:
            print(f"\nNumero '{file_number}' non valido. Ignorato.\n")
            exit(1)

def getTempCredentials(homeDir, configJson):
    """
    Ottiene credenziali temporanee AWS tramite SSO usando il tuo credential_manager.py
    """
    if _USE_SSO:
        try:
            print("🔐 === Autenticazione AWS SSO ===")
            
            # Istanzia direttamente la classe AWSCredentialManager
            credential_manager = AWSCredentialManager()
            
            # Prima cleanup file scaduti
            credential_manager.cleanup_expired_files()
            
            # Controlla se ci sono file validi esistenti (solo per info, non per bloccare)
            valid_files = credential_manager.get_valid_credential_files()
            
            if not valid_files:
                print("🎯 Nessun file SSO valido trovato - il credential manager gestirà la configurazione")
            else:
                print("🎯 File SSO validi trovati - avvio menu di selezione profilo SSO...")
            
            # Usa sempre il processo SSO completo (gestisce sia configurazione che selezione)
            print("🚀 Avvio processo di autenticazione SSO...")
            
            # Assicurati che l'output sia visibile in tempo reale
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            
            # Il credential_manager gestisce tutto: file esistenti, menu, rigenerazione, configurazione
            # MODIFICATO: credential_manager.py ora mostra l'output SSO direttamente (no capture_output)
            result = credential_manager.process_sso_authentication()
            
            # CONTROLLO USCITA UTENTE: Se il process_sso_authentication ritorna False o un valore 
            # che indica uscita dell'utente, termina il programma invece di andare in fallback
            if result is False or (isinstance(result, str) and result.lower() in ['exit', 'quit', 'esci']):
                print("👋 Utente ha scelto di uscire dal menu SSO - terminazione programma")
                import sys
                sys.exit(0)
            
            # IMPORTANTE: Il process_sso_authentication può gestire profili esistenti internamente
            # Se l'utente ha selezionato un profilo esistente, dobbiamo intercettare questa scelta
            # e non procedere con il "file più recente" ma con il profilo effettivamente selezionato
            
            # Ottieni i file validi dopo il processo SSO (potrebbero essere stati creati nuovi file)
            valid_files_after = credential_manager.get_valid_credential_files()
            
            # Se non ci sono file validi dopo il processo E l'utente non è uscito volontariamente,
            # potrebbe essere un errore o l'utente potrebbe aver scelto di uscire in modo diverso
            if not valid_files_after:
                # Controlla se l'utente ha veramente scelto di uscire controllando se result è None
                # in combinazione con l'assenza di file validi
                if result is None:
                    print("👋 Nessun profilo selezionato - l'utente potrebbe aver scelto di uscire")
                    print("🚪 Terminazione programma")
                    import sys
                    sys.exit(0)
                else:
                    raise Exception("Nessun file SSO valido disponibile dopo il processo di autenticazione")
            
            # CORREZIONE CRITICA: Non prendere il file più recente!
            # Il problema è che quando l'utente seleziona un profilo nel menu del credential manager,
            # noi ignoriamo questa selezione e prendiamo sempre il file più recente.
            # Dobbiamo invece cercare di capire quale profilo è stato effettivamente selezionato.
            
            # Strategia: Confronta i file prima e dopo per vedere se ne è stato aggiunto uno nuovo
            # Se non è stato aggiunto nessun file nuovo, significa che l'utente ha selezionato un profilo esistente
            files_before_names = set(f[0] for f in valid_files) if valid_files else set()
            files_after_names = set(f[0] for f in valid_files_after)
            
            new_files = files_after_names - files_before_names
            
            if new_files:
                # È stato creato un nuovo file - usa quello
                new_file_name = list(new_files)[0]
                selected_file = next(f for f in valid_files_after if f[0] == new_file_name)
                print(f"🆕 Nuovo file SSO creato: {selected_file[1] if len(selected_file) > 1 else 'unknown'}")
            else:
                # Nessun nuovo file - l'utente ha probabilmente selezionato un profilo esistente
                # In questo caso, non possiamo sapere quale profilo è stato selezionato dal menu
                # perché il credential manager non ci passa questa informazione
                
                # SOLUZIONE: Controlla se le variabili d'ambiente sono già state impostate dal credential manager
                if os.environ.get('AWS_ACCESS_KEY_ID'):
                    print("🔍 Rilevate credenziali AWS già impostate dal credential manager")
                    
                    # Trova il file corrispondente alle credenziali attuali
                    current_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
                    matching_file = None
                    
                    for file_info in valid_files_after:
                        if len(file_info) >= 5:  # Ha contenuto credenziali
                            content = file_info[4]
                            if current_access_key in content:
                                matching_file = file_info
                                break
                    
                    if matching_file:
                        selected_file = matching_file
                        print(f"✅ Trovato profilo corrispondente alle credenziali attuali: {selected_file[1] if len(selected_file) > 1 else 'unknown'}")
                    else:
                        # CONTROLLO PRIMA DEL FALLBACK: Verifica se l'utente ha scelto di uscire
                        if result is None:
                            print("🚪 Nessun profilo corrispondente trovato e processo SSO terminato - possibile uscita utente")
                            print("👋 Terminazione programma")
                            import sys
                            sys.exit(0)
                        
                        # Fallback: usa il file più recente SOLO se non è un'uscita
                        files_sorted = sorted(valid_files_after, key=lambda x: x[2] if len(x) > 2 else "", reverse=True)
                        selected_file = files_sorted[0]
                        print("⚠️  Fallback: usando file più recente disponibile")
                else:
                    # CONTROLLO AGGIUNTIVO: Prima del fallback, verifica se l'utente ha scelto di uscire
                    # Se result è None e non ci sono credenziali ambiente, potrebbe significare uscita
                    if result is None and not os.environ.get('AWS_ACCESS_KEY_ID'):
                        print("🚪 Nessuna credenziale disponibile e processo SSO terminato - possibile uscita utente")
                        print("👋 Terminazione programma")
                        import sys
                        sys.exit(0)
                    
                    # Fallback: usa il file più recente SOLO se siamo sicuri che non è un'uscita
                    files_sorted = sorted(valid_files_after, key=lambda x: x[2] if len(x) > 2 else "", reverse=True)
                    selected_file = files_sorted[0]
                    print("⚠️  Fallback: usando file più recente disponibile")
            
            if not selected_file or len(selected_file) < 5:
                raise Exception("File SSO non valido o incompleto")
            
            # Il processo SSO deve permettere all'utente di scegliere il profilo
            # Controlla se l'utente ha selezionato un profilo ENEL (che contiene 'esol-')
            profile_name = selected_file[1] if len(selected_file) > 1 else "unknown"
            timestamp = selected_file[2] if len(selected_file) > 2 else "N/A"
            
            print(f"🎯 Profilo selezionato dall'utente: {profile_name} (timestamp: {timestamp})")
            
            # IMPORTANTE: Non forzare il nome del profilo! Usa quello selezionato dall'utente
            if 'esol-' not in profile_name:
                print("⚠️  ATTENZIONE: Il profilo selezionato non sembra essere un profilo ENEL")
                print(f"    Profilo: {profile_name}")
                print("    Per progetti ENEL, assicurati di selezionare un profilo che contiene 'esol-'")
            
            # Estrai le credenziali dal formato SSO
            sso_content = selected_file[4]  # Il contenuto delle credenziali
            
            # Parse del contenuto SSO
            lines = sso_content.strip().split('\n')
            access_key = None
            secret_key = None
            session_token = None
            
            for i, line in enumerate(lines):
                if line == 'AccessKeyId' and i + 1 < len(lines):
                    access_key = lines[i + 1]
                elif line == 'SecretAccessKey' and i + 1 < len(lines):
                    secret_key = lines[i + 1]
                elif line == 'SessionToken' and i + 1 < len(lines):
                    session_token = lines[i + 1]
            
            if not all([access_key, secret_key, session_token]):
                raise Exception("Credenziali SSO incomplete")
            
            # Crea file credenziali AWS standard
            aws_credentials_path = os.path.join(homeDir, ".aws", "credentials")
            os.makedirs(os.path.dirname(aws_credentials_path), exist_ok=True)
            
            # Scrivi le credenziali in formato AWS
            with open(aws_credentials_path, 'w') as f:
                f.write("[default]\n")
                f.write(f"aws_access_key_id = {access_key}\n")
                f.write(f"aws_secret_access_key = {secret_key}\n")
                f.write(f"aws_session_token = {session_token}\n")
                f.write(f"aws_security_token = {session_token}\n")  # Stesso token per compatibilità
            
            # Estrai il nome del ruolo dal profilo selezionato dall'utente
            if 'esol-' in profile_name and '-' in profile_name:
                # Per profili ENEL, usa il nome completo del profilo
                role_arn = profile_name
                print(f"🎯 Usando nome profilo ENEL selezionato: {role_arn}")
            elif '-' in profile_name:
                # Per altri profili come "E-Solution-Prod-IOTSupport-876591523896"
                parts = profile_name.split('-')
                # Cerca un account ID (numero di 12 cifre)
                for part in parts:
                    if part.isdigit() and len(part) >= 10:  # Account ID AWS
                        role_arn = part
                        break
                else:
                    role_arn = parts[-1]  # Ultimo elemento se nessun match
                print(f"🎯 Estratto account ID da profilo generico selezionato: {role_arn}")
            else:
                role_arn = profile_name
                print(f"🎯 Usando nome profilo semplice selezionato: {role_arn}")
            
            print("✅ Credenziali SSO convertite con successo!")
            return aws_credentials_path, role_arn
            
        except Exception as e:
            print(f"❌ Errore SSO: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Autenticazione SSO fallita: {e}")
    else:
        raise Exception("AWS SSO Credential Manager non disponibile. Installare il modulo credential_manager.")

def getRoleArn(homeDir, configJson):
    """
    Ottiene il ruolo ARN dalle credenziali SSO
    """
    if _USE_SSO:
        try:
            # Per SSO, estrai il ruolo dall'ultimo file utilizzato
            credential_manager = AWSCredentialManager()
            valid_files = credential_manager.get_valid_credential_files()
            
            if valid_files:
                # Usa il primo file valido disponibile
                profile_name = valid_files[0][1] if len(valid_files[0]) > 1 else "unknown"
                role_arn = profile_name.split('-')[-1] if '-' in profile_name else profile_name
                configJson["awsCredentials"]["AWSProjectRole"] = role_arn
                return role_arn
            else:
                raise Exception("Nessun file SSO valido per estrarre il ruolo")
                
        except Exception as e:
            print(f"⚠️ Errore estrazione ruolo SSO: {e}")
            raise Exception(f"Impossibile ottenere ruolo da SSO: {e}")
    else:
        raise Exception("AWS SSO Credential Manager non disponibile")

def extract_string(fullString):
    extracted_str = None
    # Estrae la parte che segue il pattern "esol-<part1>-<part2>-<12digits>"
    # Es: "esol-ap3241101-test-039931352532" -> "esol_ap3241101_test"
    match = re.search(r"(esol-[^-]+-[^-]+)-\d{12}", fullString)

    if match:
        # Estrae la parte "esol-ap3241101-test", sostituisce i trattini con underscore
        base_part = match.group(1)  # "esol-ap3241101-test"
        base_part_underscored = base_part.replace("-", "_")  # "esol_ap3241101_test"
        extracted_str = base_part_underscored  # "esol_ap3241101_test" (senza suffisso)
        print(f"🔧 extract_string: '{fullString}' -> '{extracted_str}'")
    return extracted_str

def saveTempCredentials(tempCredentials, role_arn, rows):
    with open(tempCredentials, "r") as file:
        credentials_content = file.read()

    # Ottieni la data e l'ora correnti
    current_time = time.strftime("%Y%m%d%H%M")

    if role_arn != None:
        # Crea il nome del file utilizzando la data e l'ora
        projConf = f"{role_arn}_{current_time}.txt"

        if role_arn != None:
            # Crea il file e copia le credenziali temporanee al suo interno
            with open(projConf, "w") as file:
                file.write(credentials_content)

            # inserisci i valori delle chiavi nel file, all'interno di una lista
            f = open(tempCredentials, "r")
            for line in f:
                rows.append(line.partition(" = ")[2].rstrip())
                #print(i)
                #print(rows[i])
                #i+=1
            f.close()
    else:
        print("\nImpossibile reperire le informazioni di ruolo, Riprova ad eseguire lo script!\n")
    return projConf

def downloadFileFromS3(bucket, key, local_path):
    # Crea il client s3
    s3 = boto3.client('s3')

    # Scarica il file da S3
    try:
        s3.download_file(bucket, key, local_path)
        print(f"\nFile '{key}' scaricato con successo in '{local_path}'\n")
    except Exception as e:
        print(f"\nErrore durante il download del file '{key}': {str(e)}\n")

def uploadFileToS3(local_files, bucket, subfolder, singleFile):
    if singleFile is not None:
        local_file = singleFile
        uploadToS3(local_file, bucket, subfolder)
    else:
        for local_file in local_files:
            uploadToS3(local_file, bucket, subfolder)

def uploadToS3(local_file, bucket, subfolder):
    import subprocess

    remote_file = os.path.basename(local_file)
    # Specifica il percorso del bucket S3 di destinazione
    bucket_s3_dest = f's3://{bucket}/{subfolder}/{remote_file}'
    
    # Esegui il comando aws s3 cp utilizzando subprocess
    comando = ['aws', 's3', 'cp', local_file, bucket_s3_dest]
    try:
        subprocess.run(comando, check=True)
        print(f"\nFile '{local_file}' uploadato con successo su S3.\n")
    except Exception as e:
        print(f"\nErrore durante l'upload del file su S3: {str(e)}\n")

def deleteFileFromS3(bucket, remote_file_path):
    import subprocess

    # Controlla se non sono stati inseriti tutti i parametri necessari
    if not (bucket and remote_file_path):
        print("Non sono stati forniti tutti i parametri necessari per eliminare un file da S3.")
        return

    # Specifica il percorso completo del file da eliminare, incluso il bucket
    bucket_s3_dest = f's3://{bucket}/{remote_file_path}'

    # Esegui il comando aws s3 rm utilizzando subprocess
    comando = ['aws', 's3', 'rm', bucket_s3_dest]
    try:
        subprocess.run(comando, check=True)
        print(f"\nFile '{remote_file_path}' eliminato con successo dal bucket S3 {bucket}.\n")
    except subprocess.CalledProcessError as e:
        print(f"\nErrore durante l'eliminazione del file da S3: {e}\n")

def listFileFromS3(bucket, remote_file_path):
    import subprocess

    # Controlla se non sono stati inseriti tutti i parametri necessari
    if not (bucket):
        print("Non è stato fornito il nome del bucket necessario per elencare i file su S3.")
        return

    # Specifica il percorso completo del file da eliminare, incluso il bucket
    bucket_s3_dest = f's3://{bucket}/{remote_file_path}'

    # Esegui il comando aws s3 rm utilizzando subprocess
    comando = ['aws', 's3', 'ls', bucket_s3_dest]
    try:
        subprocess.run(comando)
        print(f"\nFiles elencati con successo dal bucket S3 {bucket}.\n")
    except subprocess.CalledProcessError as e:
        print(f"\nErrore durante l'enumerazione dei file da S3: {e}\n")

def enumarateConfigElements(conf):
    for index, role in enumerate(conf):
        print(f"\n{index}: {role['name']} - {role['comment']}")
    # Chiedi all'utente di inserire il numero desiderato
    while True:
        try:
            choice = int(input("\nInserisci il numero dell'opzione desiderata: "))
            if 0 <= choice <= len(conf):
                serialId = conf[choice]
                print(f"\n\nHai scelto: {serialId['name']} - {serialId['comment']}\n\n")
                Id = choice  # ID basato su zero
                break
            else:
                print("\nScelta non valida. Inserisci un numero valido.\n")
                exit(1)
        except ValueError:
            print("\nInserisci un numero valido.\n")
            exit(1)
    return int(Id)

def generateUUID():
    import uuid
    uuidNumber = str(uuid.uuid4())
    return uuidNumber

def get_dynamodb_items(table_name):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.scan(TableName=table_name)
    return response.get('Items', [])

def get_nested_value(d, path):
    for k in path:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d

def select_entry(items, key_path="sw_thing_type.S"):
    """Seleziona un elemento da una lista. Usa inquirer se disponibile, altrimenti fallback numerico."""
    path = key_path.split('.')
    labels = []
    for item in items:
        value = get_nested_value(item, path)
        label = value if value is not None else "N/A"
        labels.append(label)

    # Prova inquirer
    if INQUIRER_AVAILABLE and labels:
        try:
            questions = [inquirer.List('choice', message='Seleziona un elemento da visualizzare e/o modificare:', choices=labels, carousel=True)]
            answers = inquirer.prompt(questions)
            if answers and 'choice' in answers:
                sel = answers['choice']
                idx = labels.index(sel)
                return items[idx]
        except Exception:
            pass

    # Fallback numerico
    print("Seleziona un elemento da visualizzare e/o modificare:")
    for i, lab in enumerate(labels, start=1):
        print(f"{i}. {lab}")
    try:
        choice = int(input("Inserisci il numero corrispondente: ")) - 1
    except Exception:
        return None
    return items[choice] if 0 <= choice < len(items) else None

def select_thing_entry(items):
    labels = [item.get('sw_thing_type', {}).get('S', 'N/A') for item in items]
    if INQUIRER_AVAILABLE and labels:
        try:
            questions = [inquirer.List('choice', message='Seleziona un elemento da visualizzare e/o modificare:', choices=labels, carousel=True)]
            answers = inquirer.prompt(questions)
            if answers and 'choice' in answers:
                sel = answers['choice']
                idx = labels.index(sel)
                return items[idx]
        except Exception:
            pass

    print("Seleziona un elemento da visualizzare e/o modificare:")
    for i, lab in enumerate(labels, start=1):
        print(f"{i}. {lab}")
    try:
        choice = int(input("Inserisci il numero corrispondente: ")) - 1
    except Exception:
        return None
    return items[choice] if 0 <= choice < len(items) else None

def choose_dynamodb_item(table_name, items):
    if not items:
        print("Nessun elemento trovato nella tabella.")
        return
    print(f"Trovati {len(items)} elementi nella tabella {table_name}")
    selected_item = select_entry(items)
    if not selected_item:
        print("Scelta non valida.")
        return
    print("JSON elemento scelto:")
    for i, it in enumerate(items, start=1):
        if it != selected_item:
            continue
        else:
            print(f"Elemento {i}:")
            print(json.dumps(it, indent=2))
            print()
    return selected_item

def get_or_create_nested(item, keys):
    """Ritorna (crea se non esiste) il dizionario annidato specificato da keys."""
    if not keys:
        return item
    key = keys[0]
    if key not in item:
        item[key] = {}
    return get_or_create_nested(item[key], keys[1:])

def update_dynamodb_entry(table_name, item, new_entry_name, path_keys):
    if not new_entry_name.strip():
        print("Nessuna entry aggiunta. Operazione annullata.")
        return

    dynamodb = boto3.client("dynamodb")

    # Naviga (o crea) i livelli richiesti (es. ["CP_map","M"] o ["CP_list","Entry","N"]) 
    sub_dict = get_or_create_nested(item, path_keys)

    # Qui si assume che l'ultimo livello contenga una struttura "M" per la mappa
    if "M" not in sub_dict:
        sub_dict["M"] = {}

    map_dict = sub_dict["M"]
    values = [int(v["S"]) for v in map_dict.values() if "S" in v]
    new_value = str(max(values) + 1) if values else "1"

    map_dict[new_entry_name] = {"S": new_value}
    dynamodb.put_item(TableName=table_name, Item=item)
    print(f"Aggiunta nuova entry: {new_entry_name} con valore {new_value}")