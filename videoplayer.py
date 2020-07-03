#!/usr/bin/env python3

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep
from datetime import datetime
from configs import SCREENSAVER_PATH


# https://python-omxplayer-wrapper.readthedocs.io/en/latest/omxplayer/#module-omxplayer.player
class VideoPlayer():

    def __init__(self, mainVideoPath,  useVideoAudio, screensaverOn):

        # 0 - no video, 1 - video ready, 2 - playing video, 3 - paused, 4 - quit

        self.audio = useVideoAudio
        self.mainVideoPath = mainVideoPath
        self.screensaverPath = SCREENSAVER_PATH
        self.screensaverOn = False
        """
        -o              audio output
        --no-osd        do not show status info on screen
        --aspect-mode   aspect of the video on screen
        --loop          continuously play the video
        """
        if screensaverOn:
            self.player = OMXPlayer(self.screensaverPath, args="-o alsa:hw:1,0 --no-osd --aspect-mode fill --loop")
            self.screensaverOn = True
        else:
            self.player = OMXPlayer(self.mainVideoPath, args="-o alsa:hw:1,0 --no-osd --aspect-mode fill --loop")

        self.status = 2

        if not self.audio:
            self.player.mute()

        self.pauseTimer = None


    def is_playing(self):

        if self.status == 2:
            return True
        else:
            return False

    def screensaver_on(self):
        return self.screensaverOn

    def has_quit(self):
        if self.status == 4:
            return True
        else:
            return False


    def paused_time(self):
        diff = (datetime.now() - self.pauseTimer).total_seconds()
        return diff


    def screensaver(self):
        # pause = True > black screen, no need to be actually playing it...
        self.player.load(self.screensaverPath, pause=True)
        self.screensaverOn = True
        self.status = 3


    def play_video(self):

        if self. screensaverOn:
            self.player.load(self.mainVideoPath, pause=False)
            self.screensaverOn = False
        else:
            self.player.play()
        self.status = 2


    def pause_video(self):
        self.player.pause()
        self.status = 3
        self.pauseTimer = datetime.now()


    def stop_video(self):
        self.player.quit()
        self.status = 4
