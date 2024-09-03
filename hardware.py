import os
import sys
import inspect
from pathlib import Path
from config import cf

import RPi.GPIO as GPIO
BUTTON = 17

from speech_tools import speech_generator
from listen_tools import speech_listener
from camera_tools import Camera
from error_handling import RaiseError

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir+'/raspberryPi/')
from rasp_leds import LEDS
#from pixels import Pixels

HW = 0

class Hardware:
    mouth = 0
    ears = 0
    eyes = 0
    leds = 0
    def __init__(self):

        # Init the body parts
        try:
            self.mouth = speech_generator()
        except Exception as e:
            RaiseError("AI():Could not init speech generator. " + str(e))
            return # fatal
        try:
            self.ears = speech_listener()
        except Exception as e:
            RaiseError("AI():Could not init listener. " + str(e))
            return # fatal
        try:
            self.eyes = Camera()
        except Exception as e:
            RaiseError("AI():Could not init camera. " + str(e))
        try:
            self.leds = LEDS()
#            self.leds = Pixels()
        except Exception as e:
            RaiseError("AI():Could not init LEDs. " + str(e))

    def Close(self):
        self.mouth.Close()
        self.ears.Close()
        self.eyes.Close()
        self.leds.Close()

HW = Hardware()
