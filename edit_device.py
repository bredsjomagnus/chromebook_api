from __future__ import print_function
import pickle
import os.path
from query_dict import *
from Device import *
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
from termcolor import cprint

SCOPES = ["https://www.googleapis.com/auth/admin.directory.device.chromeos"]

device_list = []
UPDATE_INFO = """
    UPPDATERINGSNYCKLAR
    - "user"
    - "location"
    - "asset_id"
"""


def get_devices(service_device, query="status:provisioned", nextPageToken=None, maxResults=200):
    """
    - Hämtar lista med alla enheter som stämmer in på query.
    - query är alla aktiva och som synkroneserats senast query_date
    - return resultat dictionary och senast synkroniserad från datumnet
    """
    return service_device.chromeosdevices().list(customerId="my_customer", query=query, pageToken=nextPageToken, maxResults=maxResults).execute(), query


def update_devices(service_device, device_list, update_key, update_value):

    body = {
        query_dict[update_key]: update_value
    }

    print(f"update: {body}")

    print()

    for d in device_list:
        print(d.get_device_id())
        print(
            f"{d.get_value('annotatedAssetId')} - {query_dict[update_key]}: {d.get_value(query_dict[update_key])} \t -> \t {update_value}")
        service_device.chromeosdevices().update(customerId="my_customer", deviceId=d.get_device_id(), body=body).execute()

def extract_devices(res, query_key, query_value):
    """
    - Skannar av listan med enheterna i dict res.
    - De som har en annan wanIpAddress än som innehåller 195.34.84 samlas data på
    - Skriver ut data på de enheter som träffats enligt ovan
    - Returnerar total antalet enheter i dict res och totala antalet träffar i dict res.
    """
    devices = res.get("chromeosdevices", [])
    device_list = []

    for device in devices:
        catched = False
        lastSync = ""
        serialNumber = ""
        resursId = "SAKNAS"
        recentUser = "SAKNAS"
        wanIp = ""
        lastActivity = 'SAKNAS'
        search_value = ""
        location = "SAKNAS"
        deviceId = False


        for i, (k, v) in enumerate(device.items()):
            
            try:
                # print(f'{i} - {k}: {v}')

                if k == 'deviceId':
                    deviceId = v

                if k == 'activeTimeRanges':
                    lastActivity = v[-1]['date']

                if k == 'recentUsers':
                    recentUser = v[0]['email']

                if k == 'lastSync':
                    lastSync = v

                if k == 'serialNumber':
                    serialNumber = v

                if k == 'annotatedAssetId':
                    resursId = v
                
                if k == 'lastKnownNetwork':
                    wanIp = v[0]['wanIpAddress']
                
                if k == 'annotatedLocation':
                    location = v

                if k == query_dict[query_key]:
                    print(query_dict[query_key])
                    search_value = v

                
                         
            except Exception as error:
                # print(error)
                if isinstance(v, dict):
                    # print(i)
                    for vk, vv in v.items():
                        # print(vv.encode("utf-8"))
                        pass
        
        if deviceId:
            d_inst = Device(device)
            device_list.append(d_inst)
            print()
            print(f"{query_key}: ", end="")
            cprint(f"{search_value}", 'yellow')
            print('Resurs-ID: ', end="")
            cprint(f'{resursId}', 'red', 'on_white')
            cprint(f'Senaste användare: {recentUser}', 'yellow')
            print(f'Serienummer: {serialNumber}')
            print(f"Plats: {location}")
            print(f'Senaste aktivitet: {lastActivity}')
            print(f'Senaste synk: {lastSync}')
            cprint(f'IP-adress: {wanIp}', 'magenta')
            print()

        

        # if catched:
        #     nc = nc + 1
        #     print()
        #     print('Resurs-ID: ', end="")
        #     cprint(f'{resursId}', 'red', 'on_white')
        #     cprint(f'Senaste användare: {recentUser}', 'yellow')
        #     print(f'Serienummer: {serialNumber}')
        #     print(f'Senaste aktivitet: {lastActivity}')
        #     print(f'Senaste synk: {lastSync}')
        #     cprint(f'IP-adress: {wanIp}', 'magenta')
        #     print()
        #     catched = False

    return device_list


def get_device_service():
    """Shows basic usage of the Admin SDK Directory API.
    Prints the emails and names of the first 10 users in the domain.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
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
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('admin', 'directory_v1', credentials=creds)
    return service

def main():

    service_device = get_device_service()

    print("MÖJLIGA SÖKNYCKLAR")
    cprint("""
    "user": "",
    "location": "",
    "orgPathUnit": "",
    "asset_id": "",
    "sync": "",
    "register": "",
    "note": "",
    "recent_user": "",
    "id": "",           # device-id
    "ethernet_mac": "",
    "status": "",       # provisioned, disabled, deprovisioned
    "wifi_mac": ""
""", 'yellow')
    query_key = input("Ange söknyckel: ")

    print("\n Söker på ", end="")
    cprint(f'[{query_key.upper()}]', 'yellow', end=" ")
    query_value = input("Sökvärde: ")

    print()
    
    cprint(f'[{query_key}:{query_value}]', 'yellow')

    query = query_key + ":" +query_value

    res, query = get_devices(service_device, query)
    device_list = extract_devices(res, query_key, query_value)

    # while nd == 200:
    #     res, query = get_devices(
    #         service_device, query, res['nextPageToken'], days_back)
    #     nd, nc = extract_devices(res)
    #     total_nd = total_nd + nd
    #     catched_d = catched_d + nc

    print()
    print("QUERY: ", end="")
    cprint(f"[{query}]", 'green')
    print("ANTAL: ", end="")
    cprint(f'{len(device_list)} st', 'green')

    print()

    update_key = ""
    update_value = ""

    valid_update_keys = ['user', 'location', 'asset_id']

    if len(device_list):
    
        update = "unknown"
        while update != 'j' and update != 'n':
            update = input("Uppdatera dessa enheter? [j/n]")
            if update == 'j':
                cprint(UPDATE_INFO, "yellow")
                
                update_key = 'unknown'

                while not update_key in valid_update_keys:

                    update_key = input("Vad vill du uppdatera? [exit] ")

                    if update_key == 'exit':
                        print("Hej då!")
                        exit()
                        

                print("\nUppdatera ", end="")
                cprint(f'[{update_key.upper()}]', 'yellow', end=" ")
                update_value = input("Nytt värde: ")

                print()
                
                print("############################################################################################")
                print(f"Uppdatera {len(device_list)} st enheter:")
                print("KEY \t nuvarand värde \t -> \t nytt värde")
                cprint(f'[{update_key.upper()}: {device_list[0].get_value(query_dict[update_key])} \t -> \t {update_value}]', 'yellow')
                # cprint(f'[{update_key.upper()}: {query_value} t -> \t {update_value}]', 'yellow')
                print("############################################################################################")

                update_verification = "unknown"
                while update_verification != 'j' and update_verification != 'n':
                    update_verification = input("Är du säker på att du vill uföra denna uppdatering? [j/n]")
                    if update_verification == 'j':
                        update_devices(service_device, device_list, update_key, update_value)
                    elif update_verification == 'n':
                        print("\nUppdatering utfördes inte!")
                        print("Hej då!")
                        exit()

            elif update == 'n':
                print("Hej då!")
                exit()
                

    

if __name__ == '__main__':
    main()
