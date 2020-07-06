import sys
import os
import uuid
import http.client as httplib
from datetime import datetime, timedelta, date

import configs
from gdriveapi import DriveService
import filemanager

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

        self.ix_id = None
        self.ix_date = None
        self.ix_start = None
        self.ix_recording = None
        self.ix_folder_today = None

        self.gdrive = DriveService()


    def internet_connected(self):

        diff = int((datetime.now() - self.ie_check_timer).total_seconds())
        if (diff > (4*60)): # every four minutes max
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Checking internet.')
            self.ie_check_timer = datetime.now()
            conn = httplib.HTTPConnection("www.google.fi", timeout=2)
            try:
                conn.request("HEAD", "/")
                conn.close()

            except Exception as e:
                conn.close()
                raise e


    def log_g_fail(self, reason):
        print(datetime.now(), 'Logging to GDrive failed:', reason)
        filemanager.log_local(
            [[datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Logging to Google Drive failed.',
            reason]], sheet=configs.local_fail_log)


    def upload_logfiles(self):

        logfiles = [configs.local_fail_log, configs.local_ix_log,
                configs.local_sensor_log, configs.local_program_log,
                configs.local_status_log]

        uploadStartTime = datetime.now()

        for file in logfiles:
            if os.path.exists(file):
                self.gdrive.upload_general_file(file)
                filemanager.delete_local_file(file)

        duration = round((datetime.now() - uploadStartTime).total_seconds() / 60, 2)
        print('Uploading logfiles duration {}'.format(duration))
        self.log_status_info('Uploading logfiles duration {}'.format(duration))


    def get_folder_id_today(self):

        if self.ix_folder_today:
            return self.ix_folder_today

        dateToday = date.isoformat(date.today())

        contents = self.gdrive.list_drive_contents()

        try:
            folderId = contents[dateToday]
        except:
            folderId = self.gdrive.create_new_folder(folderName=dateToday)

        self.ix_folder_today = folderId
        return folderId


    def upload_recordings(self, max_nof_uploads=0):

        nof_records = filemanager.nof_recordings()
        # if there are files in folder left from previous day in the local dir,
        # the date-folder will end up being wrong but this is not really
        # an issue since there wont be that many videos..

        if nof_records == 0:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'No recordings to upload.')
            return

        try:
            self.internet_connected()
        except:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 'Not connected to internet, could not upload files.')
            reason = "Could not upload files, no internet."
            self.log_g_fail(reason)
            return

        folderId = self.get_folder_id_today()
        uploadedFiles = []
        records, directory = filemanager.list_recordings()

        until = len(records)
        if max_nof_uploads > 0:
            until = max_nof_uploads

        uploadStartTime = datetime.now()

        for i in range(until):
            filename = records[i]
            try:
                print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Uploading file {}'.format(filename))
                self.gdrive.upload_video_file(filename, folderId)
                filemanager.delete_local_file(directory + filename)

            except Exception as e:
                print('Could not upload file: {}'.format(e))
                self.log_g_fail('{}'.format(type(e).__name__))

        duration = round((datetime.now() - uploadStartTime).total_seconds() / 60, 2)
        print('Uploading {} recordings duration {}'.format(until, duration))
        self.log_status_info('Uploading {} recordings duration {}'.format(until, duration))


    def new_recording_name(self):
        self.ix_recording = self.ix_id + '_' + (self.ix_start).strftime("%Y-%m-%d_%H-%M")
        return self.ix_recording


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
                print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Logging interaction to drive.')
                self.tempdata = self.gdrive.log_to_drive(data, 'ix')

            except Exception as e:
                self.log_g_fail('{}'.format(type(e).__name__))
                filemanager.log_local(data, sheet=configs.local_ix_log)


    def log_alive(self, start=False):

        timeDiff = (datetime.now() - self.alivelog_timer).total_seconds() / 60
        if timeDiff < 5 and not start: # log every 5 minutes
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [self.pid, timestamp]
        data = [data] # for gdrive.logToDrive this needs to be in [[row1],[row2],..] format

        print(timestamp,'Pinging alive.')

        try:
            self.test_ie_for_logging()
            #print('Logging alive to drive.')
            data = self.gdrive.log_to_drive(data, 'alive')

            if len(data) > 0:
                print('Could not upload program data due to too small quota.')
            else:
                self.alivelog_timer = datetime.now()

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))


    def log_status_info(self, msg):

        print(msg)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [[self.pid, timestamp, msg]]

        try:
            self.test_ie_for_logging()
            data = self.gdrive.log_to_drive(data, 'status')

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))
            filemanager.log_local(data, sheet=configs.local_status_log)


    def log_sensor_status(self, sensorsInRange, sensorVolts, playingAudio,
                          playingVideo, cameraIsRecording, ixID=None):

        ixOngoing = False
        if ixID:
            ixOngoing = True

        passedTime = (datetime.now() - self.sensorlog_timer).total_seconds()

        # log only at these intervals
        if not ixOngoing and (passedTime / 60 < 5) :
            return
        elif ixOngoing and passedTime < 1:
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

        self.sensors_temp.append(
            [self.pid, ixID, timestamp, sensor1_r, sensor1_v, sensor2_r, sensor2_v,
             sensor3_r, sensor3_v, playingAudio, playingVideo, cameraIsRecording])

        self.update_sensor_logs()


    def update_sensor_logs(self):

        data = self.sensors_temp
        if len(data) > 0:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Updating sensor logs')
            try:
                self.test_ie_for_logging()
                #print('Logging sensor data to drive.')
                self.sensors_temp = self.gdrive.log_to_drive(data, 'sensors')
                self.sensorlog_timer = datetime.now()

            except Exception as e:
                self.log_g_fail('{}'.format(type(e).__name__))
                filemanager.log_local(data, sheet=configs.local_sensor_log)


    def log_program_run_info(self):

        # not testing for log interval because only done in beginning of
        # program run - these details wond change

        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Logging program run info.')

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

        data = [data] # for gdrive.logToDrive this needs to be in [[row1],[row2],..] format

        try:
            self.test_ie_for_logging()
            #print('Logging progrum run info to drive.')
            dataLeft = self.gdrive.log_to_drive(data, 'progrun')

            if len(dataLeft) > 0:
                print('Could not upload program data due to too small quota.')

        except Exception as e:
            self.log_g_fail('{}'.format(type(e).__name__))
            filemanager.log_local(data, sheet=configs.local_program_log)
