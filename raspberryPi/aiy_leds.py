import sys
import os
from time import sleep
import math

from gpiozero import LED
from apa102 import APA102
#from config import cf

sys.path.insert(0, '..')
from globals import STATE, SleepOn
from config import cf
from error_handling import *

class AIY_LEDS:
    led = False
    is_listening = False
    should_quit = False
    def __init__(self):
        self.led = LED(cf.g('LED_PIN'))

    def SetColor(self, inColor):
        return inColor

    def LEDThread(self):
        LogInfo("AIY_LEDThread started")
        has_error = False
        dt = False
        while not self.should_quit:
            dt = datetime.now()
            try:
                if self.is_listening:
                    self.led.on()
                else: self.led.off()
                sleep(max((1-(min(cf.g('LIGHT_SPEED'),99.5)/100))  - (datetime.now()-dt).microseconds/1000000, 0))
            except Exception as e:
                LogError(f"AYI_LEDS:LedThread exception: {str(e)}:{e.args}")
                if has_error: self.should_quit = True
                else: has_error = True
        LogInfo("LEDThread ended")

    def blue(self):
        pass
    def green(self):
        pass
    def orange(self):
        pass
    def pink(self):
        pass
    def purple(self):
        pass
    def red(self):
        pass
    def white(self):
        pass
    def yellow(self):
        pass
    def off(self):
        self.is_listening = False
    def talking(self):
        self.is_listening = False

    def listening(self):
        self.is_listening = True

    def thinking(self):
        self.is_listening = False

    def looking(self):
        self.is_listening = False

    def idle(self):
        self.is_listening = False

    def Close(self):
        self.should_quit = True
