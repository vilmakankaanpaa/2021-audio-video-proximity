import subprocess

class Microphone():

    def __init__(self):
        self.recorder = None
        self.is_recording = False

    def record(self, filepath):

        if not self.is_recording:
            self.recorder = subprocess.Popen(args=["arecord", "--format=S16_LE", "--file-type=wav", filepath + ".wav"], stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.is_recording = True

    def stop(self):
        if self.is_recording:
            self.recorder.terminate()
            self.is_recording = False
