import gspread
import csv
import sys
#from gspread.httpsession import HTTPSession
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import http.client as httplib

sys.excepthook = sys.__excepthook__

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
            
    def internet_connected(self):
        conn = httplib.HTTPConnection("www.google.fi", timeout=2)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(e)
            return False
            
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
        diff = (time - self.prev_log_time).total_seconds()
        print(time, self.prev_log_time)
        print(diff)
        log_interval = 2
        if diff >= log_interval:
            if not self.internet_connected():
                self.prev_log_time = time + timedelta(0, 120)
                with open('logfail.csv', 'a', newline='') as logfile:
                    logwriter = csv.writer(logfile, delimiter=',')
                    logwriter.writerow(['Logging to Google Drive failed: no Internet connection', time.strftime("%Y-%m-%d %H:%M:%S")])
                return
            
            nof_rows = int(log_interval + log_interval / 2)
            print(nof_rows)
            try:
                print('Data to be logged before:', len(self.tempdata) )
                self.sheets()
                for row in self.tempdata[0:nof_rows]:
                    self.sheet.append_row(row)
                self.tempdata = self.tempdata[nof_rows:]
                self.prev_log_time = time
                print('Data to be logged after:', len(self.tempdata) )
            except Exception as e: 
                print('Logging to Google Drive failed at', time)
                print('Exception {}'.format(type(e).__name__))
                #print(e)
                with open('logfail.csv', 'a', newline='') as logfile:
                    logwriter = csv.writer(logfile, delimiter=',')
                    logwriter.writerow(['Logging to Google Drive failed: {}'.format(type(e).__name__), time.strftime("%Y-%m-%d %H:%M:%S")])
        #elif not self.internet_connected():
                #if not self.internet_connected():
            # If no internet wait a few minutes before trying again
   
        
    def log_alive(self):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.sheets()
            print('Try to insert')
            self.alive.insert_row([time])
            print('Insert successful')
        except TypeError as e:
            print('Error logging alive: weird buffering error:', e)
        except:
            print('Error logging alive: something else')
        
    def get_all(self):
        return self.sheet.get_all_values()