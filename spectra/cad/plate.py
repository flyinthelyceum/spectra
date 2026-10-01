"""The detector plate, drawn to the measured AS7341 breakout.

    python -m spectra.cad.plate

This is the one part of the head that is gated on a measurement nobody has taken
yet, and it is gated deliberately rather than guessed around.

Every dimension here comes from `components.as7341_breakout`, which is the one
writer for measured physical dimensions on this system. Nothing in this file may
type a number that describes the board. If a number is missing, this module
raises and `assembly.py` leaves the plate out; the head, the tube, the trap and
the tiles all still build and still render. A missing caliper reading costs one
part, not the build.

As of 2026-09-17 the board has been measured except for `PCB_W`. That is one
reading with a caliper and one `python -m components measure` away.
"""

from __future__ import annotations

import math

from build123d import Align, Box, Cylinder, Part, Pos, Rot

from components import as7341_breakout as B

from . import head, params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

PLATE_T = 3.0
"""CHOSEN. Thickness of the plate. Stiff enough to hold the sensor square to the
tube, since a tilted detector turns the collection axis into something other
than the surface normal and quietly stops the instrument being 0 degrees."""

PLATE_CLEAR = 0.2
"""CHOSEN. Print clearance on the mounting holes."""


SPIGOT_H = 1.5
SPIGOT_T = 1.2
"""CHOSEN. A ring under the plate that drops 1.5 mm into the head's cavity, three
perimeters thick. It is what locates the plate on the head, so the M2 screws
only clamp. Broken into three arcs by the head's webs, which reach the top of
the cavity."""

SPIGOT_CLEAR = 0.1
"""CHOSEN. Radial clearance of the spigot in the cavity bore, and tangential
clearance of the key arc against its two webs. A locating fit for PETG."""

SPIGOT_LOOSE = 1.0
"""CHOSEN. Tangential clearance of the other two arcs against their webs. One arc
clocks the plate; two would fight each other through the print's tolerance."""

KEY_WEBS = (0, 1)
"""CHOSEN. The two webs the key arc fits between."""


class MissingMeasurement(RuntimeError):
    """A dimension the plate needs has not been measured yet."""


#: What this part needs from the components library, and why.
NEEDS = {
    "PCB_L": "board length; sets the plate footprint",
    "PCB_W": "board width; without it the sensor's position across the board is unknown, "
             "so the sensor cannot be placed on the optical axis",
    "HOLE_PITCH_X": "mounting hole pitch",
    "HOLE_PITCH_Y": "mounting hole pitch",
    "HOLE_DIA": "mounting hole diameter",
    "THICKNESS": "board thickness",
    "PKG_H": "sensor package height above the board",
}


def missing() -> list[str]:
    """Names this part needs that the components library does not have yet."""
    return [name for name in NEEDS if getattr(B, name, None) is None]


def available() -> bool:
    return not missing()


def _require() -> None:
    gaps = missing()
    if gaps:
        detail = "; ".join(f"{n} ({NEEDS[n]})" for n in gaps)
        raise MissingMeasurement(
            f"as7341_breakout is missing {detail}. "
            f"Measure it and record it with `python -m components measure` in the "
            f"components repo — never by typing the number here."
        )


def _web_angle(i: int) -> float:
    return 360.0 * i / P.WEB_N


def _web_cut(i: int, clear: float, r0: float, r1: float) -> Part:
    return Rot(0, 0, _web_angle(i)) * Pos((r0 + r1) / 2, 0, -SPIGOT_H - 1.0) * Box(
        r1 - r0 + 2.0, P.WEB_T + 2 * clear, SPIGOT_H + 3.0, align=_MIN)


