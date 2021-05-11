import spidev
#import Adafruit_GPIO.SPI as SPI
#import Adafruit_MCP3008
from time import sleep

from filemanager import printlog


class Sensors():

    def __init__(self, logger):

    # Spidev used to connect to and read the sensors
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000000

    self.monkeyInside = False
    self.sensorsInRange = [False, False, False]
    self.threshold = 2 # how many checks is needed to determine otherwise
    self.factor = 5
    self.currentValue = self.threshold # where the checks are on scale currently

    # # Save the first timestamp when sensor gave FALSE reading
    #self.nofChecks = 0
    # self.firstFalseReadingTime = None

    self.logger = logger


    def read_channel(self, channel=0):

      val = spi.xfer2([1,(8+channel)<<4,0])
      data = ((val[1]&3) << 8) + val[2]
      volts = data/1023.0)*3.3
      return volts


    def is_in_range(self, voltsValue, sensorIndex):
        # Threshold for every sensor: probably depends on the location
        # and have to be tested and adjusted

        # 0-3 from right to left when facing screen
        if sensorIndex == 0 and voltsValue > 0.40:
            return True
        elif sensorIndex == 1 and voltsValue > 0.50:
            return True
        elif sensorIndex == 2 and voltsValue > 0.50:
            return True
        else:
            return False


    def check_sensors(self):

        voltsList = [] # the closer, the larger volts
        rangeList = []
        for i in range(3):
            v = self.read_channel(i)
            voltsList.append(v)
            r = self.is_in_range(v, i)
            rangeList.append(r)

        self.sensorsInRange = rangeList
        return voltsList


    def update(self):

        # Read the sensor values now
        sensorVolts, sensorsInRange = self.check_sensors()
        anyInRange = any(sensorsInRange)

        # # Checking whether it is first FALSE reading after monkey has been in for interaction
        # if (not anyInRange and self.monkeyInside):
        #     # if monkey was inside last round and now not detected
        #     if self.nofChecks == 0:
        #         # First check
        #         self.firstFalseReadingTime = datetime.now()
        #     else:
        #         # Not first check
        #         self.nofChecks += 1
        # else:
        #     self.nofChecks = 0


        # When enough no. of consecutive checks are same, set new value. Checks
        # are done once per _loop_ (0.4 seconds). ScaleValue vary between 0 to
        # threshold*factor. The set threshold is for determining if monkey
        # inside or not (value = false or true). The more _loops_ are needed to
        # change the userDetected value, the less sensitive the system is.

        # Update value on the scale to determine monkeyInside value.
        if anyInRange:
            # Sensors in range. Raise the value on scale.
            if self.currentValue < (self.threshold*self.factor)-1: # don't go higher than this value.
                self.currentValue += 2 # go up fast
        else:
            # Sensors not in range. Lower the value on scale. (Not below 0). This basically will determine how long interaction is thought to last after monkey leaves (how slowly it is determined it's not inside.)
            if self.currentValue > 0:
                self.currentValue -= 1 # but down slower

        if self.currentValue > self.threshold and not self.monkeyInside:
            printlog('Main','Monkey came in!')
            self.monkeyInside = True
        elif thresholdReading < threshold and monkeyDetected:
            printlog('Main','All monkeys left. :(')
            self.monkeyInside = False
        else:
            # Don't do anything yet, keep values same.
            # scaleValue is now same as threshold.
            pass

        return self.monkeyInside
