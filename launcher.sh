#!/bin/sh
# launcher.sh

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

# mount usb stick here - automatic mounting did not ...
# ...work for getting permissions for python
# sudo mount /dev/sda1 /home/pi/sakis-video-tunnel/USB

# kill omxplayer from previous run if on!
killall "omxplayer.bin"
pkill -9 python3

cd /
cd home/pi/sakis-video-tunnel
python3 monkeytunnel.py >> output.txt
cd /

