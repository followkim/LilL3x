import sys
import threading
sys.path.insert(0, './raspberryPi/')
from apa102 import APA102
from animate import Screen
from rasp_leds import LEDS
from config import cf
from error_handling import *

sys.path.insert(0, '..')
LogInfo("Importing Face...")

class Face:
    screen = 0
    leds = 0
    def __init__(self):
        self.screen = Screen()
        self.leds = LEDS()
        animate_thread = threading.Thread(target=self.screen.AnimateThread, daemon=True)
        animate_thread.name = f"AnimateThread: {animate_thread.native_id}"
        animate_thread.start()
        
        led_thread = threading.Thread(target=self.leds.LEDThread, daemon=True)
        led_thread.name = f"LedThread: {led_thread.native_id}"
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
        pass
    face = Face()
    face.SetViewControl(dummy, dummy)
    STATE.ChangeState('ActiveIdle')
    
    '''
    # state test
    face.talking()
    sleep(2)

    face.listening()
    sleep(2)

    face.thinking()
    sleep(2)
    '''
    face.idle()
    b = 0
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
    face.idle()
    STATE.ChangeState('Surveil')
    sleep(30)
    '''
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
    '''
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
