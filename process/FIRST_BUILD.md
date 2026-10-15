# First build

The order to put the first unit together in, from parts on the shelf to the first
Stage 1a number. Written 2026-10-04, the day Jared reported every part in hand.
Each step says why it comes where it does; the order is the point.

The short version: print the bore coupon, bring the electronics up on the ESP32 with
no head at all, print the head once the coupon has picked its bore, then run the
dark test, the white and the ten-read repeat. The puck and the dock come after the
head has produced a number, not before.

## Where the pieces are

Nothing below is on `main` yet. Each lives on an open PR, and only Jared merges.

| PR | Carries | State for this build |
|---|---|---|
| #6 | The 2026-09-22 rulings: 5 mm LEDs, `LED_Z` 18, `LED_SEAT_D` 5.3, ColorChecker patch 19 as the 1a white, the Pi (superseded by the ESP32, 2026-10-06) | Needed. Every LED on the shelf is 5 mm; the head on `main` has 3 mm bores. |
| #8 | `spectra.capture`: reads the AS7341 and drives the TLC59711 | Needed, and merged into this PR, which adds the ESP32 path to it (2026-10-06). |
| #7 | Stage 0 colour maths | Not needed for the first number. Needed for ΔE00. |
| #9 | The puck, and the head and detector plate to print | Carries the 5 mm rulings since 6f37bf2, all puck checks pass. **The head and plate for step 3 come from here.** |
| #10 | The dock, and the light trap | Being brought up to #9. |
| this PR | The bore coupon, this file | Print the coupon first. |

Suggested merge order: #6, then #8 (it will need #6's test fix; see #8's body),
then this one. #7 whenever.

## 1. Print the bore coupon

`python -m spectra.cad.coupon coupon.stl`, or the STL in the project files. Black
PETG, bed face down, same settings the head will use. Five 45 degree bores, 5.2 to
5.6 mm, a notch at the 5.2 end.

Press a 5 mm LED into each from the top. The right bore is the smallest one the LED
goes fully into by hand and stays in when the coupon is turned over and tapped. Set
`LED_SEAT_D` in `spectra/cad/params.py` to that bore's nominal size.

**Done 2026-10-05: 5.2 mm grips.** Jared printed the coupon and the 5.2 bore held.
5.2 is the smallest bore on the coupon, so nothing tighter was tried; it grips, so
it is the value. The case thread set `LED_SEAT_D` to 5.2 on #9 and regenerated
`head.stl` and `puck_plate.stl`. The light trap (`light-trap.stl`, a 14 x 14 x 30 mm
column) was printed alongside it and is ready for step 4.

Why first: the head is the long print and its eight bores are the one feature that
cannot be fixed after. A loose bore lets an LED tilt off 45 degrees; a tight one
cracks the wall.

## 2. Bring the electronics up on the ESP32, with no head

The head is not needed to prove the wiring, and finding a bad solder joint is
easier with everything on the bench in the open.

Ruled 2026-10-06 (`docs/DECISIONS.md`): the first unit reads through the ESP32, never
a Pi. The board runs CircuitPython and `firmware/circuitpython/code.py`, which only
answers "read" and "light channel N" over USB; the measurement is still
`spectra.capture`, run on the computer the cable goes to. Flashing, the wiring table
and the two checks are in `firmware/circuitpython/README.md`. The short wiring:

| ESP32 pin | To |
|---|---|
| 3V3, G, 8, 9 | AS7341 VIN, GND, SDA, SCL |
| 5V, G | TLC59711 V+, GND |
| 12, 11 | TLC59711 CI, DI |
| nothing | TLC59711 VCC |

Before any LED goes near the head, prove which output is channel 0 (the README's
second check; on the bench it is R3, the numbering runs backwards), because the white must sit in the bore that channel lights and the
driver's silkscreen groups outputs as R/G/B triples rather than numbering them.

Four more things:

- **Bridge the ESP32's IN-OUT pads first** (front, beside the diodes at pins 11
  and 12; not the USB-OTG pads on the back, which were the wrong guess). Open
  as shipped. Without the bridge the port marked USB powers the ESP32 but not its 5V
  pin, so the driver gets no power, and the only symptom is LEDs that never light
  while every command returns OK. Found on 2026-10-08, fixed on the bench board
  2026-10-15; the bare puck board needs it too. `firmware/circuitpython/README.md` has
  the detail and the one caution it brings.
