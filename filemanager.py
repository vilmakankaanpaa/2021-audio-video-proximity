import sys
import os
import csv
import shutil
from datetime import datetime
import configs

sys.excepthook = sys.__excepthook__

def log_local(data, sheet):
    print(datetime.isoformat(datetime.now()),'Logging to local file:',sheet)
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
    
    print('Listing recordings..')

    try:
        dirContent = os.listdir(configs.RECORDINGS_PATH)
        if len(dirContent) == 0:
            # there is nothing in the folder while there should be at least test.txt
            # --> could not read directory
            raise
        for filename in dirContent:
            print('Size of dir:', len(dirContent))
            if filename.endswith('.h264'):
                videos.append(filename)
        pathdir = configs.RECORDINGS_PATH
        
    except:
        dirContent = os.listdir(configs.RECORDINGS_PATH_2)
        for filename in dirContent:
            if filename.endswith('.h264'):
                videos.append(filename)
        pathdir = configs.RECORDINGS_PATH_2
    
    print(datetime.isoformat(datetime.now()), 'Path for videos:', pathdir)
    print(datetime.isoformat(datetime.now()),'Videos:', videos)

    return videos, pathdir


def check_disk_space(disk):
    total, used, free = shutil.disk_usage(disk)

    print("Total: %d GiB" % (total // (2**30)))
    print("Used: %d GiB" % (used // (2**30)))
    print("Free: %d GiB" % (free // (2**30)))
    
    relative = free/total
    
    return round(relative, 2)