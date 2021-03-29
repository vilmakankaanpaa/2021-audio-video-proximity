# -*- coding: utf-8 -*-

# Configurations for paths and URLs

# roots
root = '/home/pi/sakis-tunnel-2021/'
external_disk = '/media/pi/KINGSTON1/'

# paths to use
RECORDINGS_PATH = external_disk + 'camera-records/'
RECORDINGS_PATH_2 = root + 'camera-records/'

# file names
audiopath = root + 'audio/'
# use 'configs.audiopath' + audioX + '.mp3'
audio1 = 'zen'
audio2 = 'rain'
audio3 = 'traffic'
audio4 = 'music'
# video files
videopath = root + 'video/'
# use 'configs.videopath' + audioX + '.mp4'
video1 = 'forest'
video2 = 'underwater'
video3 = 'worms'
video4 = 'abstract'

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
GDRIVE_FOLDER_ID = '1F-kDuVRUCY_HZTpls-HjgoMZfQsHHsFy'  #recordings
GDRIVE_FOLDER_ID_LOGS = '1ZhqiXGb0yIBRg-h_UlASro2tIVav0YmO'  #system logs
