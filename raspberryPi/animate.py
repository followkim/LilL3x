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

# import local modules
from apa102 import APA102

sys.path.insert(0, '..')
from globals import STATE, SleepOn
from config import cf
from error_handling import *

class Screen:
    display = 0
    picts = {}
    displayPicts = []
    blackPict = 0
    state = ''
    _message = False
    lastWIS = False
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
                     LogError("Error loading file {file}: {e.args}")
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
        errCnt = 0
        self.lastWIS = datetime.now()

        # Load default font.
        font = ImageFont.load_default()
        dt = datetime.now() + timedelta(seconds=-1)
        real_fps = 0
        LogInfo(f"Animate Thread started.  Screen {width}x{height}")
        while not self.state=='Quit':
            thisState = self.state              #lock in the state at the start
            thisDisplayPicts = self.displayPicts

            last_fps = round(1000000/(datetime.now()-dt).microseconds)
            dt = datetime.now()
            try:
                # Turn off display in idle/sleep state, or show tracking
                if thisState == 'Idle':
                    if STATE.IsSleeping():
                        self.disp.fill(0)
                        self.disp.show()
                        SleepOn(varf=STATE.IsSleeping, wakeOn=False)
                        continue
                    elif random.randint(0, cf.g('FPS')*5) == 1 or STATE.CheckState('Idle'):
                        thisDisplayPicts = self.picts['blinking']

                    else: #determine wich "Idle" animation we should use
                        if STATE.CheckState('Surveil'): thisDisplayPicts = self.picts['surveil']
                        elif STATE.cx: thisDisplayPicts = self.picts['tracking']
#                        else: thisDisplayPicts = self.picts['active'] # is set on state change, but need to reset here

                # See if we should be showing camera images #TODO Speed up frame rate and match to incoming images
                if thisState == 'Look' and os.path.exists(cf.g('WIS_FILE')):
                    image = Image.open(cf.g('WIS_FILE')).convert("1").copy() # make a copy as file might be gone

                else: # using displayPicts: (not Look)
                    if frame >= len(thisDisplayPicts): frame = 0

                    # float the screen 
                    if thisState == 'Idle' and not thisDisplayPicts == self.picts['tracking'] and not STATE.IsInteractive() and not self._message:  # dont' float the image if there is a message showing 
                        image = self.blackPict.copy()
                        locx = locx + (movX* cf.g('SCREEN_SPEED'))
                        locy = locy + (movY * cf.g('SCREEN_SPEED'))
                        image.paste(thisDisplayPicts[frame], (locx, locy))
                        if locx > 20 or locx < -20:  movX = movX * -1
                        if locy > 20 or locy < -5:  movY = movY * -1

                    # just show the image
                    else:
                        image = thisDisplayPicts[frame].copy()
                        locx = 0
                        locy = 0
                    frame = frame + 1
                
                # draw the selected image
                draw = ImageDraw.Draw(image)

                # Draw additional info on screen when idle
                if thisState == 'Idle':

                   # if tracking, draw the pupils (need to call this AFTER getting the image above)
                   # make SURE that the pupils are always drawn when the tracking image is used cause it looks super creepy otherwise
                    if thisDisplayPicts == self.picts['tracking']:
                        pupilX = int((15/1280)*STATE.cx)
                        pupilY = int((25/720)*STATE.cy)
                        #LogDebug(f"pupilX: {pupilX}, pupilY: {pupilY}")
                        draw.ellipse((eyeL+pupilX, pupilY+eyeY, eyeL+pupilX+pupilSize, eyeY+pupilY+pupilSize), outline="black", fill="black")
                        draw.ellipse((eyeR+pupilX, pupilY+eyeY, eyeR+pupilX+pupilSize, eyeY+pupilY+pupilSize), outline="black", fill="black")

                    if not STATE.IsInteractive() or cf.g('SCREEN_DEBUG'):
                        #draw text objects
                        if not self._message:
                            show_temp = STATE.temp >= cf.g('CPU_MAX_TEMP')*0.9 or cf.g('SCREEN_DEBUG')
                            locStr = 'lr'
                            if not show_temp and not cf.g('SCREEN_DEBUG'):
                                if movY > 0: locStr = 'u'+locStr[1]
                                if movX > 0: locStr = locStr[0]+'l'
                            self.DrawText(draw, datetime.now().strftime("%-I:%M%p"), locStr, font) # defaults to top right

                            # temperature: botton left
                            if show_temp: self.DrawText(draw, f"{STATE.temp}C", 'bl', font)

                            # debug messages: CPU and fps
                            if not self._message and cf.g('SCREEN_DEBUG'):  # show debug messages
                                if STATE.cpu: self.DrawText(draw, f"{STATE.cpu}%", 'ur', font)
