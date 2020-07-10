import os
import sys
from time import sleep
from datetime import datetime, date, time

# Local sources
from sensors import check_sensors
from filemanager import check_disk_space, printlog
from logger import Logger
from audioplayer import AudioPlayer
from videoplayer import VideoPlayer
from camera import Camera
import configs

sys.excepthook = sys.__excepthook__


def print_configurations():

    print('Audio on:', configs.USE_AUDIO)
    print('Video on:', configs.USE_VIDEO)
    print('Using video audio:', configs.VIDEO_AUDIO_ON)
    print('Recording on:', configs.RECORDING_ON)

    if configs.USE_AUDIO: print('Audio file in use:', configs.AUDIO_PATH)
    if configs.USE_VIDEO: print('Video file in use:', configs.VIDEO_PATH)
    if configs.RECORDING_ON: print('Recording to folder:', configs.RECORDINGS_PATH)


def update_sensor_reading(monkeyDetected, thresholdReading, anyInRange, threshold):

    # When enough no. of consecutive checks are same, set new value
    # thresholdReading will vary between 0–threshold and the middle point
    # will determine if false or true (monkey in)

    if anyInRange:
        if thresholdReading < (threshold*2):
            ++thresholdReading
    else:
        if thresholdReading > 0:
            --thresholdReading

    if thresholdReading > threshold and not monkeyDetected:
        printlog('Main','Monkey came in!')
        monkeyDetected = True
    elif thresholdReading < threshold and monkeyDetected:
        printlog('Main','All monkeys left. :(')
        monkeyDetected = False
    else:
        # don't do anything yet, keep values same
        # value is now same as threshold
        pass

    return monkeyDetected, thresholdReading

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
        if freeSpace < 0.15: # 1.17/7.8 GB of the total free space on Pi
            printlog('Main','Disk space on Pi getting small! Uploading files already.')
            # Pi is so small that we just need them all out.
            logger.upload_recordings()
    else:
        pass


if __name__ == "__main__":

    print(datetime.isoformat(datetime.now()))
    pid = os.getpid()
    print('pid:',pid)

    printlog('Main','Starting up monkeytunnel..')

    # Configurations for this run of the program
    usingAudio = configs.USE_AUDIO
    usingVideo = configs.USE_VIDEO
    recordingOn = configs.RECORDING_ON

    playingAudio = False
    playingVideo = False
    cameraIsRecording = False
    camDirectory = None

    # Sensorthreshold:
    # This number + 1 of consecutive readings determines
    # if the value of monkeyDetected changes
    sensorThreshold = 2
    # threshold is "middle ground", it won't determine any change yet
    thresholdReading = sensorThreshold
    monkeyDetected = False

    # Timer for when files (recordings, logfiles) should be uploaded
    uploadFiles_timer = datetime.now()
    # Timer for when data should be uploaded (interactions & sensors readings)
    uploadData_timer = datetime.now()
    # Timer for when disk space should be checked
    checkSpace_timer = datetime.now()

    # Timer to avoid uploading data during and right after interactions
    ix_timer = datetime.now()

    if usingVideo:
        videoPlayer = VideoPlayer(videoPath=configs.VIDEO_PATH,
                                useVideoAudio=configs.VIDEO_AUDIO_ON)
    if usingAudio:
        audioPlayer = AudioPlayer()

    if recordingOn:
        camera = Camera()

    logger = Logger(pid)
    logger.log_program_run_info()

    while True:

        # Checking if should update the request quota for Google Sheets
        # It is 100 requests per 100 seconds (e.g. logging of 100 rows)
        logger.gsheets.check_quota_timer()

        sensorVolts, sensorsInRange = check_sensors()

        monkeyDetected, thresholdReading = update_sensor_reading(
            monkeyDetected, thresholdReading,
            any(sensorsInRange), sensorThreshold)

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

        if monkeyDetected:

            ixID = logger.ix_id
            if not ixID:
                ixID = logger.log_interaction_start()
                printlog('Main','Interaction started.')

            if recordingOn and not cameraIsRecording:
                fileName = logger.new_recording_name()
                camDirectory = filemanager.get_directory_for_recordings()
                camera.start_recording(fileName, camDirectory)
                printlog('Main','Camera started recording.')

            if usingAudio and not playingAudio:
                audioPlayer.play_audio()
                printlog('Main','Audio started playing.')

            if usingVideo and not playingVideo:
                videoPlayer.play_video()
                printlog('Main','Video started playing.')

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio,
                                        playingVideo, cameraIsRecording, ixID)

        else:

            if recordingOn and cameraIsRecording:
                camera.stop_recording()
                printlog('Main','Camera stopped recording.')

            if usingAudio and playingAudio:
                audioPlayer.pause_audio()
                printlog('Main','Audio stopped playing.')

            if usingVideo and playingVideo:
                videoPlayer.pause_video()
                printlog('Main','Video stopped playing.')

            if logger.ix_id:
                logger.log_interaction_end()
                ix_timer = datetime.now()
                printlog('Main','Interaction ended.')

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio,
                                        playingVideo, cameraIsRecording)



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
                    logger.upload_recordings()
                    logger.upload_logfiles()
                    uploadFiles_timer = datetime.now()

        sleep(0.4)
