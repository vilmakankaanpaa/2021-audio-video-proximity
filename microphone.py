import subprocess

class Microphone():

    def __init__(self):
        self.recorder = None

    def start_microphone(self, filename):

        self.recorder = subprocess.Popen(args=["arecord", "--format=S16_LE", "--rate=2500", "--file-type=wav", filename])

    def stop_microphone(self):
        self.recorded.terminate()
