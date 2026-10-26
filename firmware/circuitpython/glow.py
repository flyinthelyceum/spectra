"""Glow: a slow demo for the bench rig. Not the measurement.

The LEDs listen and answer. Each breath they go dark for a moment while the
AS7341 reads the room, then a slow wave rolls from violet to deep red across the
seven coloured LEDs, each one as bright as the room is in its band. Hold a
coloured card or a phone screen over the sensor and the next breath answers in
that colour.

To run it, copy this file onto the CIRCUITPY drive as `code.py`. It replaces the
bridge for as long as it runs, so `spectra.capture` and `scripts/ledtest.py` get
no answer. To go back, copy the bridge `code.py` from this folder onto the drive
again and press RST.

Same pins and channel map as the bridge and `scripts/ledtest.py`. Each breath
prints one line on the console: the gain, the room's eight bands, and the clear
channel twice, dark and at the middle of the wave. The difference is the LEDs' own
light coming back to the sensor.
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

# TLC channel, and the AS7341 bands that LED answers for, in wavelength order so
# the wave rolls violet to red. White (channel 0) stays dark: it would wash the
# others out.
LEDS = (
    (1, (0,)),      # 400 UV          f1 415
    (2, (1, 2)),    # 460 blue        f2 445, f3 480
    (3, (2, 3)),    # 501 cyan        f3 480, f4 515
    (4, (4,)),      # 565 green       f5 555
    (5, (5,)),      # 590 yellow      f6 590
    (6, (6,)),      # 625 red         f7 630
    (7, (7,)),      # 660 deep red    f8 680
)

RISE = 3.0        # seconds for one LED to swell
FALL = 3.0        # and to fade
STAGGER = 0.45    # seconds between one LED starting and the next
LISTEN = 1.2      # dark seconds between waves, while the sensor reads
MAX_LEVEL = 0.6   # the brightest any LED gets, as a fraction of full
GAMMA = 2.2       # so a fade looks even to the eye, not to the meter

# 50 ms per pass. Full scale is (ATIME + 1) * (ASTEP + 1) counts.
ATIME = 29
ASTEP = 599
FULL = min(65535, (ATIME + 1) * (ASTEP + 1))
TOO_DARK = 20     # counts at the top gain below which the room says nothing

GAIN_NAMES = (
    "GAIN_0_5X", "GAIN_1X", "GAIN_2X", "GAIN_4X", "GAIN_8X", "GAIN_16X",
    "GAIN_32X", "GAIN_64X", "GAIN_128X", "GAIN_256X", "GAIN_512X",
)

WAVE = (len(LEDS) - 1) * STAGGER + RISE + FALL


def smooth(x):
    return x * x * (3 - 2 * x)


def envelope(u):
    """0 to 1 to 0 over RISE + FALL seconds, flat zero outside."""
    if u <= 0 or u >= RISE + FALL:
        return 0.0
    if u < RISE:
        return smooth(u / RISE)
    return smooth(1 - (u - RISE) / FALL)


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


class Glow:
    def __init__(self):
        i2c = busio.I2C(getattr(board, SCL_PIN), getattr(board, SDA_PIN))
        self.sensor = adafruit_as7341.AS7341(i2c)
        self.sensor.led = False
        self.sensor.atime = ATIME
        self.sensor.astep = ASTEP
        spi = busio.SPI(getattr(board, SCK_PIN), MOSI=getattr(board, MOSI_PIN))
        self.tlc = adafruit_tlc59711.TLC59711(spi)
        self.gain = 7                       # 64x, then it finds its own
        self.shares = [0.0] * len(LEDS)
        self.dark()

    def dark(self):
        for ch in range(TLC_CHANNELS):
            self.tlc.set_channel(ch, 0)
        self.tlc.show()

    def show(self, levels):
        for (ch, _), level in zip(LEDS, levels):
            self.tlc.set_channel(ch, int(65535 * MAX_LEVEL * level ** GAMMA))
        self.tlc.show()

    def listen(self):
        """Read the room with every LED off, stepping the gain until the
        brightest band sits between a tenth of full scale and nine tenths."""
        for _ in range(4):
            self.sensor.gain = getattr(adafruit_as7341.Gain, GAIN_NAMES[self.gain])
            bands = list(self.sensor.all_channels)
            peak = max(bands)
            if peak > 0.9 * FULL and self.gain > 0:
                self.gain -= 1
            elif peak < 0.1 * FULL and self.gain < len(GAIN_NAMES) - 1:
                self.gain += 1
            else:
                break
        clear = self.sensor.channel_clear
        if peak >= TOO_DARK:
            # Each LED's share of the room, against the brightest band. Square
            # root, so a faint band still shows as a faint glow, not nothing.
            raw = [sum(bands[i] for i in idx) / len(idx) for _, idx in LEDS]
            top = max(raw) or 1
            self.shares = [(max(r, 0) / top) ** 0.5 for r in raw]
        return bands, peak, clear

    def wave(self):
        """One violet-to-red roll. Reads the clear channel once at the middle,
        where every fade is at its slowest, so the read cannot be seen."""
        t0 = time.monotonic_ns()
        lit = None
        while True:
            t = (time.monotonic_ns() - t0) / 1e9
            if t >= WAVE:
                break
            self.show([s * envelope(t - i * STAGGER) for i, s in enumerate(self.shares)])
            if lit is None and t >= WAVE / 2:
                lit = self.sensor.channel_clear
            time.sleep(0.01)
        self.dark()
        return lit


def main():
    status_led_off()
    try:
        glow = Glow()
    except Exception as e:  # noqa: BLE001
        print("glow: hardware not found:", e)
        while True:
            time.sleep(1)
    print("glow: listening, then answering, every %.0f s" % (WAVE + LISTEN))
    breath = 0
    while True:
        start = time.monotonic_ns()
        bands, peak, clear = glow.listen()
        rest = LISTEN - (time.monotonic_ns() - start) / 1e9
        if rest > 0:
            time.sleep(rest)
        lit = glow.wave()
        breath += 1
        x = 2 ** (glow.gain - 1)
        room = " ".join(str(b) for b in bands)
        note = "" if peak >= TOO_DARK else "  (too dark, last colour kept)"
        print("breath %d  gain %gx  room %s  clear dark %d lit %d%s" % (breath, x, room, clear, lit, note))


main()
