import sys
import os
import csv
import configs

sys.excepthook = sys.__excepthook__

def log_local(data, sheet):
    print('Logging to local file:',sheet)
    with open(sheet, 'a', newline='') as logfile:
        logwriter = csv.writer(logfile, delimiter=',')
        for row in data:
            logwriter.writerow(row)

def delete_local_video(fileName):
    records, pathdir = list_recordings()
    try:
        index = records.index(fileName)
    except:
        print('Cannot remove local file: no such file.')
        return

    path = pathdir + fileName
    os.remove(path)
    print('Removed file at', path)

def list_recordings():
    videos = []
    pathdir = None
    try:
        for filename in os.listdir(configs.RECORDINGS_PATH):
            videos.append(filename)
            pathdir = configs.RECORDINGS_PATH
    except:
        for filename in os.listdir(configs.RECORDINGS_PATH_2):
            videos.append(filename)
            pathdir = configs.RECORDINGS_PATH_2

    return videos, pathdir
