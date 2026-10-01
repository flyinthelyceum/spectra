"""Case concepts: three massing studies of what could hold the head in a hand.

    SPECTRA_CASE=puck  python -m spectra.cad.case     # report one concept
    python -m spectra.cad.case                        # report all three

These are **massing models, not parts.** Each is a hollow shell drawn around the
real head and the real boards, so its size is what the parts inside force it to
be rather than what a sketch would like it to be. None is meant to be printed as
drawn: there is no split line, no fastening, no seal, no boss. The question a
concept answers is how big the thing has to be and where the hand goes.

The three forms come from the handheld instruments that already solve this
problem, and each makes a different bet:

``puck``
    Nix Spectro 2 (60 x 60 x 45 mm). The head faces down, everything else stacks
    above it, and the flat base is the foot. Pressed with a fingertip on top, so
    the load goes straight down the optical axis.
``torch``
    Datacolor ColorReader Spectro (30 dia x 105 mm, an 8-channel 45/0 device,
    which is the closest thing on the market to this head). The boards stand up
    along the axis above the head. Held like a fat marker.
``palm``
    X-Rite i1Pro / ColorMunki. The head sits under the front of a long flat body
    and the boards lie flat behind it. The palm presses on the body; the broad
    base is coplanar with the port face and resists tilt.

Two rules from `OPTICAL_HEAD.md` bind every concept and are asserted in
`check()` rather than hoped for:

- **The port face is the stop.** No part of a case may reach below z = 0, or the
  case rather than the port land becomes the standoff, and the standoff is ruled
  fixed. A case foot may be *coplanar* with the port face, which is how a palm
  body gains tilt resistance.
- **The case does not touch the optics.** The head is its own printed solid; the
  case wraps it with clearance and grips it above the LED plane, never around
  the port.
"""

from __future__ import annotations

import math
import os

from build123d import Align, Box, Cylinder, Part, Pos, SlotOverall, extrude

from components import esp32_s3_devkitc1 as E
from components import ssd1306_oled as O

from . import params as P, plate

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

FORMS = ("puck", "torch", "palm")

DETAILED = ("puck-v1",)
"""Concepts that have been carried on into real parts. See puck.py."""

FAMILIES = ("case_shell", "esp32_board", "battery_cell", "oled_display",
            "puck_base", "puck_plate", "puck_tray", "puck_lid")
"""Every part family any concept places. The viewer needs a material for each."""

CASE_WALL = 2.4
"""CHOSEN. Same six perimeters as the head wall, for the same opacity reason."""

CASE_CLEAR = 1.0
"""CHOSEN. Air between the head and the case on every side. The case must never
bear on the head's optics; see the module docstring."""

STACK_GAP = 2.0
"""CHOSEN. Air between stacked boards, for wiring and for the kernel: boards
that share a face with each other are one solid's worth of trouble."""

ESP_STACK_H = 10.0
"""ESTIMATE. Height of the ESP32-S3 DevKitC-1 above and below its PCB — the
module can on top, pin headers underneath. The components library has the PCB
and nothing proud of it. Owed: a caliper reading across the populated board."""

CELL_L, CELL_W, CELL_T = 50.0, 34.0, 10.0  # lint: not-a-measurement (placeholder for an unchosen cell)
"""ESTIMATE. A generic 103450 LiPo, about 1800 mAh. No cell is chosen and no cell
is on the BOM: the head as specified is tethered by USB. A handheld is a battery
decision, and this is only a placeholder so the concepts are not flattering
themselves by leaving it out. Owed: the chosen cell, measured."""


def form() -> str | None:
    """The concept selected by SPECTRA_CASE, or None for the bare head."""
    raw = os.environ.get("SPECTRA_CASE", "").strip().lower()
    if not raw:
        return None
    if raw not in FORMS + DETAILED:
        raise ValueError(f"SPECTRA_CASE={raw!r}; expected one of "
                         f"{', '.join(FORMS + DETAILED)}")
    return raw


def detector_top() -> float:
    """Top of the detector stack: plate, board, and the STEMMA QT socket on it.

    Derived from the components library so a better caliper reading moves every
    case at once. Falls back to the plate face if the plate is gated.
    """
    if not plate.available():
        return P.PLATE_Z + plate.PLATE_T
    from components import as7341_breakout as B

    return P.PLATE_Z + plate.PLATE_T + B.THICKNESS + B.QT_SOCKET_H


