
# Priority order
# 1. Log sensor data in short intervals, with timestamp
# 2. Set threshold when "interacting" and label data
# 3. Start at boot
# 4. Quick way for modifying threshold on spot

import sys
import os
from time import sleep
import spidev
from datetime import datetime
import csv

# Spidev used to connect to and read the sensors
spi = spidev.SpiDev()
spi.open(0,0)


def read_channel(channel):
  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data


def log_data(data):

    with open('prototype.csv', 'a', newline='') as logfile:
        logwriter = csv.writer(logfile, delimiter=',')
        for row in data:
            logwriter.writerow(row)

if __name__ == "__main__":

    boottime = datetime.now()
    threshold = 600
    detected = False
    ix_readings = []
    ix_count = 0


    while True:

        reading = read_channel(0)
        print(reading)

        if reading > threshold:
            # interaction detected
            if detected == False:
                ix_count += 1
                print('new interaction!')

            detected = True
            # append to ix_readings
            since_boot = (datetime.now() - boottime).total_seconds()
            ix_readings.append([datetime.now(), since_boot, ix_count, reading])

        else:
            if detected == True:
                log_data(ix_readings)
                ix_readings = []
            detected = False

        sleep(0.1)
