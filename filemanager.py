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

def delete_local_file(path):

    if os.path.exists(path):
        os.remove(path)
        print('Removed file at', path)
    else:
        print('Could not delete local file at {}, it does not exist'.format(path))

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

def nof_recordings():

    try:
        dirContent = os.listdir(configs.RECORDINGS_PATH)
        if len(dirContent) == 0:
            raise
        else:
            # there is one file for testing in the folder: test.txt, hence -1
            return len(dirContent)-1
    except:
        dirContent = os.listdir(configs.RECORDINGS_PATH_2)

    return len(dirContent)


def check_usb_disk_access():
    # can e.g. check whether usb is connected via if you can access the test.txt init
    pathdir = None
    path = configs.RECORDINGS_PATH + 'test.txt'
    print('Checking if path exists:', path)
    exists = os.path.exists(path)
    print(exists)
    return exists


def get_directory_for_recordings():
    usb = check_usb_disk_access()
    if usb:
        return configs.RECORDINGS_PATH
    return configs.RECORDINGS_PATH_2


def check_disk_space(disk):
    total, used, free = shutil.disk_usage(disk)

    print("Total: %d GiB" % (total // (2**30)))
    print("Used: %d GiB" % (used // (2**30)))
    print("Free: %d GiB" % (free // (2**30)))

    relative = free/total

    return round(relative, 2)
