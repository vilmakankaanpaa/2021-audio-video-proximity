#!/usr/bin/python
import os
import sys
import time
from datetime import datetime
import spidev
from sound_control import MyPlayer
from sound_log import Logger
import configs

sys.excepthook = sys.__excepthook__

# Spidev used to connect to and read the sensors
spi = spidev.SpiDev()
spi.open(0,0)

"""
TODO: audio and video status dicts
"""

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

def update_log(logger, startAudio=False, endAudio=False, activeSensors=[]):
    timeNow = datetime.now()
    timestr = timeNow.strftime("%Y-%m-%d %H:%M:%S")
    """
    TODO log readable values
    """
    data = [timestr, startAudio, endAudio] + activeSensors
    logger.log_local(data)

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


def play_video(videoPlayer):

    # video paused -> start playing
    # video is not started -> start playing
    videoPlayer._play_video()
    startValue = True

    # if already playing -> dont do anything
    # startValue = False

    # IN ANY CASE:
    playingVideo = True
    """ TODO: redundant? """

    return startValue, playingVideo


def pause_video(videoPlayer):
    videoPlayer._pause_video()


if __name__ == "__main__":

    print(os.getpid())

    usingAudio = configs.USE_AUDIO
    usingVideo = configs.USE_VIDEO

    inRangeStatus = False
    userDetected = False

    sensorIndices = [0,1,2]

    if usingAudio:
        audioPlayer = MyPlayer()
        playingAudio = False

    if usingVideo:
        videoPlayer = VideoPlayer()
        videoPlayer._load_video(configs.VIDEO_PATH)
        playingVideo = False

    logger = Logger()

    prevAliveTime = datetime.now()
    logger.log_alive()

    while True:

        timeNow = datetime.now()
        timeDiff = (timeNow - prevAliveTime).total_seconds() / 60.0

        if timeDiff > 5:
            #print('Log alive!', diff)
            logger.log_alive()
            prevAliveTime = timeNow

        # Sheets API has a quota so if there are too many requests within 100s they need to be postponed TODO!!
        # Note on 03/06/20: I think the above TODO is old and everything works, but just in case it doesn't I'll
        # leave this here to point to a potential problem.

        # online logging intitated separate from sensor readings, so that if the quota is passed and data accumulated
        # only locally, the waiting records will be logged as soon as possible whether there is activity going on
        # or not
        """
        logger.log_drive(timeNow) SKIP LOGGING TO DRIVE UNTIL CONNECTED TO API AGAIN
        """

        sensorsInRange = [is_in_range(get_volts(i), i) for i in sensorIndices]
        anyInRange = any(sensorsInRange)
        #print("Movement detected", sensorsInRange)

        # if the audioPlayer has quit, spawn new
        if usingAudio and audioPlayer.status == 4:
            audioPlayer = MyPlayer()
        #print("audioPlayer status:", audioPlayer.status)

        """TODO: if videoplayer has quit, spawn new """

        """TODO: change this to a numerical value to hace freedom to choose the threshold"""
        # When two consecutive checks are same, set new value
        if anyInRange == True and inRangeStatus == True:
            userDetected = True
            print("Monkey came in")

        elif anyInRange == False and inRangeStatus == False:
            userDetected = False
            print("No monkeys in tunnel")

        #else:
            # two consecutive checks are different
            #print("Status change of inRange:", anyInRange)

        if userDetected:

            if usingAudio:
                audioStartValue, playingAudio = play_audio(audioPlayer) # if just started or not, if playing or not (of course is?? also, needed?)
                update_log(logger, startAudio=audioStartValue, activeSensors=sensorsInRange)

            if usingVideo:
                videoStartValue, playingVideo = play_video(videoPlayer)
                """ TODO: logging """

        else:
            if usingAudio and playingAudio:
                pause_audio(audioPlayer)
                print('Audio paused')
                playingAudio = False # TODO: not used
                update_log(logger, endAudio=True, activeSensors=sensorsInRange)

            if usingVideo and playingVideo:
                pause_video(videoPlayer)
                print('Video paused')
                playingVideo = False
                """TODO: logging"""

        #info for next loop:
        inRangeStatus = anyInRange
        time.sleep(0.4)
