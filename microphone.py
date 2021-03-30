import subprocess

class Microphone():

    def __init__(self):
        self.recorder = None

    def record(self, filepath):

        self.recorder = subprocess.Popen(args=["arecord", "--format=S16_LE", "--file-type=wav", filepath], stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

    def stop(self):
        self.recorder.terminate()