- **The TLC59711 sinks.** LED anodes go to the board's V+, cathodes to the channel
  outputs. The Adafruit 1455 sets every channel to about 15 mA with an on-board
  3.3 kΩ resistor, so **no series resistors**. 5 V on V+ covers every LED in the
  set, including the 400 nm and 460 nm parts.
- **Sleeve every LED's back in black heat-shrink before it goes in the head**, not
  only the white. Ruled in `OPTICAL_HEAD.md`: the bores open into the case, and an
  unsealed LED back is a path for room light into the head.
- **Stray light from the boards themselves.** The AS7341 breakout has a power LED
  and a switchable white LED; the firmware keeps the white one off, and the power
  LED gets covered (or its jumper cut). The ESP32's RGB LED is switched off by the
  firmware; its red power LED is not switchable, so tape it. Red team round two
  found the ESP32's LEDs.

Then, on the computer:

```sh
python -m spectra.capture --fake session new /tmp/s     # the CLI works at all
python -m spectra.capture session new ~/spectra-sessions/2026-10-xx-bench
```

`--port auto` is the default and finds the board by asking each serial port for its
ID. The real `session new` will take a dark and ask for the white. With no head, hold
the white patch near the sensor under the white LED just to see counts move and to
find a gain that does not trip the saturation stop. Nothing from this step is kept.

## 3. Print the head, plate and trap

From **#9**, not #6 or `main`. #9 carries the 5 mm rulings (since 6f37bf2) and is
the head and plate the puck uses, so they are printed once: `head.stl` and
`puck_plate.stl` in the project files' `case-concepts/puck-v1/`. **Do not print the
detector plate from #6 or `main`**: theirs is a solid disc over all eight bore
mouths, with no notches for the LED leads. The light trap is the standalone
`trap.light_trap()` on this branch (`light-trap.stl` in the project files' `build/`),
until the dock, which has a trap cup of its own, is printed.

Those STLs are drawn at `LED_SEAT_D` 5.2, the coupon's result (#9, 8152b47;
the head is 54.5 mm across). **Print it flat rim down, upside down, supports
off**, which is how `head.stl` is exported. Port face down, the earlier
instruction, leaves only the lip on the bed and starts the collection tube in mid
air (case thread, 2026-10-05). Black PETG. Check `python -m spectra.cad.head` says
one solid before slicing.

Seat the LEDs, white in the position channel 0 is wired to. Mount the AS7341 on the
plate and screw the plate down with the M2s into the head's inserts. Black tape
round that joint until the case exists.

## 4. The dark test, which is also the torch test

Head on the light trap, every LED off. Three dark readings: room lights off, room
lights on, then a torch held at each opening in turn (the plate joint, the LED
backs, the leads). If the counts move beyond their own read-to-read noise, there is
a leak, and it gets found now with the head in the open rather than later inside a
case. Red team round two asked for exactly this before any fix is modelled.

## 5. The white

`session new` for real: dark on the trap, then ColorChecker patch 19 on the port as
the white (ruled 2026-09-22; the PTFE tile is a 1d item). Lower the gain until the
saturation stop stays quiet. Note the gain and the settle time used; the session
records both.

## 6. The first number

Print a few flat matte black PLA chips (ruled 2026-09-22 as the first samples).
Then:

```sh
python -m spectra.capture repeat SESSION black-pla-1 --count 10
```

lifting and replacing the head between reads. That table is the Stage 1a
repeatability row, minus the ΔE00, which waits on #7 and the eight-channel fitter.

## 7. Write it down

One entry in `process/BENCH_LOG.md`: commit, gain, settle time, what the torch did,
the worst channel's spread. The next session reads nothing else about the bench.

## Not in this build

- **The puck shell and the dock.** They wait until the head has produced a number.
  The puck to print is the 49 mm one on #9 (5bd5a8e), with the LED driver under the
  lid.
- **The seven colour LEDs.** Wire them to channels 1 to 7 now if convenient; they
  are Stage 1b.
