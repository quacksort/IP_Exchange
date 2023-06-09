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


def main(argv):
    device_type = DeviceType.CLIENT
    opts, args = getopt.getopt(argv, "t:", ["type="])
    for opt, arg in opts:
        if opt == '-h':
            print('-t \t type: c or s')
            sys.exit()
        elif opt in ("-t", "--type"):
            device_type = DeviceType.SERVER if arg.lower().startswith("s") else DeviceType.CLIENT

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
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
        # 1ajIOB5oH9NhtsverLbVx7C_1VtD_Fgu4

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
        # client_file_name_local = "my_ip.txt"
        # server_file_name_local = "other_ip.txt"
        if device_type == DeviceType.SERVER:
            client_file_name, server_file_name = server_file_name, client_file_name

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

        client_file = service.files().list(
            q=f"'{folder_id}' in parents and name = '{client_file_name}'",
            includeItemsFromAllDrives=True, supportsAllDrives=True, ).execute()
        client_file_media = MediaFileUpload(client_file_name_local)
        client_file_object = {'name': client_file_name, 'parents': [folder_id]}
        if len(client_file.get('files', [])) != 0:
            for f in client_file.get('files', []):
                service.files().delete(fileId=f.get('id')).execute()
        service.files().create(body=client_file_object, media_body=client_file_media).execute()

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')
    except FileNotFoundException as error:
        print(f'Not found on Google Drive: {error}')


if __name__ == '__main__':
    main(sys.argv[1:])
