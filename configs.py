# program run settings
USE_AUDIO = False
USE_VIDEO = True
VIDEO_AUDIO_ON = False # audio of the video file
RECORDING_ON = True # record interaction with camera module

# files to use
AUDIO_PATH = 'None'
VIDEO_PATH = 'video/test_video_1.mp4'
RECORDINGS_PATH = 'USB/camera-records/'
RECORDINGS_PATH_2 = 'camera-records/'
SCREENSAVER_PATH = 'video/black.mp4'

# Google sheets API parameters for logging data
DOCNAME = 'Monkey-logs'
IX_SHEET = 'main-logs'
ALIVE_SHEET = 'alive-logs'
PROGRUN_SHEET = 'prog-run-logs'
SENSOR_SHEET = 'sensor-logs'
TEST_PHASE = 'testing'

# Google Drive API parameters for uploading listDriveFiles
GDRIVE_FOLDER_ID = '15-VeIBr0SVHk2_aWBVe_F2UmiXJw0tr7'
GDRIVE_USER_EMAIL = 'vilma.kankaanpaa@aalto.fi' # to grant access for yourself for the uploaded file
