"""The calibration dock: where the puck lives, and where its two standards live.

    python -m spectra.cad.dock                  # build, check, report
    python -m spectra.cad.dock --export         # STEP + STL, print-oriented
    python -m spectra.cad.viewer --dock         # the puck on each station

One printed part. Two cups side by side, each a station the puck drops into
port down:

``white``
    The sintered PTFE tile in a pocket, its face the only thing the puck lands
    on. This is where the puck parks, so the tile spends its life covered by
    the instrument that reads it.
``trap``
    The light trap from `trap.py`, bored into the dock's body, its mouth ringed
    by a flat annulus the puck lands on.

`OPTICAL_HEAD.md` rules dark, black and white before every session. The dock
exists to make that the path of least resistance: the puck is always sitting on
one of its standards when it is not reading a sample. The reasoning, the
research and what is still open are in `docs/DOCK.md`.

**Everything is driven from the puck.** The cup radius is the puck's outer
radius plus clearance, the well depth is the lip's reach plus clearance, the tile
pocket is the tile. When the puck's lid moves with the board heights still owed,
or the tile arrives at a thickness other than the estimate, the dock follows and
its checks say whether it still holds.

Coordinates are the head's: z = 0 is the port face, and a docked puck's port
face sits on the station's stop plane. The white station is at the origin and
the trap station at +X, `PITCH` away.
"""

from __future__ import annotations

import math
import os

from build123d import Align, Box, Cone, Cylinder, Part, Pos

from . import head, params as P, puck as K, trap

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# ------------------------------------------------------------------ chosen --

CUP_CLEAR = 0.5
"""CHOSEN. Radial clearance between the puck and its cup. The cup guides the
puck down; the stop is below it and the cup must not also try to be one. Half a
millimetre drops in freely off a printer that holds a tenth, and it bounds how
far off centre the port can land, which the pocket and the trap mouth are
checked against."""

DOCK_WALL = 2.4
"""CHOSEN. Six perimeters, as the puck and the head. Opaque."""

CUP_TOP = 16.0
"""CHOSEN. Height of the cup's rim above the stop plane. The cup is the light
seal, not the lip (see LIP_CLEAR), so taller is darker; it must stay well under
the puck's USB-C opening so the plug and its cable clear the rim whichever way
the puck is turned. See check()."""

CUP_LEAD = 1.5
"""CHOSEN. Chamfer on the cup's mouth, so a puck set down slightly off centre is
guided in rather than landing on the rim."""

LIP_CLEAR = 0.8
"""CHOSEN, and the decision the whole station shape follows from. On a sample
the lip is crushed by a finger until the port face lands; in the dock nobody is
pressing, and the puck's weight alone may not crush it. A lip that stood on the
dock would then hold the port face off the tile, which is a standoff error in
the one reading that cannot have one. So the lip is given nowhere to land: the
station floor is sunk LIP_PROUD + LIP_CLEAR below the stop plane and the lip
hangs in air. Light is kept out by the cup instead."""

TILE_PROUD = 0.3
"""CHOSEN. How far the tile's face stands above the pedestal it sits in. A face
flush with printed plastic around it is two stops at one height, and the
printer decides which one wins. Standing the tile proud makes the PTFE the only
stop at the white station. It is also the thickness tolerance: a tile up to this
much thinner than TILE_T still lands first. See tile_window()."""

TILE_FIT = 0.1
"""CHOSEN. Radial clearance around the tile in its pocket. A clearance fit, not a
press: the dock is never turned over in use, and a pressed-in tile has to be
pried out, which is how a PTFE face gets scratched. It lifts out by its edge at
the notch."""

PEDESTAL_WALL = 1.2
"""CHOSEN. Wall of the pedestal around the tile. Three perimeters; it carries no
load but the tile's edge."""

NOTCH_W = 3.0
NOTCH_DROP = 0.8
"""CHOSEN. A slot through the pedestal wall on the side away from the trap, down
past the pocket floor, so a fingernail or a pick gets under the tile's edge
without touching its face. Labsphere's handling guide wants the face touched by
nothing but air; sanding it clean means taking it out."""

