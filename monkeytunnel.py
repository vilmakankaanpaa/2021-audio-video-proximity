import os
import sys
from time import sleep
from datetime import datetime, date, time

# Local sources
from filemanager import check_disk_space, printlog, get_directory_for_recordings
from logger import Logger
from audioplayer import AudioPlayer
from videoplayer import VideoPlayer
from camera import Camera
import configs
import settings

sys.excepthook = sys.__excepthook__

def ensure_disk_space(logger, recDirectory):

    printlog('Main','Checking disk space.')

    if recDirectory == configs.RECORDINGS_PATH:
        # Path to the USB

        freeSpace = check_disk_space(configs.external_disk)
        printlog('Main','Directory {}, free: {}'.format(recDirectory, freeSpace))

        if freeSpace < 0.04: # this is ca. 1.1/28.0 GB of the USB stick left
            # if space is scarce, we need to upload some files ASAP
            printlog('Main','Disk space on USB getting small! Uploading files already.')
            # But let's not upload all in order not to disturb
            # the functioning of the tunnel for too long..
            logger.upload_recordings(max_nof_uploads=5)

    elif recDirectory == configs.RECORDINGS_PATH_2:
        # PATH to local directory

        printlog('Main','ERROR: Camera has been recording to Pi local folder!')
        freeSpace = check_disk_space(configs.root)
        if freeSpace < 0.02: # 2% of the 7.8 GB of the total free space on Pi, so less than 156MB
            printlog('Main','Disk space on Pi getting small! Uploading files already.')
            # Pi is so small that we just need them all out.
            logger.upload_recordings()
    else:
        pass


if __name__ == "__main__":

    print(datetime.isoformat(datetime.now()))
    global pid
    pid = os.getpid()

    print('pid:',pid)

    printlog('Main','Starting up monkeytunnel..')

    # Variables for keep track of the state of system
    playingAudio = False
    playingVideo = False
    cameraIsRecording = False
    camDirectory = None
    logfilesUploadedToday = False

    # sensornote: setted the threshold here

    # Timer for when files (recordings, logfiles) should be uploaded
    uploadFiles_timer = datetime.now()
    # Timer for when data should be uploaded (interactions & sensors readings)
    uploadData_timer = datetime.now()
    # Timer for when disk space should be checked
    checkSpace_timer = datetime.now()

    pingTimer = datetime.now()

    # Timer to avoid uploading data during and right after interactions
    ix_timer = datetime.now()

    if usingAudio:
        audioPlayer = AudioPlayer()

    elif usingVideo:
        # TODO how to initialize with many videos?
        videoPlayer = VideoPlayer(videoPath=configs.VIDEO_PATH,
                                useVideoAudio=configs.VIDEO_AUDIO_ON)
    if recordingOn:
        camera = Camera()

    logger = Logger(pid)
    logger.log_program_run_info()

    logger.ping()

    while True:

        if (datetime.now() - pingTimer).total_seconds() / 60 > 10:
            # ping every 10 minutes
            logger.ping()
            pingTimer = datetime.now()

        # Checking if should update the request quota for Google Sheets
        # It is 100 requests per 100 seconds (e.g. logging of 100 rows)
        logger.gsheets.check_quota_timer()

        # snesornote: reading sensors here
        # sensornote: handling the FALSe readings here
        # sensornote: determined if monkey was detected or not

        if recordingOn:
            cameraIsRecording = camera.is_recording()

        if usingAudio:
            playingAudio = audioPlayer.is_playing()
            if not playingAudio and audioPlayer.has_quit():
                # if quit, spawn new
                audioPlayer = AudioPlayer()

        if usingVideo:
            playingVideo = videoPlayer.is_playing()
            if not playingVideo and videoPlayer.has_quit():
                # if quit, spawn new
                videoPlayer = VideoPlayer(videoPath=configs.VIDEO_PATH,
                            useVideoAudio=configs.VIDEO_AUDIO_ON)



        timeSinceIx = (datetime.now() - ix_timer).total_seconds() / 60

        # Upload log data to Sheets every 6 minutes
        # Sometimes the Google Sheets kept logging in every time logging
        # was done and this slowed down the program a lot. So in case happening,
        # it will be done less often
        if (datetime.now() - uploadData_timer).total_seconds() / 60 > 6:
            if not logger.ix_id and timeSinceIx > 1:
                printlog('Main','Uploading data from logs..')
                logger.upload_ix_logs()
                logger.upload_sensor_logs()
                uploadData_timer = datetime.now()

        # Check disk space every 4 minutes
        if (datetime.now() - checkSpace_timer).total_seconds() / 60 > 4:
            ensure_disk_space(logger, camDirectory)
            checkSpace_timer = datetime.now()

        # Upload recordings and log files in the evening
        hourNow = datetime.now().hour
        if not logger.ix_id and timeSinceIx > 1:
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
