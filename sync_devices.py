
from __future__ import print_function
import pickle
import os.path
import os
from functions import *
from env import *
from Device import *
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from termcolor import cprint


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/admin.directory.device.chromeos"]


# def clearConsole():
#     command = 'clear'
#     if os.name in ('nt', 'dos'):  # If Machine is running on Windows, use cls
#         command = 'cls'
#     os.system(command)


def clearConsole(): return print('\n' * 150)


def get_sheet_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('sheet_token.pickle'):
        with open('sheet_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('sheet_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    return service


def get_device_service():
    """Shows basic usage of the Admin SDK Directory API.
    Prints the emails and names of the first 10 users in the domain.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('device_token.pickle'):
        with open('device_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('device_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('admin', 'directory_v1', credentials=creds)
    return service


# def get_devices(service_device, query="status:provisioned", nextPageToken=None, maxResults=200):
#     """
#     - Hämtar lista med alla enheter som stämmer in på query.
#     - query är alla aktiva och som synkroneserats senast query_date
#     - return resultat dictionary och senast synkroniserad från datumnet
#     """
#     return service_device.chromeosdevices().list(customerId="my_customer", query=query, pageToken=nextPageToken, orgUnitPath="Grundskola", maxResults=maxResults).execute(), query

def check_resurs_id(service_device, user_resurs_id_list, klass):
    """
    Går igenom resurs_id_list och kollar så att det finns enhet att hämta till varje resurs_id i listan.
    Skriver ut en checklist för att visa om det saknas någon i listan eller ej.
    Avbryter programmet om någon enhet saknas.

    resurs_id_list:list [['förnamn.efternamn@edu.hellefors.se','edubookxxx'], ['förnamn.efternamn@edu.hellefors.se','edubookxxx'],... ]

    1. För varje resurs_id i listan -> hämtar enheter med asset_id:edubookxxx
    2. Instansierar en Device per hämtad enhet
    3. Device läggs i device_list:

    return device_list:list [Device, Device,... ]
    """
    nextPageToken = None
    maxResults = 200
    device_list = []
    for e in user_resurs_id_list:
        user = e[0]
        rid = e[1]

        if len(rid) > 0:

            MISMATCH = False
            FOUND = False

            query = "asset_id:"+rid

            try:
                res = service_device.chromeosdevices().list(customerId="my_customer", query=query, pageToken=nextPageToken, maxResults=maxResults).execute()
                FOUND = True
            except Exception as e:
                print(e)
            
            d = res.get("chromeosdevices", [])


            if len(d) == 1 and FOUND:

                # for k, v in d[0].items():
                #     print(f"{k}: {v}")

                # RESURS ID
                if rid.lower() == d[0].get('annotatedAssetId', 'SAKNAS').lower():
                    cprint(f"{rid}[{d[0]['annotatedAssetId']}]", "green")
                else:
                    cprint(f"{rid}[{d[0]['annotatedAssetId']}]", "red")
                    MISMATCH = True
                
                # PLATS
                print(f"Plats=", end="")
                unitPlats = d[0].get('annotatedLocation', 'SAKNAS')
                # if d[0].get('annotatedLocation', 'SAKNAS') != 'SAKNAS':
                if klass.lower() in unitPlats.lower():
                    cprint(f"{d[0].get('annotatedLocation', 'SAKNAS')}", "green")
                else:
                    cprint(f"{d[0].get('annotatedLocation', 'SAKNAS')}", "yellow")
                    MISMATCH = True

                # OU
                print(f"orgUnitPath", end="")
                unitOU = d[0].get('orgUnitPath', 'SAKNAS')
                if klass.lower() in unitOU.lower():
                    cprint(f"{d[0].get('orgUnitPath', 'SAKNAS')}", "green")
                else:
                    cprint(f"{d[0].get('orgUnitPath', 'SAKNAS')}", "yellow")
                    MISMATCH = True

                unitNote = d[0].get('notes', '')
                if len(unitNote) > 0:
                    print("notes: ", end="")
                    cprint(unitNote, "cyan")

                # USER
                if user == d[0].get('annotatedUser', 'SAKNAS') and not MISMATCH:
                    cprint(f"{user}:{d[0].get('annotatedUser', 'SAKNAS')}", 'green')
                else:
                    cprint(f"{user}:{d[0].get('annotatedUser', 'SAKNAS')}", 'yellow')
                    
                print()
                d_inst = Device(d[0])
                d_inst.set_user(user)
                device_list.append(d_inst)
            elif len(d) > 1:
                print("WUUT!")
                exit()
            else:
                print(f"{rid} FINNS INTE")
                exit()

        else:
            cprint(f"{user} saknar enhet", "red")
            print()
    
    return device_list


def update_devices(service_device, device_list, ny_klass):
    """
    För varje Device i device_list:list -> uppdatera 'annotatedLocation' till ny_klass
    """
    
    body = dict()
    # print(f"update: {body}")

    print()

    for d in device_list:
        # print(d.get_user())
        new_user = d.get_user()
        UPDATE = False
        body = dict()
        
        if d.get_value('annotatedLocation') != ny_klass:
            body['annotatedLocation'] = ny_klass
            
            # print(f"{d.get_value('annotatedAssetId')}: {d.get_value('annotatedLocation')} \t -> \t {ny_klass}")

            UPDATE = True

        if d.get_value('annotatedUser') != new_user:
            body['annotatedUser'] = new_user
            # print(f"{d.get_value('annotatedUser')}: {d.get_value('annotatedUser')} \t -> \t {new_user}")
            UPDATE = True
        
        if UPDATE:
            print(f"{d.get_device_id()}:{d.get_value('annotatedAssetId')}")
            print("body: {")
            for k, v in body.items():
                print(f"\t {k}: {v}")
            print("}")
            print()
            service_device.chromeosdevices().update(customerId="my_customer", deviceId=d.get_device_id(), body=body).execute()


def main():
    """
    1. Hämtar spreadsheetet Chromebooks och tar ut elevernas edu-adresser och elevernas Edubook-nummer.
    
    2. 
    """
    sheet_service = get_sheet_service()
    device_service = get_device_service()
    MSG ="""    
Steg 1 skannar av.
Eleverna är hämtas från Chromebook spreadheet klass som anges.
De som elever som har enhet ligger i annat OU eller har annan plats inskriven markers med gult.
"""
    print(MSG)

    newclass = 'j'
    while newclass == 'j':
        klass = input("Klass [hämtar denna klassen från dess Chromebookblad]: ").strip()

        _range = klass+"!C1:D"

        col_map = {
            'Edukonto': 'edukonto',
            'Enhet': 'resurs_id'
        }

        cb_df, error = get_sheet_as_df(sheet_service, CHROMEBOOKS_ID, _range, col_map)

        # print(cb_df)
        print(f'error: {error}')

        resurs_id_list = cb_df['resurs_id'].tolist()
        user_list = cb_df['edukonto'].tolist()

        user_resurs_id_list = [list(a) for a in zip(user_list, resurs_id_list)]

        
        device_list = check_resurs_id(device_service, user_resurs_id_list, klass)

        newclass = input("Vill du kolla en annan klass? [j] ")
        # clearConsole()
    
    _exit = input("Vill du fortsätta med att lägga till ny klass? [j] ")

    if _exit != 'j':
        print()
        print("Hej då!")
        exit()
    ny_klass = input("Ange ny klass: ")

    update_devices(device_service, device_list, ny_klass)



if __name__ == '__main__':
    main()
