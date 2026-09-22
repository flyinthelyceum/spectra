"""Stage 1a: read the optical head on a Pi.

The capture side runs against two Protocols (`hw.Sensor`, `hw.Lamp`) so the
measurement code in `cycle.py` and `session.py` never imports an Adafruit library
directly. The real implementations wrap `adafruit_as7341` and `adafruit_tlc59711`
and are loaded lazily inside `hw.py`, so this package imports on a machine that
does not have Blinka installed, and the fakes let the whole CLI run on the Mac.

What this stage does not do: turn eight channels into XYZ, walk the LED ring, or
keep a sample registry. See `specs/2026-09-22-capture-1a.md`.
"""

from __future__ import annotations

__all__: list[str] = []
