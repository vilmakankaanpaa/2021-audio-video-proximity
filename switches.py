
import RPi.GPIO as GPIO
import settings

# Called when one of the four switches is triggered
def react(channel):

    settings.switchesOpen # Use global variable to update the switch statuses
    switchNo = settings.switchChannels.get(channel)

    if GPIO.input(channel) == GPIO.HIGH:
        print('Switch', switchNo, 'is open.')
        settings.switchesOpen[switchNo] = True
        #log([datetime.now(),'flip','Flip open {}'.format(count), since_boot])

    else:
        print('Switch', switchNo, 'is closed.')
        settings.switchesOpen[switchNo] = False
        #log([datetime.now(),'flip','Flip closed {}'.format(count), since_boot])
