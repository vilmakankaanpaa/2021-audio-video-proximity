import gspread
import csv
#from gspread.httpsession import HTTPSession
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class Logger:
    
    def __init__(self):
        self.sheet = None
        self.alive = None
        self.tempdata = []
        self.prev_log_time = datetime.now()
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        #http_session = HTTPSession(headers={'Connection':'Keep-Alive'})
        self.client = gspread.authorize(self.creds)#, http_session)
        self.client.login()
        
        
        self.sheets()
        
        # reset sheet rows if empty
        if 1 == len(self.sheet.get_all_values()):
            self.sheet.resize(rows=1)
            
    def log_local(self, data):
        # add data to tempdata to wait uploading to google sheets
        self.tempdata.append(data)
        with open('log.csv', 'a', newline='') as logfile:
            logwriter = csv.writer(logfile, delimiter=',')
            logwriter.writerow(data)

    def sheets(self):
        if not self.creds.access_token_expired and self.sheet and self.alive:
            print('All good already')
            return
        if self.creds.access_token_expired:
            self.client.login()
        self.sheet = self.client.open("Thesis-logs").worksheet("Proto 1 v 2")
        self.alive = self.client.open("Thesis-logs").worksheet("Alive")
    
    def log_drive(self, time):
        #self.tempdata.append(data)
        #self.log_local(data)
        #now = datetime.now()
        #diff = (now - self.prev_log_time).total_seconds() / 60.0
        #if diff >= 1:
        try:
            self.sheets()
            for row in self.tempdata:
                self.sheet.append_row(row)
            self.tempdata = []
            self.prev_log_time = time
        except:
            print('Logging to Google Drive failed at', time)
        
        
    def log_alive(self):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sheets()
        try:
            print('Try to insert')
            self.alive.insert_row([time])
            print('Insert successful')
        except TypeError as e:
            print('Error logging alive: weird buffering error:', e)
        except:
            print('Error logging alive: something else')
        
    def get_all(self):
        return self.sheet.get_all_values()