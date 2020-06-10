#!/usr/bin/env python3

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep

# 0 - no video, 1 - video ready, 2 - playing video, 3 - paused, 4 - quit
class VideoPlayer():

    def __init__(self, useVideoAudio):
        self.player = None
        self.currentVideoPath = None
        self.audio = useVideoAudio
        self.status = 0

    def _load_video(self, videoPath):
        # load video first to simplify the usage in the code -> does not start playing the video until told so.
        self.currentVideoPath = videoPath

        if self.audio:
            self.player = OMXPlayer(self.currentVideoPath, args="-o alsa:hw:1,0 --loop")
        else:
            self.player = OMXPlayer(self.currentVideoPath, args="--loop")

        self.player.pause()
        self.status = 1

    def _play_video(self):
        self.player.play()
        self.status = 2

    def _pause_video(self):
        self.player.pause()
        self.status = 3

    def _stop_video(self):
        self.player.quit()
        self.status = 4


""" Advcanced:

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep
import logging
logging.basicConfig(level=logging.INFO)


VIDEO_1_PATH = "../tests/media/test_media_1.mp4"
player_log = logging.getLogger("Player 1")

player = OMXPlayer(VIDEO_1_PATH,
        dbus_name='org.mpris.MediaPlayer2.omxplayer1')
player.playEvent += lambda _: player_log.info("Play")
player.pauseEvent += lambda _: player_log.info("Pause")
player.stopEvent += lambda _: player_log.info("Stop")

# it takes about this long for omxplayer to warm up and start displaying a picture on a rpi3
sleep(2.5)

player.set_position(5)
player.pause()


sleep(2)

player.set_aspect_mode('stretch')
player.set_video_pos(0, 0, 200, 200)
player.play()

sleep(5)

player.quit()
"""
