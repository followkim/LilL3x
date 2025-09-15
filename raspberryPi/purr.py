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
    face = False
    fsr1 = 22
    fsr2 = 23
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.fsr1, GPIO.IN)
        GPIO.setup(self.frs2, GPIO.IN)

        # Define the GPIO pin connected to the LED
        led_pin = 13
        self.motor = PWMLED(led_pin)

    def PurrThread(self, audio, face):
        startPet = False
        lastPet = False
        self.audio = audio
        self.face = face
        LogInfo("PurrThread started")
        while not self.should_quit:

            if GPIO.input(self.fsr1) or GPIO.input(self.fsr2):
                waitFsr = self.fsr1 if GPIO.input(self.fsr2) else self.fsr2
                is_petting = True
                LogDebug("Petting Detected")
                startPet = datetime.now()
                lastPet = startPet
                while is_petting == True:
                    while notGPIO.input(waitFsr) and is_petting and not self.should_quit:
                        if lastPet + timedelta(seconds=cf.g('STROKE_TO')) < datetime.now() or self.should_quit:
                            is_petting = False
                            self.is_purring = False
                            LogDebug("Petting Ended")
                            break
                        else: sleep(0.1)
                    if not is_petting: break
                    waitFsr = self.fsr1 if GPIO.input(self.fsr2) else self.fsr2
                    lastPet = datetime.now()
                    if startPet + timedelta(seconds=cf.g('PURR_SEC')) < datetime.now():
                        self.purr_motor()
            else: sleep(cf.g('PURR_SLEEP'))
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
        startPurr = datetime.now()
        purr_channel = self.audio.PlaySound(cf.g('PURR_MP3'), asyn=True, loop=True)

        # Define sine wave parameters
        frequency = 0.5  # Hz (determines how fast the sine wave cycles)
        amplitude = 0.5  # Controls the range of brightness (0 to 1)
        offset = 0.5     # Shifts the sine wave up to ensure values are positive (0 to 1)

        # Loop to continuously update LED brightness
        t = 0
        while self.is_purring and not self.should_quit:
            volume = (min((datetime.now() - startPurr).total_seconds() / (10 * 60), 1) * 0.75) + 0.25
            self.audio.SetChannelVolume(purr_channel, volume)
            # Calculate sine wave value (scaled and offset for brightness)
            brightness = amplitude * sin(2 * pi * frequency * t) + offset
            t += 0.01  # Adjust for smoother or faster animation

            # Ensure brightness stays within valid range (0 to 1)
            brightness = max(0, min(1, brightness))
            self.motor.value = (brightness)/2 + 0.5 # range 0.5-1 to always have some power

            if startPurr + timedelta(seconds=cf.g('PURR_SEC')) < datetime.now(): self.face.loving()

            # Increment time and control update speed
            sleep(0.25) # Small sleep to allow the Pi to perform other tasks


        self.motor.off() # Turn off the LED on exit
        self.audio.StopChannel(purr_channel, cf.g("PURR_FO"))
        self.face.off()

    def Close(self):
        self.should_quit = True


if __name__ == '__main__':
    class A:
        def PlaySound(s):
            print(s)
        def IsBusy():
            return False
    a = A()

    class B:
        def loving():
            print(s)
        def off():
            return False
    b = B()

    p = Purr()
    p.PurrThread(a, b)
