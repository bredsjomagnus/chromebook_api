from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
from termcolor import cprint

SCOPES = ["https://www.googleapis.com/auth/admin.directory.device.chromeos.readonly"]


def get_devices(service_device, nextPageToken, maxResults, days_back=2):
    """
    - Hämtar lista med alla enheter som stämmer in på query.
    - query är alla aktiva och som synkroneserats senast query_date
    - return resultat dictionary och senast synkroniserad från datumnet
    """
    tod = datetime.datetime.now()
    d = datetime.timedelta(days=days_back)
    a = tod - d
    query_date = a.strftime("%Y-%m-%d")
    # query = "user: magnus.andersson@edu.hellefors.se"
    query = "status:provisioned sync:"+query_date+".."
    return service_device.chromeosdevices().list(customerId="my_customer", query=query, pageToken=nextPageToken, orgUnitPath="Grundskola", maxResults=maxResults).execute(), query


def extract_devices(res):
    """
    - Skannar av listan med enheterna i dict res.
    - De som har en annan wanIpAddress än som innehåller 195.34.84 samlas data på
    - Skriver ut data på de enheter som träffats enligt ovan
    - Returnerar total antalet enheter i dict res och totala antalet träffar i dict res.
    """
    devices = res.get("chromeosdevices", [])
    nc = 0

    for device in devices:
        catched = False
        lastSync = ""
        serialNumber = ""
        resursId = "SAKNAS"
        recentUser = "SAKNAS"
        wanIp = ""
        lastActivity = 'SAKNAS'

        for i, (k, v) in enumerate(device.items()):
            try:
                # print(f'{i} - {k}: {v}')

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
                    if '195.34.84' not in v[0]['wanIpAddress']:
                        wanIp = v[0]['wanIpAddress']
                        catched = True
            except Exception as error:
                # print(error)
                if isinstance(v, dict):
                    # print(i)
                    for vk, vv in v.items():
                        # print(vv.encode("utf-8"))
                        pass

        if catched:
            nc = nc + 1
            print()
            print('Resurs-ID: ', end="")
            cprint(f'{resursId}', 'red', 'on_white')
            cprint(f'Senaste användare: {recentUser}', 'yellow')
            print(f'Serienummer: {serialNumber}')
            print(f'Senaste aktivitet: {lastActivity}')
            print(f'Senaste synk: {lastSync}')
            cprint(f'IP-adress: {wanIp}', 'magenta')
            print()
            catched = False

    return len(devices), nc


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


service_device = get_device_service()

days_back = 3
res, query = get_devices(service_device, None, 200, days_back)
nd, nc = extract_devices(res)

total_nd = nd
catched_d = nc

while nd == 200:
    res, query = get_devices(
        service_device, res['nextPageToken'], 200, days_back)
    nd, nc = extract_devices(res)
    total_nd = total_nd + nd
    catched_d = catched_d + nc

print()
print("QUERY: ", end="")
cprint(f"[{query}]", 'green')
print("ANTAL/TRÄFFAR: ", end="")
cprint(f'{total_nd} st/{catched_d} st', 'green')