LEDGE_DROP = 0.2
"""CHOSEN. The ledge under the puck's foot ring sits this far below the stop
plane. On a sample the foot stands FOOT_RELIEF above the sample and catches a
tilt; the ledge gives it the same job here. Dropping it a little keeps it from
ever being a second stop if the tile comes out a little thin, at the cost of a
slightly larger tilt before the foot catches. See check()."""

LEDGE_IN = 1.0
"""CHOSEN. The ledge starts this far outside where the head's bottom edge can
reach with the puck pushed hard against the cup, so the head's rim never lands
on it."""

FLOOR_T = 2.0
"""CHOSEN. Solid under the trap's apex."""

PETG_DENSITY = 1.27
"""CHOSEN, a material constant not a measurement of anything here: g/cm^3 for
PETG, used only to put a mass on the report."""

# ----------------------------------------------------------------- derived --

R_CUP = K.R_OUT + CUP_CLEAR
R_DOCK = R_CUP + DOCK_WALL
PITCH = 2 * R_CUP + DOCK_WALL
"""DERIVED. Station centres. The two cups share a wall DOCK_WALL thick where
they come closest."""

WELL_DEPTH = P.LIP_PROUD + LIP_CLEAR
"""DERIVED. How far the station floor sits below the stop plane."""

HEAD_R = P.BODY_OD / 2
LEDGE_R0 = HEAD_R + CUP_CLEAR + LEDGE_IN
"""DERIVED. Inner edge of the foot ledge."""

TILE_POCKET_R = P.TILE_D / 2 + TILE_FIT
TILE_PEDESTAL_R = TILE_POCKET_R + PEDESTAL_WALL
TRAP_LAND_R = P.TRAP_OD / 2
"""DERIVED. The annulus around the trap mouth the puck lands on is the trap's
own wall, the thickness TRAP_WALL the trap was designed with."""

Z_BOTTOM = -P.TRAP_L - FLOOR_T
"""DERIVED. The trap is the deepest thing in the dock; its length sets the
height."""

STATIONS = {"white": 0.0, "trap": PITCH}


def usb_opening_bottom() -> float:
    """Lowest point of the puck's USB-C opening, in head coordinates."""
    from components import esp32_s3_devkitc1 as E

    return K.esp_z() + E.THICKNESS + K.USB_Z - K.USB_PLUG_H / 2


# ------------------------------------------------------------------- parts --

def _cyl(r: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0) -> Part:
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=_MIN)


def _cup(x: float) -> Part:
    """The cutting tool for one station's cup, ledge and well."""
    cup = _cyl(R_CUP, -LEDGE_DROP, CUP_TOP + 1.0, x)
    lead = Pos(x, 0, CUP_TOP - CUP_LEAD) * Cone(
        R_CUP, R_CUP + CUP_LEAD + 1.0, CUP_LEAD + 1.0, align=_MIN)
    well = _cyl(LEDGE_R0, -WELL_DEPTH, -LEDGE_DROP + 0.5, x)
    return cup + lead + well


