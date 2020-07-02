import os

def sleepscreen(on):
    # shows black image
    if on:
        os.system("fbi -a black.jpg")
    if not on:
        os.system("pkill fbi")
        
