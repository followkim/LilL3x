import sys
import os
from time import sleep
import math
import time

import board

import neopixel

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D12

# The number of NeoPixels
num_pixels = 48

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

#from gpiozero import LED
#from apa102 import APA102
#from config import cf

sys.path.insert(0, '..')
from globals import STATE, SleepOn
from config import cf
from error_handling import *

COLORS_RGB = {
    'blue':[0, 0, 255, 100],
    'green':[0, 255, 0, 100],
    'orange':[255, 128, 0, 100],
    'pink':[255, 51, 153, 100],
    'purple':[128, 0, 128, 100],
    'red':[255, 0, 0, 100],
    'white':[255, 255, 255, 100],
    'yellow':[255, 255, 51, 100],
    'off':[0, 0, 0, 0],
}

COLOR_CYCLE = [COLORS_RGB['red'], COLORS_RGB['orange'], COLORS_RGB['yellow'], COLORS_RGB['green'], COLORS_RGB['blue'], COLORS_RGB['purple']]
#MAX_BRIGHTNESS = APA102.MAX_BRIGHTNESS
#NUM_LEDS = 12

class LEDS:
    color = COLORS_RGB['off']
    should_quit = False
    state = "idle"
    pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER)
    def __init__(self):
        pass

    def SetColor(self, inColor):
        color = None
        try:
            if isinstance(inColor, str):
                if inColor[0]=="#":
                    int_value = int(inColor[1:], 16)
                    color = [(int_value >> 16) & 0xFF, (int_value >> 8) & 0xFF, int_value & 0xFF, 100].copy()

                else: color = COLORS_RGB[inColor].copy()
            else:
                color = inColor.copy()
        except Exception as e:
            LogError(f"LEDS:SetColor Exception setting color {str(inColor)}: {e.args}")
        return color

    def LEDThread(self):
        LogInfo("LEDThread started")
        r = 0    # r for rainbow cycle
        brightDelta = 1
        br = 0   # brightness for pulsing
        has_error = False
        cycle_index = 0  # for cycling through solid colors
        while not self.should_quit:
            try:
#                LogDebug(f"Eye state = {self.state}")
                if not self.state or self.state == "idle":

                    #reset other states
                    br = 0  # reset brightness for pulsing to off 
                    brightDelta = 1

                    # If sleeping, dim the lights
                    self.pixels.fill((0, 0, 0)) # Sets all pixels to black
                    self.pixels.show()          # Updates the strip to show the change
                    while self.state == "idle" and not self.should_quit:
                        if STATE.IsSleeping(): sleep(1)
                        else: sleep(0.1)  # brief stay in idle, be ready 

                elif self.state == "thinking":
                    r = self.rainbow_cycle(r)
                    self.pixels.show()
                    sleep(0.001)

                elif self.state == "loving":
                    c  = self.SetColor(COLOR_CYCLE[cycle_index])
                    (br, brightDelta) = bounce(br, 0.01, brightDelta)
                    if br == 0:
                        cycle_index = (cycle_index + 1) % len(COLOR_CYCLE)
                    self.pixels.fill((int(c[0] * br), int(c[1] * br), int(c[2] * br)))
                    self.pixels.show()
                    sleep(0.1)

                elif self.state == "listening":
                    br = (max(min(STATE.volume/cf.g('MAX_VOLUME'), 1.0), 0) * 0.90) + 0.10
                    talk = self.SetColor(cf.g('LISTEN_LED'))
                    self.pixels.fill((int(talk[0] * br), int(talk[1] * br), int(talk[2] * br)))
                    self.pixels.show()
                    has_error = False
            except Exception as e:
                LogError(f"LEDS:LedThread exception: {str(e)}:{e.args}")
                if has_error: self.should_quit = True
                else: has_error = True

        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        LogInfo("LEDThread ended")


    def off(self):
        self.state = "idle"
        LogDebug("LEDS idle")

    def listening(self):
        self.state = 'listening'
        LogDebug("LEDS Listening")

    def thinking(self):
        self.state = "thinking"
        LogDebug("LEDS thinking")

    def loving(self):
        if self.state != "loving": LogDebug("LEDS loving")
        self.state = "loving"

    def idle(self):
        self.off()

    def Close(self):
        self.should_quit = True

    def rainbow_cycle(self, j, step=1):
        if j >= 255: j = j % 255
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            self.pixels[i] = wheel(pixel_index & 255)
        return j + step

def rainbow_cycle(i, j, step=1):
    color = wheel((i+j) & 255)
    i = i + step
    if i >= 256:
        i = i % 256
        j = j + step
        if j >= 256: j = j % 256
    return (i, j, color)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in {neopixel.RGB, neopixel.GRB} else (r, g, b, 0)

def bounce(cur, step=0.1, delta=1, min_val=0, max_val=0.5):
    """Bounces a number between two values."""
    cur = cur + (step * delta)
    if cur > max_val:
        cur = max_val
        delta = -1
    elif cur < min_val:
        cur = min_val
        delta = 1
    return (cur, delta)
