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

As of 2026-09-17 the board is fully measured, `PCB_W` included, and this part
builds. The gate stays: a future board revision that loses a reading costs one
part, not the build.
"""

from __future__ import annotations

from build123d import Align, Box, Cylinder, Part, Pos

from components import as7341_breakout as B

from . import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

PLATE_T = 3.0
"""CHOSEN. Thickness of the plate. Stiff enough to hold the sensor square to the
tube, since a tilted detector turns the collection axis into something other
than the surface normal and quietly stops the instrument being 0 degrees."""

PLATE_CLEAR = 0.2
"""CHOSEN. Print clearance on the mounting holes."""


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


def detector_plate() -> Part:
    """The plate the sensor board bolts to, capping the collection tube."""
    _require()
    part = Pos(0, 0, 0) * Cylinder(P.BODY_OD / 2, PLATE_T, align=_MIN)

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
