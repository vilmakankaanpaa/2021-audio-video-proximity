# program run settings
TEST_PHASE = '4-worms-video'
USE_AUDIO = False
USE_VIDEO = True
VIDEO_AUDIO_ON = False # audio of the video file
RECORDING_ON = True # record interaction with camera module

# roots
root = '/home/pi/sakis-video-tunnel/'
external_disk = '/mnt/kingston/'

# paths to use
AUDIO_PATH = 'None'
VIDEO_PATH = root + 'video/worms.mp4'
RECORDINGS_PATH = external_disk + 'camera-records/'
RECORDINGS_PATH_2 = root + 'camera-records/'

# local logfile names
local_ix_log = 'ix_backup.csv'
local_sensor_log = 'sensor_backup.csv'
local_program_log = 'progrun_backup.csv'
local_printlog = 'printlog.csv'

# Google sheets API parameters for logging data
DOCNAME = 'Monkey-logs'
IX_SHEET = 'main-logs'
PROGRUN_SHEET = 'prog-run-logs'
SENSOR_SHEET = 'sensor-logs'
PING_SHEET = 'ping-logs'

# Google Drive API parameters for uploading listDriveFiles
GDRIVE_FOLDER_ID = '15-VeIBr0SVHk2_aWBVe_F2UmiXJw0tr7'  #"Recordings"
GDRIVE_FOLDER_ID_LOGS = '1fM7o2FK_5D_PxNM8PCx6b8cfGwPvBY86'  #"Local logs" folder in drive