def _shell(outer: Part, inner: Part) -> Part:
    """Outer minus inner, plus the hole the head's port comes through."""
    port_hole = Pos(0, 0, -1.0) * Cylinder(P.BODY_OD / 2 + CASE_CLEAR, CASE_WALL + 2.0, align=_MIN)
    return outer - inner - port_hole


def _esp_board(flat: bool) -> Part:
    """The ESP32-S3 DevKitC-1 PCB, from the components library, at the origin."""
    if flat:
        return Box(E.PCB_L, E.PCB_W, E.THICKNESS, align=_MIN)
    return Box(E.THICKNESS, E.PCB_W, E.PCB_L, align=_MIN)


def _cell(flat: bool) -> Part:
    if flat:
        return Box(CELL_L, CELL_W, CELL_T, align=_MIN)
    return Box(CELL_T, CELL_W, CELL_L, align=_MIN)


def puck() -> list[tuple[str, Part]]:
    """Head down, boards stacked above, battery on top.

    The DevKitC-1 is 62.74 mm long and lies flat, so its diagonal — not the head
    — sets the diameter. That is the finding this concept exists to show.
    """
    esp_z = detector_top() + STACK_GAP
    cell_z = esp_z + E.THICKNESS + ESP_STACK_H + STACK_GAP
    top = cell_z + CELL_T + STACK_GAP

    diag = math.hypot(E.PCB_L, E.PCB_W)
    inner_r = max(P.BODY_OD / 2 + CASE_CLEAR, diag / 2 + CASE_CLEAR,
                  math.hypot(CELL_L, CELL_W) / 2 + CASE_CLEAR)
    outer = Cylinder(inner_r + CASE_WALL, top + CASE_WALL, align=_MIN)
    inner = Pos(0, 0, CASE_WALL) * Cylinder(inner_r, top - CASE_WALL, align=_MIN)
    return [
        ("case_shell", _shell(outer, inner)),
        ("esp32_board", Pos(0, 0, esp_z) * _esp_board(flat=True)),
        ("battery_cell", Pos(0, 0, cell_z) * _cell(flat=True)),
    ]


def torch() -> list[tuple[str, Part]]:
    """Head at the tip, boards standing on the axis above it.

    The diameter is the head's plus clearance and wall, and nothing else gets a
    vote: both boards stand edge-on inside that circle.
    """
    inner_r = P.BODY_OD / 2 + CASE_CLEAR
    base = detector_top() + STACK_GAP
    # Board and cell stand side by side, faces parallel, straddling the axis.
    esp_x = STACK_GAP / 2
    cell_x = -STACK_GAP / 2 - CELL_T
    top = base + max(E.PCB_L, CELL_L) + STACK_GAP
    outer = Cylinder(inner_r + CASE_WALL, top + CASE_WALL, align=_MIN)
    inner = Pos(0, 0, CASE_WALL) * Cylinder(inner_r, top - CASE_WALL, align=_MIN)
    return [
        ("case_shell", _shell(outer, inner)),
        ("esp32_board", Pos(esp_x + E.THICKNESS / 2 + ESP_STACK_H / 2, 0, base)
                        * _esp_board(flat=False)),
        ("battery_cell", Pos(cell_x + CELL_T / 2, 0, base) * _cell(flat=False)),
    ]


