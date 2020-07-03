import os
import sys
from time import sleep
from datetime import datetime, date, time

from sensors import check_sensors
from audioplayer import AudioPlayer
from videoplayer import VideoPlayer
from logger import Logger
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


def update_sensor_reading(userDetected, sensorReading, anyInRange, sensorThreshold):

    # When enough no of consecutive checks are same, set new value
    # sensorReading will vary between 0–threshold and the middle point will divide if false or true

    if anyInRange:
        if sensorReading < (sensorThreshold*2): # max
            sensorReading = sensorReading + 1
    else:
        if sensorReading > 0: # 0 is min
            sensorReading = sensorReading - 1

    if sensorReading > sensorThreshold and not userDetected:
        print("Monkey came in")
        userDetected = True
    elif sensorReading < sensorThreshold and userDetected:
        print("All monkeys left")
        userDetected = False
    else:
        # don't do anything yet, keep values same
        pass

    return userDetected, sensorReading


if __name__ == "__main__":

    print(datetime.isoformat(datetime.now()))
    print('Starting up monkeytunnel..')
    pid = os.getpid()
    print('pid:',pid)
    # TODO: save the pid to temp file

    # configurations for this run of the program
    usingAudio = configs.USE_AUDIO
    usingVideo = configs.USE_VIDEO
    recordingOn = configs.RECORDING_ON

    sensorThreshold = 2 # after this number of consecutive readings, change value of userDetected
    sensorReading = sensorThreshold # this is the middle grounf between True and False
    userDetected = False

    playingAudio = False
    playingVideo = False
    cameraIsRecording = False

    uploadTimer = datetime.now()

    # Put screensaver on regardless if using video
    videoPlayer = VideoPlayer(mainVideoPath=configs.VIDEO_PATH,
                                useVideoAudio=configs.VIDEO_AUDIO_ON,
                                screensaverOn=True)

    if usingAudio:
        audioPlayer = AudioPlayer()

    if recordingOn:
        camera = Camera()

    logger = Logger(pid)
    logger.log_program_run_info()
    logger.log_alive(start=True)

    while True:

        logger.log_alive()
        logger.gdrive.check_quota_timer()

        sensorVolts, sensorsInRange = check_sensors()
        anyInRange = any(sensorsInRange)

        userDetected, sensorReading = update_sensor_reading(
            userDetected, sensorReading, anyInRange, sensorThreshold)

        if recordingOn:
            cameraIsRecording = camera.is_recording()

        if usingAudio:
            playingAudio = audioPlayer.is_playing()
            if not playingAudio and audioPlayer.has_quit():
                # if quit, spawn new
                audioPlayer = AudioPlayer()


        playingVideo = videoPlayer.is_playing()
        if not playingVideo and videoPlayer.has_quit():
            # if quit, spawn new
            videoPlayer = VideoPlayer(videoPath=configs.VIDEO_PATH,
                            useVideoAudio=configs.VIDEO_AUDIO_ON,
                            screensaverOn=True)


        if userDetected:

            ixID = logger.ix_id
            if not ixID:
                ixID = logger.log_interaction_start()

            if recordingOn and not cameraIsRecording:
                fileName = logger.new_recording_name()
                camera.start_recording(fileName)

            if usingAudio and not playingAudio:
                audioPlayer.play_audio()

            if usingVideo and not playingVideo: # or videoPlayer.screensaver_on()):
                # Puts on the main video on and stops screensaver
                videoPlayer.hide(False)
                videoPlayer.play_video()

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio,
                                        playingVideo, cameraIsRecording, ixID)

        else:

            if recordingOn and cameraIsRecording:
                camera.stop_recording()

            if usingAudio and playingAudio:
                audioPlayer.pause_audio()

            if usingVideo and playingVideo:
                # pause the video first. After some time, start screensaver
                videoPlayer.pause_video()
                videoPlayer.hide(True)

            #if usingVideo and not playingVideo and not videoPlayer.screensaver_on():
            #    if videoPlayer.paused_time() > 2:
            #        videoPlayer.screensaver()

            if logger.ix_id:
                logger.log_interaction_end()

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio,
                                        playingVideo, cameraIsRecording)

        logger.update_ix_logs()

        if (datetime.now().hour > 23):
        #if ((datetime.now()-uploadTimer).total_seconds() / 60) > 5:
            logger.upload_recordings()
            uploadTimer = datetime.now()

        sleep(0.4)
