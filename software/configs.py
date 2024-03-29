# -*- coding: utf-8 -*-
#!/usr/bin/env python3

# Configurations for paths and URLs

# roots
root = '/home/pi/sakis-tunnel-2021-distance/'
external_disk = '/media/pi/KINGSTON2/'

# paths to use
RECORDINGS_PATH = external_disk + 'camera-records/'
RECORDINGS_PATH_2 = root + 'camera-records/'
MIC_RECORDINGS = root + 'mic-records/'

# file names
audiopath = root + 'audio/'
# use 'configs.audiopath' + audioX + '.mp3'
#audio1 = 'zen'
audio1 = 'rain'
audio2 = 'traffic'
audio3 = 'music'
# video files
videopath = root + 'video/'
# use 'configs.videopath' + audioX + '.mp4'
#video1 = 'forest'
video1 = 'underwater'
video2 = 'worms'
video3 = 'abstract'
video5 = 'black'

# local logfile names
local_ix_log = 'ix_backup.csv'
local_program_log = 'progrun_backup.csv'
local_printlog = 'printlog.csv'
local_output = 'output.txt'
# To store file names not being able to upload
local_uploadlog = "uploadlog.txt"
local_mic_uploadlog = "mic_uploadlog.txt"

# Google sheets API parameters for logging data
SPREADSHEET_ID = '1-sFTPHnKqSMEMJ6mKf0D3lMXn77QECNJbL_vR-Prskg'
IX_SHEET = 'interactions'
STARTS_SHEET = 'system-starts'
PING_SHEET = 'ping-alive'
SYSTEM_SHEET = 'system-status'

# Google Drive API parameters for uploading listDriveFiles
GDRIVE_FOLDER_ID = '1F-kDuVRUCY_HZTpls-HjgoMZfQsHHsFy'  #recordings
GDRIVE_FOLDER_ID_LOGS = '1ZhqiXGb0yIBRg-h_UlASro2tIVav0YmO'  #system logs

service_account_file = '/home/pi/sakis-tunnel-2021-distance/service_account.json'
