# Bench log

What actually happened at the bench, newest last. The human is the test runner: no
agent here can hold a paint-out against a port, lift it and replace it ten times, or
know that the room light was on. Without an entry, the next session codes blind.

One entry per bench session. Keep it short and factual.

```
## YYYY-MM-DD — what was on the bench
Commit: <sha>
Did: ...
Saw: ...
Next: ...
```

## Owed before the first entry

- ~~Calipers on the AS7341 breakout.~~ Done 2026-09-17; the plate builds.
- A ColorChecker on the shelf. Ordered 2026-09-22.
- ~~A sintered PTFE white tile on the shelf.~~ Not for 1a (ruled 2026-09-22): the ColorChecker white patch is the reference. The tile is a 1d item.
- ~~The LED part chosen from a datasheet, so `LED_HALF_ANGLE` is no longer an estimate.~~ Done 2026-09-22: eight parts ruled and ordered, `LED_HALF_ANGLE` 10 (CHOSEN), `LED_Z` 18, `LED_SEAT_D` 5.3.
- ~~A bore coupon printed and `LED_SEAT_D` set.~~ Done 2026-10-05: 5.2 mm grips (`spectra/cad/coupon.py`); set on #9.
- Matte black PLA chips printed: the first samples (ruled 2026-09-22; paint-outs wait for 1c+).
- ~~The cure interval fixed.~~ Deferred to 1c+ by the same ruling; still owed before the first paint-out.

## 2026-10-15 — first bridge bring-up, ESP32-S3 + AS7341 + TLC59711
Commit: this one
Did: USB-OTG pads bridged (wrong pads; see the next entry). Bridge brought up over ssh on
the MacBook. The two-channel `boot.py` (console off, data on) enumerated but macOS
never configured it: no serial port appeared, and safe-mode double-tap did not get
the board back. Recovered in ROM download mode (hold BOOT, tap RST), erased and
reflashed CircuitPython 10.3.1 N8R8, left ROM mode with `esptool --after watchdog-reset`.
Dropped `boot.py`; `code.py` now answers on the console with auto-reload off.
Saw: `ID` -> `SPECTRA ESP32 1`. `READ` through `serial_hw.connect('auto')`:
f1..f8 18 44 47 77 153 496 264 59, clear 546, nir 46 (room light, no head on).
Channel 0 driven at 1.0 for 60 s; which output lit not yet recorded.
`connect('auto')` fails if run inside the ~10 s boot; run it after the drive mounts.
Next: record which output channel 0 is, then seat the LEDs in the head.

