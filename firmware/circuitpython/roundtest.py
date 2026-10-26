"""One-shot test round: dark, all lit, each LED alone. Prints RT lines, then idles."""
import time, board, busio, adafruit_as7341, adafruit_tlc59711
ATIME, ASTEP = 29, 599
FULL = min(65535, (ATIME + 1) * (ASTEP + 1))
G = ("GAIN_0_5X","GAIN_1X","GAIN_2X","GAIN_4X","GAIN_8X","GAIN_16X","GAIN_32X","GAIN_64X","GAIN_128X","GAIN_256X","GAIN_512X")
i2c = busio.I2C(board.IO9, board.IO8)
s = adafruit_as7341.AS7341(i2c); s.led = False; s.atime = ATIME; s.astep = ASTEP
tlc = adafruit_tlc59711.TLC59711(busio.SPI(board.IO12, MOSI=board.IO11))
for n in ("bcr","bcg","bcb","red_brightness","green_brightness","blue_brightness"):
    if hasattr(tlc, n): setattr(tlc, n, 127)
def setch(on):
    for c in range(12): tlc.set_channel(c, 65535 if c in on else 0)
    tlc.show(); time.sleep(0.3)
def read(g=10):
    while True:
        s.gain = getattr(adafruit_as7341.Gain, G[g])
        rows = [list(s.all_channels) + [s.channel_clear] for _ in range(3)]
        b = [sum(c) // 3 for c in zip(*rows)]
        if max(b[:8]) > 0.9 * FULL and g > 0: g -= 1; continue
        return 2 ** (g - 1), b
time.sleep(1)
for label, on in [("dark", ()), ("all", range(8))] + [("ch%d" % c, (c,)) for c in range(8)] + [("dark2", ())]:
    setch(on); x, b = read()
    print("RT %s gain %g %s" % (label, x, " ".join(str(v) for v in b)))
setch(())
print("RT done")
while True: time.sleep(1)
