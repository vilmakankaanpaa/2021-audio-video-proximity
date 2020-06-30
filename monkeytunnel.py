import os
import sys
from time import sleep
from datetime import datetime, date, time
import spidev

from audioplayer import AudioPlayer
from videoplayer import VideoPlayer
from logger import Logger
from camera import Camera
import configs

sys.excepthook = sys.__excepthook__

""" Sensor stuff """

# Spidev used to connect to and read the sensors
spi = spidev.SpiDev()
spi.open(0,0)

def read_channel(channel):
  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data

def get_volts(channel=0):
    volts = (read_channel(channel)/1023.0)*3.3
    return volts

def is_in_range(voltsValue, sensorIndex):
    # Threshold for every sensor: probably depends on the location
    # and have to be tested and adjusted

    if sensorIndex == 0 and voltsValue > 0.50:
        # rightmost sensor when looking "at the screen"
        return True
    elif sensorIndex == 1 and voltsValue > 0.80:
        # left of above
        return True
    elif sensorIndex == 2 and voltsValue > 0.30:
        # left of above
        return True
    else:
        return False

def check_sensors():

    i = 0
    sensorVolts = []
    sensorResults = []
    for i in range(3):
        v = get_volts(i)
        sensorVolts.append(v)
        r = is_in_range(v, i)
        sensorResults.append(r)

    return sensorVolts, sensorResults


""" Sensor stuff end"""

def play_audio(audioPlayer):

    # Player status: 0 - ready; 1 - playing; 2 - paused; 3 - stopped; 4 - quit
    playerStatus = audioPlayer.status

    startValue = False # record start of sound play for logging

    if playerStatus == 2:
        # currently paused
        audioPlayer.resume()
        startValue = True
        """
        TODO: is this correct log?
        """
        print('Resuming audio')
    elif playerStatus != 1:
        # currently not paused and not playing -> start
        print('Starting audio')
        startValue = True
        audioPlayer.play_song(configs.AUDIO_PATH)
    else:
        pass

    playingAudio = True
    """ TODO: redundant? """

    return startValue, playingAudio


def pause_audio(audioPlayer):
    audioPlayer.pause()
    print('Pausing audio')


def play_video(videoPlayer):

    videoPlayer.play_video()
    startValue = True
    playingVideo = True

    return startValue, playingVideo


def pause_video(videoPlayer):
    videoPlayer.pause_video()


def new_video_name(logger):
    """have to first create new folder per date, if using"""
    # options: datetime.isoformat(timeObject) OR timeObject.hour + .minute + .second
    """dateStr = date.isoformat(date.today())
    t = datetime.time(datetime.now())
    timestr = str(t.hour)+'-'+str(t.minute)+'-'+str(t.second)"""

    ixID, ixStart = logger.get_ix_info()
    name = ixID + '_' + ixStart
    return name


def print_configurations():

    print('Audio on:', configs.USE_AUDIO)
    print('Video on:', configs.USE_VIDEO)
    print('Using video audio:', configs.VIDEO_AUDIO_ON)
    print('Recording on:', configs.RECORDING_ON)

    if configs.USE_AUDIO: print('Audio file in use:', configs.AUDIO_PATH)
    if configs.USE_VIDEO: print('Video file in use:', configs.VIDEO_PATH)
    if configs.RECORDING_ON: print('Recording to folder:', configs.RECORDINGS_FOLDER)


if __name__ == "__main__":

    print('Starting up monkeytunnel..')
    pid = os.getpid()
    print('pid:',pid)
    """ TODO: save the pid to temp file """

    # configurations for this run of the program
    usingAudio = configs.USE_AUDIO
    usingVideo = configs.USE_VIDEO
    recordingOn = configs.RECORDING_ON

    inRangeStatus = False
    userDetected = False
    sensorIndices = [0,1,2]

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

        # if quit, spawn new
        if usingAudio and audioPlayer.status == 4:
            audioPlayer = AudioPlayer()

        # if quit, spawn new
        if usingVideo and videoPlayer.status == 4:
            videoPlayer = VideoPlayer(configs.VIDEO_AUDIO_ON)
            videoPlayer.load_video(configs.VIDEO_PATH)

        """TODO: change this to a numerical value to have freedom to choose the threshold"""
        # When two consecutive checks are same, set new value
        if anyInRange == True and inRangeStatus == True:
            if not userDetected:
                print("Monkey came in")
            userDetected = True

        elif anyInRange == False and inRangeStatus == False:
            if userDetected:
                print("All monkeys left")
            userDetected = False

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
                audioStartValue, playingAudio = play_audio(audioPlayer) # if just started or not, if playing or not (of course is?? also, needed?)

            if usingVideo and not playingVideo:
                videoStartValue, playingVideo = play_video(videoPlayer)

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio, playingVideo,
                                     cameraIsRecording, ixID)

        else:

            if recordingOn and cameraIsRecording:
                camera.stop_recording()

            if usingAudio and playingAudio:
                pause_audio(audioPlayer)
                playingAudio = False # TODO: not used

            if usingVideo and playingVideo:
                pause_video(videoPlayer)
                playingVideo = False

            if logger.ix_id:
                logger.log_interaction_end()

            logger.log_sensor_status(sensorsInRange, sensorVolts, playingAudio, playingVideo,
                                     cameraIsRecording)

        logger.update_ix_logs()
        #info for next loop:
        inRangeStatus = anyInRange
        sleep(0.4)
