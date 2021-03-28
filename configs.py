# Configurations for paths and URLs

# roots
root = '/home/pi/sakis-tunnel-2021/'
external_disk = '/mnt/kingston/'

# paths to use
RECORDINGS_PATH = external_disk + 'camera-records/'
RECORDINGS_PATH_2 = root + 'camera-records/'

# audio files
AUDIO1 = root + 'audio/zen.mp3'
AUDIO2 = root + 'audio/rain.mp3'
AUDIO3 = root + 'audio/traffic.mp3'
AUDIO4 = root + 'audio/music.mp3'
# video files
VIDEO1 = root + 'video/forest.mp4'
VIDEO2 = root + 'video/underwater.mp4'
VIDEO3 = root + 'video/worms.mp4'
VIDEO4 = root + 'video/abstract.mp4'

# local logfile names
local_ix_log = 'ix_backup.csv'
local_sensor_log = 'sensor_backup.csv'
local_program_log = 'progrun_backup.csv'
local_printlog = 'printlog.csv'

# Google sheets API parameters for logging data
SPREADSHEET_ID = '1-sFTPHnKqSMEMJ6mKf0D3lMXn77QECNJbL_vR-Prskg'
IX_SHEET = 'interactions'
STARTS_SHEET = 'system-starts'
SENSORS_SHEET = 'sensor-readings'
PING_SHEET = 'ping-alive'

# Google Drive API parameters for uploading listDriveFiles
GDRIVE_FOLDER_ID = '15-VeIBr0SVHk2_aWBVe_F2UmiXJw0tr7'  #"Recordings"
GDRIVE_FOLDER_ID_LOGS = '1fM7o2FK_5D_PxNM8PCx6b8cfGwPvBY86'  #"Local logs" folder in drive
