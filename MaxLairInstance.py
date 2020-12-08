#   MaxLairInstance
#       Eric Donders
#       2020-11-20

import cv2, time, pytesseract, enchant
from datetime import datetime

class MaxLairInstance():
    def __init__(self, boss, balls, com, cap, datetime):
        self.reset_run()
        
        self.start_date = datetime
        self.filename = ''.join(('Logs//',boss,'_',datetime.strftime('%Y-%m-%d %H-%M-%S'),'_log.txt'))
        self.boss = boss
        self.balls = balls
        self.runs = 0
        self.wins = 0

        # Video capture and serial communication objects
        self.cap = cap
        self.com = com

        self.resolution = (1280, 720)

        # Rectangles for checking shininess and reading specific text
        self.shiny_rect = ((0.09,0.53), (0.12,0.58))
        self.sel_rect_1 = ((0.48,0.29), (0.60,0.34))
        self.sel_rect_2 = ((0.48,0.54), (0.60,0.59))
        self.sel_rect_3 = ((0.48,0.79), (0.60,0.84))
        self.sel_rect_4 = ((0.48,0.57), (0.60,0.63))
        self.sel_rect_5 = ((0.46,0.37), (0.58,0.42))


    def reset_run(self):
        """Reset in preparation for a new Dynamax Adventure"""
        self.reset_stage()
        self.pokemon = None
        self.HP = 1 # 1 = 100%
        self.num_caught = 0
        
    def reset_stage(self):
        """Reset to substage 0 and timer at current time."""
        self.timer = time.time()
        self.substage = 0
        self.move_index = 0
        self.dmax_timer = -1
        self.opponent = None
        

    def get_frame(self, resolution=(1280,720), stage=''):
        """Get a scaled and annotated image of the current Switch output"""
        ret, img = self.cap.read()
        img = cv2.resize(img, resolution)

        # Draw rectangles around detection areas
        h, w, channels = img.shape
        if stage == 'select_pokemon':
            cv2.rectangle(img, (round(self.shiny_rect[0][0]*w)-2,round(self.shiny_rect[0][1]*h)-2),
                          (round(self.shiny_rect[1][0]*w)+2,round(self.shiny_rect[1][1]*h)+2), (0,255,0), 2)
        elif stage == 'join':
            cv2.rectangle(img, (round(self.sel_rect_1[0][0]*w)-2,round(self.sel_rect_1[0][1]*h)-2),
                          (round(self.sel_rect_1[1][0]*w)+2,round(self.sel_rect_1[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.sel_rect_2[0][0]*w)-2,round(self.sel_rect_2[0][1]*h)-2),
                          (round(self.sel_rect_2[1][0]*w)+2,round(self.sel_rect_2[1][1]*h)+2), (0,255,0), 2)
            cv2.rectangle(img, (round(self.sel_rect_3[0][0]*w)-2,round(self.sel_rect_3[0][1]*h)-2),
                          (round(self.sel_rect_3[1][0]*w)+2,round(self.sel_rect_3[1][1]*h)+2), (0,255,0), 2)
        elif stage == 'catch':
            cv2.rectangle(img, (round(self.sel_rect_4[0][0]*w)-2,round(self.sel_rect_4[0][1]*h)-2),
                          (round(self.sel_rect_4[1][0]*w)+2,round(self.sel_rect_4[1][1]*h)+2), (0,255,0), 2)
        elif stage == 'battle':
            cv2.rectangle(img, (round(self.sel_rect_5[0][0]*w)-2,round(self.sel_rect_5[0][1]*h)-2),
                          (round(self.sel_rect_5[1][0]*w)+2,round(self.sel_rect_5[1][1]*h)+2), (0,255,0), 2)

        # Return the scaled and annotated image
        return img


    def read_text(self, section=((0,0),(1,1)), threshold=True, invert=False, language='eng', segmentation_mode='--psm 11', img=None):
        """Read text from a section (default entirety) of an image using Tesseract."""
        # Image is optionally supplied, usually when multiple text areas must be read so the image only needs to be fetched once
        if img is None:
            img = self.get_frame()

        # Process image according to instructions
        h, w, channels = img.shape
        if threshold:
            img = cv2.inRange(cv2.cvtColor(img, cv2.COLOR_BGR2HSV), (0,0,100), (180,15,255))
        if invert:
            img = cv2.bitwise_not(img)
        img = img[round(section[0][1]*h):round(section[1][1]*h),
                  round(section[0][0]*w):round(section[1][0]*w)]
        #cv2.imshow('Text Area', img) # DEBUG

        # Read text using Tesseract and return the raw text
        text = pytesseract.image_to_string(img, lang=language, config=segmentation_mode)
        return text

    def read_selectable_pokemon(self, stage):
        """Return a list of available Pokemon names."""
        # Fetch the image from the Switch output
        image = self.get_frame()

        # Get a list of Pokemon names present, depending on stage
        pokemon_names = []
        if stage == 'join':
            pokemon_names.append(self.read_text(self.sel_rect_1, threshold=False, invert=True, language=None, segmentation_mode='--psm 8', img=image).strip())
            pokemon_names.append(self.read_text(self.sel_rect_2, threshold=False, language=None, segmentation_mode='--psm 8', img=image).strip())
            pokemon_names.append(self.read_text(self.sel_rect_3, threshold=False, language=None, segmentation_mode='--psm 3', img=image).strip()) # This last name shifts around between runs necessitating a bigger rectangle and different text segmentation mode
        elif stage == 'catch':
            pokemon_names.append(self.read_text(self.sel_rect_4, threshold=False, language=None, segmentation_mode='--psm 3', img=image).strip().split('\n')[-1])
        elif stage == 'battle':
            pokemon_names.append(self.read_text(self.sel_rect_5, threshold=True, invert=True, segmentation_mode='--psm 8', img=image).strip())
        print(pokemon_names) # DEBUG

        # Return the list of Pokemon names
        return pokemon_names
    
    def check_shiny(self):
        """Detect whether a Pokemon is shiny by looking for the icon in the summary screen."""
        # Fetch, crop, and threshold image so the red shiny star will appear white and everything else appears black
        img = cv2.cvtColor(self.get_frame(), cv2.COLOR_BGR2HSV)
        h, w, channels = img.shape
        shiny_area = img[round(self.shiny_rect[0][1]*h):round(self.shiny_rect[1][1]*h),
                         round(self.shiny_rect[0][0]*w):round(self.shiny_rect[1][0]*w)]
        # Measure the average value in the shiny star area
        measured_value = cv2.inRange(shiny_area, (0,100,0), (180,255,255)).mean()
        #cv2.imshow('Shiny area', cv2.inRange(shiny_area, (0,100,0), (180,255,255)))
        #print(measured_value)
        if measured_value > 1: # The shiny star results in a measured_value greater than 10
            return True
        else:
            return False

    def log(self, string=''):
        """Print a string to the log file with a timestamp."""
        with open(self.filename, 'a') as file:
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\t'+string+'\n')
        print(string)
        

        
