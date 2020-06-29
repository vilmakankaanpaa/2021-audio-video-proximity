import gspread
import csv
import sys
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import http.client as httplib
import uuid
import configs

sys.excepthook = sys.__excepthook__

class Logger:

    def __init__(self):

        # Name of the Google Sheets document and the worksheets inside of it
        self.DOCNAME = configs.G_LOG_FILE
        self.IXSHEET = configs.G_LOG_SHEET_IX
        self.TECHSHEET = configs.G_LOG_SHEET_TECH
        self.ALIVESHEET = configs.G_LOG_SHEET_ALIVE

        # The actual connection instances (set by self._connect_sheets())
        self.ix_sheet_ = None
        self.alive_sheet_ = None
        self.tech_sheet_ = None

        self.tempdata = []
        self.prev_log_time = datetime.now()
        self.ix_id = None
        self.ix_start = None
        self.test_phase = configs.TEST_PHASE

        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        self.client = gspread.authorize(self.creds)
        self.client.login()

        self.connect_sheets() # logs in and connects to the sheet instances

        # reset sheet rows if empty (since rows are appended and default sheet already has empty rows)
        if 1 == len(self.ix_sheet_.get_all_values()):
            self.ix_sheet_.resize(rows=1)


    def connect_sheets(self):
        
        print('Connecting sheets..')

        if not self.creds.access_token_expired:
            if self.ix_sheet_ and self.alive_sheet_ and self.tech_sheet_:
                #print('Logged in and G sheets are setup.')
                return

        if self.creds.access_token_expired:
            self.client.login()

        self.ix_sheet_ = self.client.open(self.DOCNAME).worksheet(self.IXSHEET)
        self.alive_sheet_ = self.client.open(self.DOCNAME).worksheet(self.ALIVESHEET)
        self.tech_sheet_ = self.client.open(self.DOCNAME).worksheet(self.TECHSHEET)


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


    def log_to_drive(self, data, sheet, append=True):

        timestamp = datetime.now()
        diff = (timestamp - self.prev_log_time).total_seconds()
        log_interval = 2
        if diff >= log_interval:
            
            print('Log interval fine. Trying to log.')

            if not self.internet_connected():
                print('No internet connection.')
                self.log_local(['Logging to Google Drive failed: no Internet connection', timestamp.strftime("%Y-%m-%d %H:%M:%S")], sheet='logfail.csv')
                raise

            try:
                self.connect_sheets()
                
                print(len(data))
                if len(data) > 1:
                    print('Logging to drive. More than 1 row in data.')
                    if append:
                        sheet.append_rows(data)
                    else:
                        sheet.insert_rows(data)
                else:
                    print('Logging to drive one row')
                    print(data)
                    if append:
                        sheet.append_row(data)
                    else:
                        sheet.insert_row(data)

                self.prev_log_time = datetime.now()
                
                return True

            except Exception as e:
                print('Logging to GDrive failed:', e)
                log_local(['Logging to Google Drive failed: {}'.format(type(e).__name__), timestamp.strftime("%Y-%m-%d %H:%M:%S"), sheet], sheet='logfail.csv')
                raise

        else:
            return False
    
    def log_interaction_start(self):

        self.ix_id = str(uuid.uuid4())[0:6]
        self.ix_start = datetime.now()


    def log_interaction_end(self):

        ID = self.ix_id
        startime = self.ix_start
        endtime = datetime.now()
        duration = (endtime - self.ix_start).total_seconds()
        phase = configs.TEST_PHASE
        # id, starttime, endtime, duration
        data = [ID, startime.strftime("%Y-%m-%d %H:%M:%S"), endtime.strftime("%Y-%m-%d %H:%M:%S"), duration, phase]

        self.tempdata.append(data)

        """
        nof_rows = int(log_interval + log_interval / 2)

        for row in self.tempdata[0:nof_rows]:
            self.ix_sheet_.append_row(row)
        self.tempdata = self.tempdata[nof_rows:]
        """

        try:
            print('Trying to log ix end data. Data:', data)
            logged = self.log_to_drive(data=self.tempdata, sheet=self.ix_sheet_, append=True)
            if logged:
                self.tempdata = []
        except:
            print(datetime.now(), " Could not log interaction to drive. Logging locally.")
            self.log_local(data, sheet='local_ix_log.csv')

        # reset
        self.ix_id = None
        self.ix_start = None


    def log_alive(self):

        print('Logging alive')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [timestamp]
        try:
            self.log_to_drive(row=data, sheet=self.alive_sheet_, append=False)
            print('alive logged to drive')
        except:
            self.log_local(data, sheet='alive_log.csv')
            print('alive logged locally')


    def log_tech_details(self):
        print('Logging tech')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [timestamp, configs.TEST_PHASE, configs.USE_VIDEO, configs.VIDEO_AUDIO_ON, configs.VIDEO_PATH, configs.USE_AUDIO, configs.AUDIO_PATH, configs.RECORDING_ON]
        try:
            self.log_to_drive(row=data, sheet=self.tech_sheet_, append=True)
            print('tech logged')
        except:
            self.log_local(data, sheet='tech_log.csv')
            print('Tech logged locally')

    def log_local(self, data, sheet):

        with open(sheet, 'a', newline='') as logfile:
            logwriter = csv.writer(logfile, delimiter=',')
            logwriter.writerow(data)
