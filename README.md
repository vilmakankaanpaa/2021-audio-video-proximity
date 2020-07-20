# Monkeytunnel

## Requirements

### Technology
```
Raspberry Pi
Three proximity sensors
LCD Screen
Camera module
Fish-eye lens
Speaker
```

### Libraries
```
omxplayer-wrapper\==0.3.3
spidev\==3.4
mpyg321\==0.0.2
gspread\==3.1.0
oauth2client\==4.1.3
httplib2\==0.14.0
google-auth\==1.18.0
google-auth-oauthlib\==0.4.1
google-api-python-client
pytest-shutil
```

**not sure if really used:**
pathlib2\==2.3.5

**not sure in installed or a side package:**
pexpect\==4.7.0 (?)
threading

## Connecting to pi
Computer needs to be connected to the same network as Pi and know the IP of the pi (might be also possible to search by name). Find out IP locally: https://www.raspberrypi.org/documentation/remote-access/ip-address.md. You can use e.g. "Fing" mobile app to scan the the IPs of devices connected to the same wifi as the phone is.
It is best to start with making your phone hotspot known for Pi, so you can do the connecting to new wifi anywhere through using the phone hotspot.
Connecting to your phone hotspot:
1. Use a netwrok know for the Pi, and connect your mobile to the same wifi
2. Use Fing mobile app to scan all the devices in the same wifi and search for Raspberry Pi. Copy the IP address shown.
3. Connect also your laptop to the same wifi.
4. Use VNC Viewer to connect to you Pi with the IP address you copied.
5. Use the username and password to log into Pi.
6. Start hotspot on your mobile and connect to that with Pi.
7. Use laptop to scan for the new IP address of Pi when connected to your hotspot.
8. Connect also your laptop on hotspot and connect to Pi with VNC viewer.

## Running the program
#### Notes
* The program needs **sudo access** to access the flash drive connected to it, where the recordings are stored.
* The USB is currently not being auto-mounted so **USB needs to be mounted** prior running the program.
* There is executable named launcher.sh that contains the scripts needed for running the program. This executable is **ran every time the Raspberry Pi reboots**. This is controlled in a file located in */home/pi/.config/autorun*.
* Closing the application "clean" works with **ctrl+C**. If for some reason it is not cleanly closed, you need to kill some scripts before starting it up again or otherwise the program will not work correctly. These are written in another executable named killprogram.sh. (Omxplayer is library for playing the video files on screen and if not closed cleanly, the player will stay running in the background.)
* The configurations for the program run instance are set in the file configs.py. Here you can set e.g. which modules and directories to use in the program run.

**Run the program normally from terminal:**
```
sudo mount /dev/sda1 /mnt/kingston
cd /home/pi/sakis-video-tunnel
sudo python3 monkeytunnel.py
```
**Killing the program in terminal:**
```
pkill -9 python3
pkill -9 launcher.sh
killall /usr/bin/omxplayer.bin
```
