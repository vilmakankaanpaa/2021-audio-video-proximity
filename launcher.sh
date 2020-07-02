#!/bin/sh
# launcher.sh
# go to home, then here, then execute python script, then back home

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

cd /
cd home/pi/sakis-video-tunnel
python3 monkeytunnel.py >> output.txt
cd /
