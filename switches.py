
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

        # TODO: do a class instead?

        # GPIO channels of the switches on RPI
        global channels
        channels = {22:0, 23:1, 24:2, 25:3}

        # Use global variable to update the switch statuses
        global switchesOpen
        switchesOpen = [False, False, False, False]

        global switchCurrentlyPlaying
        switchCurrentlyPlaying = None
        
        global switchOnQueue
        switchOnQueue = None

        global delay
        delay = 3 # seconds

        global starttime
        starttime = None


#
# Called when one of the four switches is triggered
def react(channel):

    switch = channels.get(channel)
    global switchesOpen
    global switchOnQueue

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
            turnOff()
        if switch == switchOnQueue:
            switchOnQueue = None


def delayPassed():
    
    global delay
    if starttime != None:
        # already was turned off
        playtime = round((datetime.now() - starttime).total_seconds(),2)
        if playtime > delay:
            return True
        else:
            return False
    else:
        # nothing palying anymore, skip
        return False


def turnOn(switch):
    
    global switchCurrentlyPlaying
    global switchOnQueue
    
    if not switchCurrentlyPlaying:
        # Nothing playing, start fresh
        startMedia(switch)
    else:
        # One is playing (but not this)
        if delayPassed():
            # turn  the other one off
            stopMedia()
            # start on new switch
            startMedia(switch)
        else:
            # Delay is not over, put on queue
            switchOnQueue = switch


def turnOff():
    if delayPassed():
        stopMedia()


def startMedia(switch):
    # TODO: start the actual media
    global starttime
    starttime = datetime.now()
    global switchCurrentlyPlaying
    switchCurrentlyPlaying = switch
    global switchOnQueue
    switchOnQueue = None # Cannot be any queue
    print(starttime, 'Starting on switch', switch)


def stopMedia():
    # TODO stop the actual media
    global switchCurrentlyPlaying
    global starttime
    
    playtime = round((datetime.now() - starttime).total_seconds(),2)
    print(datetime.now(), 'Stopping on switch', switchCurrentlyPlaying, playtime)
    
    switchCurrentlyPlaying = None
    starttime = None
    
