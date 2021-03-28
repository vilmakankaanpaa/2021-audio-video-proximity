import sys
import gspread
from httplib2 import Http
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Local source
import configs
from filemanager import printlog

sys.excepthook = sys.__excepthook__

class SheetsService:

    def __init__(self):

        self.spreadsheet_id = configs.SPREADSHEET_ID
        self.sheets = {
                    'ix': configs.IX_SHEET,
                    'progrun': configs.STARTS_SHEET,
                    'sensors': configs.SENSORS_SHEET,
                    'ping': configs.PING_SHEET
                }

        self.nof_rows_left = 100
        self.quota_timer = datetime.now() # The service account has request quota of 100 requests per 100 seconds

        SERVICE_ACCOUNT_FILE = '/home/pi/sakis-tunnel-2021/service_account.json'
        SCOPE = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

        self.creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)

        # Service for Google Sheets
        #printlog('Sheets','Logging in to Google Sheets..')
        print('Logging to sheets')
        self.service = build('sheets', 'v4', credentials=self.creds)
        print('Logging to drive')
        self.driveService = build('drive', 'v3', credentials=self.creds)

        #print(self.creds.expiry) # this is "None" so the credentials should not expire ever
        #self._check_connection()
        #self._reset_sheets() # TODO: is this really needed?


    # def _reset_sheets(self):
    #     # reset sheet rows if empty (since rows are appended and default sheet
    #     # already has empty rows)
    #     if len(self.ix_sheet.get_all_values()) == 1:
    #         self.ix_sheet.resize(rows=1,cols=8)
    #
    #     if len(self.progrun_sheet.get_all_values()) == 1:
    #         self.progrun_sheet.resize(rows=1,cols=9)
    #
    #     if len(self.sensor_sheet.get_all_values()) == 1:
    #         self.sensor_sheet.resize(rows=1,cols=12)
    #
    #     if len(self.ping_sheet.get_all_values()) == 1:
    #         self.ping_sheet.resize(rows=1,cols=1)
    #
    # def _open_sheets(self):
    #
    #     printlog('Sheets','Opening worksheets..')
    #     self.ix_sheet = self.client.open(configs.DOCNAME).worksheet(configs.IX_SHEET)
    #     self.progrun_sheet = self.client.open(configs.DOCNAME).worksheet(configs.PROGRUN_SHEET)
    #     self.sensor_sheet = self.client.open(configs.DOCNAME).worksheet(configs.SENSOR_SHEET)
    #     self.ping_sheet = self.client.open(configs.DOCNAME).worksheet(configs.PING_SHEET)


    def _reduce_nof_rows_left(self, amount):
        # TODO are the quotas still same?
        pass
        self.nof_rows_left = (self.nof_rows_left - amount)
        if (self.nof_rows_left < 10):
            printlog('Sheets','Less than 10 ({}) rows left in quota'.format(self.nof_rows_left))
        return self.nof_rows_left

    def check_quota_timer(self):
        # reset log timer every 100s – quota for google is 100 requests per 100 seconds
        pass
        diff = (datetime.now()-self.quota_timer).total_seconds()
        if diff >= 100:
            self.quota_timer = datetime.now()
            self.nof_rows_left = 100
            timeLeft = 0

    def log_to_drive(self, data, sheet):

        print('logging to drive')

        rowLimit = self.nof_rows_left
        if rowLimit == 0:
            # Quota is full ATM
            return data

        dataToLog = data
        truncated = False

        if len(data) > rowLimit:
            dataToLog = data[0:rowLimit]
            truncated = True

        #self._check_connection()

        spreadsheet_id = self.spreadsheet_id
        value_input_option = 'USER_ENTERED'

        body = {
            'values': dataToLog
        }

        try:
            range_name = self.sheets[sheet]
        except:
            printlog('Sheets','ERROR: No such sheet.')

        try:

            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption=value_input_option, body=body).execute()

            print('{0} cells appended.'.format(result \
                                                   .get('updates') \
                                                   .get('updatedCells')))
        except:
            printlog('Sheets', 'ERROR: Uplaoding to sheets failed.')
            raise # TODO: take off

        self._reduce_nof_rows_left(len(dataToLog))
        dataLeft = []

        if truncated:
            dataLeft = data[rowLimit:]

        return dataLeft
