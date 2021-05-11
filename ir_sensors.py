import spidev
#import Adafruit_GPIO.SPI as SPI
#import Adafruit_MCP3008
from time import sleep

# Spidev used to connect to and read the sensors
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000


def read_channel(channel):
  

  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data


def get_volts(channel=0):
    volts = (read_channel(channel)/1023.0)*3.3
    return volts


def is_in_range(voltsValue, sensorIndex):
    # Threshold for every sensor: probably depends on the location
    # and have to be tested and adjusted

    if sensorIndex == 0 and voltsValue > 0.40:
        # rightmost sensor when looking "at the screen"
        return True
    elif sensorIndex == 1 and voltsValue > 0.50:
        # left of above
        return True
    elif sensorIndex == 2 and voltsValue > 0.50:
        # left of above
        return True
    else:
        return False


def check_sensors():

    sensorVolts = []
    sensorResults = []
    for i in range(3):
        v = get_volts(i)
        sensorVolts.append(v)
        r = is_in_range(v, i)
        sensorResults.append(r)

    return sensorVolts, sensorResults


if __name__ == "__main__":

    while True:

        sensorVolts, sensorsInRange = check_sensors()
        print('Volts:', sensorVolts)
        print('SensorisInRange:', sensorsInRange)
        #anyInRange = any(sensorsInRange)

        sleep(0.5)
