import sys
import os
from gpiozero import PWMLED
from math import sin, pi
from time import sleep
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import gpiozero

sys.path.insert(0, '..')
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
    def __init__(self):
        START_BUTTON = 22
        END_BUTTON = 23
#        GPIO.setmode(GPIO.BCM)
#        GPIO.setup(self.BUTTON, GPIO.IN)
        self.aBtn = gpiozero.Button(START_BUTTON)
        self.bBtn = gpiozero.Button(END_BUTTON)

        # Define the GPIO pin connected to the LED
        led_pin = 13
        self.motor = PWMLED(led_pin)

    def PurrThread(self, audio):
        startPet = False
        lastPet = False
        self.audio = audio
        LogInfo("PurrThread started")
        while not self.should_quit:

            if self.aBtn.is_pressed or self.bBtn.is_pressed:
                waitBtn = self.aBtn if self.bBtn.is_pressed else self.bBtn
                is_petting = True
                LogDebug("Petting Detected")
                startPet = datetime.now()
                lastPet = startPet
                while is_petting == True:
                    while not waitBtn.is_pressed and is_petting and not self.should_quit:
                        if lastPet + timedelta(seconds=cf.g('STROKE_TO')) < datetime.now() or self.should_quit:
                            is_petting = False
                            self.is_purring = False
                            LogDebug("Petting Ended")
                            break
                        else: sleep(0.1)
                    if not is_petting: break
                    waitBtn = self.aBtn if self.bBtn.is_pressed else self.bBtn
                    lastPet = datetime.now()
                    LogDebug("Stroke")
                    if startPet + timedelta(seconds=cf.g('PURR_SEC')) < datetime.now():
                        self.purr_motor()
                sleep(1)
            else: sleep(30)
        LogInfo("PurrThread exit.")

    def purr_motor(self):
        self.is_purring = True
        if not self.Purring():
            self.purr_thread = threading.Thread(target=self.purr_motor_thread, daemon=True)
            self.purr_thread.name = f"{GetHostname()} PurrMotorThread"
            self.purr_thread.start()

    def Purring(self):
        return self.purr_thread and self.purr_thread.is_alive()

    def purr_motor_thread(self):
        # play purring
        purr_channel = self.audio.PlaySound(cf.g('PURR_MP3'), asyn=True, loop=True)

        # Define sine wave parameters
        frequency = 0.5  # Hz (determines how fast the sine wave cycles)
        amplitude = 0.5  # Controls the range of brightness (0 to 1)
        offset = 0.5     # Shifts the sine wave up to ensure values are positive (0 to 1)

        # Loop to continuously update LED brightness
        t = 0
        while self.is_purring and not self.should_quit:
            # Calculate sine wave value (scaled and offset for brightness)
            brightness = amplitude * sin(2 * pi * frequency * t) + offset

            # Ensure brightness stays within valid range (0 to 1)
            brightness = max(0, min(1, brightness))
            self.motor.value = (brightness)/2 + 0.5 # range 0.5-1 to always have some power

            # Increment time and control update speed
            t += 0.01  # Adjust for smoother or faster animation
            sleep(0.01) # Small sleep to allow the Pi to perform other tasks

        self.motor.off() # Turn off the LED on exit
        self.audio.StopChannel(purr_channel, cf.g("PURR_FO"))

    def Close(self):
        self.should_quit = True


if __name__ == '__main__':
    class A:
        def PlaySound(s):
            print(s)
        def IsBusy():
            return False
    a = A()

    p = Purr()
    p.PurrThread(a)
