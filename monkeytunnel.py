# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import sys
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime, date, time
import random

# Local sources
from filemanager import check_disk_space, printlog, get_directory_for_recordings, log_local
from logger import Logger
from camera import Camera
from microphone import Microphone
from switches import Switches
import configs
import globals

sys.excepthook = sys.__excepthook__


def ensure_disk_space(logger):

    directory = get_directory_for_recordings()
    # TODO: don't depend on the given directory
    if directory == configs.RECORDINGS_PATH:
        # Path to the USB

        freeSpace = check_disk_space(configs.external_disk)
        logger.log_system_status('Main','Directory {}, free: {}'.format(directory, freeSpace))

        if freeSpace < 0.04: # this is ca. 1.1/28.0 GB of the USB stick left
            # if space is scarce, we need to upload some files ASAP
            logger.log_system_status('Main','Disk space on USB getting small! Uploading files already.')
            # But let's not upload all in order not to disturb
            # the functioning of the tunnel for too long..
            logger.upload_recordings(max_nof_uploads=5)

    elif directory == configs.RECORDINGS_PATH_2:
        # PATH to local directory

        logger.log_system_status('Main','Issue: Camera is recording local folder.')
        freeSpace = check_disk_space(configs.root)
        printlog('Main','Directory {}, free: {}'.format(directory, freeSpace))
        if freeSpace < 0.10: # 10% of the ca. 17 GB of free space on Pi
            logger.log_system_status('Main','Disk space on Pi getting small! Uploading files already.')
            # Pi is so small that we just need them all out.
            logger.upload_recordings()
    else:
        pass


def check_testMode():

    modeSet = globals.modeSince
    modeSince = datetime.now()-modeSet
    minutes = modeSince.total_seconds() / 60

    if globals.testMode == 0 or globals.testMode == 3:
        #if minutes > 10080:
        if minutes > 1:
            printlog('Main','Changing mode from no-stimulus to audio')
            logger.log_system_status('Main','Changing from no-stimulus to audio.')
            globals.testMode = 1
            globals.usingAudio = True
            globals.usingVideo = False
            globals.mediaorder = [configs.audio1,configs.audio2,configs.audio3,configs.audio4]
            random.shuffle(globals.mediaorder)
            globals.modeSince = datetime.now()
            printlog('Main','Mediaorder: {}.'.format(globals.mediaorder))
            return

    #if minutes >= 4320:
    if minutes > 2:
        if globals.testMode == 1:
            printlog('Main','Changing mode from audio to video')
            logger.log_system_status('Main','Changing from audio to video.')
            # Was audio, start video
            globals.testMode = 2
            globals.usingAudio = False
            globals.usingVideo = True
            globals.mediaorder = [configs.video1,configs.video2,configs.video3,configs.video4]

        elif globals.testMode == 2:
            printlog('Main','Changing mode from video to audio')
            logger.log_system_status('Main','Changing from video to audio.')
            # Was video, start audio
            globals.testMode = 1
            globals.usingAudio = True
            globals.usingVideo = False
            globals.mediaorder = [configs.audio1,configs.audio2,configs.audio3,configs.audio4]

        random.shuffle(globals.mediaorder)
        globals.modeSince = datetime.now()
        printlog('Main','Mediaorder: {}.'.format(globals.mediaorder))
        logger.log_system_status('Main','Mediaorder: {}.'.format(globals.mediaorder))