def body() -> Part:
    """The dock: a stadium block, two cups, the tile pocket and the trap."""
    xw, xt = STATIONS["white"], STATIONS["trap"]
    h = CUP_TOP - Z_BOTTOM
    block = (_cyl(R_DOCK, Z_BOTTOM, CUP_TOP, xw) + _cyl(R_DOCK, Z_BOTTOM, CUP_TOP, xt)
             + Pos((xw + xt) / 2, 0, Z_BOTTOM) * Box(PITCH, 2 * R_DOCK, h, align=_MIN))
    part = block - _cup(xw) - _cup(xt)

    # White: a pedestal standing up out of the well, the tile's pocket in it.
    # Each pedestal starts half a millimetre inside the floor so it fuses.
    part = part + _cyl(TILE_PEDESTAL_R, -WELL_DEPTH - 0.5, -TILE_PROUD, xw)
    part = part - _cyl(TILE_POCKET_R, -P.TILE_T, 1.0, xw)
    notch_len = TILE_PEDESTAL_R - (P.TILE_D / 2 - 1.0) + 1.0
    part = part - Pos(xw, -(P.TILE_D / 2 - 1.0) - notch_len / 2, -P.TILE_T - NOTCH_DROP) * Box(
        NOTCH_W, notch_len, P.TILE_T + NOTCH_DROP + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Trap: the land around the mouth, then the cone from trap.py.
    part = part + _cyl(TRAP_LAND_R, -WELL_DEPTH - 0.5, 0.0, xt)
    part = part - Pos(xt, 0, 0) * trap.cavity()
    part = part - _cyl(P.TRAP_MOUTH_D / 2, -0.01, 1.0, xt)
    return part


def tile() -> Part:
    """The PTFE tile in its pocket, face on the stop plane. Bought, not printed."""
    return Pos(STATIONS["white"], 0, -P.TILE_T) * trap.ptfe_tile()


# ---------------------------------------------------------------- viewing --

def station() -> str | None:
    """The station SPECTRA_DOCK puts the puck on, or None for no dock."""
    raw = os.environ.get("SPECTRA_DOCK", "").strip().lower()
    if not raw:
        return None
    if raw not in STATIONS:
        raise ValueError(f"SPECTRA_DOCK={raw!r}; expected one of {', '.join(STATIONS)}")
    return raw


FAMILIES = ("dock_body",)
REPLACES = ("sample_card",)
"""Head-assembly families the dock stands in for: at the white station the tile
is the sample."""


def placed(where: str | None = None) -> list[tuple[str, Part]]:
    """The dock and its tile, moved so the chosen station is under the port."""
    where = station() if where is None else where
    if where is None:
        return []
    shift = Pos(-STATIONS[where], 0, 0)
    return [("dock_body", shift * body()), ("ptfe_tile", shift * tile())]


# ------------------------------------------------------------------ checks --

def _overlap(a: Part, b: Part) -> float:
    hit = a & b
    return 0.0 if hit is None else sum(s.volume for s in hit.solids())


def _puck_solids() -> list[Part]:
    """What of the puck can reach down to the dock: the head and the base."""
    return [head.body(), K.base()]


def _pivot_tilt(pivot_r: float, extra: float = 0.0) -> float:
    """Tilt, in degrees, at which the foot touches the ledge, rocking about the
    edge of the stop at pivot_r. `extra` raises the stop (a thicker tile)."""
    gap = K.FOOT_RELIEF + LEDGE_DROP + extra
    return math.degrees(math.atan2(gap, K.R_OUT - pivot_r))


def tile_window() -> tuple[float, float]:
    """How much thinner and thicker than TILE_T the real tile may be and the
    dock still hold: thinner until the pedestal becomes the stop, thicker until
    the foot's tilt cap reaches the ruled tolerance."""
    lever = K.R_OUT - P.TILE_D / 2
    thicker = lever * math.tan(math.radians(P.ILLUM_ANGLE_TOL)) - K.FOOT_RELIEF - LEDGE_DROP
    return TILE_PROUD, thicker


def check() -> list[tuple[str, bool, str]]:
    dock = body()
    ptfe = tile()
    out = []
    n = len(dock.solids())
    out.append(("dock is one solid", n == 1, f"{n} solid(s)"))

    # The stops. Lower the puck a tenth: at the white station only the tile may
    # be in the way; at the trap only the land around the mouth.
    probe = 0.1
    low = [Pos(0, 0, -probe) * s for s in _puck_solids()]
    v = sum(_overlap(dock, s) for s in low)
    out.append(("white: the tile is the only stop", v < 1e-6,
                f"dock within {probe:g} of the puck: {v:.3f} mm^3"))
    at_trap = Pos(-PITCH, 0, 0) * dock
    land = _cyl(TRAP_LAND_R + 0.01, -WELL_DEPTH - 1.0, 1.0)
    v = sum(_overlap(at_trap - land, s) for s in low)
    out.append(("trap: the land is the only stop", v < 1e-6,
                f"dock outside the land within {probe:g} of the puck: {v:.3f} mm^3"))

    for name, d in (("white", dock), ("trap", at_trap)):
        v = sum(_overlap(d, s) for s in _puck_solids())
        out.append((f"{name}: puck seats without touching the cup", v < 1e-6,
                    f"overlap {v:.3f} mm^3"))
    v = _overlap(dock, ptfe)
    out.append(("tile clear of its pocket", v < 1e-6, f"overlap {v:.3f} mm^3"))

    # Off-centre seating, as far as the cup allows.
    port_r = P.PORT_D / 2 + CUP_CLEAR
    out.append(("white: the port sees only PTFE", port_r < P.TILE_D / 2,
                f"port reaches r={port_r:.2f} off centre; tile r={P.TILE_D / 2:.2f}"))
    out.append(("trap: the port sees only the trap mouth", port_r < P.TRAP_MOUTH_D / 2,
                f"port reaches r={port_r:.2f}; mouth r={P.TRAP_MOUTH_D / 2:.2f}"))
    lip_in = P.LIP_ID / 2 - CUP_CLEAR
    ped = max(TILE_PEDESTAL_R, TRAP_LAND_R)
    out.append(("the lip hangs clear of both pedestals", lip_in > ped,
                f"lip inner edge down to r={lip_in:.2f}; pedestals out to r={ped:.2f}"))
    out.append(("the lip hangs clear of the well floor", WELL_DEPTH > P.LIP_PROUD,
                f"lip reaches z={-P.LIP_PROUD:g}; floor at z={-WELL_DEPTH:g}"))
    out.append(("the head's rim cannot reach the ledge", HEAD_R + CUP_CLEAR < LEDGE_R0,
                f"head edge out to r={HEAD_R + CUP_CLEAR:.2f}; ledge from r={LEDGE_R0:.2f}"))

    for name, pivot in (("white", P.TILE_D / 2), ("trap", TRAP_LAND_R)):
        t = _pivot_tilt(pivot)
        out.append((f"{name}: the foot catches a tilt inside the ruled tolerance",
                    t < P.ILLUM_ANGLE_TOL,
                    f"foot meets the ledge at {t:.2f}deg; ruled +/-{P.ILLUM_ANGLE_TOL:g}deg"))

    usb = usb_opening_bottom()
    out.append(("the cup rim clears the USB-C plug", CUP_TOP < usb,
                f"rim at z={CUP_TOP:g}; USB-C opening from z={usb:.2f}"))

    below = -P.TILE_T - NOTCH_DROP
    out.append(("the tile pocket is inside the body", below > Z_BOTTOM,
                f"deepest cut z={below:.2f}; dock bottom z={Z_BOTTOM:g}"))
    return out


# ---------------------------------------------------------------- export --

def print_ready() -> dict[str, Part]:
    """The dock on its bottom face, as modelled. Every cut opens upward."""
    d = body()
    return {"dock": Pos(0, 0, -d.bounding_box().min.Z) * d}


def export(out_dir) -> list:
    from pathlib import Path

    from build123d import export_step, export_stl

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, part in print_ready().items():
        for ext, fn in (("step", export_step), ("stl", export_stl)):
            path = out / f"{name}.{ext}"
            fn(part, str(path))
            written.append(path)
    return written


def report() -> int:
    d = body()
    bb = d.bounding_box()
    mass = d.volume / 1000 * PETG_DENSITY
    print(f"dock: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"{d.volume / 1000:.0f} cm^3 ({mass:.0f} g of PETG if printed solid)")
    print(f"  cups r={R_CUP:.2f} for the puck's r={K.R_OUT:.2f}, {PITCH:.1f} apart; "
          f"rim {CUP_TOP:g} above the stop plane, floor {WELL_DEPTH:g} below")
    thin, thick = tile_window()
    print(f"  tile {P.TILE_D:g} dia x {P.TILE_T:g} (ESTIMATE); the dock holds for a tile "
          f"{thin:.2f} thinner to {thick:.2f} thicker\n")
    fails = 0
    for name, ok, detail in check():
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {name}  {detail}")
    print("\n  [est] TILE_T follows the tile when it is bought; the puck's board "
          "heights move CUP_TOP's margin")
    return fails


if __name__ == "__main__":
    import sys

    if "--export" in sys.argv:
        from pathlib import Path

        dest = Path(__file__).resolve().parents[2] / "export" / "dock"
        for path in export(dest):
            print(f"wrote {path.relative_to(dest.parents[1])}")
    raise SystemExit(report())
