"""The LED bore coupon: the first thing printed, before the head.

    python -m spectra.cad.coupon      # build it, report, export the STL

`params.LED_SEAT_D` is 5.3 as a model value. FDM holes print small by an amount
that depends on the printer, the filament and the hole's angle, so the bore that
holds a 5 mm LED by friction is found by printing, not by arithmetic. This part
is that print: five bores from `COUPON_D_MIN` to `COUPON_D_MAX` in 0.1 mm steps,
one block, a notch at the small end.

The bores are tilted to the head's own `ILLUM_ANGLE` from vertical and the block
prints flat on the bed, as the head does (rim down), because a 45 degree hole prints rounder or
squarer than a vertical one and the head's bores are 45 degree holes. A vertical
coupon would answer a question the head never asks.

Press an LED into each bore from the top. The right bore is the smallest one the
LED enters fully by hand and stays in when the coupon is turned over and tapped.
Set `LED_SEAT_D` to that bore's printed label, not to a caliper reading of it:
the knob is the CAD value that produces a bore that grips, which is the number
the head needs.

Result, 2026-10-05: the 5.2 bore grips (Jared, black PETG). It is the smallest
bore here, so nothing tighter was tried. `LED_SEAT_D` is 5.2 on the puck branch
(#9, 8152b47).
"""

from __future__ import annotations

import math

from build123d import Align, Box, Cylinder, Part, Pos, Rot

from . import params as P

COUPON_D_MIN = 5.2
"""CHOSEN, from the 2026-09-22 ruling: a coupon at 5.2 to 5.6."""

COUPON_D_MAX = 5.6
"""CHOSEN, same ruling."""

COUPON_STEP = 0.1
"""CHOSEN. Finer than a printer resolves reliably would only add bores."""

COUPON_H = 8.0
"""CHOSEN. Block height. Along a 45 degree bore that is 11.3 mm of hole, more
than `LED_SEAT_L` (6), so the grip tested is at least the grip the head gives."""

COUPON_PITCH = 10.0
"""CHOSEN. Bore centre to centre. Leaves over 4 mm of web between the largest
two, so one bore's fit does not loosen its neighbour."""

COUPON_WALL = 2.5
"""CHOSEN. Material beyond the widest bore at either face."""

NOTCH = 2.0
"""CHOSEN. Side of the square notch that marks the small end."""

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def diameters() -> list[float]:
    """The bores, smallest first. Derived from the limits, never listed."""
    n = round((COUPON_D_MAX - COUPON_D_MIN) / COUPON_STEP) + 1
    return [round(COUPON_D_MIN + i * COUPON_STEP, 2) for i in range(n)]


def _size() -> tuple[float, float, float]:
    """Length along the row, width across the tilt, height."""
    drift = COUPON_H * math.tan(math.radians(P.ILLUM_ANGLE))
    width = drift + max(diameters()) / math.cos(math.radians(P.ILLUM_ANGLE)) + 2 * COUPON_WALL
    length = COUPON_PITCH * len(diameters())
    return length, width, COUPON_H


def bore_axes() -> list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    """(point on the bed face, unit direction) for each bore, in coupon coordinates.

    The tilt is about X, so each bore leans in Y and the row runs along X. The
    axis enters the bed face at y = -drift/2 and leaves the top at y = +drift/2,
    which centres the whole slanted hole in the block's width.
    """
    length, _, height = _size()
    a = math.radians(P.ILLUM_ANGLE)
    drift = height * math.tan(a)
    out = []
    for i, _d in enumerate(diameters()):
        x = -length / 2 + COUPON_PITCH * (i + 0.5)
        out.append(((x, -drift / 2, 0.0), (0.0, math.sin(a), math.cos(a))))
    return out


def body() -> Part:
    """The coupon as one solid, bed face at z = 0."""
    length, width, height = _size()
    part = Box(length, width, height, align=_MIN)

    a = P.ILLUM_ANGLE
    # Each cutter starts a millimetre below the bed along its own axis and runs
    # long enough to clear the top, so both faces are cut through, not tangent.
    cut_len = height / math.cos(math.radians(a)) + 4.0
    for ((x, y, _z), (_dx, dy, dz)), d in zip(bore_axes(), diameters()):
        start = (x, y - dy * 1.5, -dz * 1.5)
        # Rot(-a, 0, 0) about X sends +Z to (0, sin a, cos a): the bore's lean.
        part = part - (Pos(*start) * Rot(-a, 0, 0) * Cylinder(d / 2, cut_len, align=_MIN))

    # The notch: a square bite out of the top edge at the small end. It runs the
    # full width so it reads from either side.
    notch = Pos(-length / 2, 0, height) * Box(NOTCH * 2, width + 2, NOTCH * 2)
    return part - notch


def report() -> int:
    """Build the coupon and say what came out. Non-zero if it is not one solid."""
    part = body()
    solids = part.solids()
    bb = part.bounding_box()
    print(f"coupon: {len(solids)} solid(s), {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
    print(f"  bores {', '.join(f'{d:.1f}' for d in diameters())} mm, "
          f"{P.ILLUM_ANGLE:.0f} deg from vertical, notch at the {COUPON_D_MIN:.1f} end")
    if len(solids) != 1:
        print("  FAIL: the coupon must be a single solid or it is not printable")
        return 1
    return 0


if __name__ == "__main__":
    import sys

    from build123d import export_stl

    code = report()
    if code == 0 and len(sys.argv) > 1:
        export_stl(body(), sys.argv[1])
        print(f"  wrote {sys.argv[1]}")
    raise SystemExit(code)