def palm() -> list[tuple[str, Part]]:
    """Head under the nose, boards flat behind it, a display on top.

    The body is a stadium in plan. Its underside is at z = 0, coplanar with the
    port face, so the whole footprint is the foot. Height is set by the head;
    length by the head plus the board lying behind it.
    """
    head_d = P.BODY_OD + 2 * CASE_CLEAR
    width = max(head_d, E.PCB_W + 2 * CASE_CLEAR, CELL_W + 2 * CASE_CLEAR)
    # The back end is a half-round, so a square-cornered board lying against it
    # needs extra length: the sag of the arc at the board's half-width.
    r = width / 2
    sag = r - math.sqrt(r * r - (E.PCB_W / 2 + CASE_CLEAR) ** 2)
    length = head_d + STACK_GAP + E.PCB_L + sag + 2 * CASE_CLEAR
    top = detector_top() + STACK_GAP

    # The head's centre is the origin; the body runs out behind it in +X.
    cx = length / 2 - head_d / 2
    outer = Pos(cx, 0, 0) * extrude(
        SlotOverall(length + 2 * CASE_WALL, width + 2 * CASE_WALL), top + CASE_WALL
    )
    inner = Pos(cx, 0, CASE_WALL) * extrude(SlotOverall(length, width), top - CASE_WALL)

    board_x0 = head_d / 2 + STACK_GAP
    esp = Pos(board_x0 + E.PCB_L / 2, 0, CASE_WALL + ESP_STACK_H / 2) * _esp_board(flat=True)
    cell_z = CASE_WALL + ESP_STACK_H + E.THICKNESS + STACK_GAP
    cell = Pos(board_x0 + CELL_L / 2, 0, cell_z) * _cell(flat=True)  # lint: not-a-measurement

    # The display sits flush under the lid over the boards, where the thumb is
    # not. The SSD1306 numbers come from the components library.
    oled = Pos(board_x0 + E.PCB_L / 2, 0, top - O.THICKNESS) * Box(
        O.PCB_W, O.PCB_H, O.THICKNESS, align=_MIN
    )
    return [
        ("case_shell", _shell(outer, inner)),
        ("esp32_board", esp),
        ("battery_cell", cell),
        ("oled_display", oled),
    ]


BUILDERS = {"puck": puck, "torch": torch, "palm": palm}


def placed(name: str | None = None) -> list[tuple[str, Part]]:
    """The selected concept's solids, placed in head coordinates."""
    name = form() if name is None else name
    if name == "puck-v1":
        from . import puck

        return puck.placed()
    return [] if name is None else BUILDERS[name]()


def replaces() -> set[str]:
    """Head-assembly families the selected case swaps out for its own version."""
    return {"detector_plate"} if form() == "puck-v1" else set()


def check(name: str) -> list[tuple[str, bool, str]]:
    """What every concept must hold, as (name, passed, detail)."""
    parts = dict(BUILDERS[name]())
    shell = parts["case_shell"]
    bb = shell.bounding_box()
    out = [
        ("case shell is one solid", len(shell.solids()) == 1,
         f"{len(shell.solids())} solid(s)"),
        ("case never reaches below the port face", bb.min.Z >= -1e-6,
         f"case bottom at z={bb.min.Z:.2f}; the port face is z=0 and is the stop"),
    ]
    from . import head

    hit = shell.intersect(head.body())
    vol = 0.0 if hit is None else sum(s.volume for s in hit.solids())
    out.append(("case does not touch the head", vol < 1e-6,
                f"overlap volume {vol:.3f} mm^3"))
    for part_name, solid in parts.items():
        if part_name == "case_shell":
            continue
        clash = shell.intersect(solid)
        v = 0.0 if clash is None else sum(s.volume for s in clash.solids())
        out.append((f"{part_name} fits inside the shell", v < 1e-6,
                    f"overlap with shell {v:.3f} mm^3"))
    return out


def size(name: str) -> tuple[float, float, float]:
    """Overall envelope of a concept, head included, in mm (X, Y, Z)."""
    from . import head

    bbs = [s.bounding_box() for _, s in BUILDERS[name]()] + [head.body().bounding_box()]
    return (
        max(b.max.X for b in bbs) - min(b.min.X for b in bbs),
        max(b.max.Y for b in bbs) - min(b.min.Y for b in bbs),
        max(b.max.Z for b in bbs) - min(b.min.Z for b in bbs),
    )


def report() -> int:
    names = [form()] if form() else list(FORMS)
    failures = 0
    for name in names:
        x, y, z = size(name)
        print(f"{name}: {x:.1f} x {y:.1f} x {z:.1f} mm overall (head and lip included)")
        for label, ok, detail in check(name):
            failures += not ok
            print(f"  [{'ok' if ok else 'FAIL'}] {label}  {detail}")
    print("\nEstimates these concepts rest on: ESP_STACK_H, CELL_L/W/T (no cell chosen)")
    return failures


if __name__ == "__main__":
    raise SystemExit(report())
