#!/usr/bin/python3
from __future__ import print_function
import pickle
import os.path
from signal import default_int_handler
from disable_devices_filter import disable_devices_filter
from Device import Device
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
from termcolor import cprint

SCOPES = ["https://www.googleapis.com/auth/admin.directory.device.chromeos"]


def get_devices(service_device, nextPageToken, maxResults, status):
    """
    - Hämtar lista med alla enheter som stämmer in på query.
    - query är alla aktiva och som synkroneserats senast query_date
    - return resultat dictionary och senast synkroniserad från datumnet
    """
    tod = datetime.datetime.now()
    # d = datetime.timedelta(days=days_back)
    # a = tod - d
    # query_date = a.strftime("%Y-%m-%d")
    # query = "user: magnus.andersson@edu.hellefors.se"
    query = "status:"+status
    return service_device.chromeosdevices().list(customerId="my_customer", pageToken=nextPageToken, query=query, maxResults=maxResults).execute()


def extract_devices(res):
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
        deviceId = "SAKNAS"
        serialNumber = ""
        resursId = "SAKNAS"
        recentUser = "SAKNAS"
        wanIp = ""
        lastActivity = 'SAKNAS'
        orgUnitPath = 'SAKNAS'

        for i, (k, v) in enumerate(device.items()):
            try:
                for filter_key, filter_value in disable_devices_filter.items():
                    # print(f'{i} - {k}: {v}')
                    
                    if filter_key == k:
                        
                        for filter_element in filter_value:
                            # print(f'filter_element: {filter_element}, v: {v}')
                            if filter_element.lower() in v.lower():
                                # print("orgUnitPath:"+v)
                                catched = True

                if k == 'deviceId':
                    deviceId = v

                if k == 'annotatedAssetId':
                    resursId = v
                    
                # if k == "status":
                    # print(v)

                # if k == 'status':
                #     print(k+":"+v)

                # if k == 'recentUsers':
                #     recentUser = v[0]['email']

                # if k == 'lastSync':
                #     lastSync = v

                # if k == 'serialNumber':
                #     serialNumber = v

                # if k == 'annotatedAssetId':
                #     resursId = v

                if k == 'orgUnitPath':
                    orgUnitPath = v
                    # print(v)

                # if k == 'lastKnownNetwork':
                #     if '195.34.84' not in v[0]['wanIpAddress']:
                #         wanIp = v[0]['wanIpAddress']
                #         catched = True
            except Exception as error:
                # print(error)
                if isinstance(v, dict):
                    # print(i)
                    for vk, vv in v.items():
                        # print(vv.encode("utf-8"))
                        pass

        if catched:
            d_inst = Device(device)
            device_list.append(d_inst)
            # print()
            # print(f'resursId: {resursId}')
            # print(f'Device-ID: {deviceId}')
            # print(f'orgUnitPath: {orgUnitPath}')
            catched = False

    return devices, device_list


def update_devices(service_device, device_list, status):

    body = {
        "action": status
    }

    print(f"update: {body}")

    print()

    for d in device_list:
        print(d.get_device_id())
        print(
            f"{d.get_value('annotatedAssetId')} \t {status}")
        service_device.chromeosdevices().action(customerId="my_customer", resourceId=d.get_device_id(), body=body).execute()

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


if __name__ == "__main__":
    print("Starting up...")
    print("Device service")
    service_device = get_device_service()
    
    res = get_devices(service_device, None, 200, "ACTIVE")
    devices, device_list = extract_devices(res)
    
    if len(device_list) > 0:
        update_devices(service_device, device_list, "disable")

    # print(f'len(device_list): {len(device_list)}')
    tot_number_of_devices = len(devices)
    found_number_of_devices = len(device_list)
    while len(devices) == 200:
        res = get_devices(service_device, res['nextPageToken'], 200, "ACTIVE")
        devices, device_list = extract_devices(res)
        
        if len(device_list) > 0:
            update_devices(service_device, device_list, "disable")
            
        tot_number_of_devices = tot_number_of_devices + len(devices)
        found_number_of_devices = found_number_of_devices + len(device_list)
    
    
    
    
    print()
    print(f'{found_number_of_devices}/{tot_number_of_devices} stycken')
    print("Exit! Bye!")
