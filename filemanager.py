import sys
import os
import csv
import configs


def log_local(data, sheet):
    print('Logging to local file:',sheet)
    with open(sheet, 'a', newline='') as logfile:
        logwriter = csv.writer(logfile, delimiter=',')
        for row in data:
            logwriter.writerow(row)


def delete_local_video(fileName):
    path = configs.RECORDINGS_PATH + fileName
    os.remove(path)
    print('Removed file at', path)


def list_recordings():
    videos = []
    for filename in os.listdir(configs.RECORDINGS_PATH):
        videos.append(filename)
    return videos
