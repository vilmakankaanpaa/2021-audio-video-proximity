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


def list_local_files(directory):
    for root, dirs, files in os.walk('./' + directory):
        for filename in files:
            print(filename)