def spigot() -> Part:
    """The locating ring under the plate, in plate coordinates (z = 0 is the
    plate's underside). Centres the plate in the cavity bore, and the key arc
    between ``KEY_WEBS`` clocks it."""
    r1 = P.LED_RING_R - SPIGOT_CLEAR
    r0 = r1 - SPIGOT_T
    z0, h = -SPIGOT_H, SPIGOT_H + 0.5  # 0.5 into the plate, so it fuses
    ring = Pos(0, 0, z0) * (Cylinder(r1, h, align=_MIN) - Cylinder(r0, h, align=_MIN))
    arcs = ring
    for i in range(P.WEB_N):
        arcs = arcs - _web_cut(i, SPIGOT_LOOSE, r0, r1)
    # The key: the sector between the two key webs, cut tight to both.
    a0, a1 = (_web_angle(i) for i in KEY_WEBS)
    big = 4 * P.BODY_OD
    left = Rot(0, 0, a0) * Pos(0, big / 2, z0 - 1.0) * Box(big, big, h + 2.0, align=_MIN)
    right = Rot(0, 0, a1) * Pos(0, -big / 2, z0 - 1.0) * Box(big, big, h + 2.0, align=_MIN)
    key = ring & left & right
    for i in KEY_WEBS:
        key = key - _web_cut(i, SPIGOT_CLEAR, r0, r1)
    return arcs + key


def spigot_play_at(r: float) -> float:
    """The most the plate can move, at radius r, with the spigot seated: the
    radial play plus the key's tangential play carried out to r."""
    r_key = P.LED_RING_R - SPIGOT_CLEAR - SPIGOT_T / 2
    return math.hypot(SPIGOT_CLEAR, SPIGOT_CLEAR * r / r_key)


def detector_plate() -> Part:
    """The plate the sensor board bolts to, capping the collection tube."""
    _require()
    part = Pos(0, 0, 0) * Cylinder(P.BODY_OD / 2, PLATE_T, align=_MIN)
    part = part + spigot()

    # The hole the tube looks through. Same diameter as the tube bore, so the
    # aperture stop stays the tube and the plate adds nothing of its own.
    part = part - Pos(0, 0, -1.0) * Cylinder(P.COLLECT_D / 2, PLATE_T + 2.0, align=_MIN)

    # Mounting holes, on the board's measured pitch, centred on the axis. The
    # sensor sits on the axis, so the hole pattern is placed relative to the
    # sensor rather than to the board outline — which is exactly why PCB_W is
    # needed: the sensor's offset across the board is measured from an edge.
    sensor_dx = B.PCB_L / 2 - B.SENSOR_X_FROM_EDGE
    sensor_dy = B.PCB_W / 2 - B.SENSOR_Y_FROM_LED_EDGE
    r = (B.HOLE_DIA + PLATE_CLEAR) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = sx * B.HOLE_PITCH_X / 2 + sensor_dx
            y = sy * B.HOLE_PITCH_Y / 2 + sensor_dy
            part = part - Pos(x, y, -1.0) * Cylinder(r, PLATE_T + 2.0, align=_MIN)

    # Notch the rim at each LED. The bores break out of the head just under
    # the plate, so without these the plate sits on the LED leads.
    part = part - Pos(0, 0, -P.PLATE_Z) * head.lead_keepouts()

    # The three M2 screws that hold the plate down on the head's rim.
    for x, y in head.plate_screw_positions():
        part = part - Pos(x, y, -1.0) * Cylinder(
            head.PLATE_SCREW_CLEAR_D / 2, PLATE_T + 2.0, align=_MIN
        )
    return part


def as7341_board() -> Part:
    """The breakout itself, as a reference solid. Not ours to build."""
    _require()
    sensor_dx = B.PCB_L / 2 - B.SENSOR_X_FROM_EDGE
    sensor_dy = B.PCB_W / 2 - B.SENSOR_Y_FROM_LED_EDGE
    pcb = Pos(sensor_dx, sensor_dy, 0) * Box(
        B.PCB_L, B.PCB_W, B.THICKNESS, align=_MIN
    )
    pkg = Pos(0, 0, -B.PKG_H) * Box(3.1, 2.0, B.PKG_H, align=_MIN)
    return pcb + pkg


def report() -> int:
    gaps = missing()
    if gaps:
        print("detector plate: BLOCKED")
        for name in gaps:
            print(f"  {name} is not measured — {NEEDS[name]}")
        print("\n  Everything else in the head builds without it. To unblock:")
        print("    cd ~/projects/components && python -m components measure "
              "as7341_breakout PCB_W <mm>")
        return 0  # not a failure of this build; a fact about the components lib
    part = detector_plate()
    print(f"detector plate: {len(part.solids())} solid(s), "
          f"volume {part.volume / 1000:.2f} cm^3")
    return 0


if __name__ == "__main__":
    raise SystemExit(report())
