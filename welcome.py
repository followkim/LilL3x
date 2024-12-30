#! /usr/bin/python
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw
import adafruit_ssd1306
from config import cf

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
image = Image.open(cf.g('WELCOME_IMAGE')).convert("1")

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
disp.image(image)
disp.show()
