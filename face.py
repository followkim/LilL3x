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
        animate_thread = threading.Thread(target=self.screen.AnimateThread)
        animate_thread.start()
        
        led_thread = threading.Thread(target=self.leds.LEDThread)
        led_thread.start()
 

    def SetViewControl(self, showViewStartFunc, showViewEndFunc):
        self.view_start = showViewStartFunc
        self.view_end = showViewEndFunc

    def Close(self):
        self.screen.Close()
        self.leds.Close()

    def talking(self):
        self.view_end()
        self.leds.talking()
        self.screen.talking()

    def listening(self):
        self.view_end()
        self.leds.listening()
        self.screen.listening()

    def thinking(self):
        self.view_end()
        self.leds.thinking()
        self.screen.thinking()

    def looking(self):
        self.leds.looking()
        self.view_start()
        self.screen.looking()

    def idle(self):
        self.view_end()
        self.screen.off()
        self.leds.off()

    def off(self):
        self.idle()

    def message(self, text):
        self.screen.message(text)

if __name__ == '__main__':
    from time import sleep
    from globals import STATE
    global STATE

    def dummy():
        return
    face = Face()
    face.SetViewControl(dummy, dummy)
#    animate_thread = threading.Thread(target=face.screen.AnimateThread)
#    animate_thread.start()
    STATE.ChangeState('ActiveIdle')
    face.idle()
    sleep(10)
    face.looking()
    sleep(10)
    face.listening()
    sleep(10)
    face.idle()
    STATE.ChangeState('ActiveIdle')
    sleep(10)
    STATE.ChangeState('Idle')
    sleep(10)
    STATE.ChangeState('SleepState')
    sleep(10)
    STATE.ChangeState('ActiveIdle')
    sleep(10)
    face.Close()
    '''
    while face:
        try:
            STATE.cx = int(input("x"))
            STATE.cy = int(input("y"))
        except Exception as e:
            print(str(e))
            STATE.ChangeState('Quit')
            sleep(5)
            face.Close()
            break
    '''
