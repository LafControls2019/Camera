import cv2 as cv
import numpy as np
import imutils
from gtts import gTTS
from io import BytesIO
import pygame

from pydub import AudioSegment
from pydub.playback import play


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
            shape = "PentaGONE"
        elif len(approx) == 6:
            shape = "HexaBONG"
        else:
            shape = "Circle"
        
        return shape



image = cv.imread("blocks_black.jpg")
image_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

cv.imshow("Gray", image_gray)

blurred = cv.GaussianBlur(image_gray, (31,31), 0)
cv.imshow("Blurred", blurred)

threshold = cv.threshold(blurred, 40, 150, cv.THRESH_BINARY)[1]

cnts = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]
sd = ShapeDetector()

print(len(cnts))
for c in cnts:
    try:
        M = cv.moments(c)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        shape = sd.detect(c)

        cv.drawContours(image, [c], -1, (0,255,0), 2)
        cv.circle(image, (cX, cY), 7, (255, 255, 255), -1)
        cv.putText(image, shape, (cX - 20, cY - 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        voice = BytesIO()
        tts = gTTS(shape, 'en')
        tts.write_to_fp(voice)
        sound = AudioSegment.from_file(voice, format="mp3")
        play(sound)

        cv.imshow("Image", image)
        cv.waitKey(0)
    except ZeroDivisionError:
        pass