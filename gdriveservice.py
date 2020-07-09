SS_SERVICEimport sys
from apiclient.discovery  import build
from httplib2 import Http
from apiclient.http import MediaFileUpload
from oauth2client import file, client, tools
from oauth2client.contrib import gce
from datetime import datetime

import configs

sys.excepthook = sys.__excepthook__

class DriveService:

    def __init__(self):

        CLIENT_SECRET = "/home/pi/sakis-video-tunnel/client_secret_drive.json"
        self.SCOPES='https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'
        self.store = file.Storage('token.json')
        # returns oauth2.client.Credentials
        # https://oauth2client.readthedocs.io/en/latest/source/oauth2client.client.html#oauth2client.client.Credentials
        # methods:
        # .athorize(httplib2.Http object)
        # .refresh(httplib2.Http object)

        self.creds = self.store.get()
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET, self.SCOPES)
            self.creds = tools.run_flow(flow, self.store)
        self.SERVICE = build('drive', 'v3', http=self.creds.authorize(Http()))

        ### Sheets
        self.SS_SERVICE = build('sheets', 'v4', http=self.creds.authorize(Http()))

        self.ix_sheet = None
        self.alive_sheet = None
        self.progrun_sheet = None
        self.sensor_sheet = None
        self.status_sheet = None

        self.nof_rows_left = 100
        self.quota_timer = datetime.now()

        self._open_sheets()
        self._reset_sheets()

### Sheets
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
        self.ix_sheet = self.SS_SERVICE.open(configs.DOCNAME).worksheet(configs.IX_SHEET)
        self.alive_sheet = self.SS_SERVICE.open(configs.DOCNAME).worksheet(configs.ALIVE_SHEET)
        self.progrun_sheet = self.SS_SERVICE.open(configs.DOCNAME).worksheet(configs.PROGRUN_SHEET)
        self.sensor_sheet = self.SS_SERVICE.open(configs.DOCNAME).worksheet(configs.SENSOR_SHEET)
        self.status_sheet = self.SS_SERVICE.open(configs.DOCNAME).worksheet(configs.STATUS_SHEET)


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

        self._check_connection()

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

### Drive

    def _check_connection(self):

        if self.creds.access_token_expired:
            self.creds.refresh(Http())
            # do I need to build again?)

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
            print('Gdrive: error in uploading:', e)
            raise e

        fileId = file.get('id')

        print('Gdrive: Uploaded file {} of type {} with id {}.'.format(
                metadata['name'], metadata['mimeType'], fileId))

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
            print(e)
            raise e

        print(datetime.isoformat(datetime.now()),
                'Gdrive: Created folder {} with id {}.'.format(
                    metadata['name'], folder.get('id')))

        return folder.get('id')


    def list_content(self):

        # NOTE! Sometimes resources are not found because this lists the
        # content only in the first page – it might not be on the first page.
        # TODO: update it to do it
        # TODO: it does not list folders now?
        self._check_connection()
        results = self.SERVICE.files().list(
                pageSize=1000, fields="nextPageToken, files(id, name)").execute()
        content = {}
        for item in results['files']:
            content[item['name']] = item['id']

        return content

    def upload_recording(self, fileName, parentFolderId):
        # Upload video file from the local camera-records folder

        localFilePath = configs.RECORDINGS_PATH + fileName
        metadata = {
            'name': fileName,
            'mimeType': '*/*', # for some reason did not work with 'application/vnd.google-apps.video'
            'parents':[parentFolderId]
            }

        fileId = self._upload_file(localFilePath, metadata)

    def upload_logfile(self, fileName):
        # Upload local logfile to drive from dir sakis-video-tunnel
        # to google drive folder 'Local log files'

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
            print('Gdrive: Deleted resource with id {}'.format(resourceId))

        except Exception as e:
            print('Deletion failed:', e)

    def delete_videos(self):

        content = self.list_content()
        videoIds = []
        for file in content:
            if file.endswith('.h264'):
                id = content[file]
                videoIds.append(id)

        for vid in videoIds:
            self.delete_drive_resource(vid)
