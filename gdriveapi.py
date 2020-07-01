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

        self.sheets = {
            'ix': self.ix_sheet,
            'alive': self.alive_sheet,
            'progrun': self.progrun_sheet,
            'sensors': self.sensor_sheet
        }

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
        self._connect_sheets()
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


    def _connect_sheets(self):

        print('Connecting to sheets..')

        if not self.creds.access_token_expired:
            if self.ix_sheet and self.alive_sheet and self.progrun_sheet and self.sensor_sheet:
                # TODO: do this better
                #print('Logged in and G sheets are setup.')
                return

        if self.creds.access_token_expired:
            self.client.login()

        self.ix_sheet = self.client.open(configs.DOCNAME).worksheet(configs.IX_SHEET)
        self.alive_sheet = self.client.open(configs.DOCNAME).worksheet(configs.ALIVE_SHEET)
        self.progrun_sheet = self.client.open(configs.DOCNAME).worksheet(configs.PROGRUN_SHEET)
        self.sensor_sheet = self.client.open(configs.DOCNAME).worksheet(configs.SENSOR_SHEET)


    def _reduce_nof_rows_left(self, amount):
        self.nof_rows_left = self.nof_rows_left-amount
        return self.nof_rows_left


    def check_quota_timer(self):
        # reset log timer every 100s – quota for google is 100 requests per 100 seconds
        diff = (datetime.now()-self.quota_timer).total_seconds()
        if diff >= 100:
            self.quota_timer = datetime.now()
            self.nof_rows_left = 100
            timeLeft = 0


    def createNewFolder(self, folderName):

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
        print('Gdrive: Created folder {} with id {}.'.format(upload_details['name'], folder.get('id')))

        # No need to grant access if the folder is under the folder owned by you

        return folder.get('id')


    def deleteDriveResource(self, resourceId):

        try:
            self.drive_service.files().delete(fileId=resourceId).execute()
            print('Gdrive: Deleted resource with id {}'.format(resourceId))
        except Exception as e:
            print('Deletion failed:', e)


    def getDriveFiles(self):
        results = self.drive_service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        return results


    def uploadFile(self, fileName, folderId):

        upload_details = {
            'name':fileName,
            'folderId': folderId,
            'localFilePath': configs.RECORDINGS_PATH + fileName,
            'grantAccessTo': configs.GDRIVE_USER_EMAIL
            }

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
        self.grantPermissions(file.get('id'), upload_details)


    def grantPermissions(self, fileId, metadata):
        user_permission = {
            'type':'user',
            'role':'writer',
            'emailAddress':metadata['grantAccessTo']
            }
        self.drive_service.permissions().create(
            fileId=fileId,body=user_permission,fields='id').execute()
        print('Gdrive: Permission to resource granted.')


    def logToDrive(self, data, sheet):

        print('Gdrive: Logging to drive, to {}'.format(sheet))
        rowLimit = self.nof_rows_left

        if rowLimit == 0:
            return data

        dataToLog = data
        truncated = False

        if len(data) > rowLimit:
            dataToLog = data[0:rowLimit]
            truncated = True

        self._connect_sheets()
        for row in dataToLog:
            self.sheets[sheet].append_row(row)

        self._reduce_nof_rows_left(len(dataToLog))

        dataLeft = []
        if truncated:
            dataLeft = data[rowLimit:]

        return dataLeft
