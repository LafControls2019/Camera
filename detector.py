# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2 as cv
import imutils
from io import BytesIO
from collections import OrderedDict
import numpy as np
from scipy.spatial import distance as dist
import RPi.GPIO as GPIO
import queue
import threading

def shapeDetect(area, xValue):
    if(xValue > 125 and xValue < 220):
        if(area > 11300 and area < 12450):
            shape = "Orange Sqaure"
        elif(area > 33000 and area < 36100):
            shape = "Yellow Hexagon"
        elif(area > 13500 and area < 16100):
            shape = "Red Trapezoid"
        elif(area > 9500 and area < 11000):
            shape = "Blue Rhombus"
        elif(area > 8300 and area < 9250):
            shape = "White Thing"
        elif(area > 4200 and area < 5700):
            shape = "Green Triangle"
        # elif(area > 2000): ## Ignore small parts of the belt
        #   shape = "Unkown!"
        else:
            shape = None
    else:
        shape = "Not in Zone"
        
    
    return shape

def crop_img(img, scale=1.0):
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x - width_scaled / 2, center_x + width_scaled / 2
    top_y, bottom_y = center_y - height_scaled / 2, center_y + height_scaled / 2
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


def sorter():
    while True:
        try:
            block = blockQueue.get()
            # print("Popped Queue!")
            if(block != None):
                while True:
                    if(time.time() - block[1] > 0.25):
                        writeToThing(block[0])
                        break
                blockQueue.task_done()
        except:
            print("Empty!")


def writeToThing(shape):
    if(shape == "Orange Sqaure"): # 1
        GPIO.output(21, 0) #2nds
        GPIO.output(13, 0) #1sts
        GPIO.output(26, 1) #0s
    elif(shape == "Yellow Hexagon"): # 2
        GPIO.output(21, 0)
        GPIO.output(13, 1)
        GPIO.output(26, 0)
    elif(shape == "Red Trapezoid"): # 4
        GPIO.output(21, 1)
        GPIO.output(13, 0)
        GPIO.output(26, 0)
    elif(shape == "Blue Rhombus"): # 6
        GPIO.output(21, 1)
        GPIO.output(13, 1)
        GPIO.output(26, 0)
    elif(shape == "White Thing"): # 0
        GPIO.output(21, 0)
        GPIO.output(13, 0)
        GPIO.output(26, 0)
    elif(shape == "Green Triangle"): # 5
        GPIO.output(21, 1)
        GPIO.output(13, 0)
        GPIO.output(26, 1)
    # else:                          # 3
        # GPIO.output(21, 0)
        # GPIO.output(13, 1)
        # GPIO.output(26, 1)

GPIO.setmode(GPIO.BCM)

GPIO.setup(27, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.exposure_mode="fixedfps"
camera.iso = 100
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))
time.sleep(0.1)


blockQueue = queue.Queue()
sorterThread = threading.Thread(target=sorter).start()

# nullFrameCount = 0

try:
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # if nullFrameCount > 200:
        #     nullFrameCount = 0
        #     GPIO.output(27, 1)
        #     print("belt on")
        # else:
        #     nullFrameCount+=1

        image = crop_img(frame.array, scale=0.5)
        blurred = cv.GaussianBlur(image, (31,31), 0)
        
        image_gray = cv.cvtColor(blurred, cv.COLOR_BGR2GRAY)
        image_lab = cv.cvtColor(blurred, cv.COLOR_BGR2LAB)
        
        threshold = cv.threshold(image_gray, 60, 80, cv.THRESH_BINARY)[1]
        cv.imshow("Image", image)
        
        key = cv.waitKey(1) & 0xFF
        
        cnts = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    
        #print(len(cnts))
        for c in cnts:
            try:
                M = cv.moments(c)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                area = cv.contourArea(c)
                shape = shapeDetect(area, cX)
                if shape:
                    blockQueue.put([shape, time.time()])

                cv.drawContours(image, [c], -1, (0,255,0), 2)
                cv.circle(image, (cX, cY), 7, (255, 255, 255), -1)
                cv.putText(image, shape, (cX - 20, cY - 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv.putText(image, str(area), (cX - 20, cY - 40), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv.putText(image, "X="+str(cX)+" | Y="+str(cY), (cX - 20, cY - 60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv.imshow("ImageDect", image)
            except ZeroDivisionError:
                pass
        
        rawCapture.truncate(0)
        rawCapture.seek(0)
            
        if key == ord('q'):
            break
except:
    GPIO.cleanup()
