import sys
import os
from gpiozero import PWMLED
from math import sin, pi
from time import sleep
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import gpiozero
import inspect 

#sys.path.insert(0, '..')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from globals import STATE, SleepOn
from config import cf
from error_handling import *


class Purr:

    aBtn = False
    bBtn = False
    motor = False
    petStart = False
    should_quit = False
    purr_thread = False
    is_purring = False
    audio = False
    fsr1 = 22
    fsr2 = 23
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.fsr1, GPIO.IN)
        GPIO.setup(self.fsr2, GPIO.IN)

        # Define the GPIO pin connected to the LED
        led_pin = 13
        self.motor = PWMLED(led_pin)

    def PurrThread(self, audio):
        startPet = False
        lastPet = False
        self.audio = audio
        LogInfo("PurrThread started")
        while not self.should_quit:

            if (GPIO.input(self.fsr1) or GPIO.input(self.fsr2)):
                waitFsr = self.fsr1 if GPIO.input(self.fsr2) else self.fsr2
                is_petting = True
                LogDebug("Petting Detected")
                startPet = datetime.now()
                lastPet = startPet
                while is_petting == True:
#                    while not GPIO.input(waitFsr) and is_petting and not self.should_quit:
                    while not (GPIO.input(self.fsr1) or GPIO.input(self.fsr2)) and is_petting and not self.should_quit:
                        if lastPet + timedelta(seconds=cf.g('STROKE_TO')) < datetime.now() or self.should_quit:
                            is_petting = False
                            self.is_purring = False
                            LogDebug("Petting Ended")
                            break
                        else: sleep(0.1)
                    if not is_petting: break
                    waitFsr = self.fsr1 if GPIO.input(self.fsr2) else self.fsr2
                    lastPet = datetime.now()
                    self.purr_motor()

#                    if startPet + timedelta(seconds=cf.g('PURR_SEC')) < datetime.now():
#                        self.purr_motor()
#            else: sleep(cf.g('PURR_SLEEP'))
            else: sleep(0.5)
        LogInfo("PurrThread exit.")

    def purr_motor(self):
        self.is_purring = True
        if not self.Purring() and STATE.temp < cf.g('CPU_MAX_TEMP'):
            self.purr_thread = threading.Thread(target=self.purr_motor_thread, daemon=True)
            self.purr_thread.name = f"{GetHostname()} PurrMotorThread"
            self.purr_thread.start()

    def Purring(self):
        return self.purr_thread and self.purr_thread.is_alive()

    def purr_motor_thread(self):
        # play purring
        startPurr = datetime.now()
        purr_channel = self.audio.PlaySound(cf.g('PURR_MP3'), asyn=True, loop=True)
        self.audio.SetChannelVolume(purr_channel, 1)

        # Define sine wave parameters
        frequency = 5  # Hz (determines how fast the sine wave cycles)
        amplitude = 1  # Controls the range of brightness (0 to 1)
        offset = 0 # 0.5 # Shifts the sine wave up to ensure values are positive (0 to 1)
        brightness = 0

        # Loop to continuously update LED brightness
        t = 0
        while self.is_purring and not self.should_quit and STATE.temp < cf.g('CPU_MAX_TEMP'):
#            volume = (min((datetime.now() - startPurr).total_seconds() / (10 * 60), 1) * 1) + 0
#            self.audio.SetChannelVolume(purr_channel, volume)
            # Calculate sine wave value (scaled and offset for brightness)
            brightness = abs(amplitude * sin(2 * pi * frequency * t) + offset)
            t += 0.01  # Adjust for smoother or faster animation

            # Ensure brightness stays within valid range (0 to 1)
            brightness = (max(0, min(1, brightness)) / 4) + 0.75
            self.motor.value = brightness

            # Increment time and control update speed
            sleep(0.1) # Small sleep to allow the Pi to perform other tasks


        self.audio.StopChannel(purr_channel, cf.g("PURR_FO"))
        while (brightness > 0): # fade out purring motor
            brightness -= 0.05
            self.motor.value = max(brightness, 0)
            sleep(0.1)
        self.motor.off() # Turn off the purring on exit

    def Close(self):
        self.should_quit = True


if __name__ == '__main__':
    class A:
        def PlaySound(self, s, asyn, loop):
            print(s)
            return s
        def IsBusy(self):
            return False
        def SetChannelVolume(self, c, v):
            pass
        def StopChannel(self, c, v):
            pass
    a = A()

    class B:
        def loving(self):
            pass
        def off(self):
            return False
    b = B()

    p = Purr()
    p.PurrThread(a)
    p.audio = a
#    p.face = b
    p.is_purring = True
    p.purr_motor_thread()
