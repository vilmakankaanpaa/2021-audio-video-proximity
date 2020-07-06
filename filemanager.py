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
        dirContent = os.listdir(configs.RECORDINGS_PATH)
        if len(dirContent) == 0:
            print('Size of dir:', len(dirContent))
            # there is nothing in the folder while there should be at least test.txt
            # --> could not read directory
            raise
        for filename in dirContent:
            if filename.endswith('.h256'):
                videos.append(filename)
        pathdir = configs.RECORDINGS_PATH
        
    except:
        dirContent = os.listdir(configs.RECORDINGS_PATH_2)
        for filename in dirContent:
            if filename.endswith('.h256'):
                videos.append(filename)
        pathdir = configs.RECORDINGS_PATH_2

    return videos, pathdir
