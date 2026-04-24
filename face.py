import sys
import threading
from datetime import datetime
from config import cf
from error_handling import *

sys.path.insert(0, './raspberryPi/')
from apa102 import APA102
from animate import Screen
from rasp_leds import LEDS

sys.path.insert(0, '..')
LogInfo("Importing Face...")

class Face:
    screen = 0
    leds = 0
    def __init__(self):
        self.screen = Screen()
        self.leds = LEDS()
        animate_thread = threading.Thread(target=self.screen.AnimateThread, daemon=True)
        animate_thread.name = f"{GetHostname()} AnimateThread"
        animate_thread.start()
        
        led_thread = threading.Thread(target=self.leds.LEDThread, daemon=True)
        led_thread.name = f"{GetHostname()} LEDThread"
        led_thread.start()
 

    def SetViewControl(self, showViewStartFunc, showViewEndFunc):
        self.view_start = showViewStartFunc
        self.view_end = showViewEndFunc

    def Close(self, run=True):
        if run:
            self.screen.Close()
            self.leds.Close()

    def talking(self, run=True):
        if run:
            self.view_end()
            self.leds.talking()
            self.screen.talking()

    def listening(self, run=True):
        if run:
            self.view_end()
            self.leds.listening()
            self.screen.listening()

    def thinking(self, run=True):
        if run:
            self.view_end()
            self.leds.thinking()
            self.screen.thinking()

    def looking(self, run=True):
        if run:
            self.leds.looking()
            self.view_start()
            self.screen.looking()

    def idle(self, run=True):
        if run:
            self.view_end()
            self.screen.off()
            self.leds.off()
 
    def off(self, run=True):
        self.idle(run)

    def message(self, text):
        self.screen.message(text)
def dummy(): pass

class DummyFace:
    def __init__(self): pass
    def SetViewControl(self, showViewStartFunc=dummy, showViewEndFunc=dummy): pass
    def Close(self, run=True):pass
    def talking(self, run=True):pass
    def listening(self, run=True):pass
    def thinking(self, run=True):pass
    def looking(self, run=True):pass
    def idle(self, run=True): pass
    def off(self, run=True): pass
    def message(self, text): pass

if __name__ == '__main__':
    from time import sleep
    from globals import STATE
    import pico_wake
    import threading
    global STATE
    import pygame
    pygame.mixer.init()


    def dummy():
        pass
    face = Face() #main
    face.SetViewControl(dummy, dummy)
    STATE.ChangeState('ActiveIdle')
    face.idle()
#    b = 0
#    while b >= 0:
#        b = int(input("Brightness: 0-100: "))
#        cf.s('BRIGHTNESS', b)

#    b = 0
#    while b >= 0:
#        b = int(input("Speed: 1-10: "))
#        cf.s('LIGHT_SPEED', b)

    face.idle()
    STATE.ChangeState('Surveil')
    sleep(5)
    face.looking()
    sleep(5)
    face.listening()
    sleep(5)
    cf.s('SCREEN_DEBUG', True)
    face.idle()
    face.message("Hi there!")
    STATE.ChangeState('Active')
    STATE.ChangeState('Idle')
    sleep(10)
    STATE.ChangeState('SleepState')
    sleep(10)
    STATE.ChangeState('ActiveIdle')
    STATE.ChangeState('Quit')
    face.Close()
    sleep(2)
