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
import psutil
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
LogDebug("LED Display Loading...")


class Screen:
    display = 0
    picts = {}
    displayPicts = []
    blackPict = 0
    state = ''
    _message = False

    def __init__(self):

        # Create the I2C interface.
        i2c = busio.I2C(SCL, SDA)

        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

#        # Clear display. -- not needed - we are showing a welcome pict
#        self.disp.fill(0)
#        self.disp.show()

        # laod the images
        self.blackPict = image = Image.new("1", (128, 64))
        self.LoadFrames()

         # init
        self.off()

    def LoadFrames(self):
        picts = {}
        filelist = os.listdir("./frames")
        filelist.sort()
        for file in filelist:
             if re.search(r"^face_(.*)ppm$", file):
                 try:
                     (func) = re.compile("^face_([a-z]*)[0-9]+.ppm$").match(file).groups()
                     if func[0]:
                         if not func[0] in picts:
                             picts[func[0]] = []
                         picts[func[0]].append(Image.open('./frames/'+file).convert("1"))
                 except Exception as e:
                     LogError("Error loading file {file}: {str(e)}")
        self.picts = picts

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
        LogInfo(f"Animate Thread started.  Screen {width}x{height}")
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

                    else: #determine wich "Idle" animation we should use
                        if STATE.CheckState('Surveil'): self.displayPicts = self.picts['surveil']
                        elif STATE.cx > 0: self.displayPicts = self.picts['tracking']
                        else: self.displayPicts = self.picts['active']

                # See if we should be showing camera images #TODO Speed up frame rate and match to incoming images
                if self.state == 'Look' and os.path.exists(cf.g('WIS_FILE')):
                    image = Image.open(cf.g('WIS_FILE')).convert("1").copy() # make a copy as file might be gone

                else: # using displayPicts: (not Look)
                    if frame >= len(self.displayPicts): frame = 0

                    # float the screen 
                    if self.state == 'Idle' and not STATE.cx > 0 and not STATE.CheckState('Active') and not self._message:  # dont' float the image if there is a message showing 
                        image = self.blackPict.copy()
                        locx = locx + (movX* cf.g('SCREEN_SPEED'))
                        locy = locy + (movY * cf.g('SCREEN_SPEED'))
                        image.paste(self.displayPicts[frame], (locx, locy))
                        if locx > 20 or locx < -20:  movX = movX * -1
                        if locy > 20 or locy < -5:  movY = movY * -1

                    # just show the image
                    else:
                        image = self.displayPicts[frame].copy()
                        locx = 0
                        locy = 0
                    frame = frame + 1
                
                # draw the selected image
                draw = ImageDraw.Draw(image)

                # Draw additional info on screen when idle
                if self.state == 'Idle':

                   # if tracking, draw the pupils (need to call this AFTER getting the image above)
                    if STATE.cx > 0:
                        pupilX = int((15/1280)*STATE.cx)
                        pupilY = int((25/720)*STATE.cy)
                        LogDebug(f"pupilX: {pupilX}, pupilY: {pupilY}")
                        draw.ellipse((eyeL+pupilX, pupilY+eyeY, eyeL+pupilX+pupilSize, eyeY+pupilY+pupilSize), outline="black", fill="black")
                        draw.ellipse((eyeR+pupilX, pupilY+eyeY, eyeR+pupilX+pupilSize, eyeY+pupilY+pupilSize), outline="black", fill="black")

                    #draw text objects
                    temp = round(CPUTemperature().temperature)
                    show_temp = temp >= cf.g('CPU_MAX_TEMP')*0.9 or cf.g('DEBUG')>=4
                    if not (STATE.CheckState('Active') or self._message) or cf.g('DEBUG')>=4:
                        time = datetime.now().strftime("%-I:%M%p")       
                        bb = draw.textbbox((0,0), time, font=font)
                        if not show_temp:
                            if   movX<0 and movY<0: clock = (width-bb[2] , height-bb[3]) #lower right
                            elif movX<0 and movY>0: clock = (width-bb[2] , 0)		   # upper right
                            elif movX>0 and movY<0: clock = (0           , height-bb[3]) # lower left
                            elif movX>0 and movY>0: clock = (0           , 0)		   # upper left
                        else: clock = (width-bb[2], 0) # defaults to top right
                        draw.rectangle((clock[0], clock[1], clock[0]+bb[2], clock[1]+bb[3]), fill=0, outline=0)
                        draw.text(clock, time, font=font, fill=255)
                   
                    # temperature: top left
                    if show_temp:
                        bb = draw.textbbox((0,0), f"{temp}C", font=font)
                        draw.rectangle((0, 0, bb[2], bb[3]), fill=0, outline=0)
                        draw.text((0,0), f"{temp}C", font=font, fill=255)

                    # debug messages: CPU and fps
                    if not self._message and cf.g('DEBUG')>=4:  # show debug messages
                        CPU = f"{psutil.cpu_percent()}%"
                        bb = draw.textbbox((0,0), CPU, font=font)
                        draw.rectangle((0, height-bb[3], bb[2], height), fill=0, outline=0)
                        draw.text((0, height-bb[3]), CPU, font=font, fill=255)

                        debugStr = f"{last_fps}fps ({real_fps})"
#                        debugStr = f"{STATE.GetState()}/{self.state}"
                        bb = draw.textbbox((0,0), debugStr, font=font) # get size
                        draw.rectangle((width-bb[2], height-bb[3], width, height), fill=0, outline=0)
                        draw.text((width-bb[2], height-bb[3]), debugStr, font=font, fill=255)
                # end if state == 'Idle'

                if self._message: # draw in any state
                    bb = draw.textbbox((0,0), self._message, font=font)
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
        exprThread.name = f"LilL3x ExpiryThread {exprThread.native_id}"
        exprThread.start()
        
    def ExpiryThread(self):
        sleep(cf.g('MESSAGE_SHOW_SECS'))
        self._message = False
        return

    def Close(self):
        self.state = 'Quit'
        # Clear display.

