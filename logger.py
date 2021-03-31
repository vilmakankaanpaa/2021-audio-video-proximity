#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import uuid
import requests
from datetime import datetime, date
from time import sleep

import configs
import globals
import filemanager
from filemanager import printlog
from googleservice import GoogleService

sys.excepthook = sys.__excepthook__

class Logger:

    def __init__(self):

        # program run id to match data from same run easily
        self.pid = str(globals.pid) + str(uuid.uuid4())[0:4]

        # Timer for how often internet is being checked
        self.ie_check_timer = datetime.now()

        self.ix_tempdata = []

        # Info on ongoing interaction with the tunnel
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_switch = None
        self.ix_content = None
        self.ix_recording = None
        self.ix_folder_today = {}

        self.gservice = GoogleService()


    def internet_connected(self):

        print('Checking internet connection')

        diff = int((datetime.now() - self.ie_check_timer).total_seconds())
        if (diff > (4*60)): # every four minutes max
            self.ie_check_timer = datetime.now()
            try:
                r = requests.get('https://google.fi',timeout=2)

            except Exception as e:
                raise e


    def test_ie_for_logging(self):
        try:
            self.internet_connected()
        except:
            printlog('Logger','ERROR: No internet – could not log to sheets.')
            raise


    def log_system_status(self, src, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = [timestamp, src, msg]
        try:
            self.test_ie_for_logging()
            self.gservice.log_to_drive([data], 'system')
        except Exception as e:
            printlog('Logger','System status update error:{}'.format(type(e).__name__, e))


    def log_program_run_info(self):

        # Logged only once in the start of monkeytunnel.py

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [
            self.pid,
            timestamp,
            globals.testMode,
            globals.usingVideo,
            globals.usingAudio,
            globals.recordingOn]

        # for gdrive.log_to_drive this needs to be in format
        # list(lists); [[row1],[row2],..]
        data = [data]

        try:
            self.test_ie_for_logging()
            printlog('Logger','Logging program run info to sheets.')
            dataLeft = self.gservice.log_to_drive(data, 'progrun')
            printlog('Logger','Finished logging.')

        except Exception as e:
            printlog('Logger','ERROR: Could not log program status: {}, {}'.format(type(e).__name__, e))
            filemanager.log_local(data, sheet=configs.local_program_log)


    def log_interaction_start(self, switch):

        self.ix_id = str(uuid.uuid4())[0:6]
        self.ix_date = date.isoformat(date.today())
        self.ix_start = datetime.now()
        self.ix_switch = switch
        self.ix_content = globals.mediaorder[switch]


    def log_interaction_end(self, endtime):

        pid = self.pid
        ID = self.ix_id
        date = self.ix_date
        startime = self.ix_start
        duration = round((endtime - self.ix_start).total_seconds(),2)

        stimulus = 'no-stimulus'
        if globals.testMode == 1:
            stimulus = 'auditory'
        elif globals.testMode == 2:
            stimulus = 'visual'

        switch = self.ix_switch
        content = self.ix_content
        video = self.ix_recording + '.h264'

        data = [self.pid, ID, date, stimulus, switch, content,
                startime.strftime("%Y-%m-%d %H:%M:%S"),
                endtime.strftime("%Y-%m-%d %H:%M:%S"), duration, video]

        self.ix_tempdata.append(data)

        # reset
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_switch = None
        self.ix_content = None


    def new_recording_name(self):

        self.ix_recording = (self.ix_start).strftime("%Y-%m-%d_%H-%M") + '_' + self.ix_id
        return self.ix_recording


    def upload_ix_logs(self):

        data = self.ix_tempdata
        if (len(data) > 0):
            try:
                self.test_ie_for_logging()
                printlog('Logger','Uploading interaction logs to sheets.')
                self.ix_tempdata = self.gservice.log_to_drive(data, 'ix')
                printlog('Logger','Finished logging.')

            except Exception as e:
                printlog('Logger','ERROR: Could not upload ix data: {}, {}'.format(type(e).__name__, e))
                filemanager.log_local(data, sheet=configs.local_ix_log)


    def get_folder_id_today(self):

        dateToday = date.isoformat(date.today())

        if dateToday in self.ix_folder_today:
            folderId = self.ix_folder_today[dateToday]
            return folderId

        _, folders = self.gservice.list_content()

        try:
            folderId = folders[dateToday]
        except:
            folderId = self.gservice.create_folder(
                        folderName=dateToday,
                        parentFolder=configs.GDRIVE_FOLDER_ID)

        self.ix_folder_today[dateToday] = folderId
        return folderId


    def upload_recordings(self, max_nof_uploads=0):

        nof_records = filemanager.nof_recordings()
        # if there are files in folder left from previous day in the local dir,
        # the date-folder will end up being wrong but this is not really
        # an issue since there wont be that many videos..

        if nof_records == 0:
            printlog('Logger','No recordings to upload.')
            return

        try:
            self.internet_connected()
        except:
            printlog('Logger','ERROR: No internet – could not upload files.')
            return

        folderId = self.get_folder_id_today()
        uploadedFiles = []
        # TODO: empty both locations if USB has not been accessed for some time?
        records, directory = filemanager.list_recordings()

        MAX = len(records)
        if max_nof_uploads > 0:
            MAX = max_nof_uploads

        startTime = datetime.now()

        # records, directory, self.ix_recording, folderId
        print('Trying to call the subprocess..')
        subprocess.Popen(args=["python uploader.py", records, directory, self.ix_recording, folderId], stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

        # filepath = "/home/pi/sakis-tunnel-2021/uploadlog.txt"
        # txt_file = open(filepath,'a+')
        # uploads = txt_file.readlines()
        #
        # i = 0
        # for filename in records:
        #     if i == MAX:
        #         break
        #     if filename != self.ix_recording or filename in uploads:
        #         # skip if currently being recorded!
        #         try:
        #             txt_file.write(filename)
        #             self.gservice.upload_recording(filename, folderId, directory)
        #             filemanager.delete_local_file(directory + filename)
        #             i += 1
        #
        #         except Exception as e:
        #             printlog('Logger','ERROR: Could not upload file: {}, {}'.format(
        #                         type(e).__name__, e))
        #             logger.log_system_status('Switches','Error when uploading recordings: {}'.format(type(e).__name__, e))
        #
        #             if type(e).__name__ == "TimeoutError":
        #                 break
        #
        # txt_file.close()
        duration = round((datetime.now() - startTime).total_seconds() / 60, 2)
        printlog('Logger','Uploaded {} recordings, duration {}'.format(
                    i, duration))


    def upload_logfiles(self):

        logfiles = [
                configs.local_ix_log,
                configs.local_program_log,
                configs.local_printlog,
                configs.local_output
                ]

        try:
            self.internet_connected()
        except:
            printlog('Logger','ERROR: No internet, could not upload logfiles.')
            return

        startTime = datetime.now()

        for file in logfiles:
            if os.path.exists(file):

                if file == configs.local_printlog:
                    printlog('Logger','Sleeping before uploading this file.')
                    # using this file constantly for logigng rows so sleep for
                    # a while to avoid collapse with trying to upload a file
                    # that has been just opened as well
                    sleep(0.5)

                try:
                    self.gservice.upload_logfile(fileName=file)
                    filemanager.delete_local_file(path=file)
                except Exception as e:
                    printlog('Logger','ERROR: Could not upload logfile {}: {}, {}'.format(
                                file, type(e).__name__, e))

        duration = round((datetime.now() - startTime).total_seconds() / 60, 2)
        printlog('Logger','Uploaded local files. Duration: {}'.format(duration))
