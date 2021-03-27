
import RPi.GPIO as GPIO
from datetime import datetime


class Switches():

    def __init__(self):

        # Use Broadcom (the GPIO numbering)
        GPIO.setmode(GPIO.BCM)
        # Set the GPIO pin numbers to use and
        # use Pull Up resistance for the reed sensor wiring
        GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(24,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(25,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Adding what happens when switch value changes. We are not using
        # bouncetime because we need to make sure to record all changes.
        # The quick changes are going to handled in other ways.
        GPIO.add_event_detect(22, GPIO.BOTH, callback=self.react)
        GPIO.add_event_detect(23, GPIO.BOTH, callback=self.react)
        GPIO.add_event_detect(24, GPIO.BOTH, callback=self.react)
        GPIO.add_event_detect(25, GPIO.BOTH, callback=self.react)

        # GPIO channels of the switches on RPI
        self.channels = {22:0, 23:1, 24:2, 25:3}
        self.switchesOpen = [False, False, False, False]
        self.switchPlaying = None
        self.queue = None
        self.starttime = None
        self.delay = 3 # seconds


    # Called when one of the four switches is triggered
    def react(self, channel):

        switch = self.channels.get(channel)

        if GPIO.input(channel) == GPIO.HIGH:
            print('Switch', switch, 'is open.')
            self.switchesOpen[switch] = True
            #log([datetime.now(),'flip','Flip open {}'.format(count), since_boot])

            # set switch always on queue first to start playing next
            self.queue = switch

        else:
            print('Switch', switch, 'is closed.')
            self.switchesOpen[switch] = False
            #log([datetime.now(),'flip','Flip closed {}'.format(count), since_boot])

            if switch == self.queue:
                # when switch was on queue but it closes before getting to play
                self.queue = None


    def delayPassed(self):

        playtime = round((datetime.now() - starttime).total_seconds(),2)
        if playtime > self.delay:
            return True
        else:
            return False


    def turnOn(self):

        self.starttime = datetime.now()
        self.switchPlaying = queue
        self.queue = None

        # TODO: turn media actually on
        print('Turning media on:', self.switchPlaying)
        # TODO: log start of interaction


    def turnOff(self):

        # TODO: log the end of interaction
        playtime = round((datetime.now() - starttime).total_seconds(),2)

        # TODO: turn media actually off
        print('Turning media off:', self.switchPlaying, playtime)


        self.starttime = None
        self.switchPlaying = None


    def updateSwitches(self):

        # 1. Swithc on queue but no switches playing media
        #       -> Turn on
        # 2. Switch on queue but already playing
        #       -> Do nothing / don't add on the queue
        # 3. Switch on queue but another one playing
        #       -> Check if delay has passed -> leave to queue or start playing
        # 4. All switches closed but one is playing
        #       -> Check if delay has passed -> continue or stop playing

        if self.switchPlaying == None:
            # media is not currently playing
            if self.queue != None:
                # Turn new switch on
                turnOn()
        else:
            # media is currently playing
            if self.queue != self.switchPlaying:
                if delayPassed():
                    turnOff()
                    turnOn()
            elif not any(self.switchesOpen):
                if delayPassed():
                    turnOff()
