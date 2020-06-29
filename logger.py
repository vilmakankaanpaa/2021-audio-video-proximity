import gspread
import csv
import sys
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, date
import http.client as httplib
import uuid
import configs

sys.excepthook = sys.__excepthook__

class Logger:

    def __init__(self):

        # The actual connection instances (set by self._connect_sheets())
        self.ix_sheet = None
        self.alive_sheet = None
        self.progrun_sheet = None
        self.sensor_sheet = None

        self.tempdata = []
        self.prev_log_time = datetime.now()
        self.nof_logs = 0 #TODO
        self.sensors_temp = []

        self.ix_id = None
        self.ix_date = None
        self.ix_start = None

        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        self.client = gspread.authorize(self.creds)
        self.client.login()

        self.connect_sheets() # logs in and connects to the sheet instances
        self.reset_sheets()


    def reset_sheets(self):
        # reset sheet rows if empty (since rows are appended and default sheet already has empty rows)
        if len(self.ix_sheet.get_all_values()) == 1:
            self.ix_sheet.resize(rows=1,cols=6)

        if len(self.progrun_sheet.get_all_values()) == 1:
            self.progrun_sheet.resize(rows=1,cols=8)

        if len(self.alive_sheet.get_all_values()) == 1:
            self.alive_sheet.resize(rows=1,cols=1)

        if len(self.sensor_sheet.get_all_values()) == 1:
            self.sensor_sheet.resize(rows=1,cols=8)


    def connect_sheets(self):

        print('Connecting sheets..')

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

        print('Testing internet..')

        conn = httplib.HTTPConnection("www.google.fi", timeout=2)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(e)
            return False


    def log_interval_okay(self):

        timestamp = datetime.now()
        diff = (timestamp - self.prev_log_time).total_seconds()
        log_interval = 2

        if diff >= log_interval:
            return True
        else:
            return False


    def update_ix_logs(self):

        if (len(self.tempdata) > 0) and self.log_interval_okay():
            try:
                self.log_ix_to_drive()
            except:
                print(datetime.now(), " Could not log interaction to drive. Logging locally.")
                self.log_local(self.tempdata, sheet='local_ix_log.csv')


    def log_ix_to_drive(self):

        """
        TODO, make sure the amount is fine for the quota
        nof_rows = int(log_interval + log_interval / 2)
        """

        print('Trying to log ix to drive..')

        if not self.internet_connected():
            print('No internet connection.')
            self.log_local(
                ['Logging to Google Drive failed: no Internet connection',
                timestamp.strftime("%Y-%m-%d %H:%M:%S")],
                sheet='logfail.csv')
            raise

        nof_rows = len(self.tempdata) # change this if problems occur
        data = self.tempdata[0:nof_rows]

        try:
            self.connect_sheets()
            print('Trying to log ix end data. Data rows:', nof_rows)
            for row in data:
                self.ix_sheet.append_row(row)

            self.prev_log_time = datetime.now()
            self.tempdata = self.tempdata[nof_rows:]

        except Exception as e:
            print('Logging to GDrive failed:', e)
            print('Data:', data)
            self.log_local(
                ['Logging to Google Drive failed: {}'.format(type(e).__name__),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.ix_sheet],
                sheet='logfail.csv')
            raise


    def log_interaction_start(self):

        self.ix_id = str(uuid.uuid4())[0:6]
        self.ix_date = date.isoformat(date.today())
        self.ix_start = datetime.now()


    def log_interaction_end(self):

        ID = self.ix_id
        date = self.ix_date
        startime = self.ix_start
        endtime = datetime.now()
        duration = (endtime - self.ix_start).total_seconds()
        phase = configs.TEST_PHASE
        # id, starttime, endtime, duration
        data = [ID, date, startime.strftime("%Y-%m-%d %H:%M:%S"),
            endtime.strftime("%Y-%m-%d %H:%M:%S"), duration, phase]

        self.tempdata.append(data)

        # reset
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None


    def log_alive(self):

        if self.log_interval_okay():
            print('Logging alive')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = [timestamp]

            if not self.internet_connected():
                print('No internet connection.')
                self.log_local(
                    ['Logging to Google Drive failed: no Internet connection',
                    timestamp.strftime("%Y-%m-%d %H:%M:%S")],
                    sheet='logfail.csv')

            try:
                self.connect_sheets()
                self.alive_sheet.insert_row(data)
                self.prev_log_time = datetime.now()

            except Exception as e:
                print('Logging to GDrive failed:', e)

                self.log_local(
                    ['Logging to Google Drive failed: {}'.format(type(e).__name__),
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    self.alive_sheet],
                    sheet='logfail.csv')

                self.log_local(data, sheet='alive_log.csv')


    def log_sensor_status(self, ixID, sensorsInRange, playingAudio,
                          playingVideo, cameraIsRecording):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor1 = sensorsInRange[0]
        sensor2 = sensorsInRange[1]
        sensor3 = sensorsInRange[2]
        self.sensors_temp.append(
            [ixID, timestamp, sensor1, sensor2, sensor3,
            playingAudio, playingVideo, cameraIsRecording])
        data = self.sensors_temp

        if self.log_interval_okay():

            if not self.internet_connected():
                print('No internet connection.')
                self.log_local(
                    ['Logging to Google Drive failed: no Internet connection',
                    timestamp.strftime("%Y-%m-%d %H:%M:%S")],
                    sheet='logfail.csv')

            try:
                self.connect_sheets()
                for row in data:
                    self.sensor_sheet.insert_row(row)
                self.prev_log_time = datetime.now()

            except Exception as e:
                print('Logging to GDrive failed:', e)
                self.log_local(
                    ['Logging to Google Drive failed: {}'.format(type(e).__name__),
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    self.sensor_sheet],
                    sheet='logfail.csv')
                self.log_local(data, sheet='sensor_log.csv')


    def log_program_run_info(self):

        # not testing for log interval because only done in beginning of program run - these details wond change
        print('Logging progrum run info')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [
            timestamp,
            configs.TEST_PHASE,
            configs.USE_VIDEO,
            configs.VIDEO_AUDIO_ON,
            configs.VIDEO_PATH,
            configs.USE_AUDIO,
            configs.AUDIO_PATH,
            configs.RECORDING_ON
            ]

        if not self.internet_connected():
            print('No internet connection.')
            self.log_local(
                ['Logging to Google Drive failed: no Internet connection',
                timestamp.strftime("%Y-%m-%d %H:%M:%S")],
                sheet='logfail.csv')
        else:
            try:
                self.connect_sheets()
                self.progrun_sheet.append_row(data)

            except Exception as e:
                print('Logging to GDrive failed:', e)
                self.log_local(
                    ['Logging to Google Drive failed: {}'.format(type(e).__name__),
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    self.progrun_sheet],
                    sheet='logfail.csv')
                self.log_local(data, sheet='progrun_log.csv')


    def get_ix_info(self):
        return self.ix_id, self.ix_start


    def log_local(self, data, sheet):

        with open(sheet, 'a', newline='') as logfile:
            logwriter = csv.writer(logfile, delimiter=',')
            logwriter.writerow(data)
