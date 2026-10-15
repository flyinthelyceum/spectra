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
