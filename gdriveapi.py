import sys
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from apiclient.discovery import build
from httplib2 import Http
from apiclient.http import MediaFileUpload
from datetime import datetime, timedelta, date

import configs

sys.excepthook = sys.__excepthook__

class DriveService:

    def __init__(self):

        self.ix_sheet = None
        self.alive_sheet = None
        self.progrun_sheet = None
        self.sensor_sheet = None
        self.status_sheet = None

        self.nof_rows_left = 100
        self.quota_timer = datetime.now()

        # use creds to create a client to interact with the Google Drive API
        SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', SCOPES)

        # Authorize access to Google Sheets
        print('Authorizing to google sheets..')
        self.client = gspread.authorize(self.creds)
        self.client.login()

        # Authorize access to Google Drive
        print('Authorizing to google drive..')
        self.drive_service = build('drive', 'v3', http=self.creds.authorize(Http()))
        self._open_sheets()
        self._reset_sheets()


    def _reset_sheets(self):
        # reset sheet rows if empty (since rows are appended and default sheet
        # already has empty rows)
        if len(self.ix_sheet.get_all_values()) == 1:
            self.ix_sheet.resize(rows=1,cols=8)

        if len(self.progrun_sheet.get_all_values()) == 1:
            self.progrun_sheet.resize(rows=1,cols=9)

        if len(self.alive_sheet.get_all_values()) == 1:
            self.alive_sheet.resize(rows=1,cols=2)

        if len(self.sensor_sheet.get_all_values()) == 1:
            self.sensor_sheet.resize(rows=1,cols=12)

        if len(self.status_sheet.get_all_values()) == 1:
            self.status_sheet.resize(rows=1, cols=3)


    def _open_sheets(self):

        print('Opening google sheets..')
        self.ix_sheet = self.client.open(configs.DOCNAME).worksheet(configs.IX_SHEET)
        self.alive_sheet = self.client.open(configs.DOCNAME).worksheet(configs.ALIVE_SHEET)
        self.progrun_sheet = self.client.open(configs.DOCNAME).worksheet(configs.PROGRUN_SHEET)
        self.sensor_sheet = self.client.open(configs.DOCNAME).worksheet(configs.SENSOR_SHEET)
        self.status_sheet = self.client.open(configs.DOCNAME).worksheet(configs.STATUS_SHEET)

    def _connect_sheets(self):
        if self.creds.access_token_expired:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Access token had expired. Logging into Google Sheets.')
            self.client = gspread.authorize(self.creds)
            self.client.login()
            self._open_sheets()

    def _connect_drive(self):
        if self.creds.access_token_expired:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Access token had expired. Connecting to Google Drive.')
            self.drive_service = build('drive', 'v3', http=self.creds.authorize(Http()))


    def _reduce_nof_rows_left(self, amount):
        self.nof_rows_left = (self.nof_rows_left - amount)
        if (self.nof_rows_left < 10):
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Only {} rows left!'.format(self.nof_rows_left))
        return self.nof_rows_left


    def check_quota_timer(self):
        # reset log timer every 100s – quota for google is 100 requests per 100 seconds
        diff = (datetime.now()-self.quota_timer).total_seconds()
        if diff >= 100:
            self.quota_timer = datetime.now()
            self.nof_rows_left = 100
            timeLeft = 0
            #print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             #   'Quota updated to 100')


    def create_new_folder(self, folderName):

        self._connect_drive()

        upload_details = {
            'name':folderName,
            'parentFolderId': configs.GDRIVE_FOLDER_ID
            }

        folder_metadata = {
            'name': upload_details['name'],
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [upload_details['parentFolderId']]
            }

        folder = self.drive_service.files().create(body=folder_metadata,
                                            fields='id').execute()
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Gdrive: Created folder {} with id {}.'.format(
                    upload_details['name'], folder.get('id')))

        # No need to grant access if the folder is under the folder owned by you

        return folder.get('id')


    def delete_drive_resource(self, resourceId):

        self._connect_drive()

        try:
            self.drive_service.files().delete(fileId=resourceId).execute()
            print('Gdrive: Deleted resource with id {}'.format(resourceId))
        except Exception as e:
            print('Deletion failed:', e)


    def get_drive_contents(self):
        # NOTE! Sometimes resources are not found because this lists the
        # content only in the first page – it might not be on the first page.
        # TODO: update it to do it
        self._connect_drive()
        results = self.drive_service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        return results

    def list_drive_contents(self):

        results = self.get_drive_contents()
        files = {}
        for item in results['files']:
            files[item['name']] = item['id']

        return files


    def upload_video_file(self, fileName, folderId):
        # For purpose of uploading recordings

        upload_details = {
            'name':fileName,
            'folderId': folderId,
            'localFilePath': configs.RECORDINGS_PATH + fileName,
            'grantAccessTo': configs.GDRIVE_USER_EMAIL
            }

        self._upload_file(upload_details)


    def upload_general_file(self, fileName):
        # For the purpose of uploading local log files like logfail.csv

        upload_details = {
            'name': datetime.now().strftime("%m-%d_%H-%M") + '_' + fileName,
            'folderId': configs.GDRIVE_FOLDER_ID_LOGS,
            'localFilePath': configs.root + fileName,
            'grantAccessTo': configs.GDRIVE_USER_EMAIL
        }

        self._upload_file(upload_details)


    def _upload_file(self, upload_details):
        # general module to upload any file to specified folder in Google Drive
        # NOTE: the app needs to have shared access to that folder

        self._connect_drive()

        file_metadata = {
            'name': upload_details['name'],
            'mimeType': '*/*',
            'parents':[upload_details['folderId']]
            }

        media = MediaFileUpload(
            upload_details['localFilePath'],
            mimetype='*/*'
            )

        try:
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id').execute()

            print('Gdrive: Uploaded file {} with id {}.'.format(
                    upload_details['name'], file.get('id')))

        except Exception as e:
            raise e

        # in case the file would not be uploaded to your own folder that you
        # share with the service account, you need to make sure to grant access
        # to your own account
        self._grant_permissions(file.get('id'), upload_details)


    def _grant_permissions(self, fileId, metadata):
        user_permission = {
            'type':'user',
            'role':'writer',
            'emailAddress':metadata['grantAccessTo']
            }
        self.drive_service.permissions().create(
            fileId=fileId,body=user_permission,fields='id').execute()
        #print('Gdrive: Permission to resource granted.')


    def log_to_drive(self, data, sheet):

        #print('Gdrive: Logging to drive, to {}'.format(sheet))
        rowLimit = self.nof_rows_left
        #print('Rowlimit {}'.format(rowLimit))
        if rowLimit == 0:
            return data

        dataToLog = data
        truncated = False

        if len(data) > rowLimit:
            dataToLog = data[0:rowLimit]
            truncated = True
        #print('Data:', data)
        #print('Datatolog:', dataToLog)

        self._connect_sheets()

        if sheet == 'ix':
            for row in dataToLog:
                self.ix_sheet.append_row(row)

        elif sheet == 'alive':
            for row in dataToLog:
                self.alive_sheet.append_row(row)

        elif sheet == 'progrun':
            for row in dataToLog:
                self.progrun_sheet.append_row(row)

        elif sheet == 'sensors':
            for row in dataToLog:
                self.sensor_sheet.append_row(row)

        elif sheet == 'status':
            for row in dataToLog:
                self.status_sheet.append_row(row)
        else:
            print('No such sheet defined')

        self._reduce_nof_rows_left(len(dataToLog))

        dataLeft = []
        if truncated:
            dataLeft = data[rowLimit:]
        #print('Datarows left {}'.format(len(dataLeft)))

        return dataLeft
