import sys
import os
import csv
import shutil
from datetime import datetime

# Local source
import configs

sys.excepthook = sys.__excepthook__

def printlog(srcfile, msg):

    print(msg)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = [[timestamp, srcfile, msg]]

    log_local(data=data, sheet=configs.local_printlog)


def log_local(data, sheet):
    
    with open(sheet, 'a', newline='') as logfile:
        logwriter = csv.writer(logfile, delimiter=',')
        for row in data:
            logwriter.writerow(row)


def delete_local_file(path):

    if os.path.exists(path):
        os.remove(path)
    else:
        printlog('Filemanager','Could not delete local file at {}, it does not exist'.format(path))


def list_recordings():
    videos = []
    pathdir = None

    try:
        dirContent = os.listdir(configs.RECORDINGS_PATH)
        if len(dirContent) == 0:
            # there is nothing in the folder while there should be at least test.txt
            # --> could not read directory
            raise
        for filename in dirContent:
            if filename.endswith('.h264'):
                videos.append(filename)
        pathdir = configs.RECORDINGS_PATH

    except:
        printlog('Filemanager','ERROR – Setting recordings folder to Pi local!')
        dirContent = os.listdir(configs.RECORDINGS_PATH_2)
        for filename in dirContent:
            if filename.endswith('.h264'):
                videos.append(filename)
        pathdir = configs.RECORDINGS_PATH_2

    return videos, pathdir


def nof_recordings():

    try:
        
        dirContent = os.listdir(configs.RECORDINGS_PATH)
        if len(dirContent) == 0:
            raise
        else:
            # there is one file for testing in the folder: test.txt, hence -1
            printlog('Filemanager','No. of recordings in {} is {}.'.format(
                configs.RECORDINGS_PATH, (len(dirContent)-1)))
            return len(dirContent)-1
    except:
        dirContent = os.listdir(configs.RECORDINGS_PATH_2)

    printlog('Filemanager','No. of recordings in {} is {}.'.format(
                configs.RECORDINGS_PATH_2, len(dirContent)))
    
    return len(dirContent)


def check_usb_disk_access():
    # can e.g. check whether usb is connected via if you can access the test.txt init
    pathdir = None
    path = configs.RECORDINGS_PATH + 'test.txt'
    exists = os.path.exists(path)
    return exists


def get_directory_for_recordings():
    usb = check_usb_disk_access()
    if usb:
        return configs.RECORDINGS_PATH
    return configs.RECORDINGS_PATH_2


def check_disk_space(disk):
    total, used, free = shutil.disk_usage(disk)

    #print("Total: %d GiB" % (total // (2**30)))
    #print("Used: %d GiB" % (used // (2**30)))
    #print("Free: %d GiB" % (free // (2**30)))

    relative = free/total

    return round(relative, 2)
