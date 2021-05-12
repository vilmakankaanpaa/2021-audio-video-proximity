import spidev

from filemanager import printlog

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
        # self.inRange = [False, False, False]
        # self.previously = [False, False, False]

        #self.sensorsInRange = {0:[False,0],1:[False,0],2:[False,0]}
        self.sensor1 = [False,0]
        self.sensor2 = [False,0]
        self.sensor3 = [False,0]
        #self.threshold = 2 # how many checks is needed to determine otherwise
        #self.factor = 5
        #self.currentValue = self.threshold # where the checks are on scale currently

        self.activatedSensors = [False, False, False]

        # # Save the first timestamp when sensor gave FALSE reading
        #self.nofChecks = 0
        # self.firstFalseReadingTime = None

        #self.logger = logger

    def read_channel(self, channel=0):

        val = spi.xfer2([1,(8+channel)<<4,0])
        data = ((val[1]&3) << 8) + val[2]
        volts = (data/1023.0)*3.3
        return volts


    def single_sensor(self, sensor, index):

        # Read the sensor value
        volts = self.read_channel(index)
        # Based on threshold, set True or False
        inRange = volts > self.voltThresholds.get(index)
        # Did the value change?
        changed = False
        if sensor[0] != inRange:
            changed = True

        # Count and mark the times the value has not changed
        counter = 0
        current = sensor[1]
        if not changed and current <= self.checkThreshold: # allow to go one above
            counter = current + 1
        elif not changed and current > self.checkThreshold:
            counter = current

        # if changed, keep at 0

        return inRange, counter


    def check_sensors(self):

        #voltsList = [] # the closer, the larger volts
        #rangeList = []

#        for i in range(3):
        #print(self.sensor1[0])
        value, checks = self.single_sensor(self.sensor1, 0)
        self.sensor1[0] = value
        self.sensor1[1] = checks
        value, checks = self.single_sensor(self.sensor2, 1)
        self.sensor2[0] = value
        self.sensor2[1] = checks
        value, checks = self.single_sensor(self.sensor3, 2)
        self.sensor3[0] = value
        self.sensor3[1] = checks
        #self.sensor1[0], self.sensor1[1] = self.single_sensor(self.sensor1, 0)
        #self.sensor2[0], self.sensor2[1] = self.single_sensor(self.sensor2, 1)
        #self.sensor3[0], self.sensor3[1] = self.single_sensor(self.sensor3, 2)
            #voltsList.append(volts)
            #rangeList.append(volts > self.voltThresholds.get(i))

        #self.previously = self.inRange
        #self.inRange = rangeList

        #return voltsList

    def check_changed(self):

        # Every time the value has been confirmed enough times (it is same as the set threshold), the value of it will be updated to activated.

        mostRecentOpen = None
        changed = False

        if self.sensor1[1] == self.checkThreshold:
            changed = True
            value = self.sensor1[0]
            self.activatedSensors[0] = value
            if value == True:
                mostRecentOpen = 0
                printlog('Switches','Switch {} open.'.format(1))
            else:
                printlog('Switches','Switch {} closed.'.format(0))

        if self.sensor3[1] == self.checkThreshold:
            changed = True
            value = self.sensor3[0]
            self.activatedSensors[2] = value
            if value == True:
                mostRecentOpen = 2
                printlog('Switches','Switch {} open.'.format(3))
            else:
                printlog('Switches','Switch {} closed.'.format(3))

        # If it'd be possible there will be multiple activated, then the middle one should be the most recent change: checked last.
        if self.sensor2[1] == self.checkThreshold:
            changed = True
            value = self.sensor2[0]
            self.activatedSensors[1] = value
            if value == True:
                mostRecentOpen = 1
                printlog('Switches','Switch {} open.'.format(2))
            else:
                printlog('Switches','Switch {} closed.'.format(2))


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
