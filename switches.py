
import RPi.GPIO as GPIO
import globals

def setupSwitches():
        # Use Broadcom (the GPIO numbering)
        GPIO.setmode(GPIO.BCM)
        # Set the GPIO pin numbers to use and
        # use Pull Up resistance for the reed sensor wiring
        GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(24,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(25,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Adding what happens when switch value changes. We are not using
        # bouncetime because we need to make sure to record all changes. The quick
        # changes are going to handled in other ways.
        GPIO.add_event_detect(22, GPIO.BOTH, callback=switches.react)
        GPIO.add_event_detect(23, GPIO.BOTH, callback=switches.react)
        GPIO.add_event_detect(24, GPIO.BOTH, callback=switches.react)
        GPIO.add_event_detect(25, GPIO.BOTH, callback=switches.react)


# Called when one of the four switches is triggered
def react(channel):

    globals.switchesOpen # Use global variable to update the switch statuses
    switchNo = globals.switchChannels.get(channel)

    if GPIO.input(channel) == GPIO.HIGH:
        print('Switch', switchNo, 'is open.')
        globals.switchesOpen[switchNo] = True
        #log([datetime.now(),'flip','Flip open {}'.format(count), since_boot])

    else:
        print('Switch', switchNo, 'is closed.')
        globals.switchesOpen[switchNo] = False
        #log([datetime.now(),'flip','Flip closed {}'.format(count), since_boot])
