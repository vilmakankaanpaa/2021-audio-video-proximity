# Following instructions here
# https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/4
from picamera import picamera
from time import sleep


class Camera(folderPath):

    self.camera = PiCamera()
    # e.g. "/home/pi/Desktop/"
    self.folderPath = folderPath


    def start_recording(videoName):
        self.camera.start_preview()
        camera.start_recording(self.folderPath + videoName + 'h264')


    def stop_recording():
        camera.stop_recording()
        camera.stop_preview()


    # example code
    def previewCamera():
        # view preview on screen (only works on connected screen)
        self.camera.start_preview()
        sleep(5)
        self.camera.stop_preview()

    # example code
    def capture_image(imageName):

        self.camera.start_preview()
        # Note: it’s important to sleep for at least two seconds
        # before capturing an image, because this gives the camera’s
        # sensor time to sense the light levels.
        sleep(5)
        """TODO: does this work with + ?"""
        self.camera.capture(self.folderPath + imageName + '.jpg')
        self.camera.stop_preview()

    # example code
    def capture_five_images(imageName):
        # looping to take five images and name them with numbers:
        self.camera.start_preview()
        for i in range(5):
            sleep(5)
            self.camera.capture(self.folderPath + imageName + %s +'.jpg' % i)
        self.camera.stop_preview()

    # example code
    def record_five_second_video(videoName):
        # example
        self.camera.start_preview()
        """ TODO: any other form possible? Converter? """
        camera.start_recording(self.folderPath + videoName + 'h264')
        sleep(5)
        camera.stop_recording()
        camera.stop_preview()
