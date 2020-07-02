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


def updateSensorReading(userDetected, sensorReading, anyInRange, sensorThreshold):

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

    sensorThreshold = 3 # after 3 consecutive readings, change value of userDetected
    sensorReading = sensorThreshold # this is the middle grounf between True and False
    userDetected = False

    playingAudio = False
    playingVideo = False
    cameraIsRecording = False

    uploadTimer = datetime.now()

    if usingAudio:
        audioPlayer = AudioPlayer()

    if usingVideo:
        videoPlayer = VideoPlayer(configs.VIDEO_AUDIO_ON)
        videoPlayer.load_video(configs.VIDEO_PATH)

    if recordingOn:
        camera = Camera(configs.RECORDINGS_PATH)

    logger = Logger(pid)
    logger.log_program_run_info()
    logger.log_alive(start=True)

    while True:

        logger.log_alive()
        logger.gdrive.check_quota_timer()

        sensorVolts, sensorsInRange = check_sensors()
        anyInRange = any(sensorsInRange)

        userDetected, sensorReading = updateSensorReading(
            userDetected, sensorReading, anyInRange, sensorThreshold)


        if recordingOn:
            cameraIsRecording = camera.isRecording()

        if usingAudio:
            playingAudio = audioPlayer.isPlaying()
            if not playingAudio and audioPlayer.hasQuit():
                # if quit, spawn new
                audioPlayer = AudioPlayer()

        if usingVideo:
            playingVideo = videoPlayer.isPlaying()
            if not playingVideo and videoPlayer.hasQuit():
                # if quit, spawn new
                videoPlayer = VideoPlayer(configs.VIDEO_AUDIO_ON)
                videoPlayer.load_video(configs.VIDEO_PATH)


        if userDetected:

            ixID = logger.ix_id
            if not ixID:
                ixID = logger.log_interaction_start()

            if recordingOn and not cameraIsRecording:
                fileName = logger.new_recording_name()
                camera.start_recording(fileName)

            if usingAudio and not playingAudio:
                audioPlayer.play_audio()

            if usingVideo and not playingVideo:
                videoPlayer.play_video()

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio,
                                        playingVideo, cameraIsRecording, ixID)

        else:

            if recordingOn and cameraIsRecording:
                camera.stop_recording()
                logger.handle_recording()

            if usingAudio and playingAudio:
                audioPlayer.pause_audio()

            if usingVideo and playingVideo:
                videoPlayer.pause_video()

            if logger.ix_id:
                logger.log_interaction_end()

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio,
                                        playingVideo, cameraIsRecording)

        logger.update_ix_logs()

        # TODO: change this. log after 22
        if ((datetime.now()-uploadTimer).total_seconds() / 60) > 30:
            logger.uploadRecordings()

        sleep(0.4)
