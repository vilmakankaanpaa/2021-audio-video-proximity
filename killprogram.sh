#!/bin/sh

pkill -9 python3
pkill -9 launcher.sh
killall "omxplayer.bin"

# in python:
#import os

#def kill_running_programs():

#  os.system('pkill -9 python3')
#  os.system('pkill -9 launcher.sh')
#  os.system('killall \"omxplayer.bin\"')
