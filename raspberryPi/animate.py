#print SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import re
import sys
import os
import threading
import random
from datetime import datetime, timedelta
from time import sleep
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from gpiozero import CPUTemperature

# import local modules
from apa102 import APA102

sys.path.insert(0, '..')
from globals import STATE
from config import cf
from error_handling import *
LogInfo("LED Display Loading...")

class Screen:
    display = 0
    picts = {}
    displayPicts = []
    blackPict = 0
    state = 'active'
    _message = False
    def __init__(self):

        # Create the I2C interface.
        i2c = busio.I2C(SCL, SDA)

        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

        # Clear display.
        self.disp.fill(0)
        self.disp.show()

        # laod the images
        self.blackPict = image = Image.new("1", (128, 64))
        filelist = os.listdir("./frames")
        filelist.sort()
        for file in filelist:
             if re.search(r"^face_(.*)ppm$", file):
                 try:
                     (func) = re.compile("^face_([a-z]*)[0-9]+.ppm$").match(file).groups()
                     if func[0]:
                         if not func[0] in self.picts:
                             self.picts[func[0]] = []
                         self.picts[func[0]].append(Image.open('./frames/'+file).convert("1"))
                 except Exception as e:
                     LogError("Error loading file {file}: {str(e)}")
         # init initial pict
        self.displayPicts = self.picts[self.state]

    def AnimateThread(self):

        frame = 0
        x = 0
        y= 0
        width = self.disp.width
        height = self.disp.height
        draw = 0
        eyeWidth = 22
        pupilSize = 5
        eyeL = 20
        eyeR = 86
        eyeY = 3
        eyeHeight=30
        movX = 1
        movY = 1
        locx = 0
        locy = 0

        # Load default font.
        font = ImageFont.load_default()
        dt = datetime.now() + timedelta(seconds=-1)
        real_fps = 0
        LogInfo(f"Animate Thread started")
        while not self.state=='Quit':
            last_fps = round(1000000/(datetime.now()-dt).microseconds)
            dt = datetime.now()
            try:
                # Turn off display in idle/sleep state, or show tracking
                if self.state == 'Idle':
                    if STATE.CheckState('SleepState'):
                        self.disp.fill(0)
                        self.disp.show()
                        sleep(max((1/cf.g('FPS')) - (datetime.now()-dt).microseconds/1000000, 0))
                        continue
                    elif random.randint(0, cf.g('FPS')*5) == 1 or STATE.CheckState('Idle'):
                        self.displayPicts = self.picts['blinking']

                    else:
                        if STATE.cx > 0: self.displayPicts = self.picts['tracking']
                        else: self.displayPicts = self.picts['active']
                    # offset the image to avoid burnin

                # get the background image, otherwise use what is assigned to displayPicts
                if self.state == 'Look' and os.path.exists("./frames/wis.ppm"):
                    image = Image.open('./frames/wis.ppm').convert("1")
                else:
                    if frame >= len(self.displayPicts): frame = 0
                    if self.state == 'Idle' and not self._message:  # dont' float the image if there is a message showing 
                        image = self.blackPict.copy()
                        locx = locx + (movX* cf.g('SCREEN_SPEED'))
                        locy = locy + (movY * cf.g('SCREEN_SPEED'))
                        image.paste(self.displayPicts[frame], (locx, locy))
                        if locx > 20 or locx < -20:  movX = movX * -1
                        if locy > 20 or locy < -5:  movY = movY * -1
                    else:
                        image = self.displayPicts[frame].copy()
                        locx = 0
                        locy = 0
                    frame = frame + 1
                
                # draw the selected image
                draw = ImageDraw.Draw(image)
              
                # if tracking, draw the pupils (need to call this AFTER getting the image above)
                if self.state == 'Idle' and STATE.cx >= 0:
                        pupilX = int((15/1280)*STATE.cx)
                        pupilY = int((25/720)*STATE.cy)
                        LogDebug(f"pupilX: {pupilX}, pupilY: {pupilY}")
                        draw.ellipse((eyeL+pupilX, pupilY+eyeY, eyeL+pupilX+pupilSize, eyeY+pupilY+pupilSize), outline="black", fill="black")
                        draw.ellipse((eyeR+pupilX, pupilY+eyeY, eyeR+pupilX+pupilSize, eyeY+pupilY+pupilSize), outline="black", fill="black")
 
                # Write four lines of text.
                time = datetime.now().strftime("%-I:%M%p")       
                bb = draw.textbbox((0,0), time, font=font)
                draw.rectangle((width-bb[2], 0, width-bb[2] + bb[2], bb[3]), fill=0, outline=0)
                draw.text((width-bb[2], 0), time, font=font, fill=255)

                temp = round(CPUTemperature().temperature)
                if temp >= 70:
                    bb = draw.textbbox((0,0), f"{temp}C", font=font)
                    draw.rectangle((width-bb[2], height-bb[3], width, height), fill=0, outline=0)
                    draw.text((width-bb[2], height-bb[3]), f"{temp}C", font=font, fill=255)
                if not self._message:
                     pass
#                    bb = draw.textbbox((0,0), self.state, font=font) # get size
#                    draw.text((width-bb[2], height-bb[3]), self.state, font=font, fill=255)
#                    bb = draw.textbbox((0,0), f"{last_fps}fps ({real_fps})", font=font) # get size
#                    draw.rectangle(bb, fill=0, outline=0)
#                    draw.text((width-bb[2], height-bb[3]), f"{last_fps}fps ({real_fps})", font=font, fill=255)
        #           self.draw.text((x, top + ((height/4)*2)), MemUsage, font=self.font, fill=255)
#                    bb = draw.textbbox((0,0), f"{STATE.GetState()}", font=font) # get size
#                    draw.text((0, height-bb[3]), f"{STATE.GetState()}", font=font, fill=255)
                else:
                    bb = draw.textbbox((0,0), self._message, font=font)
#                    draw.rectangle(bb, fill=0, outline=0)
                    draw.text(((width-bb[2])/2, height-bb[3]), self._message, font=font, fill=255)

                # Display image.
#                self.disp.image(image.transpose(Image.ROTATE_180))
                self.disp.image(image)
                self.disp.show()
                real_fps = round(1000000/(datetime.now()-dt).microseconds, 1)
                sleep(max((1/cf.g('FPS')) - (datetime.now()-dt).microseconds/1000000, 0))
            except Exception as e:
                LogError(f"AnimateThreadException: {str(e)}")
        self.disp.fill(0)
        self.disp.show()
        LogInfo(f"Animate Thread ended")

    def talking(self):
        self.state = 'Talk'
        self.displayPicts = self.picts['talking']
    def listening(self):
        self.state = 'Listen'
        self.displayPicts = self.picts['listening']
    def thinking(self):
        self.state = 'Think'
        self.displayPicts = self.picts['thinking']
    def looking(self):
        self.state = 'Look'
        self.displayPicts = self.picts['looking']
    def off(self):
        self.state = 'Idle'
        self.displayPicts = self.picts['active']
    def message(self, text):
        self._message = text
        exprThread = threading.Thread(target=self.ExpiryThread)
        exprThread.start()
        
    def ExpiryThread(self):
        sleep(cf.g('MESSAGE_SHOW_SECS'))
        self._message = False
        return

    def Close(self):
        self.state = 'Quit'
        # Clear display.
if __name__ == '__main__':

    global STATE
    s = Screen()
    STATE.ChangeState('ActiveIdle')
    sleep(60)
    s.off()
