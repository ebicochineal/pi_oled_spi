#! /usr/bin/env python3
import sys
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

class spioled:
    def __init__(self):
        self.w = 128
        self.h = 64
        self.fontsize = 16
        self.fontpath = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
        RST = 24
        DC = 23
        SPI_PORT = 0
        SPI_DEVICE = 0
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))
        self.image = Image.new('1', (self.w, self.h))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.truetype(self.fontpath, self.fontsize, encoding='unic')
        self.disp.begin()
        self.disp.clear()
        self.disp.display()
    
    def __del__(self):
        self.disp.clear()
        self.disp.display()
    
    def image_clear(self):
        self.draw.rectangle((0, 0, self.w, self.h), outline=0, fill=0)
    
    def print(self, s, c):
        start = time.time()
        while time.time() - start < c:
            self.image_clear()
            self.draw.text((8, 8), s,  font=self.font, fill=255)
            self.disp.image(self.image)
            self.disp.display()
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        app = spioled()
        app.print(sys.argv[1], 3)