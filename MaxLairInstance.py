#   MaxLairInstance
#       Eric Donders
#       2020-11-20

import cv2, time, pytesseract

class MaxLairInstance():
    def __init__(self, boss, balls, com, cap):
        self.t0 = time.time()
        self.timer = self.t0
        self.substage = 0

        self.pokemon = None
        self.HP = 100
        self.num_caught = 0
        
        self.boss = boss
        self.balls = balls
        self.runs = 0
        self.wins = 0

        self.text = ''
        self.cap = cap
        self.com = com

    def read_text(self, section=(0,1,0,1)):
        """Read text from a section (default entirety) of an image using Tesseract."""
        img = cv2.cvtColor(self.get_frame(), cv2.COLOR_BGR2HSV)
        height, width, channels = img.shape
        img = img[round(height*section[0]):round(height*section[1]), round(width*section[2]):round(width*section[3])]
        img = cv2.inRange(img, (0,0,150), (180,15,255))
        cv2.imshow('Thresholded', img)

        self.text = pytesseract.image_to_string(img, lang='eng')
        return self.text

    def check_shiny(self):
        """Detect whether a Pokemon is shiny by looking for the icon in the summary screen."""
        img = cv2.cvtColor(self.get_frame(), cv2.COLOR_BGR2HSV)
        height, width, channels = img.shape
        img = img[round(0.53*height):round(0.58*height), round(0.09*width):round(0.12*width)]
        measured_value = cv2.inRange(img, (0,100,0), (180,255,255)).mean()
        #cv2.imshow('Shiny area', cv2.inRange(img, (0,100,0), (180,255,255)))
        #print(measured_value)
        if measured_value > 1:
            return True
        else:
            return False
        
    def reset_stage(self):
        """Reset to substage 0 and timer at current time."""
        self.timer = time.time()
        self.substage = 0

    def reset_run(self):
        """Reset in preparation for a new Dynamax Adventure"""
        self.t0 = time.time()
        self.timer = self.t0
        self.substage = 0
        self.pokemon = None
        self.HP = 100
        self.num_caught = 0
        self.text = ''
    def get_frame(self, resolution=(1280,720)):
        """Get a scaled and annotated image of the current Switch output"""
        ret, img = self.cap.read()
        img = cv2.resize(img, resolution)
        height, width, channels = img.shape
        cv2.rectangle(img, (round(0.09*width)-2,round(0.53*height)-2), (round(0.12*width)+2,round(0.58*height)+2), (0,255,0), 2)
        return img
        
