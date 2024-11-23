#print SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import sys
import threading
sys.path.insert(0, './raspberryPi/')
from apa102 import APA102
from animate import Screen
from rasp_leds import LEDS
sys.path.insert(0, '..')

class Face:
    screen = 0
    leds = 0
    def __init__(self):
        self.screen = Screen()
        self.leds = LEDS()

    def Close(self):
        self.screen.Close()
        self.leds.Close()

    def talking(self):
        self.leds.talking()
        self.screen.talking()

    def listening(self):
        self.leds.listening()
        self.screen.listening()

    def thinking(self):
        self.leds.thinking()
        self.screen.thinking()

    def looking(self):
#        self.leds.looking()
        self.screen.looking()

    def off(self):
        self.screen.off()
        self.leds.off()

    def message(self, text):
        self.screen.message(text)

if __name__ == '__main__':
    from time import sleep
    from globals import STATE
    global STATE
    face = Face()
    animate_thread = threading.Thread(target=face.screen.AnimateThread)
    animate_thread.start()
    face.talking()
    sleep(2)
    face.message("Feel better Mork!")
    sleep(5)
    face.thinking()
    STATE.ChangeState('Quit')
    sleep(5)
    face.Close()
