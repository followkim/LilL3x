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

import argparse
import struct
import sys
from time import sleep
from threading import Thread
#from config import config
from gpiozero import LED

from apa102 import APA102
from config import cf

COLORS_RGB = {
    'blue':(0, 0, 255),
    'green':(0, 255, 0),
    'orange':(255, 128, 0),
    'pink':(255, 51, 153),
    'purple':(128, 0, 128),
    'red':(255, 0, 0),
    'white':(255, 255, 255),
    'yellow':(255, 255, 51),
    'off':(0, 0, 0),
}

class LEDS:
    driver = 0
    power = 0
    
    def __init__(self):
        self.driver = APA102(num_led=12)
        self.power = LED(5)
        self.power.on()

    def SetColor(self, inColor):
        if isinstance(inColor, str):
            color = COLORS_RGB[inColor]
        else:
            color = inColor
        color = [int(x*cf.g('BRIGHTNESS')) for x in color]
        for i in range(12):
            self.driver.set_pixel(i, color[0], color[1], color[2])
        try:
            self.driver.show()
        except Exception as e:
            self.off()
            return
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

    def talking(self):
        self.red()
    def listening(self):
        self.green()
    def thinking(self):
        self.purple()
    def looking(self):
        self.yellow()

    def Close(self):
        self.power.off()

if __name__ == '__main__':

     l = LEDS()
     for k in COLORS_RGB.keys():
         print(k)
         l.SetColor(k)
         sleep(1)
     l.red()
     sleep(1)
     l.off()
