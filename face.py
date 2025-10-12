import sys
import threading
from datetime import datetime
from config import cf
from error_handling import *

sys.path.insert(0, './raspberryPi/')
from eyes import LEDS

#sys.path.insert(0, './raspberryPi/')
#from apa102 import APA102
#from animate import DummyScreen
#from rasp_leds import LEDS


sys.path.insert(0, '..')
LogInfo("Importing Face...")

class Face:
#    screen = 0
    leds = 0
    def __init__(self):
        self.leds = LEDS()
        led_thread = threading.Thread(target=self.leds.LEDThread, daemon=True)
        led_thread.name = f"{GetHostname()} LEDThread"
        led_thread.start()

    def Close(self):
        self.leds.Close()

    def listening(self, run=False):
        if run: 
            LogError("Run is set!")
            DumpStack()
        self.leds.listening()

    def thinking(self, run=False):
        if run: 
            LogError("Run is set!")
            DumpStack()
        self.leds.thinking()

    def looking(self, run=False):
        if run: 
            LogError("Run is set!")
            DumpStack()
        self.leds.looking()

    def loving(self, run=False):
        if run: 
            LogError("Run is set!")
            DumpStack()
        self.leds.loving()

    def idle(self, run=False):
        if run: 
            LogError("Run is set!")
            DumpStack()
        self.leds.off()

    def off(self, run=False):
        if run: 
            LogError("Run is set!")
            DumpStack()
        self.idle(run)

    def message(self, text):
        pass 
#       self.screen.message(text)
def dummy(): pass

class DummyFace:
    def __init__(self): pass
    def SetViewControl(self, showViewStartFunc=dummy, showViewEndFunc=dummy): pass
    def Close(self):pass
    def talking(self):pass
    def listening(self):pass
    def thinking(self):pass
    def looking(self):pass
    def idle(self): pass
    def off(self): pass
    def message(self, text): pass

if __name__ == '__main__':
    from time import sleep
    from globals import STATE
    import os

    face = Face() #main
    face.thinking()
    os.system(f"touch .running")
    while (os.path.exists(".running")): sleep(0.1)
    face.off()
    sleep(0.25)
    face.Close()
    
