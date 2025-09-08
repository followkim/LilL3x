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
    import threading
    global STATE


    def dummy():
        pass
    face = Face() #main

#    ww = pico_wake.pico_wake()
#    ww_thread = threading.Thread(target=ww.ww_thread, daemon=True)
#    ww_thread.name = f"{GetHostname()} WakeWordThread"
#    ww_thread.start()


#    sleep(20)
    # state test
#    LogDebug("talking")
#    face.talking()
#    sleep(2)

#    LogDebug("listening")
#    face.listening()
#    sleep(2)

    LogDebug("thinking")
    face.thinking()
    sleep(10)

    LogDebug("idle")
    face.idle()
    sleep(2)

    LogDebug("loving")
    face.loving()
    sleep(10)

    face.Close()
    sleep(2)
#    b = 0
#    while b >= 0:
#        b = int(input("Brightness: 0-100: "))
#        cf.s('BRIGHTNESS', b)

#    b = 0
#    while b >= 0:
#        b = int(input("Speed: 1-10: "))
#        cf.s('LIGHT_SPEED', b)

# showview test
#    face.looking()
#    sleep(600)
        
#    animate_thread = threading.Thread(target=face.screen.AnimateThread)
#    animate_thread.start()
#    face.idle()
#    STATE.ChangeState('Looking')
#    sleep(5)
#    STATE.ChangeState('Surveil')
#    sleep(5)

    
#    face.looking()
#    sleep(10)
#    face.listening()
#    sleep(10)
#    cf.s('SCREEN_DEBUG', True)
#    face.idle()
##    face.message("Hi there!")
    '''
    STATE.ChangeState('Active')
#    face.looking()
#    sleep(360)
    STATE.ChangeState('Idle')
    sleep(10)
    STATE.ChangeState('SleepState')
    sleep(10)
    STATE.ChangeState('ActiveIdle')
    sleep(10)
    face.Close()
    '''
    '''
    while face:
        try:
            STATE.cx = int(input("x"))
            STATE.cy = int(input("y"))
        except Exception as e:
            print(e.args)
            STATE.ChangeState('Quit')
            sleep(5)
            face.Close()
            break
    '''
