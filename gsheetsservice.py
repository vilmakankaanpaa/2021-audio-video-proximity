import sys
import gspread
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Local source
import configs
from filemanager import printlog

sys.excepthook = sys.__excepthook__

class SheetsService:

    def __init__(self):

        self.ix_sheet = None
        self.progrun_sheet = None
        self.sensor_sheet = None

        self.nof_rows_left = 100
        self.quota_timer = datetime.now() # The service account has request quota of 100 requests per 100 seconds

        CLIENT_SECRET = "/home/pi/sakis-video-tunnel/client_secret_sheets.json"
        SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CLIENT_SECRET, SCOPES)

        printlog('Sheets','Logging in to Google Sheets..')
        self.client = gspread.authorize(self.creds)
        self.client.login()
        self._open_sheets()
        self._reset_sheets()

    def _reset_sheets(self):
        # reset sheet rows if empty (since rows are appended and default sheet
        # already has empty rows)
        if len(self.ix_sheet.get_all_values()) == 1:
            self.ix_sheet.resize(rows=1,cols=8)

        if len(self.progrun_sheet.get_all_values()) == 1:
            self.progrun_sheet.resize(rows=1,cols=9)

        if len(self.sensor_sheet.get_all_values()) == 1:
            self.sensor_sheet.resize(rows=1,cols=12)

    def _open_sheets(self):

        printlog('Sheets','Opening worksheets..')
        self.ix_sheet = self.client.open(configs.DOCNAME).worksheet(configs.IX_SHEET)
        self.progrun_sheet = self.client.open(configs.DOCNAME).worksheet(configs.PROGRUN_SHEET)
        self.sensor_sheet = self.client.open(configs.DOCNAME).worksheet(configs.SENSOR_SHEET)

    def _check_connection(self):
        if self.creds.access_token_expired:
            printlog('Sheets','Access token had expired. Logging in.')
            self.client.login()
            self._open_sheets()

    def _reduce_nof_rows_left(self, amount):
        self.nof_rows_left = (self.nof_rows_left - amount)
        if (self.nof_rows_left < 10):
            printlog('Sheets','Less than 10 ({}) rows left in quota'.format(self.nof_rows_left))
        return self.nof_rows_left

    def check_quota_timer(self):
        # reset log timer every 100s – quota for google is 100 requests per 100 seconds
        diff = (datetime.now()-self.quota_timer).total_seconds()
        if diff >= 100:
            self.quota_timer = datetime.now()
            self.nof_rows_left = 100
            timeLeft = 0

    def log_to_drive(self, data, sheet):

        rowLimit = self.nof_rows_left
        if rowLimit == 0:
            # Quota is full ATM
            return data

        dataToLog = data
        truncated = False

        if len(data) > rowLimit:
            dataToLog = data[0:rowLimit]
            truncated = True

        self._check_connection()

        if sheet == 'ix':
            for row in dataToLog:
                self.ix_sheet.append_row(row)

        elif sheet == 'progrun':
            for row in dataToLog:
                self.progrun_sheet.append_row(row)

        elif sheet == 'sensors':
            for row in dataToLog:
                self.sensor_sheet.append_row(row)

        else:
            printlog('Sheets', 'ERROR: No such sheet defined')

        self._reduce_nof_rows_left(len(dataToLog))
        dataLeft = []

        if truncated:
            dataLeft = data[rowLimit:]

        return dataLeft
