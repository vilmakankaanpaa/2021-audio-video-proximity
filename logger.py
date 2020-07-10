import sys
import os
import uuid
import http.client as httplib
from datetime import datetime, date

import configs
import filemanager
from filemanager import printlog
from gsheetsservice import SheetsService
from gdriveservice import DriveService

sys.excepthook = sys.__excepthook__

class Logger:

    def __init__(self, pid):

        # program run id to match data from same run easily
        self.pid = str(pid) + str(uuid.uuid4())[0:4]

        # Timer for counting how often data from sensors is logged
        self.sensorlog_timer = datetime.now()
        # Timer for how often internet is being checked
        self.ie_check_timer = datetime.now()

        self.ix_tempdata = []
        self.sensors_tempdata = []

        # Info on ongoing interaction with the tunnel
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None
        self.ix_folder_today = {}

        self.gdrive = DriveService()
        self.gsheets = SheetsService()

    def internet_connected(self):

        diff = int((datetime.now() - self.ie_check_timer).total_seconds())
        if (diff > (4*60)): # every four minutes max
            self.ie_check_timer = datetime.now()
            conn = httplib.HTTPConnection("www.google.fi", timeout=2)
            try:
                conn.request("HEAD", "/")
                conn.close()

            except Exception as e:
                conn.close()
                raise e

    def upload_logfiles(self):

        logfiles = [
                configs.local_ix_log,
                configs.local_sensor_log,
                configs.local_program_log,
                configs.local_printlog
                ]

        try:
            self.internet_connected()
        except:
            printlog('Logger','ERROR: No internet, could not upload logfiles.')
            return

        startTime = datetime.now()

        for file in logfiles:
            if os.path.exists(file):
                try:
                    self.gdrive.upload_logfile(fileName=file)
                    filemanager.delete_local_file(path=file)
                except Exception as e:
                    printlog('Logger','ERROR: Could not upload logfile {}: {}'.format(
                                file, type(e).__name__))

        duration = round((datetime.now() - startTime).total_seconds() / 60, 2)
        printlog('Logger','Uploaded local files. Duration: {}'.format(duration))

    def get_folder_id_today(self):

        dateToday = date.isoformat(date.today())

        if dateToday in self.ix_folder_today:
            folderId = self.ix_folder_today[dateToday]
            return folderId

        _, folders = self.gdrive.list_content()

        try:
            folderId = folders[dateToday]
        except:
            folderId = self.gdrive.create_folder(
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
        records, directory = filemanager.list_recordings()

        MAX = len(records)
        if max_nof_uploads > 0:
            MAX = max_nof_uploads

        startTime = datetime.now()

        i = 0
        for filename in records:
            if i == MAX:
                break
            if filename != self.ix_recording:
                # skip if currently being recorded!
                try:
                    self.gdrive.upload_recording(filename, folderId)
                    filemanager.delete_local_file(directory + filename)
                    ++i
                except Exception as e:
                    printlog('Logger','ERROR: Could not upload file: {}'.format(
                                type(e).__name__))

        duration = round((datetime.now() - startTime).total_seconds() / 60, 2)
        printlog('Logger','Uploaded {} recordings, duration {}'.format(
                    MAX, duration))

    def new_recording_name(self):

        self.ix_recording = (self.ix_start).strftime(
                                "%Y-%m-%d_%H-%M") + '_' + self.ix_id
        return self.ix_recording

    def test_ie_for_logging(self):
        try:
            self.internet_connected()
        except:
            printlog('Logger','ERROR: No internet – could not log to sheets.')
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

        self.ix_tempdata.append(data)

        # reset
        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None

    def upload_ix_logs(self):

        data = self.ix_tempdata
        if (len(data) > 0):
            try:
                self.test_ie_for_logging()
                printlog('Logger','Uploading interaction logs to sheets.')
                self.ix_tempdata = self.gsheets.log_to_drive(data, 'ix')
            except Exception as e:
                printlog('Logger','ERROR: Could not upload ix data: {}'.format(
                            type(e).__name__))
                filemanager.log_local(data, sheet=configs.local_ix_log)

    def log_sensor_status(self, sensorsInRange, sensorVolts, playingAudio, playingVideo, cameraIsRecording, ixID=None):

        ixOngoing = False
        if ixID:
            ixOngoing = True

        passedTime = (datetime.now() - self.sensorlog_timer).total_seconds()

        # log only at these intervals
        if not ixOngoing and (passedTime / 60 < 5) :
            # Every 5 minutes when not active
            return
        elif ixOngoing and passedTime < 1:
            # Every second when active
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor1_r = sensorsInRange[0]
        sensor2_r = sensorsInRange[1]
        sensor3_r = sensorsInRange[2]

        sensor1_v = ('%.2f' % sensorVolts[0])
        sensor2_v = ('%.2f' % sensorVolts[1])
        sensor3_v = ('%.2f' % sensorVolts[2])

        #print('IxID:', ixID)
        #for i in range(3):
        #    print(sensorsInRange[i], sensorVolts[i])

        self.sensors_tempdata.append(
            [self.pid, ixID, timestamp, sensor1_r, sensor1_v, sensor2_r, sensor2_v,
             sensor3_r, sensor3_v, playingAudio, playingVideo, cameraIsRecording])
        self.sensorlog_timer = datetime.now()

    def upload_sensor_logs(self):

        data = self.sensors_tempdata
        if len(data) > 0:
            try:
                self.test_ie_for_logging()
                printlog('Logger','Uploading sensor logs to sheets.')
                self.sensors_tempdata = self.gsheets.log_to_drive(data, 'sensors')

            except Exception as e:
                printlog('Logger','ERROR: Could not upload sensor data: {}'.format(
                            type(e).__name__))
                filemanager.log_local(data, sheet=configs.local_sensor_log)

    def log_program_run_info(self):

        # Logged only once in the start of monkeytunnel.py
        printlog('Logger','Logging program run info.')

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
            configs.RECORDING_ON]

        # for gdrive.log_to_drive this needs to be in format
        # list(lists); [[row1],[row2],..]
        data = [data]

        try:
            self.test_ie_for_logging()
            printlog('Logger','Logging program run info to sheets.')
            dataLeft = self.gsheets.log_to_drive(data, 'progrun')

        except Exception as e:
            printlog('Logger','ERROR: Could not log program status: {}'.format(
                            type(e).__name__))
            filemanager.log_local(data, sheet=configs.local_program_log)
