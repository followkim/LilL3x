#
# Copyright 2020 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

import sys
import os
from time import sleep
import math

from gpiozero import LED
from apa102 import APA102
#from config import cf

sys.path.insert(0, '..')
from globals import STATE
from config import cf
from error_handling import *

COLORS_RGB = {
    'blue':[0, 0, 255, 100],
    'green':[0, 255, 0, 100],
    'orange':[255, 128, 0, 100],
    'pink':[255, 51, 153, 100],
    'purple':[128, 0, 128, 100],
    'red':[255, 0, 0, 100],
    'white':[255, 255, 255, 100],
    'yellow':[255, 255, 51, 100],
    'off':[0, 0, 0, 0],
}

MAX_BRIGHTNESS = APA102.MAX_BRIGHTNESS
NUM_LEDS = 12

class LEDS:
    driver = 0
    power = 0
    color = COLORS_RGB['white']
    color[3] = cf.g('BRIGHTNESS') # se we aren't asking driver to set constantly
    should_quit = False
    is_idle = True

    def __init__(self):
        self.driver = APA102(num_led=NUM_LEDS)

    def SetColor(self, inColor):
        self.is_idle = False
        if isinstance(inColor, str):
            self.color = COLORS_RGB[inColor].copy()
        else:
            self.color = inColor.copy()

    def LEDThread(self):
        LogInfo("LEDThread started")
        jr = 0
        ir = 0
        thisColor = self.color.copy()          # keep track of the current color/brightness

        brightDelta = 1
        while not self.should_quit:
            self.color[3] = cf.g('BRIGHTNESS') # set now but might be reset below
            if self.is_idle:
                if STATE.CheckState('SleepState'):                                      # dim the lights
                    brightDelta = -1
                    print(f"thisColor[3]: {thisColor[3]}")
                    if thisColor[3] > 0:
                        (ir, jr, self.color) = rainbow_cycle(ir, jr) # continuie to cycle
                        self.color[3] = max(thisColor[3] + (cf.g('BRIGHT_SPEED') * brightDelta), 0)  # reset brightness from default
                    elif thisColor[:3] != COLORS_RGB['off'][:3]: self.color = COLORS_RGB['off'].copy()
                    else:
                        sleep(cf.g('SLEEP_SLEEP'))
                elif STATE.CheckState('Surveil'):
                    self.color = COLORS_RGB['red'].copy()
                    (self.color[3], brightDelta) = bounce(thisColor[3], cf.g('BRIGHT_SPEED')*2, brightDelta)
                else:
                    if (STATE.CheckState('ActiveIdle') or STATE.CheckState('Idle')):
                        (ir, jr, self.color) = rainbow_cycle(ir, jr)

            if thisColor != self.color:            # don't change colors if not asked to change
                thisColor = self.color.copy()
                for i in range(NUM_LEDS):
                    self.driver.set_pixel(i, self.color[0], self.color[1], self.color[2], self.color[3])
                try:
                    self.driver.show()
                except Exception as e:
                    self.off()



            sleep(1-(min(cf.g('LIGHT_SPEED'),99.5)/100))
        # exit: set to black and quit
#        for i in range(12): self.driver.set_pixel(i, 0, 0, 0)
#        self.driver.show()
        self.driver.clear_strip()
        self.driver.cleanup()
        LogInfo("LEDThread ended")

    def blue(self):
        self.SetColor(COLORS_RGB['blue'])
    def green(self):
        self.SetColor(COLORS_RGB['green'])
    def orange(self):
        self.SetColor(COLORS_RGB['orange'])
    def pink(self):
        self.SetColor(COLORS_RGB['pink'])
    def purple(self):
        self.SetColor(COLORS_RGB['purple'])
    def red(self):
        self.SetColor(COLORS_RGB['red'])
    def white(self):
        self.SetColor(COLORS_RGB['white'])
    def yellow(self):
        self.SetColor(COLORS_RGB['yellow'])
    def off(self):
        self.SetColor(COLORS_RGB['off'])
        self.is_idle = True

    def talking(self):
        self.red()
    def listening(self):
        self.green()
    def thinking(self):
        self.purple()
    def looking(self):
        self.blue()
    def idle(self):
        self.off()
 
    def Close(self):
        self.should_quit = True

def rainbow_cycle(i, j):
    color = wheel((i+j) & 255)
    i = i + 1
    if i >= 256:
        i = 0
        j = j + 1
        if j >= 256: j = 0
    return (i, j, color)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return [pos * 3, 255 - pos * 3, 0, 100]
    elif pos < 170:
        pos -= 85
        return [255 - pos * 3, 0, pos * 3, 100]
    else:
        pos -= 170
        return [0, pos * 3, 255 - pos * 3, 100]

def bounce(cur, step=1, delta=1, min_val=1, max_val=100):
    """Bounces a number between two values."""
    cur = cur + (step * delta)
    if cur > max_val:
        cur = max_val
        delta = delta*-1
    elif cur < min_val:
        cur = min_val
        delta = delta*-1
    return (cur, delta)