## 2026-10-15 — first light: 5V fixed, channel map found
Commit: this one
Did: 5Vin read 0.3 V with 5 V across the USB-OTG bridge. On this clone board the
header pin is fed through a diode bypassed by the front IN-OUT pads; Jared moved the
bridge there and V+ read 4.67 V. Channel 9 still dark, with R3 at 2.43 V (V+ minus the
LED's drop: wired right, not sinking). All twelve channels on from the REPL lit it,
so the driver was taking data. The library numbers backwards: channel 0 is R3.
Saw: channel 0 alone lit R3. AS7341 dark vs lit, ATIME 29, ASTEP 599, 5 reads each,
lit minus dark:
  gain 8x:  f1 65  f2 301  f3 217  f4 475  f5 760  f6 903  f7 939  f8 438  clear 1229  nir 101
  gain 64x: f1 511 f2 2378 f3 1704 f4 3734 f5 5972 f6 7090 f7 7356 f8 3449 clear 9676 nir 789
A blue bump at 445, a dip at 480 and a broad peak at 590-630: a phosphor white, on the
warm side (uncorrected for per-channel sensitivity). 8x to 64x scales 7.9x, linear.
Peak 7382 of 18000 at 64x, no saturation. Dark near zero on every channel.
Next: seat the white in the bore channel 0 lights; the other seven LEDs by the table
in the firmware README.

## 2026-10-16 — all eight LEDs lit, one at a time: seven good, green still dim
Commit: this one (adds `scripts/ledtest.py`)
Did: all eight LEDs wired (yellow 590 on ch5 B2, clear-lens red 625 on ch6 R1,
diffused red 660 on ch7 G1, per the firmware README table). `scripts/ledtest.py`
on the MacBook: per channel, gain stepped down from 64x until nothing read over 90%
of full scale, ATIME 29, ASTEP 599, 5 dark and 5 lit reads, level 1.0.
Saw (lit minus dark; "per 1x" = peak band divided by the gain):

| ch | out | LED | gain | peak | per 1x | f1 | f2 | f3 | f4 | f5 | f6 | f7 | f8 | clear |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | R3 | white C513A | 64x | f7 | 80 | 380 | 1777 | 1219 | 2762 | 4292 | 5056 | 5128 | 2369 | 10585 |
| 1 | G3 | 400 UV | 32x | f1 | 223 | 7134 | 332 | 211 | 660 | 441 | 475 | 288 | 304 | 15697 |
| 2 | B3 | 460 blue | 16x | f2 | 588 | 315 | 9410 | 5346 | 426 | 212 | 206 | 278 | 446 | 6605 |
| 3 | R2 | 501 cyan | 64x | f3 | 216 | 422 | 246 | 13821 | 13185 | 1107 | 316 | 458 | 414 | 9555 |
| 4 | G2 | 565 green | 64x | f5 | 1 | 1 | 1 | 1 | 7 | 72 | 21 | 4 | 2 | 62 |
| 5 | B2 | 590 yellow | 64x | f6 | 31 | 35 | 30 | 58 | 38 | 701 | 2001 | 54 | 47 | 1166 |
| 6 | R1 | 625 red | 32x | f7 | 426 | 359 | 176 | 361 | 678 | 347 | 8034 | 13647 | 634 | 12321 |
| 7 | G1 | 660 red | 8x | f7 | 902 | 87 | 135 | 172 | 79 | 121 | 300 | 7212 | 1275 | 448 |

Every peak sits in the band its wavelength predicts; no channel saturated; the order
of the two reds is right (ch6 spills into f6, ch7 into f8).
- ch4 green: right colour, about 27x down from the same LED at the 10-15 test
  (72 vs 1652 counts at 64x), now after reseating. The TLC59711 sinks constant
  current, so a resistive joint would read full or dark, not dim. A dim LED of the
  right colour points at the LED itself (damaged) or its aim. Next: swap in a fresh
  WP7113SGC from the bag and rerun `ledtest.py 4`.
- ch5 yellow: right band but about 14x dimmer per 1x than the 625. Not yet known
  whether that is the part (datasheet intensity) or aim. Check after the green.
- ch7 660: f7 is 5.7x f8, which reads closer to 640 than to 660 (the BOM gives 660
  peak, 640 dominant). Uncorrected for per-band sensitivity; inference, not a
  measured peak. The C12880MA settles it.
Next: fresh green, rerun ch4 and ch5, then seat the head.

## 2026-10-16 — the dim green was aim, not the part
Commit: this one
Did: fresh WP7113SGC on ch4; `ledtest.py 4 5` read worse (green f5 17 at 64x, yellow
f6 1137, the yellow untouched since the last run). Then ch4 and ch5 alternated for
120 s at 64x (ATIME 29, ASTEP 599, ~1.5 s each) while Jared aimed each LED at the
AS7341 by hand.
Saw: green f5 17 -> about 1270 once aimed (the same LED read 1652 in the R2 spot on
10-15); yellow f6 hit full scale (17989) at first, then held about 4490. Steady from
about 20 s. Over the last 100 s, untouched: green +3% (1247 -> 1285), yellow -1.5%
(4544 -> 4473): warm-up drift, likely LED temperature.
The 10-16 diagnosis above ("the LED itself") was wrong. These are 10 degree parts:
loose on the bench, a small tilt misses the sensor, so per-LED brightness means
nothing until the head's bores set the aim. The drift says capture needs a warm-up
or a settle longer than the 0.2 s ESTIMATE before repeat reads.
Next: seat the eight LEDs in the head, rerun `ledtest.py`, then a drift run per
channel to size the warm-up.

## 2026-10-23: first round in the assembled head (PR #15), over white printer paper

The head is assembled and sitting on plain white paper. `firmware/circuitpython/roundtest.py`
ran as code.py: one exposure of 50 ms (ATIME 29, ASTEP 599, full scale 18000), 3 reads
averaged, gain stepped down from 512x only if a band passed 90%. Nothing needed it:
every row is at 512x.

| row | LED | f1 | f2 | f3 | f4 | f5 | f6 | f7 | f8 | clear |
|---|---|---|---|---|---|---|---|---|---|---|
| dark | none | 0 | 0 | 0 | 2 | 4 | 0 | 0 | 0 | 11 |
| all | 0-7 | 4596 | 10153 | 8525 | 4254 | 2554 | 6676 | 13370 | 1986 | 18000 |
| ch0 | white C513A | 50 | 236 | 169 | 386 | 591 | **707** | 706 | 347 | 1352 |
| ch1 | 400 UV | 4110 | **5201** | 3036 | 1311 | 539 | 456 | 333 | 311 | 8405 |
| ch2 | 460 blue | 148 | **4499** | 2916 | 251 | 117 | 108 | 142 | 225 | 4029 |
| ch3 | 501 cyan | 60 | 41 | **2104** | 1993 | 164 | 51 | 72 | 62 | 1884 |
| ch4 | 565 green | 1 | 0 | 0 | 14 | **112** | 35 | 6 | 1 | 74 |
| ch5 | 590 yellow | 47 | 41 | 81 | 50 | 900 | **2970** | 112 | 69 | 1461 |
| ch6 | 625 red | 109 | 60 | 112 | 206 | 108 | 2242 | **8076** | 220 | 4154 |
| ch7 | 660 red | 46 | 75 | 89 | 48 | 69 | 183 | **3936** | 724 | 2163 |
| dark2 | none | 0 | 0 | 0 | 1 | 4 | 0 | 0 | 0 | 10 |

- **The 10-22 "eight LEDs give nothing" is gone.** All eight light and land in their bands.
  Yellow alone now reads f6 2970 over a dark of 0; on 10-21 its spill was 175 over 116.
- **Dark is clean:** at most 4 counts at 512x, the same before and after.
- **Additive:** the eight single-LED f7 readings sum to 13383; all-on reads 13370.
- **Green (ch4) is the weak channel, as the GaP part predicts.** Its f5 112 is 1/26 of the
  yellow's f6, brighter than the 1/40 to 1/60 estimated from datasheets on 10-22. It is
  still 28x over dark in one 50 ms pass.
- **The spread is 72x** between the brightest peak (ch6, 8076) and the dimmest (ch4, 112),
  all at the same gain. One exposure cannot serve every LED, so per-LED exposure is
  required: roughly 16-32x longer integration for green and about 8x for white.
- **UV on paper peaks in f2 (445), not f1.** On the bare bench on 10-15 it peaked in f1
  (7134 vs f2 332). The likely cause is the optical brighteners in printer paper,
  fluorescing blue under UV (inference). **Paper is a bad white reference;** the ruled
  ColorChecker patch 19 is the right one.
- The clear channel saturates (18000) with all eight on. Measurement does not use clear.
- ch7 again peaks in f7 rather than f8, as on 10-15.

**Board:** auto-reload is off, so a new code.py needs Ctrl-C then Ctrl-D on the USB
console to take effect. Afterwards the bridge was restored ("sensor and driver found;
listening"; `find_port` answers), with the LEDs off. full.py is backed up on the drive as
`full.py`.

**Next:** white reference on ColorChecker patch 19 with per-LED exposure (5 reads each,
then lift and replace 5 times for repeatability), then a drift run per channel.
