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
#from gpiozero import LED

#from apa102 import APA102
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
 
    def SetColor(self, inColor):
        if isinstance(inColor, str):
            return
    def blue(self):
            return
    def green(self):
            return
    def orange(self):
            return
    def pink(self):
            return
    def purple(self):
            return
    def red(self):
            return
    def white(self):
            return
    def yellow(self):
            return
    def off(self):
            return

    def talking(self):
            return
   def listening(self):
            return
   def thinking(self):
            return
   def looking(self):
            return

    def Close(self):
             return

if __name__ == '__main__':

     l = LEDS()
     for k in COLORS_RGB.keys():
         print(k)
         l.SetColor(k)
         sleep(1)
     l.red()
     sleep(1)
     l.off()
