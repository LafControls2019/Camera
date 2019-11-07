from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.start_preview(alpha=200)
sleep(10)
camera.stop_preview()