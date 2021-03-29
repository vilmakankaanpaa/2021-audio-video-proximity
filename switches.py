#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
from datetime import datetime
from filemanager import printlog, get_directory_for_recordings
from audioplayer import AudioPlayer
from videoplayer import VideoPlayer
import globals
import configs


class Switches():

    def __init__(self, logger, camera):

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
        GPIO.add_event_detect(22, GPIO.BOTH, callback=self.react)
        GPIO.add_event_detect(23, GPIO.BOTH, callback=self.react)
        GPIO.add_event_detect(24, GPIO.BOTH, callback=self.react)
        GPIO.add_event_detect(25, GPIO.BOTH, callback=self.react)

        # GPIO channels of the switches on RPI
        self.channels = {22:0, 23:1, 24:2, 25:3}
        self.switchesOpen = [False, False, False, False]
        self.switchPlaying = None
        self.queue = None
        self.second_queue = None # for rare cases of X is changed to Y but X is still kept open: when Y closes, X should be put back
        self.starttime = None
        self.endtime = None
        self.delay = 3 # seconds

        self.logger = logger
        self.camera = camera
        self.audioPlayer = AudioPlayer()
        self.videoPlayer = None


    def react(self, channel):
    # Called when one of the four switches is triggered

        switch = self.channels.get(channel)

        if GPIO.input(channel) == GPIO.HIGH:
            self.switchesOpen[switch] = True
            printlog('Switches','Switch {} open.'.format(switch))

            # Set switch always on queue first to start playing next
            if switch != self.switchPlaying:
                self.queue = switch

        else:
            self.switchesOpen[switch] = False
            printlog('Switches','Switch {} closed.'.format(switch))

            if switch == self.queue:
                # when switch was on queue but it closes before getting to play
                self.queue = None


    def delayPassed(self):
    # Check if delay for starting/stopping/changing media has passed

        playtime = round((datetime.now() - self.starttime).total_seconds(),2)
        if playtime > self.delay:
            return True
        else:
            return False


    def turnOn(self):
    # Turn media on

        self.starttime = datetime.now()
        self.endtime = None

        if self.queue != None:
            self.switchPlaying = self.queue
            self.queue = None
        else:
            self.switchPlaying = self.second_queue
            self.second_queue = None

        # New interaction starts whenever new media turns on
        self.logger.log_interaction_start(self.switchPlaying)
        printlog('Switches','Interaction started,')

        # Start recording
        if globals.recordingOn and not self.camera.is_recording:
            file = self.logger.new_recording_name()
            directory = get_directory_for_recordings()
            self.camera.start_recording(file, directory)
            printlog('Switches','Starting to record.')

        filename = globals.mediaorder[self.switchPlaying]
        if globals.usingAudio:
            printlog('Switches','Playing audio {}.'.format(filename))
            filepath = configs.audiopath + filename + '.mp3'
            if self.audioPlayer.has_quit():
                self.audioPlayer = AudioPlayer()
            self.audioPlayer.play_audio(filepath)

        elif globals.usingVideo:
            printlog('Switches','Playing video {}.'.format(filename))
            filepath = configs.videopath + filename + '.mp4'
            self.videoPlayer = VideoPlayer(filepath, globals.videoAudio)

        else:
            # no stimulus
            pass


    def turnOff(self):
    # Turn media off

        self.endtime = datetime.now()
        self.logger.log_interaction_end(self.endtime,)
        printlog('Switches','Interaction ended.')

        if self.audioPlayer.is_playing():
            printlog('Switches','Turning audio off.'.format(self.switchPlaying))
            self.audioPlayer.stop()

        if self.videoPlayer != None:
            printlog('Switches','Turning video off.'.format(self.switchPlaying))
            if self.videoPlayer.is_playing():
                self.videoPlayer.stop_video()
                self.videoPlayer = None

        self.starttime = None
        self.switchPlaying = None


    def changeSwitch(self):
    # For cases when switch X is palying but the switch Y will be turned on.
        changedSwitch = self.switchPlaying

        self.turnOff()
        self.turnOn()

        if self.switchesOpen[changedSwitch]:
            # switch that was turned off is still open
            self.second_queue = changedSwitch


    def updateSwitches(self):

    # 1. Swithc on queue but no switches playing media
    #       -> Turn on
    # 2. Switch on queue but already playing
    #       -> Do nothing / don't add on the queue
    # 3. Switch on queue but another one playing
    #       -> Check if delay has passed -> leave to queue or start playing
    # 4. No queue, delay passed, switch still open -> keep playing
    # 5. All switches closed but one is playing
    #       -> Check if delay has passed -> continue or stop playing

        if self.switchPlaying == None:
            # media is not currently playing
            if self.queue != None:
                # Turn new switch on
                self.turnOn()
        else:
            # media is currently playing
            if self.queue != None:
                if self.delayPassed():
                    self.changeSwitch()
            else:
                # queue is empty
                if not any(self.switchesOpen):
                    # all switches closed too
                    if self.delayPassed():
                        self.turnOff()
                else:
                    # either the switch currently playing is open or another one
                        # another one must be in second_queue
                    if not self.switchesOpen[self.switchPlaying] and self.second_queue != None:
                        # the switch playing is not open anymore, but another switch is
                        self.changeSwitch()
                    else:
                        # the switch playing is still open, don't turn off
                        pass
