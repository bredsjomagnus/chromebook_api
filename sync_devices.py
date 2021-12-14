
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


def get_devices(service_device, query="status:provisioned", nextPageToken=None, maxResults=200):
    """
    - Hämtar lista med alla enheter som stämmer in på query.
    - query är alla aktiva och som synkroneserats senast query_date
    - return resultat dictionary och senast synkroniserad från datumnet
    """
    return service_device.chromeosdevices().list(customerId="my_customer", query=query, pageToken=nextPageToken, orgUnitPath="Grundskola", maxResults=maxResults).execute(), query

def check_resurs_id(service_device, resurs_id_list):
    nextPageToken = None
    maxResults = 200
    device_list = []
    for rid in resurs_id_list:
        query = "asset_id:"+rid

        res = service_device.chromeosdevices().list(customerId="my_customer", query=query,
                                                    pageToken=nextPageToken, orgUnitPath="Grundskola", maxResults=maxResults).execute()
        d = res.get("chromeosdevices", [])


        if len(d) == 1:
            print(f"{rid} - {d[0]['annotatedAssetId']}: {d[0].get('annotatedLocation', 'SAKNAS')}")
            d_inst = Device(d[0])
            device_list.append(d_inst)
        elif len(d) > 1:
            print("WUUT!")
            exit()
        else:
            print(f"{rid} FINNS INTE")
            exit()
    
    return device_list


def update_devices(service_device, device_list, ny_klass):

    body = {
        'annotatedLocation': ny_klass
    }

    print(f"update: {body}")

    print()

    for d in device_list:
        if d.get_value('annotatedLocation') != ny_klass:
            print(d.get_device_id())
            print(f"{d.get_value('annotatedAssetId')}: {d.get_value('annotatedLocation')} \t -> \t {ny_klass}")
            service_device.chromeosdevices().update(customerId="my_customer", deviceId=d.get_device_id(), body=body).execute()


def main():
    sheet_service = get_sheet_service()
    device_service = get_device_service()

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

    print(resurs_id_list)

    device_list = check_resurs_id(device_service, resurs_id_list)

    ny_klass = input("Ange ny klass: ")

    update_devices(device_service, device_list, ny_klass)



if __name__ == '__main__':
    main()
