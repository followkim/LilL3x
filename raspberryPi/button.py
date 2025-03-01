#!/usr/bin/env python3
from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO
import gpiozero
import sys

from globals import STATE
from error_handling import *
from config import cf

beeps = {
    1: 'Wake',
    2: 'Restart',
    3: 'Reboot'
}

class Button:

    BUTTON = 17
    btn = False
    def __init__(self):
#        GPIO.setmode(GPIO.BCM)
#        GPIO.setup(self.BUTTON, GPIO.IN)
        self.btn = gpiozero.Button(17)

    def ButtonThread(self, audio):
        while not STATE.ShouldQuit():
    
#            if not (GPIO.input(self.BUTTON)):
            if self.btn.is_pressed:
                if not audio.IsBusy():
                    audio.PlaySound(cf.g('WAKE_MP3'))
                pressDT = datetime.now()
                restartBeeps = 1

                while self.btn.is_pressed and restartBeeps < 3:
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
               sleep(0.5)
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
