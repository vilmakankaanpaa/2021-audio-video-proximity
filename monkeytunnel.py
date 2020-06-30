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

def new_video_name(logger):
    """have to first create new folder per date, if using"""
    # options: datetime.isoformat(timeObject) OR timeObject.hour + .minute + .second
    """dateStr = date.isoformat(date.today())
    t = datetime.time(datetime.now())
    timestr = str(t.hour)+'-'+str(t.minute)+'-'+str(t.second)"""

    ixID, ixStart = logger.get_ix_info()
    name = ixID + '_' + ixStart
    logger.set_ix_recording_name(name)
    return name

def print_configurations():

    print('Audio on:', configs.USE_AUDIO)
    print('Video on:', configs.USE_VIDEO)
    print('Using video audio:', configs.VIDEO_AUDIO_ON)
    print('Recording on:', configs.RECORDING_ON)

    if configs.USE_AUDIO: print('Audio file in use:', configs.AUDIO_PATH)
    if configs.USE_VIDEO: print('Video file in use:', configs.VIDEO_PATH)
    if configs.RECORDING_ON: print('Recording to folder:', configs.RECORDINGS_FOLDER)

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

    print('Starting up monkeytunnel..')
    pid = os.getpid()
    print('pid:',pid)
    """ TODO: save the pid to temp file """

    # configurations for this run of the program
    usingAudio = configs.USE_AUDIO
    usingVideo = configs.USE_VIDEO
    recordingOn = configs.RECORDING_ON

    sensorThreshold = 3 # after 3 consecutive readings, change value of userDetected
    sensorReading = sensorThreshold # this is the middle grounf between True and False
    userDetected = False

    """Todo use player status attribute instead? This is messy"""
    playingAudio = False
    playingVideo = False
    cameraIsRecording = False

    if usingAudio:
        audioPlayer = AudioPlayer()

    if usingVideo:
        videoPlayer = VideoPlayer(configs.VIDEO_AUDIO_ON)
        videoPlayer.load_video(configs.VIDEO_PATH)

    if recordingOn:
        camera = Camera(configs.RECORDINGS_FOLDER)

    logger = Logger(pid)
    logger.log_program_run_info()

    while True:

        logger.log_alive()
        logger.check_quota_counter()

        sensorVolts, sensorsInRange = check_sensors()
        anyInRange = any(sensorsInRange)

        userDetected, sensorReading = updateSensorReading(
            userDetected, sensorReading, anyInRange, sensorThreshold)

        # if quit, spawn new
        if usingAudio and audioPlayer.status == 4:
            audioPlayer = AudioPlayer()

        # if quit, spawn new
        if usingVideo and videoPlayer.status == 4:
            videoPlayer = VideoPlayer(configs.VIDEO_AUDIO_ON)
            videoPlayer.load_video(configs.VIDEO_PATH)

        if recordingOn:
            cameraIsRecording = camera.recording

        if userDetected:

            ixID = logger.ix_id
            if not ixID:
                ixID = logger.log_interaction_start()

            if recordingOn and not cameraIsRecording:
                fileName = new_video_name(logger)
                camera.start_recording(fileName)

            if usingAudio and not playingAudio:
                audioPlayer.play_audio()
                playingAudio = True

            if usingVideo and not playingVideo:
                videoPlayer.play_video()
                playingVideo = True

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio, playingVideo,
                                     cameraIsRecording, ixID)

        else:

            if recordingOn and cameraIsRecording:
                camera.stop_recording()

            if usingAudio and playingAudio:
                audioPlayer.pause_audio()
                playingAudio = False # TODO: not used

            if usingVideo and playingVideo:
                videoPlayer.pause_video()
                playingVideo = False

            if logger.ix_id:
                logger.log_interaction_end()

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio, playingVideo,
                                     cameraIsRecording)

        logger.update_ix_logs()

        sleep(0.4)
