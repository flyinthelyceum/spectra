"""Calibration-bench parts: the collar for the full ColorChecker, and the PLA chips.

    python -m spectra.cad.calibrate            # report
    python -m spectra.cad.calibrate OUT_DIR    # report, then write the STLs

**The collar** (`process/cc-adapter-2026-10-26/PLAN.md`, primary plan) is one ring
that grips the outside of the puck base. Its bottom ring presses up against the
base foot and hangs a black skirt just above the card, so room light has to travel
about 14 mm through a sub-millimetre gap to reach the port. Four grooves up the
outside mark the port axis, so the puck can be centred on a patch by eye. It adds
nothing below the lip: the port still sits `LIP_PROUD` above the patch, the same
standoff every sample sees, so the calibration and the measurements match.

The grip is a press fit on a printed part, so the right clearance is found by
printing, not computed. `collar(fit)` takes the diametral clearance and the bench
prints three (`FITS`) side by side; the one that slides on and does not rock wins.

**The chips** are the Stage 1a samples (ruled 2026-09-22: matte black PLA prints
before paint-outs). Flat, opaque, larger than the lip with room to aim. Chip n has
n notches on one edge so ten reads can be traced to the chip they came from.
"""

from __future__ import annotations

import math
import os
import sys

from build123d import Align, Box, Cylinder, Part, Pos, Rot, export_stl

from . import params as P, puck

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# Collar. z = 0 is the port face, as in puck.py; the card is at -LIP_PROUD.
FITS = (0.15, 0.25, 0.35)  # diametral clearance on the base OD, CHOSEN (PLAN.md)
COLLAR_WALL = 2.0  # CHOSEN
COLLAR_TOP = 12.0  # grip reaches this high up the base, CHOSEN
SKIRT_GAP = 0.3  # skirt bottom above the card, CHOSEN
SKIRT_R_IN = 34.0  # clears the head body (puck.HEAD_R) with room to see the lip, CHOSEN
FINGERS = 6
SLOT_W = 1.5  # CHOSEN
SLOT_BOTTOM = 3.0  # slots run from the top down to here, CHOSEN
TICK_W = 1.0  # CHOSEN
TICK_D = 0.6  # CHOSEN

# Chips.
CHIP_W = 40.0  # CHOSEN: lip OD plus about 9 mm of aim each side
CHIP_T = 3.0  # CHOSEN: opaque in black PLA with margin
CHIP_N = 4
NOTCH = 1.2  # CHOSEN


def collar(fit: float) -> Part:
    r_in = puck.R_OUT + fit / 2
    r_out = r_in + COLLAR_WALL
    skirt_bottom = -P.LIP_PROUD + SKIRT_GAP
    ring = Pos(0, 0, skirt_bottom) * (
        Cylinder(r_out, puck.FOOT_RELIEF - skirt_bottom, align=_MIN)
        - Cylinder(SKIRT_R_IN, 50, align=_MIN)
    )
    # The tube starts inside the ring, so the two overlap and fuse into one solid.
    tube = Pos(0, 0, 0) * (
        Cylinder(r_out, COLLAR_TOP, align=_MIN) - Cylinder(r_in, COLLAR_TOP + 1, align=_MIN)
    )
    body = ring + tube
    slot_h = COLLAR_TOP - SLOT_BOTTOM + 1
    for i in range(FINGERS):
        a = 360 / FINGERS * (i + 0.5)  # between the ticks
        body -= Rot(0, 0, a) * Pos(r_in + COLLAR_WALL / 2, 0, SLOT_BOTTOM) * Box(
            COLLAR_WALL * 3, SLOT_W, slot_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    for a in (0, 90, 180, 270):  # 180 is the USB-C side of the base
        body -= Rot(0, 0, a) * Pos(r_out, 0, skirt_bottom - 1) * Box(
            2 * TICK_D, TICK_W, COLLAR_TOP - skirt_bottom + 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    return body


def collar_print(fit: float) -> Part:
    """Skirt down on the bed, fingers up."""
    return Pos(0, 0, P.LIP_PROUD - SKIRT_GAP) * collar(fit)


def chip(n: int) -> Part:
    body = Box(CHIP_W, CHIP_W, CHIP_T, align=_MIN)
    pitch = NOTCH * 2.5
    x0 = -pitch * (n - 1) / 2
    for i in range(n):
        body -= Pos(x0 + i * pitch, CHIP_W / 2, -1) * Box(NOTCH, 2 * NOTCH, CHIP_T + 2, align=_MIN)
    return body


def parts() -> dict[str, Part]:
    out = {f"collar_fit{int(round(f * 100)):03d}": collar_print(f) for f in FITS}
    out.update({f"chip_{n}": chip(n) for n in range(1, CHIP_N + 1)})
    return out


def check() -> list[str]:
    """What has to be true for the collar to work, checked against the puck CAD."""
    bad = []
    base = puck.base()
    bb = base.bounding_box()
    # Nothing on the base pokes outside R_OUT in the band the collar grips.
    band = Pos(0, 0, 0) * (
        Cylinder(puck.R_OUT + 5, COLLAR_TOP, align=_MIN) - Cylinder(puck.R_OUT + 0.01, COLLAR_TOP + 1, align=_MIN)
    )
    poke = base & band
    if poke.volume > 1e-3:
        bad.append(f"base has {poke.volume:.3f} mm^3 outside R_OUT below z {COLLAR_TOP}")
    if abs(bb.min.Z - puck.FOOT_RELIEF) > 1e-3:
        bad.append(f"base foot at z {bb.min.Z:.3f}, collar assumes {puck.FOOT_RELIEF}")
    for f in FITS:
        c = collar(f)
        if c.bounding_box().min.Z <= -P.LIP_PROUD:
            bad.append(f"collar fit {f} reaches the card")
        if (c & base).volume > 1e-3:
            bad.append(f"collar fit {f} overlaps the base")
    if SKIRT_R_IN <= puck.HEAD_R:
        bad.append("skirt inner edge inside the head body")
    if CHIP_W / 2 - NOTCH * 2 <= P.LIP_OD / 2:
        bad.append("chip too small for the lip")
    return bad


def report() -> int:
    bad = 0
    for name, part in parts().items():
        n = len(part.solids())
        bb = part.bounding_box()
        print(f"{name}: {n} solid(s), {part.volume / 1000:.2f} cm^3, "
              f"{bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.2f}, z0 {bb.min.Z:.3f}")
        if n != 1:
            print(f"  FAIL: {name} is not a single solid")
            bad += 1
    for msg in check():
        print("  FAIL:", msg)
        bad += 1
    print(f"skirt: r {SKIRT_R_IN} to {puck.R_OUT + FITS[1] / 2 + COLLAR_WALL:.2f}, "
          f"{SKIRT_GAP} above the card; light path under it {puck.R_OUT + COLLAR_WALL - puck.HEAD_R:.1f} mm")
    return bad


if __name__ == "__main__":
    rc = report()
    if len(sys.argv) > 1 and rc == 0:
        os.makedirs(sys.argv[1], exist_ok=True)
        for name, part in parts().items():
            export_stl(part, os.path.join(sys.argv[1], name + ".stl"))
        print("wrote", sys.argv[1])
    raise SystemExit(rc)
