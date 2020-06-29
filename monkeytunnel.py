#!/usr/bin/python
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
    #print("Voltage: %.2f V" % v)
    return volts

def is_in_range(voltsValue, sensorIndex):
    # Threshold for every sensor: probably depends on the location
    # and have to be tested and adjusted
    if sensorIndex == 1 and voltsValue > 0.71:
        return True
    elif sensorIndex == 2 and voltsValue > 0.42:
        return True
    elif sensorIndex == 0 and voltsValue > 0.50:
        return True
    else:
        return False


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

    # video paused -> start playing
    # video is not started -> start playing
    videoPlayer.play_video()
    startValue = True

    # if already playing -> dont do anything
    # startValue = False

    # IN ANY CASE:
    playingVideo = True
    """ TODO: redundant? """

    print('Playing video')

    return startValue, playingVideo


def pause_video(videoPlayer):
    videoPlayer.pause_video()
    print('Pausing video')


def new_video_name():
    """have to first create new folder per date, if using"""
    # options: datetime.isoformat(timeObject) OR timeObject.hour + .minute + .second
    dateStr = date.isoformat(date.today())
    t = datetime.time(datetime.now())
    timestr = str(t.hour)+'-'+str(t.minute)+'-'+str(t.second)

    return (dateStr + 'T' + timestr)


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
    print('pid:',os.getpid())
    """ TODO: save the pid to temp file """
    print_configurations()

    # configurations for this run of the program
    usingAudio = configs.USE_AUDIO
    usingVideo = configs.USE_VIDEO
    recordingOn = configs.RECORDING_ON

    inRangeStatus = False
    userDetected = False
    sensorIndices = [0,1,2]

    if usingAudio:
        audioPlayer = AudioPlayer()
        """Todo use player status attribute instead? This is messy"""
        playingAudio = False

    if usingVideo:
        videoPlayer = VideoPlayer(configs.VIDEO_AUDIO_ON)
        videoPlayer.load_video(configs.VIDEO_PATH)
        """Todo use player status attribute instead? This is messy"""
        playingVideo = False

    if recordingOn:
        camera = Camera(configs.RECORDINGS_FOLDER)

    logger = Logger()

    prevAliveTime = datetime.now()
    
    logger.log_alive()
    logger.log_tech_details()

    while True:

        timeNow = datetime.now()
        timeDiff = (timeNow - prevAliveTime).total_seconds() / 60.0

        if timeDiff > 5:
            #print('Log alive!', diff)
            logger.log_alive()
            prevAliveTime = timeNow

        sensorsInRange = [is_in_range(get_volts(i), i) for i in sensorIndices]
        anyInRange = any(sensorsInRange)
        # Log sensors in range

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

            if recordingOn and not cameraIsRecording:
                fileName = new_video_name()
                camera.start_recording(fileName)

            if usingAudio and not playingAudio:
                audioStartValue, playingAudio = play_audio(audioPlayer) # if just started or not, if playing or not (of course is?? also, needed?)

            if usingVideo and not playingVideo:
                videoStartValue, playingVideo = play_video(videoPlayer)

            if not logger.ix_id:
                logger.log_interaction_start()

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

        #info for next loop:
        inRangeStatus = anyInRange
        sleep(0.4)
