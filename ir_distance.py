activeSensors#!/usr/bin/python
import os
import sys
import time
from datetime import datetime
import spidev
from sound_control import MyPlayer
from sound_log import Logger

sys.excepthook = sys.__excepthook__

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
    elif sensorIndex == 2 voltsValue > 0.42:
        return True
    elif sensorIndex == 0 and voltsValue > 0.50:
        return True
    else:
        return False

def update_log(logger, start=False, end=False, activeSensors=[]):
    timeNow = datetime.now()
    timestr = timeNow.strftime("%Y-%m-%d %H:%M:%S")
    data = [timestr, start, end] + activeSensors
    logger.log_local(data)

if __name__ == "__main__":

    print(os.getpid())

    inRangeStatus = False
    playingAudio = False
    sensorIndices = [0,1,2]

    audioPlayer = MyPlayer()
    logger = Logger()

    prevAliveTime = datetime.now()
    logger.log_alive()

    while True:

        timeNow = datetime.now()
        diff = (timeNow - prevAliveTime).total_seconds() / 60.0

        # ping alive every 5 mins
        if diff > 5:
            #print('Log alive!', diff)
            logger.log_alive()
            prevAliveTime = timeNow

        # Sheets API has a quota so if there are too many requests within 100s they need to be postponed TODO!!
        # Note on 03/06/20: I think the above TODO is old and everything works, but just in case it doesn't I'll
        # leave this here to point to a potential problem.

        # online logging intitated separate from sensor readings, so that if the quota is passed and data accumulated
        # only locally, the waiting records will be logged as soon as possible whether there is activity going on
        # or not
        #logger.log_drive(timeNow) SKIP LOGGING TO DRIVE UNTIL CONNECTED TO API AGAIN

        sensorsInRange = [is_in_range(get_volts(i), i) for i in sensorIndices]
        anyInRange = any(sensorsInRange)
        #print("Movement detected", sensorsInRange)
        print("Any in range?", anyInRange)

        # if the audioPlayer has quit, spawn new
        if audioPlayer.status == 4:
            audioPlayer = MyPlayer()
        audioPlayerStatus = audioPlayer.status

        # Require two consecutive sensor readings before
        # (this is done by saving the first "new in range" to
        # "inRangeStatus" and then eventually here both of these are true)
        # triggering play to prevent random activations
        if anyInRange and inRangeStatus:
            # record start of sound play for logging
            start = True
            # if paused resume
            if audioPlayerStatus == 2:
                audioPlayer.resume()
            # otherwise start playing if not already on
            elif audioPlayerStatus != 1:
                # music file name here
                print("Starting audio")
                audioPlayer.play_song("music.mp3")
            else:
                # status is 1 i.e. already playing
                start = False
            playingAudio = True
            update_log(logger, start=True, activeSensors=sensorsInRange)
        if playingAudio and not anyInRange:
            audioPlayer.pause()
            playingAudio = False
            update_log(logger, end=True, activeSensors=sensorsInRange)
        inRangeStatus = anyInRange
        time.sleep(0.4)
