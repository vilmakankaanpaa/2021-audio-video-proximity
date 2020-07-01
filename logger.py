import gspread
import csv
import sys
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, date
import http.client as httplib
from httplib2 import Http
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
import uuid
import configs

sys.excepthook = sys.__excepthook__

class Logger:

    def __init__(self, pid):

        # program run id to match data from same run easily
        self.pid = str(pid) + str(uuid.uuid4())[0:4]

        # The actual connection instances (set by self._connect_sheets())
        self.ix_sheet = None
        self.alive_sheet = None
        self.progrun_sheet = None
        self.sensor_sheet = None

        self.sensorlog_timer = datetime.now()
        self.quota_timer = datetime.now()
        self.alivelog_timer = datetime.now()
        self.ie_check_timer = datetime.now()

        self.max_nof_rows = 100
        self.tempdata = []
        self.sensors_temp = []

        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None

        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

        # Authorize access to Google Sheets
        self.client = gspread.authorize(self.creds)
        self.client.login()

        # Authorize access to Google Drive
        self.drive_service = build('drive', 'v3', http=self.creds.authorize(Http()))

        self.connect_sheets() # logs in and connects to the sheet instances
        self.reset_sheets()


    def createNewFolder(self, folderName):

        upload_details = {
            'name':folderName,
            'parentFolderId': configs.GDRIVE_FOLDER_ID
            }

        file_metadata = {
            'name': upload_details['name'],
            'mimeType': 'application/vnd.google-apps.folder'
            'parents':[upload_details['parentFolderId']]
            }

        file = self.drive_service.files().create(body=file_metadata,
                                            fields='id').execute()
        print('Created folder {} with id {}.'.format(name, file.get('id')))

        # No need to grant access if the folder is under the folder owned by you (?)


    def deleteDriveFile(self, resourceId):

        try:
            self.drive_service.delete(resourceId).execute()
            print('Deleted resource with id {}'.format(resourceId))
        except Exception as e:
            print('Deletion failed:', e)


    def listDriveFiles(self):
        results = self.drive_service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
        print(results)


    def uploadFile(self, fileName):

        upload_details = {
            'name':fileName,
            'folderId': configs.GDRIVE_FOLDER_ID,
            'filePath': configs.RECORDINGS_PATH + fileName,
            'grantAccessTo': configs.GDRIVE_USER_EMAIL
            }

        file_metadata = {
            'name': upload_details['name'],
            'mimeType': '*/*',
            'parents':[upload_details['folderId']]
            }

        media = MediaFileUpload(
            upload_details['filePath'],
            mimetype='*/*'
            )

        try:
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id').execute()

            print('Uploaded file {} with id {}.'.format(
                    upload_details['name'], file.get('id')))

        except Exception as e:
            print(e)

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


    def reset_sheets(self):
        # reset sheet rows if empty (since rows are appended and default sheet already has empty rows)
        if len(self.ix_sheet.get_all_values()) == 1:
            self.ix_sheet.resize(rows=1,cols=8)

        if len(self.progrun_sheet.get_all_values()) == 1:
            self.progrun_sheet.resize(rows=1,cols=9)

        if len(self.alive_sheet.get_all_values()) == 1:
            self.alive_sheet.resize(rows=1,cols=2)

        if len(self.sensor_sheet.get_all_values()) == 1:
            self.sensor_sheet.resize(rows=1,cols=12)


    def connect_sheets(self):

        #print('Connecting to sheets')

        if not self.creds.access_token_expired:
            if self.ix_sheet and self.alive_sheet and self.progrun_sheet and self.sensor_sheet:
                #print('Logged in and G sheets are setup.')
                return

        if self.creds.access_token_expired:
            self.client.login()

        self.ix_sheet = self.client.open(configs.DOCNAME).worksheet(configs.IX_SHEET)
        self.alive_sheet = self.client.open(configs.DOCNAME).worksheet(configs.ALIVE_SHEET)
        self.progrun_sheet = self.client.open(configs.DOCNAME).worksheet(configs.PROGRUN_SHEET)
        self.sensor_sheet = self.client.open(configs.DOCNAME).worksheet(configs.SENSOR_SHEET)


    def internet_connected(self):

        diff = int((datetime.now() - self.ie_check_timer).total_seconds())
        if (diff > (4*60)): # every four minutes max
            print('Checking internet.')
            self.ie_check_timer = datetime.now()
            conn = httplib.HTTPConnection("www.google.fi", timeout=2)
            try:
                conn.request("HEAD", "/")
                conn.close()

            except Exception as e:
                conn.close()
                print(e)
                raise


    def check_quota_counter(self):
        # reset log timer every 100s – quota for google is 100 requests per 100 seconds
        if (datetime.now()-self.quota_timer).total_seconds() > 100:
            self.quota_timer = datetime.now()
            self.max_nof_rows = 100


    def update_ix_logs(self):

        if (len(self.tempdata) > 0):
            try:
                self.log_ix_to_drive()
            except:
                self.log_local(self.tempdata, sheet='local_ix_log.csv')


    def log_ix_to_drive(self):

        print('Logging ix to drive')
        try:
            self.internet_connected()
        except:
            reason = "No internet."
            self.log_g_fail(reason)
            raise

        nof_rows = self.max_nof_rows
        if len(self.tempdata) > nof_rows:
            data = self.tempdata[0:nof_rows]
        else:
            data = self.tempdata

        try:
            self.connect_sheets()

            for row in data:
                self.ix_sheet.append_row(row)

            if len(self.tempdata)==len(data):
                self.tempdata = []
            else:
                self.tempdata = self.tempdata[nof_rows:]
            self.max_nof_rows = self.max_nof_rows - len(data)

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))
            raise


    def log_interaction_start(self):

        self.ix_id = str(uuid.uuid4())[0:6]
        self.ix_date = date.isoformat(date.today())
        self.ix_start = datetime.now()

        return self.ix_id


    def log_interaction_end(self):

        pid = self.pid
        ID = self.ix_id
        date = self.ix_date
        startime = self.ix_start
        endtime = datetime.now()
        duration = (endtime - self.ix_start).total_seconds()
        phase = configs.TEST_PHASE
        video = self.ix_recording
        # id, starttime, endtime, duration
        data = [self.pid, ID, date, startime.strftime("%Y-%m-%d %H:%M:%S"),
            endtime.strftime("%Y-%m-%d %H:%M:%S"), duration, phase, video]

        self.tempdata.append(data)

        # reset
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None


    def log_alive(self):

        timeDiff = (datetime.now() - self.alivelog_timer).total_seconds() / 60
        if timeDiff < 5: # log every 5 minutes
            return

        if self.max_nof_rows > 0:
            print('Logging alive')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = [self.pid, timestamp]

            try:
                self.internet_connected()
            except:
                reason = "No internet."
                self.log_g_fail(reason)

            try:
                self.connect_sheets()
                self.alive_sheet.insert_row(data)
                self.max_nof_rows = self.max_nof_rows - 1
                self.alivelog_timer = datetime.now()

            except Exception as e:
                self.log_g_fail('{}'.format(type(e).__name__))


    def log_sensor_status(self, sensorsInRange, sensorVolts, playingAudio,
                          playingVideo, cameraIsRecording, ixID=None):

        if (datetime.now() - self.sensorlog_timer).total_seconds() < 2:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor1_r = sensorsInRange[0]
        sensor2_r = sensorsInRange[1]
        sensor3_r = sensorsInRange[2]

        sensor1_v = ('%.2f' % sensorVolts[0])
        sensor2_v = ('%.2f' % sensorVolts[1])
        sensor3_v = ('%.2f' % sensorVolts[2])

        print('IxID:', ixID)
        for i in range(3):
            print(sensorsInRange[i], sensorVolts[i])

        self.sensors_temp.append(
            [self.pid, ixID, timestamp, sensor1_r, sensor1_v, sensor2_r, sensor2_v,
             sensor3_r, sensor3_v, playingAudio, playingVideo, cameraIsRecording])

        nof_rows = self.max_nof_rows
        if len(self.sensors_temp) > nof_rows:
            data = self.sensors_temp[0:nof_rows]
        else:
            data = self.sensors_temp

        try:
            self.internet_connected()
        except:
            reason = "No internet."
            self.log_g_fail(reason)

        try:
            self.connect_sheets()
            for row in data:
                self.sensor_sheet.append_row(row)

            self.sensorlog_timer = datetime.now()
            if len(data) == len(self.sensors_temp):
                self.sensors_temp = []
            else:
                self.sensors_temp = self.sensors_temp[nof_rows:]

            self.max_nof_rows = self.max_nof_rows - len(data)

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))
            self.log_local(data, sheet='sensor_log.csv')


    def log_program_run_info(self):

        # not testing for log interval because only done in beginning of program run - these details wond change
        #print('Logging progrum run info')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [
            self.pid,
            timestamp,
            configs.TEST_PHASE,
            configs.USE_VIDEO,
            configs.VIDEO_AUDIO_ON,
            configs.VIDEO_PATH,
            configs.USE_AUDIO,
            configs.AUDIO_PATH,
            configs.RECORDING_ON
            ]

        try:
            self.internet_connected()
        except:
            reason = "No internet."
            self.log_g_fail(reason)
            raise

        try:
            self.connect_sheets()
            self.progrun_sheet.append_row(data)
        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))
            self.log_local(data, sheet='progrun_log.csv')


    def get_ix_info(self):
        return self.ix_id, self.ix_start


    def set_ix_recording_name(self, videoName):
        self.ix_recording = videoName


    def log_local(self, data, sheet):
        print('Logging to local file:',sheet)
        with open(sheet, 'a', newline='') as logfile:
            logwriter = csv.writer(logfile, delimiter=',')
            logwriter.writerow(data)


    def log_g_fail(self, reason):
        print('Logging to GDrive failed:', reason)
        self.log_local(
            [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Logging to Google Drive failed.',
            reason], sheet='logfail.csv')
