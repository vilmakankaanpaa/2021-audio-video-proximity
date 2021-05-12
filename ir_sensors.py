import spidev

from filemanager import printlog
from datetime import datetime

# Spidev used to connect to and read the sensors
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

class Sensors():

    def __init__(self):

        # Channels and thresholds. 0-3 from right to left when facing screen. Might
        # depend on location so good to test every time the device moves.
        self.voltThresholds = {0:0.40, 1:0.50, 2:0.50}
        self.checkThreshold = 3
        self.monkeyInside = False
        self.sensorReadings = [[False,0],[False,0],[False,0]]

        # Determined state of sensors
        self.activatedSensors = [False, False, False]

        # # Save the first timestamp when sensor gave FALSE reading
        # self.firstFalseReadingTime = None


    def read_channel(self, channel=0):

        val = spi.xfer2([1,(8+channel)<<4,0])
        data = ((val[1]&3) << 8) + val[2]
        volts = (data/1023.0)*3.3
        return volts


    def single_sensor(self, sensorNo):

        # Read the sensor value
        volts = self.read_channel(sensorNo)
        # Based on threshold, set True or False
        inRange = volts > self.voltThresholds.get(sensorNo)
        # Did the value change?
        changed = False
        if self.sensorReadings[sensorNo][0] != inRange:
            changed = True

        self.sensorReadings[sensorNo][0] = inRange

        # Count and mark the times the value has not changed
        counter = 0
        current = self.sensorReadings[sensorNo][1]
        if not changed and current <= self.checkThreshold: # allow to go one above
            counter = current + 1
        elif not changed and current > self.checkThreshold:
            counter = current
        # elif changed, keep at 0

        self.sensorReadings[sensorNo][1] = counter

        return volts


    def check_sensors(self):

        voltsList = [] # the closer, the larger volts

        for i in range(3):
            volts = self.single_sensor(i)
            voltsList.append(volts)

        print(datetime.isoformat(datetime.now()))
        print(self.sensorReadings)
        print(voltsList)


    def check_changed(self):

        # Every time the value has been confirmed enough times (it is same as the set threshold), the value of it will be updated to activated.

        mostRecentOpen = None
        changed = False

        for i in [0,2,1]: # check the sensors in this order

            inRange = self.sensorReadings[i][0]
            nofChecks = self.sensorReadings[i][1]

            if nofChecks == self.checkThreshold:
                changed = True
                # set the new status of the sensor ('determined' now)
                self.activatedSensors[i] = inRange
                if inRange == True:
                    mostRecentOpen = i
                    printlog('Switches','Switch {} open.'.format(i))
                else:
                    printlog('Switches','Switch {} closed.'.format(i))

        return mostRecentOpen, changed


    def update(self):

        # Read the sensor values now
        self.check_sensors()
        # After checking with threshold, which are activated?
        mostRecentOpen, someChanged = self.check_changed()

        if not self.monkeyInside and any(self.activatedSensors):
            printlog('Main','Monkey came in!')
            self.monkeyInside = True
        elif self.monkeyInside and not any(self.activatedSensors):
            printlog('Main','All monkeys left. :(')
            self.monkeyInside = False

        return self.activatedSensors, mostRecentOpen, someChanged


        #anyInRange = any(sensorsInRange)

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

        # if anyInRange:
        #     # Sensors in range. Raise the value on scale.
        #     if self.currentValue < (self.threshold*self.factor)-1: # don't go higher than this value.
        #         self.currentValue += 2 # go up fast
        # else:
        #     # Sensors not in range. Lower the value on scale. (Not below 0). This basically will determine how long interaction is thought to last after monkey leaves (how slowly it is determined it's not inside.)
        #     if self.currentValue > 0:
        #         self.currentValue -= 1 # but down slower
        #
        # if self.currentValue > self.threshold and not self.monkeyInside:
        #     printlog('Main','Monkey came in!')
        #     self.monkeyInside = True
        # elif thresholdReading < threshold and monkeyDetected:
        #     printlog('Main','All monkeys left. :(')
        #     self.monkeyInside = False
        # else:
        #     # Don't do anything yet, keep values same.
        #     # scaleValue is now same as threshold.
        #     pass
        #
        # return self.monkeyInside
