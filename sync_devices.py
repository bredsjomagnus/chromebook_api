
from __future__ import print_function
import pickle
import os.path
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
#     - H??mtar lista med alla enheter som st??mmer in p?? query.
#     - query ??r alla aktiva och som synkroneserats senast query_date
#     - return resultat dictionary och senast synkroniserad fr??n datumnet
#     """
#     return service_device.chromeosdevices().list(customerId="my_customer", query=query, pageToken=nextPageToken, orgUnitPath="Grundskola", maxResults=maxResults).execute(), query

def check_resurs_id(service_device, user_resurs_id_list):
    """
    G??r igenom resurs_id_list och kollar s?? att det finns enhet att h??mta till varje resurs_id i listan.
    Skriver ut en checklist f??r att visa om det saknas n??gon i listan eller ej.
    Avbryter programmet om n??gon enhet saknas.

    H??mtat fr??n spreadsheetet Chromebooks:
    resurs_id_list:list [['f??rnamn.efternamn@edu.hellefors.se','edubookxxx'], ['f??rnamn.efternamn@edu.hellefors.se','edubookxxx'],... ]

    1. F??r varje resurs_id i listan -> h??mtar enheter med asset_id:edubookxxx
    2. Instansierar en Device per h??mtad enhet
    3. Device l??ggs i device_list:

    return device_list:list [Device, Device,... ]
    """
    nextPageToken = None
    maxResults = 200
    device_list = []
    for e in user_resurs_id_list:
        user = e[0]
        rid = e[1]

        # s?? l??nge inte rid ??r en tom str??ng
        if rid:
            query = "asset_id:"+rid
            res = service_device.chromeosdevices().list(customerId="my_customer", query=query,
                                                        pageToken=nextPageToken, maxResults=maxResults).execute()
            d = res.get("chromeosdevices", [])


            if len(d) == 1:

                # for k, v in d[0].items():
                #     print(f"{k}: {v}")

                # RESURS ID
                if rid.lower() == d[0].get('annotatedAssetId', 'SAKNAS').lower():
                    cprint(f"Enhet: {rid}", "green")
                else:
                    cprint(
                        f"Enhet i chromebooks spreadheet: {rid}, Enhet i Google Admin: {d[0]['annotatedAssetId']}", "red")
                
                # PLATS
                print(f"[orgUnitPath={d[0].get('orgUnitPath', 'SAKNAS')}]:Plats=", end="")
                if d[0].get('annotatedLocation', 'SAKNAS') != 'SAKNAS':
                    cprint(f"{d[0].get('annotatedLocation', 'SAKNAS')}", "green")
                else:
                    cprint(f"{d[0].get('annotatedLocation', 'SAKNAS')}", "yellow")

                # USER
                if user == d[0].get('annotatedUser', 'SAKNAS') and user:
                    cprint(f"Anv??ndare: {d[0].get('annotatedUser', 'SAKNAS')}", 'green')
                else:
                    cprint(f"Anv??ndare i chromebooks spreadsheet: {user}, anv??ndare i Google Admin: {d[0].get('annotatedUser', 'SAKNAS')}", 'yellow')
                    
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
    
    return device_list


def update_devices(service_device, device_list, ny_klass):
    """
    F??r varje Device i device_list:list -> uppdatera 'annotatedLocation' till ny_klass


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
    sheet_service = get_sheet_service()
    device_service = get_device_service()

    info_msg = """
    *******************************************************************
    H??MTAR OCH VISAR LISTAN ??VER CHROMEBOOKLISTAN I DRIVEN. 
    SEN KAN MAN SKRIVA IN VILKEN KLASS DESSA ENHETER SKALL S??TTAS TILL I GOOGLE ADMIN.
    DET SOM S??TTS ??R ENBART PLATS OCH INTE OU.
    *******************************************************************
    """
    print(info_msg)
    print()
    klass = input("Klass: ").strip()

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

    # print(resurs_id_list)
    # print(user_list)

    user_resurs_id_list = [list(a) for a in zip(user_list, resurs_id_list)]

    device_list = check_resurs_id(device_service, user_resurs_id_list)

    ny_klass = input("Ange ny klass (eller quit (q)): ")

    if ny_klass.lower() == 'q':
        print("Quit! Hej d??!")
        exit()

    update_devices(device_service, device_list, ny_klass)



if __name__ == '__main__':
    main()
