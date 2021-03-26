
import RPi.GPIO as GPIO
import settings

# Called when one of the four switches is triggered
def react(channel):

    global switchesOpen # Use global variable to update the switch statuses
    switchNo = switchChannels.get(channel)

    if GPIO.input(channel) == GPIO.HIGH:
        print('Switch', switchNo, 'is open.')
        switchesOpen[switchNo] = True
        #log([datetime.now(),'flip','Flip open {}'.format(count), since_boot])

    else:
        print('Switch', switchNo, 'is closed.')
        switchesOpen[switchNo] = False
        #log([datetime.now(),'flip','Flip closed {}'.format(count), since_boot])
