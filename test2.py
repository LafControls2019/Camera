import sys

sys.path.append('/usr/local/lib/python3/dist-packages')

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2 as cv
import imutils
from io import BytesIO
import pygame
from collections import OrderedDict
import numpy as np
from scipy.spatial import distance as dist
from neopixel import *

LED_COUNT = 14
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

class ColorLabeler:
    def __init__(self):
        colors = OrderedDict({
            "red":(255, 0, 0),
            "green":(0, 255, 0),
            "blue":(0, 0, 255)
            })
        
        self.lab = np.zeros((len(colors), 1, 3), dtype="uint8")
        self.colorNames = []
        
        for (i, (name, rgb)) in enumerate(colors.items()):
            self.lab[i]
            self.colorNames.append(name)
            
        self.lab = cv.cvtColor(self.lab, cv.COLOR_RGB2LAB)
        #print(self.colorNames)
    
    def label(self, image, c):
        mask = np.zeros(image.shape[:2], dtype="uint8")
        cv.drawContours(mask, [c], -1, 255, -1)
        mask = cv.erode(mask, None, iterations=2)
        mean = cv.mean(image, mask=mask)[:3]
        
        #print(mean)
        
        minDist = (np.inf, None)
        
        for (i, row) in enumerate(self.lab):
            #print(row[0])
            d = dist.euclidean(row[0], mean)
            #print(d)
            if d < minDist[0]:
                    minDist = (d, i)
            
        
        print(minDist)
        return self.colorNames[minDist[1]]

class ShapeDetector:
    def __init__(self):
        pass
    
    def detect(self, c):
        shape = "IDFK"
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.04*peri, True)

        if len(approx) == 3:
            shape = "Triangle"
        elif len(approx) == 4:
            (x, y, w, h) = cv.boundingRect(approx)
            ar = w / float(h)
            shape = "Sqaure" if ar >= 0.95 and ar <= 1.05 else "Rectangle"
        elif len(approx) == 5:
            shape = "Pentagon"
        elif len(approx) == 6:
            shape = "Hexagon"
        else:
            shape = "Circle"
        
        return shape

		
def crop_img(img, scale=1.0):
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x - width_scaled / 2, center_x + width_scaled / 2
    top_y, bottom_y = center_y - height_scaled / 2, center_y + height_scaled / 2
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped
	
		
try:
    # Init LEDs
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(255, 255, 255))
        strip.show()
        time.sleep(0.2)
except:
    print("dickhead")


# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.exposure_mode="fixedfps"
camera.iso = 100
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))
time.sleep(0.1)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = crop_img(frame.array, scale=0.5)
    blurred = cv.GaussianBlur(image, (31,31), 0)
    
    image_gray = cv.cvtColor(blurred, cv.COLOR_BGR2GRAY)
    image_lab = cv.cvtColor(blurred, cv.COLOR_BGR2LAB)
    
    threshold = cv.threshold(image_gray, 60, 80, cv.THRESH_BINARY)[1]
    cv.imshow("Image", image)
	
    #cv.imshow('image', image_gray)
    key = cv.waitKey(1) & 0xFF
    
    
    #cv.imshow("Gray", image_gray)
    #cv.imshow("Blurred", blurred)

    cnts = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    sd = ShapeDetector()
    cl = ColorLabeler()

    #print(len(cnts))
    for c in cnts:
        try:
            M = cv.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            shape = sd.detect(c)
            try:
                color = cl.label(image_lab, c)
            except TypeError:
                color = "Error"
            
            area = cv.contourArea(c)
            perimeter = cv.arcLength(c,True)
            relativearea = str(area/perimeter)

            cv.drawContours(image, [c], -1, (0,255,0), 2)
            cv.circle(image, (cX, cY), 7, (255, 255, 255), -1)
            cv.putText(image, shape, (cX - 20, cY - 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv.putText(image, str(area), (cX - 20, cY - 40), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv.putText(image, color, (cX - 20, cY - 60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv.imshow("ImageDect", image)
        except ZeroDivisionError:
            pass
    
    rawCapture.truncate(0)
    rawCapture.seek(0)
        
    if key == ord('q'):
        break

