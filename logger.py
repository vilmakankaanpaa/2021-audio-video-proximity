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

        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        self.client = gspread.authorize(self.creds)
        self.client.login()

        self._connect_sheets() # logs in and connects to the sheet instances

        # reset sheet rows if empty (since rows are appended and default sheet already has empty rows)
        if 1 == len(self.ix_sheet_.get_all_values()):
            self.ix_sheet_.resize(rows=1)


    def connect_sheets(self):

        if not self.creds.access_token_expired:
            if self.ix_sheet_ and self.alive_sheet_ and self.tech_sheet_
                #print('Logged in and G sheets are setup.')
                return

        if self.creds.access_token_expired:
            self.client.login()

        self.ix_sheet_ = self.client.open(self.DOCNAME).worksheet(self.IXSHEET)
        self.alive_sheet_ = self.client.open(self.DOCNAME).worksheet(self.ALIVESHEET)
        self.tech_sheet_ = self.client.open(self.DOCNAME).worksheet(self.TECHSHEET)


    def internet_connected(self):
        # Try to connect to Google to see if there is internet

        conn = httplib.HTTPConnection("www.google.fi", timeout=2)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(e)
            return False


    def log_drive(self):

        diff = (datetime.now() - self.prev_log_time).total_seconds()
        # Log online every two seconds
        log_interval = 2
        if diff >= log_interval:

            # If there is no internet connection only log locally
            if not self.internet_connected():
                log_local(['Logging to Google Drive failed: no Internet connection', timestamp.strftime("%Y-%m-%d %H:%M:%S")], sheet='logfail.csv')
                return

            nof_rows = int(log_interval + log_interval / 2)

            try:
                self.connect_sheets()
                for row in self.tempdata[0:nof_rows]:
                    self.ix_sheet_.append_row(row)
                self.tempdata = self.tempdata[nof_rows:]
                self.prev_log_time = timestamp

            except Exception as e:
                log_local(['Logging to Google Drive failed: {}'.format(type(e).__name__), timestamp.strftime("%Y-%m-%d %H:%M:%S")], sheet='logfail.csv')


    def log_interaction_start(self):

        self.ix_id = str(uuid.uuid4())[0:6]
        self.ix_start = datetime.now()

    def log_interaction_end(self):

        ID = self.ix_id
        startime = self.ix_start
        endtime = datetime.timeNow()
        duration = (endtime - self.ix_start).total_seconds()
        # id, starttime, endtime, duration
        data = [ID, startime.strftime("%Y-%m-%d %H:%M:%S"), endtime.strftime("%Y-%m-%d %H:%M:%S"), duration]

        log_local(data, sheet='local_ix_log.csv')

        # reset
        self.ix_id = None
        self.ix_start = None


def log_local(data, sheet):

    with open(sheet, 'a', newline='') as logfile:
        logwriter = csv.writer(logfile, delimiter=',')
        logwriter.writerow(data)
