from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

import io

from enum import Enum
import sys, getopt
from commons import *

class DeviceType(Enum):
    CLIENT = 0
    SERVER = 1


class FileNotFoundException(Exception):
    pass


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']


def update_ip_files(device_type):
    server_ip_downloaded = False
    client_ip_uploaded = False
    server_ip = None

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('drive', 'v3', credentials=creds)
        page_token = None
        folder_id = None
        found = False
        while not found:
            # pylint: disable=maybe-no-member
            response = service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                            spaces='drive',
                                            fields='nextPageToken, '
                                                   'files(id, name)',
                                            includeItemsFromAllDrives=True, supportsAllDrives=True,
                                            pageToken=page_token).execute()
            for folder in response.get('files', []):
                if folder.get("name") == "IP Exchange":
                    folder_id = folder.get("id")
                    found = True
                    break
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        if not found:
            print('No "IP Exchange" directory found')
            raise FileNotFoundException("IP Exchange folder")

        client_file_name = "ip_client.txt"
        server_file_name = "ip_server.txt"
        if device_type == DeviceType.SERVER:
            client_file_name, server_file_name = server_file_name, client_file_name
        try:
            client_file = service.files().list(
                q=f"'{folder_id}' in parents and name = '{client_file_name}'",
                includeItemsFromAllDrives=True, supportsAllDrives=True, ).execute()
            client_file_media = MediaFileUpload(client_file_name_local)
            client_file_object = {'name': client_file_name, 'parents': [folder_id]}
            if len(client_file.get('files', [])) != 0:
                for f in client_file.get('files', []):
                    service.files().delete(fileId=f.get('id')).execute()
            service.files().create(body=client_file_object, media_body=client_file_media).execute()
            client_ip_uploaded = True
        except FileNotFoundException as error:
            print(f'Not found on Google Drive: {error}')
        except Exception as e:
            print("Error while uploading your IP file to Google Drive")
        try:
            server_file = service.files().list(
                q=f"'{folder_id}' in parents and name = '{server_file_name}'",
                includeItemsFromAllDrives=True, supportsAllDrives=True, ).execute()
            if len(server_file.get('files', [])) == 0:
                print('No IP files found in directory')
                raise FileNotFoundException(server_file_name)
            request = service.files().get_media(fileId=server_file.get('files', [])[0].get('id'))
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(F'Download {int(status.progress() * 100)}.')
            with open(server_file_name_local, 'wb') as server_file_local:
                server_file_local.write(file.getvalue())
                server_ip = file.getvalue().decode("utf-8").strip()
            server_ip_downloaded = True
        except FileNotFoundException as error:
            print(f'Not found on Google Drive: {error}')
        except Exception as e:
            print("Error while downloading other IP file from Google Drive")
    except HttpError as error:
        print(f'A Google API error occurred: {error}')
    return server_ip_downloaded, client_ip_uploaded, server_ip



if __name__ == '__main__':
    update_ip_files(sys.argv[1:])
