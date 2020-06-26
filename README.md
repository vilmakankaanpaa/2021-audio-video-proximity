#### Connecting to pi:

Needs to be connected to the same network and know the IP of the pi (might be also possible to search by name)
Find out the IP: https://www.raspberrypi.org/documentation/remote-access/ip-address.md
E.g. can use "Fing" phone app to find out the IP, if the pi and phone are on the same network.


#### Running the system:

run the file 'ir_distance.py': python3 ir_distance.py
I'm pretty sure it's python3 but if I remember that incorrectly and it doesn't work try python.

Forgot to make a requirements file but everything is installed on the pi.

#### Online logging to Google Sheets

There needs to be a 'client_secret.json' file that contains the creds for Google Drive API.

The Logger class in sound_log.py deterines the sheets to write to; change names in init function. All the data should be also logged locally, and any failures to log to the Google document are logged in 'logfail.csv'.

The frequency to attempt online logging is quite short, because as it is now, logging blocks the script i.e. when it's happening the sensors are not read. So better to log small amounts of data often than block for a longer time at once. I'm sure there are better ways to do it but this worked well enough for my case.

Data is logged as:
 - timestamp
 - start (flag True if start of an interaction)
 - end (flag True if end of an interaction)
 - sensor1 (flag True if sensor 1 is active at this time)
 - sensor2 (flag True if sensor 2 is active at this time)
 - sensor3 (flag True if sensor 3 is active at this time)

#### Requirements

omxplayer-wrapper==0.3.3
pathlib2==2.3.5
spidev==3.4
mpyg321==0.0.2

threading ?
pexpect==4.7.0
gspread==3.1.0
oauth2client==4.1.3
csv ?
httplib2=0.14.0
