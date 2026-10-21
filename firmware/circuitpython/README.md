# ESP32 firmware (CircuitPython)

The board end of Stage 1a. It drives the LEDs and reads the sensor when the computer
asks; the measurement itself is `spectra.capture` on the computer. Ruled 2026-10-06
in `docs/DECISIONS.md`.

## Wiring, with the board seen from the top

The GPIO numbers are printed beside each header pin on the DevKitC-1.

| ESP32 pin | To |
|---|---|
| 3V3 | AS7341 VIN |
| G | AS7341 GND |
| 8 | AS7341 SDA |
| 9 | AS7341 SCL |
| 5V | TLC59711 V+ (chip power and LED supply) |
| G | TLC59711 GND |
| 12 | TLC59711 CI (clock in) |
| 11 | TLC59711 DI (data in) |
| nothing | TLC59711 VCC |

The driver's VCC stays unconnected: Adafruit's wiring for 3.3 V logic is V+ at 4 to
17 V and VCC left open, so the chip runs from its own regulator and reads the ESP32's
3.3 V clock and data cleanly. Eight LEDs at 15 mA is 120 mA, well inside a USB port.

**The 5V pin is dead until the IN-OUT pads are bridged.** The boards in hand are a
DevKitC-1 clone (N16R8 module, the pin is labelled **5Vin**). A diode lets 5Vin feed
the board but blocks USB power from coming out of it. Two solder pads on the front,
marked **IN-OUT** with an arrow, beside the three small diodes at pins 11 and 12,
bypass that diode, and they ship open. Found on the bench on 2026-10-08: the sensor
answered and every command returned OK, but no LED lit on any of the twelve
channels. 3V3 read 3.3 V while 5V read near zero. The driver had no power, and an
unpowered TLC59711 takes its data without complaint and lights nothing.

**Not the USB-OTG pads on the back.** Those send the board's 5 V out to the USB port
for host mode and do nothing for the header pin. They were bridged first, by mistake;
5Vin still read 0.3 V with 5 V on both pads. IN-OUT bridged on 2026-10-15 put 4.67 V
on the driver's V+. The bare board that goes in the puck needs the same bridge before
it is closed in.

Bridged, the 5V pin is wired straight to the computer's USB power. Power the board
from its USB cable only, never also from a supply on the 5V pin, or that supply drives
current back into the computer's port. The puck is USB-powered, so this costs it
nothing. The check, if a board is in doubt: 5V to G should read about 5 V with only
the USB cable in.

LEDs: long leg (anode) to the driver's V+, short leg (cathode) to a channel output.
No series resistors; the board fixes each channel at about 15 mA.

## Flashing, once

Plug into the port marked **COM** and run, from the repo root:

```sh
firmware/circuitpython/flash.sh
```

It reads the chip's flash and PSRAM with esptool and picks the matching
CircuitPython build. It flashes the board and tells you to move the cable to the
port marked **USB** (the port the puck's opening is cut for). Then it copies
`code.py` onto the CIRCUITPY drive, installs `adafruit_as7341` and
`adafruit_tlc59711` with circup, and asks for one press of RST so `code.py` starts
with its drivers in place. It ends by asking the board for `ID` and one `READ`.
`--no-flash` redoes only the files and drivers. Its tools live in `~/.venvs/esp`.

If esptool cannot reach the chip, close anything holding the port (a browser tab
counts). If it still can't, hold BOOT, tap RST, release BOOT, and run it again.

**The bridge answers on the console, on the port marked USB.** There is no
`boot.py`. On macOS (2026-10-15) every USB setup that enabled CircuitPython's
separate data channel enumerated but was never configured, so no serial port
appeared; with two serial channels and the drive the S3 also runs out of endpoints
and boots into safe mode. The default setup (console + drive) works, so `code.py`
reads commands on the console and turns auto-reload off, so a save to the drive
cannot print into a reading. The port marked **COM** carries only the ROM boot log.

## Checking it

On the computer, from this repo with `pip install -e '.[capture]'`:

```sh
python -c "from spectra.capture import serial_hw as s; S, L = s.connect('auto'); print(S.read())"
```

Ten counts printed means the cable, the firmware and the sensor all work.

**Channel numbers run backwards against the driver's silkscreen.** The library's
channel 0 is the last output group, checked on the bench on 2026-10-15 (an LED on R3
lit on channel 0 and not on 9):

| channel | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| output | R3 | G3 | B3 | R2 | G2 | B2 | R1 | G1 | B1 | R0 | G0 | B0 |

Only R3 = 0 was lit on the bench; the rest of the row follows from the library
source (`set_channel` and the chip's B3-first shift order). Light channel 0 alone
before any LED goes in the head:

```sh
python -c "from spectra.capture import serial_hw as s; S, L = s.connect('auto'); L.set(0, 1.0); input('Enter for off '); L.off()"
```

If it says the hardware was not found, open the port marked USB at 115200 and
press Ctrl-D: the board reboots and prints the exact error.

## What it does not do

No maths, no session files, no averaging, no saturation check: all of that is
`spectra.capture`, tested on the computer. The board's own RGB LED is switched off at
start; its red power LED is not switchable, so cover it with black tape before any
dark reading.

## The glow demo

`glow.py` is a slow demo, not the measurement: each breath the LEDs go dark while
the sensor reads the room, then a wave rolls violet to deep red, each LED as bright
as its band. Copy it onto the drive as `code.py`; copy the bridge `code.py` back to
return to `spectra.capture`.
