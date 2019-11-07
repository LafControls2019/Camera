# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2 as cv

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (1280, 720)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(1280, 720))

time.sleep(0.1)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = frame.array
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    cv.imshow('image', gray)
    key = cv.waitKey(1) & 0xFF
        
    rawCapture.truncate(0)
    rawCapture.seek(0)
        
    if key == ord('q'):
        break

#while(True):
#    camera.capture(rawCapture, format='bgr')
#    frame = rawCapture.array
#    print(frame)
#    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
#    cv.imshow('frame', gray)
#    if cv.waitKey(1) & 0xFF == ord('q'):
#        break
    
cap.release()
cv.destroyAllWindows()