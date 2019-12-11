#!/usr/bin/python
import os
import sys
import time
from datetime import datetime
import spidev
from sound_control import MyPlayer
from sound_log import Logger

sys.excepthook = sys.__excepthook__
 
spi = spidev.SpiDev()
spi.open(0,0)
 
 
def read_channel(channel):
  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data

def get_volts(channel=0):
    v=(read_channel(channel)/1023.0)*3.3
    print("Voltage: %.2f V" % v) 
    return v

def is_in_range(v, i):
    if i == 1 and v > 0.71:
        return True
    elif i in [0, 2] and v > 0.45:
        return True
    else:
        return False
 
# Update local log file
def update_log(logger, start=False, end=False, sensors_active=[]):
    now = datetime.now()
    timestr = now.strftime("%Y-%m-%d %H:%M:%S")
    data = [timestr, start, end] + sensors_active
    logger.log_local(data)
    
  
if __name__ == "__main__":
    print(os.getpid())
    status_in_range = False
    playing = False
    channel_indices = [0,1,2]
    player = MyPlayer()
    logger = Logger()
    prev_alive_time = datetime.now()
    logger.log_alive()
    while True:
        now = datetime.now()
        diff = (now - prev_alive_time).total_seconds() / 60.0
        # ping alive every 5 mins
        if diff > 5:
            #print('Log alive!', diff)
            logger.log_alive()
            prev_alive_time = now
        # Sheets API has a quota so if there are too many requests within 100s they need to be postponed TODO!!
        #if (now - logger.prev_log_time).total_seconds() >= 10:
        logger.log_drive(now)
        sensors_in_range = [is_in_range(get_volts(i), i) for i in channel_indices]
        new_in_range = any(sensors_in_range)
        #print("In range?", sensors_in_range)

        # if player has quit, spawn new
        if player.status == 4:
            player = MyPlayer()
        p_status = player.status

        # Require two consecutive sensor readings before
        # triggering play
        if new_in_range and status_in_range:
            # record start of sound play for logging
            start = True
            # if paused resume  
            if p_status == 2:
                pass
                #player.resume()
            # otherwise start playing if not already on
            elif p_status != 1:
                pass
                #player.play_song("rain.mp3")
            else:
                # status is 1 i.e. already playing
                start = False
            playing = True
            update_log(logger, start=start, sensors_active=sensors_in_range)
        if playing and not new_in_range:
            #player.pause()
            playing = False
            update_log(logger, end=True, sensors_active=sensors_in_range)
            pass
        status_in_range = new_in_range
        time.sleep(0.4)
        

