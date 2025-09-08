#!/usr/bin/env python3
from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO
#import gpiozero
import sys

sys.path.insert(0, '..')
from globals import STATE
from error_handling import *
from config import cf

beeps = {
    1: 'Wake',
    2: 'Restart',
    3: 'Reboot'
}

class Button:
    BUTTON = 27
    btn = False
    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON, GPIO.IN)

#        self.btn = gpiozero.Button(BUTTON)

    def ButtonThread(self, audio):
        while not STATE.ShouldQuit():
    
#            if not (GPIO.input(self.BUTTON)):
            if GPIO.input(self.BUTTON):
                if not audio.IsBusy():
                    audio.PlaySound(cf.g('WAKE_MP3'))
                pressDT = datetime.now()
                restartBeeps = 1

                while GPIO.input(self.BUTTON) and restartBeeps < 3:
                    if restartBeeps==1 and (datetime.now()-pressDT).total_seconds() >= cf.g('RESTART_SEC'):
                        audio.PlaySound(cf.g('WAKE_MP3'))
                        restartBeeps = 2

                    if restartBeeps==2 and (datetime.now()-pressDT).total_seconds() >= cf.g('REBOOT_SEC'):
                        audio.PlaySound(cf.g('WAKE_MP3'))
                        audio.PlaySound(cf.g('WAKE_MP3'))
                        restartBeeps = 3
                STATE.ChangeState(beeps[restartBeeps])
                LogInfo(f"Button: {beeps[restartBeeps]}")
            else:
               sleep(0.25)
        LogInfo("ButtonThread exit.")


if __name__ == '__main__':
    class A: 
        def PlaySound(str):
            print(str)
        def IsBusy():
            return False
    a = A()
    b = Button()
    b.ButtonThread(A)
