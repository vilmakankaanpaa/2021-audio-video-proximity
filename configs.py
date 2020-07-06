# program run settings
USE_AUDIO = False
USE_VIDEO = True
VIDEO_AUDIO_ON = False # audio of the video file
RECORDING_ON = True # record interaction with camera module

# roots
root = '/home/pi/sakis-video-tunnel/'
external_disk = '/mnt/kingston/'

# paths to use
AUDIO_PATH = 'None'
VIDEO_PATH = root + 'video/test_video_1.mp4'
RECORDINGS_PATH = external_disk + 'camera-records/'
RECORDINGS_PATH_2 = root + 'camera-records/'

# local logfile names
local_fail_log = 'fail_log.csv'
local_ix_log = 'ix_log.csv'
local_sensor_log = 'sensor_log.csv'
local_program_log = 'progrun_log.csv'
local_status_log = 'status_log.csv'

# Google sheets API parameters for logging data
DOCNAME = 'Monkey-logs'
IX_SHEET = 'main-logs'
ALIVE_SHEET = 'alive-logs'
PROGRUN_SHEET = 'prog-run-logs'
SENSOR_SHEET = 'sensor-logs'
STATUS_SHEET = 'status-log'
TEST_PHASE = 'testing'

# Google Drive API parameters for uploading listDriveFiles
GDRIVE_FOLDER_ID = '15-VeIBr0SVHk2_aWBVe_F2UmiXJw0tr7'
GDRIVE_FOLDER_ID_LOGS = '1fM7o2FK_5D_PxNM8PCx6b8cfGwPvBY86'
GDRIVE_USER_EMAIL = 'vilma.kankaanpaa@aalto.fi' # to grant access for yourself for the uploaded file
