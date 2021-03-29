# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import sys
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime, date, time
import random

# Local sources
from filemanager import check_disk_space, printlog, get_directory_for_recordings
from logger import Logger
from camera import Camera
from switches import Switches
import configs
import globals

sys.excepthook = sys.__excepthook__

def ensure_disk_space(logger):

    printlog('Main','Checking disk space.')

    directory = get_directory_for_recordings()
    # TODO: don't depend on the given directory
    if directory == configs.RECORDINGS_PATH:
        # Path to the USB

        freeSpace = check_disk_space(configs.external_disk)
        printlog('Main','Directory {}, free: {}'.format(directory, freeSpace))

        if freeSpace < 0.04: # this is ca. 1.1/28.0 GB of the USB stick left
            # if space is scarce, we need to upload some files ASAP
            printlog('Main','Disk space on USB getting small! Uploading files already.')
            # But let's not upload all in order not to disturb
            # the functioning of the tunnel for too long..
            logger.upload_recordings(max_nof_uploads=5)

    elif directory == configs.RECORDINGS_PATH_2:
        # PATH to local directory

        printlog('Main','ERROR: Camera has been recording to Pi local folder!')
        freeSpace = check_disk_space(configs.root)
        printlog('Main','Directory {}, free: {}'.format(directory, freeSpace))
        if freeSpace < 0.10: # 10% of the ca. 17 GB of free space on Pi
            printlog('Main','Disk space on Pi getting small! Uploading files already.')
            # Pi is so small that we just need them all out.
            logger.upload_recordings()
    else:
        pass

def check_testMode():

    modeSet = globals.modeSince
    modeSince = datetime.now()-modeSet
    minutes = modeSince.total_seconds() / 60
    
    if globals.testMode == 0:
        printlog('Main','Changing mode from no-stimulus to audio') 
        if minutes > 10080:
            globals.testMode = 1
            globals.usingAudio = True
            globals.usingVideo = False
            globals.mediaorder = [configs.audio1,configs.audio2,configs.audio3,configs.audio4]
            random.shuffle(globals.mediaorder)
            globals.modeSince = datetime.now()
            return
            
    #TODO:if minutes >= 4320:
    if minutes >= 2:
        if globals.testMode == 1:
            printlog('Main','Changing mode from audio to video')
            # Was audio, start video
            globals.testMode = 2
            globals.usingAudio = False
            globals.usingVideo = True
            globals.mediaorder = [configs.video1,configs.video2,configs.video3,configs.video4]

        elif globals.testMode == 2:
            printlog('Main','Changing mode from video to audio')
            # Was video, start audio
            globals.testMode = 1
            globals.usingAudio = True
            globals.usingVideo = False
            globals.mediaorder = [configs.audio1,configs.audio2,configs.audio3,configs.audio4]

        random.shuffle(globals.mediaorder)
        globals.modeSince = datetime.now()

if __name__ == "__main__":

    globals.init()

    printlog('Main',datetime.isoformat(datetime.now()))
    globals.modeSince = datetime.now()
    globals.pid = os.getpid()

    printlog('Main','Starting up monkeytunnel..')

    if globals.usingAudio:
        globals.mediaorder = [configs.audio1,configs.audio2,configs.audio3,configs.audio4]
    elif globals.usingVideo:
        globals.mediaorder = [configs.video1,configs.video2,configs.video3,configs.video4]

    # TODO: don't use shuffling unless doing changing stimulus automatically during system run and this works well
    #random.shuffle(globals.mediaorder)

    logger = Logger()
    camera = Camera()

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

    logfilesUploadedToday = False

    try:
        switches = Switches(logger, camera)

        logger.log_program_run_info()
        logger.ping()
        
        printlog('Main','Ready for use!')

        while True:

            check_testMode()

            if (datetime.now() - pingTimer).total_seconds() / 60 > 10:
                #ping every 10 minutes
                logger.ping()
                pingTimer = datetime.now()

            # Checking if should update the request quota for Google Sheets
            # It is 100 requests per 100 seconds (e.g. logging of 100 rows)
            logger.gservice.check_quota_timer()

            # Checks the state of switches and handles what to do with media: should it start or stop or content switched.
            # Also logs when interaction starts and ends.
            switches.updateSwitches()

            if switches.endtime != None:
                lastActivity = switches.endtime

            if globals.recordingOn:
                if not switches.switchPlaying and camera.is_recording:
                    # Stop recording after certain time since interaction ended
                    timeSinceActivity = round((datetime.now() - lastActivity).total_seconds(),2)

                    if timeSinceActivity > camera.delay:
                        camera.stop_recording()
                        printlog('Main','Stopping to record.')


            timeSinceIx = (datetime.now() - lastActivity).total_seconds() / 60
            # Upload log data to Sheets every 6 minutes
            # Sometimes the Google Sheets kept logging in every time logging
            # was done and this slowed down the program a lot. So in case happening,
            # it will be done less often
            # TODO: change timer threshold back
            if (datetime.now() - uploadData_timer).total_seconds() / 60 > 1:
                if not switches.switchPlaying and timeSinceIx > 1:
                    # Upload data logs after some time passed since activity
                    printlog('Main','Uploading data from ix logs..')
                    logger.upload_ix_logs()
                    #logger.upload_sensor_logs()
                    uploadData_timer = datetime.now()
                    printlog('Main','Try upload recordings..')
                    logger.upload_recordings(50)

            # Check disk space every 4 minutes
            if (datetime.now() - checkSpace_timer).total_seconds() / 60 > 4:
                ensure_disk_space(logger)
                checkSpace_timer = datetime.now()

            sleep(0.2)


            # Upload recordings and log files in the evening
            hourNow = datetime.now().hour
            if not switches.switchPlaying and timeSinceIx > 1:
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


    except KeyboardInterrupt:
        printlog('Main','Exiting, KeyboardInterrupt')

    finally:
        # Remove the channel setup always
        GPIO.cleanup()
        if camera.is_recording:
            camera.stop_recording()
        # TOOD use globals audioplayer etc to be able to stop them here?
        # or just do killall omxplayer.bin ?
