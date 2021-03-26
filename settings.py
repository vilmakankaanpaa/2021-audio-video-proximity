# Global variables

# 0 = no-stimulus, 1 = audio, 2 = video
global testMode
testMode = 1

global usingAudio
global usingVideo
if testMode == 1:
    usingAudio = True
elif testMode == 2:
    usingVideo = True

# use camera to record interactions
global recordingOn
recordingOn = True

# use the audio of the video files
global videoAudio
videoAudio = False

global pid