if __name__ == "__main__":

    globals.init()

    printlog('Main',datetime.isoformat(datetime.now()))
    globals.modeSince = datetime.now()
    globals.pid = os.getpid()

    printlog('Main','Starting up monkeytunnel..')


    if globals.testMode == 1:
        globals.mediaorder = [configs.audio1,configs.audio2,configs.audio3,configs.audio4]
    elif globals.testMode == 2:
        globals.mediaorder = [configs.video1,configs.video2,configs.video3,configs.video4]
    elif globals.testMode == 3:
        globals.mediaorder = [configs.video5,configs.video5,configs.video5,configs.video5]
    else:
        globals.mediaorder = [None, None, None, None]

    # TODO: don't use shuffling unless doing changing stimulus automatically during system run and this works well
    random.shuffle(globals.mediaorder)

    printlog('Main','Mediaorder: {}.'.format(globals.mediaorder))

    logger = Logger()
    camera = Camera()
    mic = Microphone()

    # Timer for when files (recordings, logfiles) should be uploaded
    uploadFiles_timer = datetime.now()
    # Timer for when data should be uploaded (interactions & sensors readings)
    uploadData_timer = datetime.now()
    # Timer for when disk space should be checked
    checkSpace_timer = datetime.now()
    pingTimer = datetime.now()
    # Timer to avoid uploading data during and right after interactions
    ix_timer = datetime.now()

    cameraDelay = 10 # seconds
    lastActivity = datetime.now()
    activated = False

    logfilesUploadedToday = False

    try:
        switches = Switches(logger, camera, mic)

        logger.log_program_run_info()
        logger.log_system_status('Main','Tunnel started.')

        printlog('Main','Ready for use!')

        while True:

            check_testMode()

            if (datetime.now() - pingTimer).total_seconds() / 60 > 10:
                #ping every 10 minutes
                readings = switches.get_readings()
                logger.log_system_status('Main','Switch readings: {}'.format(readings))
                pingTimer = datetime.now()

            # Checking if should update the request quota for Google Sheets
            # It is 100 requests per 100 seconds (e.g. logging of 100 rows)
            logger.gservice.check_quota_timer()

            # Checks the state of switches and handles what to do with media: should it start or stop or content switched.
            # Also logs when interaction starts and ends.
            switches.updateSwitches()

            if logger.ix_id == None:
                activated = False
            else:
                activated = True

            if switches.endtime != None:
                lastActivity = switches.endtime

            if globals.recordingOn:
                if not activated and camera.is_recording:
                    # Stop recording after certain time since interaction ended
                    timeSinceActivity = round((datetime.now() - lastActivity).total_seconds(),2)

                    if timeSinceActivity > camera.delay:
                        try:
                            camera.stop_recording()
                            mic.stop()
                            printlog('Main','Stopping to record, time since: {}.'.format(timeSinceActivity))
                        except Exception as e:
                            logger.log_system_status('Main','Error when trying to stop camera or mic from recording: {}'.format(type(e).__name__, e))



            timeSinceIx = (datetime.now() - lastActivity).total_seconds() / 60
            # Upload log data to Sheets every 6 minutes
            # Sometimes the Google Sheets kept logging in every time logging
            # was done and this slowed down the program a lot. So in case happening,
            # it will be done less often
            if (datetime.now() - uploadData_timer).total_seconds() / 60 > 6:
                if not activated and timeSinceIx > 1:
                    # Upload data logs after some time passed since activity
                    printlog('Main','Uploading data from ix logs..')
                    logger.upload_ix_logs()
                    uploadData_timer = datetime.now()

            # Check disk space every 4 minutes
            if (datetime.now() - checkSpace_timer).total_seconds() / 60 > 4:
                try:
                    ensure_disk_space(logger)
                    checkSpace_timer = datetime.now()
                except Exception as e:
                    printlog('Main','Error in reading / logging disk space: {}'.format(type(e).__name__, e))


            # Upload recordings and log files in the evening
            hourNow = datetime.now().hour
            if not activated and timeSinceIx > 1:
                if (hourNow == 22 or hourNow == 23):
                    if (datetime.now()-uploadFiles_timer).total_seconds() / 60 > 25:
                        # During these hours, only check about 4 times if there are any
                        # videos / logfiles to upload
                        printlog('Main','Starting to upload files from today.')
                        logger.upload_recordings(50)

                        if not logfilesUploadedToday:
                            # do this only once a day
                            logger.upload_logfiles()
                            logfilesUploadedToday = True

                        uploadFiles_timer = datetime.now()

                elif hourNow == 0:
                    logfilesUploadedToday = False

            sleep(0.4)


    except KeyboardInterrupt:
        printlog('Main','Exiting, KeyboardInterrupt')

    finally:
        # Remove the channel setup always
        GPIO.cleanup()
        if camera.is_recording:
            printlog('Exit','Stopping camera recording.')
            camera.stop_recording()
        if mic.is_recording:
            printlog('Exit','Stopping mic recording.')
            mic.stop()

        if globals.videoPlayer != None:
            printlog('Exit','Stopping video.')
            globals.videoPlayer.stop_video()

        if globals.audioPlayer.is_playing():
            printlog('Exit','Stopping audio.')
            globals.audioPlayer.stop()

        ix_data = logger.ix_tempdata
        if len(ix_data) != 0:
            printlog('Exit','Logging ix data to csv.')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file = timestamp + '_ix_backup.csv'
            log_local(ix_data, sheet=file)
