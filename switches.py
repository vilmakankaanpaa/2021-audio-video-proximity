
import RPi.GPIO as GPIO
import globals
from datetime import datetime

def init():
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
        GPIO.add_event_detect(22, GPIO.BOTH, callback=react)
        GPIO.add_event_detect(23, GPIO.BOTH, callback=react)
        GPIO.add_event_detect(24, GPIO.BOTH, callback=react)
        GPIO.add_event_detect(25, GPIO.BOTH, callback=react)

        # GPIO channels of the switches on RPI
        global channels
        channels = {22:0, 23:1, 24:2, 25:3}

        # Use global variable to update the switch statuses
        global switchesOpen
        switchesOpen = [False, False, False, False]

        global switchCurrentlyPlaying # 0-3
        switchCurrentlyPlaying = None

        global delay
        delay = 3 # seconds

        global starttime
        starttime = None

#
# Called when one of the four switches is triggered
def react(channel):

    switch = channels.get(channel)

    if GPIO.input(channel) == GPIO.HIGH:
        print('Switch', switch, 'is open.')
        switchesOpen[switch] = True
        #log([datetime.now(),'flip','Flip open {}'.format(count), since_boot])
        if switch != switchCurrentlyPlaying:
            turnOn(switch)

    else:
        print('Switch', switch, 'is closed.')
        switchesOpen[switch] = False
        #log([datetime.now(),'flip','Flip closed {}'.format(count), since_boot])
        if switch == switchCurrentlyPlaying:
            # sometimes another switch was opened during other one was open, then it would not be stopped
            turnOff(switch)


def delayPassed():
    playtime = round((datetime.now() - starttime).total_seconds(),2)
    if playtime > delay:
        return True
    else:
        return False


def turnOn(switch):

    if not switchCurrentlyPlaying:
        # Nothing playing, start fresh
        startMedia(switch)
    else:
        # One is playing (but not this)
        if delayPassed:
            # turn  the other one off
            stopMedia(switchCurrentlyPlaying)
            # start on new switch
            startMedia(switch)
        else:
            # Delay is not over, do nothing
            pass


def turnOff(switch):
    if delayPassed:
        stopMedia(switchCurrentlyPlaying)
        switchCurrentlyPlaying = None
        starttime = None


def startMedia(switch):
    starttime = datetime.now()
    switchCurrentlyPlaying = switch
    print(starttime, 'Starting on switch', switch)


def stopMedia(switch):
    playtime = round((datetime.now() - starttime).total_seconds(),2)
    switchCurrentlyPlaying = None
    print(datetime.now(), 'Stopping on switch', switch, playtime)




    # Is the same already playing?