#                                self.DrawText(draw, f"{last_fps}fps ({real_fps})", 'ul', font)
                                self.DrawText(draw, f"{STATE.volume}", 'ul', font)
                    # end if state == 'Idle'
                elif thisState == 'Listen' and cf.g('SCREEN_DEBUG'):
                    self.DrawVolume(draw)

                if self._message: # draw in any state - lower center
                    self.DrawText(draw, self._message, 'lc', font)
                # Display image.
#                self.disp.image(image.transpose(Image.ROTATE_180))
                self.disp.image(image)
                self.disp.show()
                real_fps = round(1000000/(datetime.now()-dt).microseconds, 1)

                # sleep
                if thisState == 'Look': SleepOn(varf=self.WakeWIS, wakeOn=True, step=0.1)
                elif thisState != self.state: pass # state changed, don't sleep
                else: sleep(max((1/cf.g('FPS')) - (datetime.now()-dt).microseconds/1000000, 0))

            except Exception as e:
                LogError(f"AnimateThreadException: {e.args}")

        self.disp.fill(0) # clear display
        self.disp.show()
        LogInfo(f"Animate Thread ended")

    def WakeWIS(self):
        if self.state != 'Look': return True  # Hacky-- break out of sleep when we come out of Look.
        elif os.path.exists(cf.g('WIS_FILE')):
            f_dt = datetime.fromtimestamp(os.path.getmtime(cf.g('WIS_FILE')))
            if f_dt > self.lastWIS:
                self.lastWIS = f_dt
                return True
        return False

    def DrawVolume(self, draw, x=5, y=20, h=40, w=4):
        xLen = 40
        width = 4
        volume_scale = max(min(int((STATE.volume/15000) * xLen), xLen), 0)
        draw.rectangle((x, y, x+w, y+h), fill=0, outline=1)
        draw.rectangle((x, y+h-volume_scale, x+w, y+h), fill=1, outline=1)
    
    def DrawText(self, draw, text, where, font):
        ret = {'x':0,'y': 0, 'xx': 0, 'yy': 0}
        width = self.disp.width
        height = self.disp.height
        bb = draw.textbbox((0,0), text, font=font)

        # y axis
        if where[0] in ('u', 't'):  #upper/top
            ret['y'] = 0
            ret['yy'] = bb[3]
        elif where[0] in ('l', 'b'): #lower/bottom
            ret['y'] = height-bb[3]
            ret['yy'] = height
        else:
            ret['y'] = (height-bb[3])/2   #center
            ret['yy'] = ret['y']+ bb[3]

        #x axis
        if where[1]=='r':           #right/leftt
            ret['x'] = width-bb[2]  
            ret['xx'] = width
        elif where[1]=='l':
            ret['x'] = 0
            ret['xx'] = bb[2]
        else:
            ret['x'] = (width-bb[2])/2
            ret['xx'] = ret['x']+ bb[2]


        draw.rectangle((ret['x'], ret['y'], ret['xx'], ret['yy']), fill=0, outline=0)
        draw.text((ret['x'], ret['y']), text, font=font, fill=255)
        return ret

    dpd = { 'Talk': 'talking', 'Listen': 'listening', 'Think': 'thinking', 'Look': 'looking', 'Idle': 'active'}

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

