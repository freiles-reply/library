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

# Splitta una stringa per mezzo di un separatore
def getStringParts(strng, sep):
    parts = re.split(f'[{sep}]', strng)
    centralPart = parts[1]
    finalPart = parts[-1]
    return centralPart, finalPart

# Genera il file delle credenziali Enel per aws
def createCredentialFile(name, user, passwd):
    print("creo il file delle credenziali ENEL...")
    with open(name, 'w') as file:
        file.write("[default]\n")
        file.write(f"username = {user}\n")
        file.write(f"password = {passwd}\n")

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
                print(f"File '{filename}' rimosso.")

# Seleziona il path della home directory dove solitamente risiede la folder .aws che ospita le credenziali temporanee
def createHomeDirPath(name):
    if not os.path.exists(name):
        # Crea una finestra principale nascosta
        root = tk.Tk()
        root.withdraw()

        # Apre la finestra di dialogo per selezionare un percorso (in questo caso la home Dir)
        print("SELEZIONA LA TUA HOME DIRECTORY PER IL SALVATAGGIO DELLE CREDENZIALI (ES. windows: C:\\Users\\NomeUtente ; Linux/MacOS /home/NomeUtente)")
        time.sleep(3)
        homeDir = filedialog.askdirectory(title="Seleziona la tua Home Directory (ES. windows: C:\\Users\\NomeUtente ; Linux/MacOS /home/NomeUtente)")
        home = open(name, "w")
        home.write(homeDir + "\n")
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
        print("Elenco dei file disponibili:")
        for index, file_name in enumerate(file_list, start=1):
            print(f"{index}. {file_name}")

        # Chiedi all'utente di selezionare un numero
        choice = input("Seleziona un numero (0 per uscire): ")

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
                print("Hai scelto di proseguire senza utilizzare le credenziali già disponibili.")
                return None
            else:
                print("Scelta non valida, si procederà con nuove credenziali temporanee")
                return None
        else:
            print("Input non valido. Si procederà con nuove credenziali temporanee.")
            return None

def getFileListSortedByDate(objects):
    # Chiedi all'utente il numero di giorni da considerare
    num_days = int(input("Inserisci il numero di giorni precedenti ad oggi per cui visualizzare i file: "))

    # Calcola la data di num_days fa
    num_days_ago = datetime.now(timezone.utc) - timedelta(days=num_days)

    # Filtra e ordina gli oggetti in base alla data
    recent_objects = [obj for obj in objects.get('Contents', []) if obj['LastModified'].replace(tzinfo=timezone.utc) >= num_days_ago]
    recent_objects.sort(key=lambda x: x['LastModified'], reverse=True)

    # Stampa l'elenco dei file recenti enumerati
    print(f"File nella cartella 'dev' degli ultimi {num_days} giorni (dal più recente al più vecchio):")
    for i, obj in enumerate(recent_objects, 1):
        print(f"{i}. Nome: {obj['Key']}  Data di modifica: {obj['LastModified']}")
    return recent_objects, num_days, i

def getEnumFileListSortedByDate(recent_objects):
    # Chiedi all'utente quali file scaricare
    files = input("Inserisci il/i numero/i del/dei file/s da elaborare [separati da virgola. (digitare ALL per selezionare tutti i files)]: ")

    if not files:
        print("Nessun file selezionato.")
        exit(1)
    elif files == 'ALL':
        ans = input('Attenzione!!! saranno selezionati tutti i file, SEI SICURO DI VOLER PROSEGUIRE? (YES per accettare): ')
        if ans =='YES':
            files = list(range(1, len(recent_objects) + 1))
            print(f'Tutti i file verranno selezionati! {files}')
        else:
            print('Non è stata confermata la selezione di tutti i file il programma terminerà')
            exit(1)
    else:
        files = [int(num.strip()) for num in files.split(',') if num.strip().isdigit()]
    return files

def getFileNamesAndDates(files, recent_objects, path_list, name_list, date_list):
    for file_number in files:
        if 1 <= file_number <= len(recent_objects):
            selected_object = recent_objects[file_number - 1]
            file_path = selected_object['Key']  # Ottieni tutto il path
            file_name = os.path.basename(selected_object['Key'])  # Ottieni solo il nome del file
            file_date = selected_object['LastModified']
            path_list.append(file_path)
            name_list.append(file_name)
            date_list.append(file_date)
        else:
            print(f"Numero '{file_number}' non valido. Ignorato.")
            exit(1)

def getTempCredentials(homeDir, configJson):
    os.system('aws-adfs reset')
    commandString = "aws-adfs login --adfs-host=sts.enel.com --no-sspi --authfile=awsauth"
    os.system(commandString)
    if not os.path.exists(homeDir+ "/.aws"):
        os.remove(homeDir)
        print("non riesco a trovare la foder '.aws' nel percorso definito nel file HomeDir. Il file HomeDir verrà cancellato.")
        exit(1)
    tempCredentials = homeDir+ "/.aws/credentials"
    configAWS = homeDir+ "/.aws/config"
    awsRole = "adfs_config.role_arn"
    role_arn = None
    with open(configAWS, "r") as file:
        for line in file:
            if line.startswith(awsRole):
                role_arn = line.split("/")[-1].strip()
                configJson["awsCredentials"]["AWSProjectRole"] = role_arn
                break
    return tempCredentials, role_arn

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
        print("Impossibile reperire le informazioni di ruolo, Riprova ad eseguire lo script!")

def downloadFileFromS3(bucket, key, local_path, s3_client):
    # Scarica il file da S3
    try:
        s3_client.download_file(bucket, key, local_path)
        print(f"File '{key}' scaricato con successo in '{local_path}'")
    except Exception as e:
        print(f"Errore durante il download del file '{key}': {str(e)}")

def uploadFileToS3(local_files, bucket, subfolder):
    import subprocess

    for local_file in local_files:
        remote_file = os.path.basename(local_file)
        # Specifica il percorso del bucket S3 di destinazione
        bucket_s3_dest = f's3://{bucket}/{subfolder}/{remote_file}'
        
        # Esegui il comando aws s3 cp utilizzando subprocess
        comando = ['aws', 's3', 'cp', local_file, bucket_s3_dest]
        try:
            subprocess.run(comando, check=True)
            print(f"File '{local_file}' uploadato con successo su S3.")
        except Exception as e:
            print(f"Errore durante l'upload del file su S3: {str(e)}")

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
        print(f"File '{remote_file_path}' eliminato con successo dal bucket S3 {bucket}.")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'eliminazione del file da S3: {e}")

def enumarateConfigElements(conf):
    for index, role in enumerate(conf):
        print(f"{index}: {role['name']} - {role['comment']}")
    # Chiedi all'utente di inserire il numero desiderato
    while True:
        try:
            choice = int(input("Inserisci il numero dell'opzione desiderata: "))
            if 0 <= choice <= len(conf):
                serialId = conf[choice]
                print(f"Hai scelto: {serialId['name']} - {serialId['comment']}")
                Id = choice  # ID basato su zero
                break
            else:
                print("Scelta non valida. Inserisci un numero valido.")
                exit(1)
        except ValueError:
            print("Inserisci un numero valido.")
            exit(1)
    return int(Id)