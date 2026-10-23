"""The ESP32 end of Stage 1a: the sensor and the LEDs, answered over USB.

Copy to the CIRCUITPY drive (no `boot.py`). Needs `adafruit_as7341` and
`adafruit_tlc59711` in `lib/` (`circup install adafruit_as7341 adafruit_tlc59711`).

Why a bridge and not the measurement itself: the dark/white/sample cycle, the
saturation stop and the session files are `spectra.capture`, already written and
tested. This file only does what the Pi did through Blinka, so that code runs
unchanged on the computer at the other end of the cable. Ruled 2026-10-06
(`docs/DECISIONS.md`).

One line in, one line out, on the USB console:

    ID                  -> SPECTRA ESP32 1
    CFG gain atime astep -> OK          gain is the AGAIN code, 0 (0.5x) to 10 (512x)
    READ                -> CH f1 f2 f3 f4 f5 f6 f7 f8 clear nir
    SET channel word    -> OK          word is the 16-bit PWM value, 0 to 65535
    OFF                 -> OK          every channel off
    anything that fails -> ERR message

Pins are the ESP32-S3's own defaults for I2C and SPI (Espressif's Arduino
variant: SDA 8, SCL 9, MOSI 11, SCK 12). CircuitPython's DevKitC-1 boards name no
I2C or SPI pins, so they are chosen here. They are clear of the strapping pins,
the USB pins and the octal PSRAM pins on N8R8 modules.
"""

PROTOCOL = "SPECTRA ESP32 1"

SDA_PIN = "IO8"
SCL_PIN = "IO9"
SCK_PIN = "IO12"
MOSI_PIN = "IO11"

TLC_CHANNELS = 12

# The Adafruit AS7341 driver waits a fixed 1.0 s for data, so a longer pass can
# only fail. Same limit as `hw.MAX_PASS_MS` on the host.
MAX_PASS_MS = 1000.0

# The AS7341 AGAIN codes, in register order. The same table as `hw.RealSensor`.
GAIN_NAMES = (
    "GAIN_0_5X", "GAIN_1X", "GAIN_2X", "GAIN_4X", "GAIN_8X", "GAIN_16X",
    "GAIN_32X", "GAIN_64X", "GAIN_128X", "GAIN_256X", "GAIN_512X",
)


class Head:
    """The AS7341 and the TLC59711 on this board's pins."""

    def __init__(self):
        import board
        import busio
        import adafruit_as7341
        import adafruit_tlc59711

        self._lib = adafruit_as7341
        i2c = busio.I2C(getattr(board, SCL_PIN), getattr(board, SDA_PIN))
        self._sensor = adafruit_as7341.AS7341(i2c)
        # The breakout's own white LED would light the sample from the wrong
        # angle. Off, and kept off: nothing here turns it on.
        self._sensor.led = False
        # No MISO: the TLC59711 is write only.
        spi = busio.SPI(getattr(board, SCK_PIN), MOSI=getattr(board, MOSI_PIN))
        self._tlc = adafruit_tlc59711.TLC59711(spi)
        self.off()

    def configure(self, gain, atime, astep):
        self._sensor.gain = getattr(self._lib.Gain, GAIN_NAMES[gain])
        self._sensor.atime = atime
        self._sensor.astep = astep

    def read(self):
        f = self._sensor.all_channels
        return tuple(f) + (self._sensor.channel_clear, self._sensor.channel_nir)

    def set(self, channel, word):
        # Outputs latch: clear every other channel in the same write, so SET
        # means "this channel alone" and two wavelengths are never on at once.
        for other in range(TLC_CHANNELS):
            self._tlc.set_channel(other, word if other == channel else 0)
        self._tlc.show()

    def off(self):
        for channel in range(TLC_CHANNELS):
            self._tlc.set_channel(channel, 0)
        self._tlc.show()


def _ints(args, n):
    if len(args) != n:
        raise ValueError("expected %d numbers, got %d" % (n, len(args)))
    return [int(a) for a in args]


def handle(line, head):
    """One command line to one reply line. Never raises: a failure is `ERR`."""
    parts = line.split()
    if not parts:
        return None
    cmd, args = parts[0].upper(), parts[1:]
    try:
        if cmd == "ID":
            return PROTOCOL
        if cmd == "CFG":
            gain, atime, astep = _ints(args, 3)
            if not 0 <= gain < len(GAIN_NAMES):
                raise ValueError("gain code must be 0-10, got %d" % gain)
            if not 0 <= atime <= 255 or not 0 <= astep <= 65534:
                raise ValueError("atime 0-255 and astep 0-65534")
            if (atime + 1) * (astep + 1) * 2.78 / 1000.0 >= MAX_PASS_MS:
                raise ValueError("integration over 1000 ms per pass; the driver cannot wait that long")
            head.configure(gain, atime, astep)
            return "OK"
        if cmd == "READ":
            _ints(args, 0)
            return "CH " + " ".join(str(v) for v in head.read())
        if cmd == "SET":
            channel, word = _ints(args, 2)
            if not 0 <= channel < TLC_CHANNELS:
                raise ValueError("channel must be 0-11, got %d" % channel)
            if not 0 <= word <= 65535:
                raise ValueError("word must be 0-65535, got %d" % word)
            head.set(channel, word)
            return "OK"
        if cmd == "OFF":
            _ints(args, 0)
            head.off()
            return "OK"
        return "ERR unknown command " + cmd
    except Exception as e:  # noqa: BLE001 - every failure must reach the host as a line
        return "ERR " + (str(e) or type(e).__name__)


def _status_led_off():
    """Dark the board's RGB LED. It sits in the case with the head, and a dark
    reading must see no light but the room's. GPIO48 on DevKitC-1 v1.0, GPIO38
    on v1.1; writing black to whichever is not the LED drives a spare pin low."""
    import board
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


def main():
    import usb_cdc

    import supervisor

    _status_led_off()
    # The data channel when boot.py enables one; otherwise the console. On the
    # MacBook (2026-10-15) any configuration with the data channel enumerated but
    # was never configured by macOS, so the default USB setup (console + drive) is
    # the one that works, and the bridge answers on the console. Auto-reload off,
    # so a save to the drive cannot print a status line into a reading.
    supervisor.runtime.autoreload = False
    port = usb_cdc.data or usb_cdc.console
    port.timeout = 0.1
    try:
        head = Head()
        print("spectra: sensor and driver found; listening")
    except Exception as e:  # noqa: BLE001
        head = None
        print("spectra: hardware not found:", e)

    buf = b""
    while True:
        chunk = port.read(64)
        if not chunk:
            continue
        buf += chunk
        while b"\n" in buf:
            raw, buf = buf.split(b"\n", 1)
            line = raw.decode("utf-8", "replace").strip()
            if head is None and line.upper().split()[:1] != ["ID"]:
                reply = "ERR hardware not found; check the wiring and press RST"
            else:
                reply = handle(line, head)
            if reply is not None:
                port.write((reply + "\n").encode())


if __name__ == "__main__":
    main()
