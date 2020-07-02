import sys
import os
import csv
from datetime import datetime, timedelta, date
import http.client as httplib
import uuid

import configs
from gdriveapi import DriveService

sys.excepthook = sys.__excepthook__

class Logger:

    def __init__(self, pid):

        # program run id to match data from same run easily
        self.pid = str(pid) + str(uuid.uuid4())[0:4]

        self.sensorlog_timer = datetime.now()
        self.quota_timer = datetime.now()
        self.alivelog_timer = datetime.now()
        self.ie_check_timer = datetime.now()

        self.max_nof_rows = 100
        self.tempdata = []
        self.sensors_temp = []
        self.recordings_temp = []

        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None
        self.ix_folder_date = None
        self.ix_folder_id = None

        self.gdrive = DriveService()


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
                raise e


    def log_local(self, data, sheet):
        print('Logging to local file:',sheet)
        with open(sheet, 'a', newline='') as logfile:
            logwriter = csv.writer(logfile, delimiter=',')
            for row in data:
                logwriter.writerow(row)


    def log_g_fail(self, reason):
        print('Logging to GDrive failed:', reason)
        self.log_local(
            [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Logging to Google Drive failed.',
            reason], sheet='logfail.csv')


    def deleteLocalVideo(self, fileName):
        path = configs.RECORDINGS_PATH + fileName
        os.remove(path)
        print('Removed file at', path)


    def uploadRecordings(self):

        if len(self.recordings_temp) == 0:
            print('No recordings to upload.')
            return

        try:
            self.internet_connected()
        except:
            print('Not connected to internet, could not upload files.')
            raise


        today = date.isoformat(date.today())
        if self.ix_folder_date != today:
            # create new, get id
            self.ix_folder_id = self.gdrive.createNewFolder(folderName=today)
            self.ix_folder_date = today

        folderId = self.ix_folder_id

        uploadedFiles = []
        for video in self.recordings_temp:

            try:
                print('Uploading file {}'.format(video))
                self.gdrive.uploadFile(video, folderId)
                uploadedFiles.append(video)
                self.deleteLocalVideo(video)

            except Exception as e:
                print('Could not upload file: {}'.format(e))
                # TODO log
                raise

        for video in uploadedFiles:
            self.recordings_temp.remove(video)


    def new_recording_name(self):
        self.ix_recording = self.ix_id + '_' + (self.ix_start).strftime("%Y-%m-%d_%H:%M:%S")
        return self.ix_recording

    def handle_recording(self):
        name = self.ix_recording + '.h264'
        self.recordings_temp.append(name)


    def test_ie_for_logging(self):
        try:
            self.internet_connected()
        except:
            reason = "No internet."
            self.log_g_fail(reason)
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
        video = self.ix_recording + '.h264'
        # id, starttime, endtime, duration
        data = [self.pid, ID, date, startime.strftime("%Y-%m-%d %H:%M:%S"),
            endtime.strftime("%Y-%m-%d %H:%M:%S"), duration, phase, video]

        self.tempdata.append(data)

        # reset
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None


    def update_ix_logs(self):

        data = self.tempdata
        if (len(data) > 0):
            try:
                self.test_ie_for_logging()
                print('Logging interaction to drive.')
                self.tempdata = self.gdrive.logToDrive(data, 'ix')

            except Exception as e:
                self.log_g_fail('{}'.format(type(e).__name__))
                self.log_local(data, sheet='local_ix_log.csv')


    def log_alive(self, start=False):

        timeDiff = (datetime.now() - self.alivelog_timer).total_seconds() / 60
        if timeDiff < 5 and not start: # log every 5 minutes
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [self.pid, timestamp]
        data = [data] # for gdrive.logToDrive this needs to be in [[row1],[row2],..] format

        try:
            self.test_ie_for_logging()
            print('Logging alive to drive.')
            data = self.gdrive.logToDrive(data, 'alive')

            if len(data) > 0:
                print('Could not upload program data due to too small quota.')
            else:
                self.alivelog_timer = datetime.now()

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))


    def log_sensor_status(self, sensorsInRange, sensorVolts, playingAudio,
                          playingVideo, cameraIsRecording, ixID=None):

        if (datetime.now() - self.sensorlog_timer).total_seconds() < 2:
            return

        # TODO: use also temp log for these and upload
        # less often? Move the timer there?

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

        self.update_sensor_logs()


    def update_sensor_logs(self):

        data = self.sensors_temp
        if len(data) > 0:
            try:
                self.test_ie_for_logging()
                #print('Logging sensor data to drive.')
                self.sensors_temp = self.gdrive.logToDrive(data, 'sensors')
                self.sensorlog_timer = datetime.now()

            except Exception as e:
                self.log_g_fail('{}'.format(type(e).__name__))
                self.log_local(data, sheet='sensor_log.csv')


    def log_program_run_info(self):

        # not testing for log interval because only done in beginning of
        # program run - these details wond change

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

        data = [data] # for gdrive.logToDrive this needs to be in [[row1],[row2],..] format

        try:
            self.test_ie_for_logging()
            #print('Logging progrum run info to drive.')
            dataLeft = self.gdrive.logToDrive(data, 'progrun')

            if len(dataLeft) > 0:
                print('Could not upload program data due to too small quota.')

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))
            self.log_local(data, sheet='progrun_log.csv')
