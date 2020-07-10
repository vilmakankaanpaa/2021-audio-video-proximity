import sys
from apiclient.discovery  import build
from httplib2 import Http
from apiclient.http import MediaFileUpload
from oauth2client import file, client, tools
from datetime import datetime

# Local source
import configs
from filemanager import printlog

sys.excepthook = sys.__excepthook__

class DriveService:

    def __init__(self):

        CLIENT_SECRET = "/home/pi/sakis-video-tunnel/client_secret_drive.json"
        SCOPES='https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'
        self.store = file.Storage('token.json')
        # returns oauth2.client.Credentials
        # https://oauth2client.readthedocs.io/en/latest/source/oauth2client.client.html#oauth2client.client.Credentials
        # methods:
        # .athorize(httplib2.Http object)
        # .refresh(httplib2.Http object)

        printlog('Drive','Accessing google drive.')
        self.creds = self.store.get()
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
            self.creds = tools.run_flow(flow, self.store)
        self.SERVICE = build('drive', 'v3', http=self.creds.authorize(Http()))

    def _check_connection(self):

        if self.creds.access_token_expired:
            printlog('Drive','Access token had expired. Refreshing token for Drive.')
            self.creds.refresh(Http())

    def _upload_file(self, localFilePath, metadata):
        # general module to upload any file to specified folder in Google Drive
        self._check_connection()
        media = MediaFileUpload(
            localFilePath,
            mimetype=metadata['mimeType']
            )
        try:
            file = self.SERVICE.files().create(
                body=metadata,
                media_body=media,
                fields='id'
                ).execute()
        except Exception as e:
            printlog('Drive','ERROR: could not upload file. Emessage:', e)
            raise e

        fileId = file.get('id')
        #printlog('Drive','Uploaded file {} of type {} with id {}.'.format(
        #        metadata['name'], metadata['mimeType'], fileId))
        return fileId


    def create_folder(self, folderName, parentFolder=None):

        self._check_connection()
        if not parentFolder:
            metadata = {
                'name': folderName,
                'mimeType': 'application/vnd.google-apps.folder',
                }
        else:
            metadata = {
                'name': folderName,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parentFolder]
                }
        try:
            folder = self.SERVICE.files().create(
                    body=metadata,
                    fields='id'
                ).execute()
        except Exception as e:
            printlog('Drive','ERROR: could not create folder. Emessage:', e)
            raise e

        folderId = folder.get('id')
        printlog('Drive','Created folder {} with id {}.'.format(
                    metadata['name'], folderId))
        return folderId

    def list_content(self):

        self._check_connection()
        results = self.SERVICE.files().list(
                pageSize=1000, fields="nextPageToken, files(id, name, mimeType)").execute()
        files = {}
        folders = {}
        for item in results['files']:
            if item['mimeType'] != 'application/vnd.google-apps.folder':
                files[item['name']] = item['id']
            else:
                folders[item['name']] = item['id']

        return files, folders

    def upload_recording(self, fileName, parentFolderId):
        # Upload video file from the local camera-records folder
        localFilePath = configs.RECORDINGS_PATH + fileName
        metadata = {
            'name': fileName,
            'mimeType': '*/*', # for some reason did not work with 'application/vnd.google-apps.video'
            'parents':[parentFolderId]
            }

        fileId = self._upload_file(localFilePath, metadata)
        #TEST

    def upload_logfile(self, fileName):
        # Upload local logfile to drive from dir sakis-video-tunnel
        localFilePath = configs.root + fileName
        metadata = {
            'name': datetime.now().strftime("%m-%d_%H-%M") + '_' + fileName,
            'mimeType': '*/*',
            'parents': [configs.GDRIVE_FOLDER_ID_LOGS]
            }

        fileId = self._upload_file(localFilePath, metadata)

    def delete_resource(self, resourceId):

        self._check_connection()

        try:
            self.SERVICE.files().delete(fileId=resourceId).execute()
            print('Deleted resource with id {}'.format(resourceId))
        except Exception as e:
            print('ERROR: Could not delete file. Emessage:', e)

    def delete_videos(self):

        content = self.list_content()
        videoIds = []
        for file in content:
            if file.endswith('.h264'):
                id = content[file]
                videoIds.append(id)

        for vid in videoIds:
            self.delete_drive_resource(vid)
