#! /usr/bin/python
# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!
import os
import inspect
import sys
import re
import time
from datetime import datetime
import subprocess
import socket
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from picamera2 import Picamera2

#import RPi.GPIO as GPIO
import gpiozero
BUTTON = 17


# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)


# check the camera
try:
    cam = Picamera2()
except:
    cam = False 
# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)


#GPIO.setmode(GPIO.BCM)
#GPIO.setup(BUTTON, GPIO.IN)
btn = gpiozero.Button(BUTTON)

hostname = socket.gethostname()
start = datetime.now()

while (not btn.is_pressed) and (datetime.now()-start).total_seconds() < (60*10):
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    SSID = ""
    IP = ""
    try:
        cmd = "hostname -I | cut -d' ' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except:
        pass

    try:
        cmd = "/usr/sbin/iwgetid -r"
        SSID = subprocess.check_output(cmd, shell=True).decode("utf-8")
#        if SSID in ("", False, None, hostname) and IP.count(".")<3:
    except Exception as e:
        start = datetime.now()  # don't time out if wainting for IP
        SSID=hostname

    # Write four lines of text.

    if IP.count(".")>=3:
        draw.text((x, top + 0), "IP: " + IP, font=font, fill=255)   # L1: write IP
        draw.text((x, top + (height/4)), SSID, font=font, fill=255) # L2: write the SSID
 
    if IP.count(".")<3:
        draw.text((x, top + ((height/4)*2)), "Waiting for IP...", font=font, fill=255)
        draw.text((x, top + ((height/4)*3)), " ", font=font, fill=255)

    elif SSID == hostname:
        draw.text((x, top + ((height/4)*2)), f"Sign onto {hostname}", font=font, fill=255)
        draw.text((x, top + ((height/4)*3)), "to select wifi", font=font, fill=255)
    else:
        draw.text((x, top + ((height/4)*2)), f"Welcome to {hostname}!", font=font, fill=255)
        draw.text((x, top + ((height/4)*3)), "Press The Button", font=font, fill=255)

    disp.image(image)
    disp.show()
    time.sleep(1)

# Clear display.
disp.fill(0)
disp.show()

#os.chdir('/home/el3ktra/LilL3x/')
#sys.path.append('/home/el3ktra/LilL3x/')

#import lillex
#l = lillex.Lill3x()
#l.loop()
