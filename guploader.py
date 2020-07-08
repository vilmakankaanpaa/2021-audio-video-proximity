import sys
from apiclient.discovery  import build
from httplib2 import Http
from apiclient.http import MediaFileUpload
from oauth2client import file, client, tools
from oauth2client.contrib import gce
from datetime import datetime

sys.excepthook = sys.__excepthook__

CLIENT_SECRET = "/home/pi/sakis-video-tunnel/client_secret_drive.json"

class GUploader:

    def __init__(self):

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

        #self.SS_SERVICE = build('sheets', 'v4', http=creds.authorize(Http()))


def _connect_drive(self):

    if self.creds.access_token_expired:
        self.creds.refresh(Http())
