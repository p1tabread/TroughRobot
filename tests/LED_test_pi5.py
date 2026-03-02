# Test for https://github.com/adafruit/Adafruit_Blinka_Raspberry_Pi5_Neopixel/issues/3
# With the bug NOT fixed, some of the pixels would be corrupted.
#
# This corruption wasn't seen (or wasn't seen as much) if the Python program
# had any sleeps between updates, such as the dual_animation example. Thus,
# a dedicated reproducer for the bug is desired.

import time

import adafruit_pixelbuf
import board
from adafruit_raspberry_pi5_neopixel_write import neopixel_write

NEOPIXEL1 = board.D18
num_pixels = 2

class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
    def __init__(self, pin, size, **kwargs):
        self._pin = pin
        super().__init__(size=size, **kwargs)

    def _transmit(self, buf):
        neopixel_write(self._pin, buf)

pixels1 = Pi5Pixelbuf(NEOPIXEL1, num_pixels, auto_write=True, byteorder="GRBW", brightness=0.2)

# --- Colours are set as (R, G, B, W) tuples ---

while True:
    # Fill all pixels with one colour
    pixels1.fill((255, 0, 0, 0))    # Red
    time.sleep(1)

    pixels1.fill((0, 255, 0, 0))    # Green
    time.sleep(1)

    pixels1.fill((0, 0, 255, 0))    # Blue
    time.sleep(1)

    pixels1.fill((0, 0, 0, 255))    # White (W channel — most efficient)
    time.sleep(1)

    pixels1.fill((255, 0, 255, 0))  # Purple
    time.sleep(1)

    # Set individual pixels
    pixels1[0] = (255, 100, 0, 0)   # Orange on pixel 0
    pixels1[1] = (0, 0, 0, 128)     # Dim white on pixel 1
    time.sleep(1)

    # Change brightness on the fly
    pixels1.brightness = 0.05       # Very dim
    pixels1.fill((255, 255, 255, 0))
    time.sleep(1)

    pixels1.brightness = 1.0        # Full blast
    pixels1.fill((255, 255, 255, 0))
    time.sleep(1)