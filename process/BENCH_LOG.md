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
Did: USB-OTG pads bridged (5V pin live, see 1cbae99). Bridge brought up over ssh on
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
