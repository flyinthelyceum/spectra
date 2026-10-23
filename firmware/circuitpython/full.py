"""Full: every LED on at full current, and it stays on. A bench test, not the measurement.

All eight LEDs (TLC channels 0-7) go to 65535 at maximum global brightness, so each
one runs at the driver's full constant current. The AS7341 reads the room once with
everything dark, then keeps reading with everything lit and prints one line every
few seconds: gain, the eight bands, and clear. Lit minus dark is the LEDs' own light
coming back. Watching the lines over time shows warm-up drift.

The 400 nm LED is UV at full current. Don't look into the head while this runs.

To run it, copy this file onto the CIRCUITPY drive as `code.py`. It replaces the
bridge for as long as it runs, so `spectra.capture` and `scripts/ledtest.py` get no
answer. To go back, copy the bridge `code.py` from this folder onto the drive again
and press RST.

Same pins and channel map as the bridge, `glow.py` and `scripts/ledtest.py`.
"""

import time

import board
import busio

import adafruit_as7341
import adafruit_tlc59711

SDA_PIN = "IO8"
SCL_PIN = "IO9"
SCK_PIN = "IO12"
MOSI_PIN = "IO11"

TLC_CHANNELS = 12
LED_CHANNELS = range(8)   # 0 white, 1 UV, 2 blue, 3 cyan, 4 green, 5 yellow, 6 red, 7 deep red
EVERY = 5.0               # seconds between lit reads

# 50 ms per pass. Full scale is (ATIME + 1) * (ASTEP + 1) counts.
ATIME = 29
ASTEP = 599
FULL = min(65535, (ATIME + 1) * (ASTEP + 1))

GAIN_NAMES = (
    "GAIN_0_5X", "GAIN_1X", "GAIN_2X", "GAIN_4X", "GAIN_8X", "GAIN_16X",
    "GAIN_32X", "GAIN_64X", "GAIN_128X", "GAIN_256X", "GAIN_512X",
)


def status_led_off():
    """Dark the board's RGB LED, as the bridge does: it sits beside the sensor."""
    import digitalio
    import neopixel_write

    for name in ("IO48", "IO38"):
        pin = getattr(board, name, None)
        if pin is None:
            continue
        try:
            io = digitalio.DigitalInOut(pin)
            io.direction = digitalio.Direction.OUTPUT
            neopixel_write.neopixel_write(io, bytearray(3))
            io.deinit()
        except Exception:  # noqa: BLE001 - pin claimed by the status LED driver
            pass


class Full:
    def __init__(self):
        i2c = busio.I2C(getattr(board, SCL_PIN), getattr(board, SDA_PIN))
        self.sensor = adafruit_as7341.AS7341(i2c)
        self.sensor.led = False
        self.sensor.atime = ATIME
        self.sensor.astep = ASTEP
        spi = busio.SPI(getattr(board, SCK_PIN), MOSI=getattr(board, MOSI_PIN))
        self.tlc = adafruit_tlc59711.TLC59711(spi)
        # Global brightness to the top of its 7-bit range. The attribute names
        # differ between library versions, so set whichever this one has.
        for name in ("bcr", "bcg", "bcb", "red_brightness", "green_brightness", "blue_brightness"):
            if hasattr(self.tlc, name):
                setattr(self.tlc, name, 127)
        self.gain = 7                       # 64x, then it finds its own

    def set_all(self, value):
        for ch in range(TLC_CHANNELS):
            self.tlc.set_channel(ch, value if ch in LED_CHANNELS else 0)
        self.tlc.show()

    def read(self):
        """Step the gain until the brightest band sits between a tenth of full
        scale and nine tenths, then return the gain and the eight bands."""
        for _ in range(11):
            self.sensor.gain = getattr(adafruit_as7341.Gain, GAIN_NAMES[self.gain])
            bands = list(self.sensor.all_channels)
            peak = max(bands)
            if peak > 0.9 * FULL and self.gain > 0:
                self.gain -= 1
            elif peak < 0.1 * FULL and self.gain < len(GAIN_NAMES) - 1:
                self.gain += 1
            else:
                break
        return 2 ** (self.gain - 1), bands, self.sensor.channel_clear


def main():
    status_led_off()
    try:
        full = Full()
    except Exception as e:  # noqa: BLE001
        print("full: hardware not found:", e)
        while True:
            time.sleep(1)
    full.set_all(0)
    time.sleep(0.2)
    x, bands, clear = full.read()
    print("full: dark  gain %gx  bands %s  clear %d" % (x, " ".join(str(b) for b in bands), clear))
    full.set_all(65535)
    print("full: channels 0-7 at 65535, brightness 127. Reading every %.0f s." % EVERY)
    t0 = time.monotonic()
    while True:
        x, bands, clear = full.read()
        saturated = "  (saturated at 0.5x)" if x == 0.5 and max(bands) > 0.9 * FULL else ""
        print("full: lit %4.0fs  gain %gx  bands %s  clear %d%s"
              % (time.monotonic() - t0, x, " ".join(str(b) for b in bands), clear, saturated))
        time.sleep(EVERY)


main()
