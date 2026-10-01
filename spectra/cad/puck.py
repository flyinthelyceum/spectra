"""The puck, version one: the case the concepts were choosing between, detailed.

    python -m spectra.cad.puck                         # build, check, report
    SPECTRA_CASE=puck-v1 python -m spectra.cad.viewer  # see it

Chosen over the palm on 2026-09-30, for the reasons in `docs/CASE.md`: a press
on the top goes straight down the optical axis, it works on anything the lip
covers, and a round body parks on a round dock.

Four printed parts and one set of screws:

``puck_base``
    The body. Printed foot down: a floor ring, a short collar that guides the
    head, one wall from the foot to the rim, and four posts the screws pass up
    through, with the screw heads counterbored into the foot.
``puck_plate``
    The detector plate from `plate.py` with four ears added. The ears sit on the
    posts. Three M2 screws hold the plate down on the head's rim, so the head
    hangs from the plate and the plate hangs from the posts. A spigot ring under
    the plate locates the head; a spigot rising from each post locates the ears.
``puck_tray``
    Carries a bare ESP32-S3 DevKitC-1, headers not soldered, which is the lowest
    the stack can be (Jared, 2026-09-30: design for the best case). The board
    has no mounting holes, so it sits on four corner pads inside four L-shaped
    corner fences, over two rails that run outside the board's footprint.
    Standoff tubes under the rails land on the plate's ears, over the posts'
    spigots, which locate the tray.
``puck_lid``
    A flat disc, printed top down, set into the body's rim so its edge is the
    only seam. It lands on the rim's step and stands ``LID_PROUD`` above the rim;
    the rebate centres it and one hidden key clocks it. Bosses with M3 heat-set
    inserts hang down onto the tray on crush ribs, and four pegs press the
    board's corners onto the pads. Its top is unbroken: no screw heads on the
    face a finger presses.

One M3 screw per post runs up from the foot through the post, the plate ear
and the tray standoff into the lid boss's insert, clamping the whole stack.
Four screws hold the entire instrument together. (Screws from below, seam at
the top edge, one-plug USB opening: Jared, 2026-10-01, from the red-team
findings in the dock thread.)

**Fasteners fasten; they do not index** (Jared, 2026-10-01). Every joint aligns
by its own geometry and every screw passes through a hole wider than that
joint's play, so the screws only clamp. The chain runs from the base: the
posts' spigots locate the plate's ears and the tray, the plate's spigot locates
the head, the tray's fences locate the board, and the rim's rebate and key
locate the lid. check() proves each screw clears its hole with its joint at the
limit of its play.

**The LED backs must be sealed** with black heat-shrink or black silicone
before the head goes in the case. A clear LED's epoxy is translucent, the
bores open into the case where the leads come out, and the USB opening lets
room light into the case. Unsealed, the black reading would depend on how
bright the room is. Sealing closes the LED end only; the detector end is
unproven until the Stage 1a dark test (see `OPTICAL_HEAD.md`).

**The load path is the point of the design.** A finger on the lid pushes down
the bosses, the standoffs, the ears and the plate onto the head's rim, and the
head onto the sample through its port land. The base hangs from the ears and
touches nothing below: its foot stands ``FOOT_RELIEF`` above the port face, so
the port land is the only stop when the puck is square, and the foot catches
it before it can tilt out of the ruled +/-2 degrees.

Powered by USB, as the BOM specifies. There is no battery; see `CASE.md`.
"""

from __future__ import annotations

import math
import os

from build123d import Align, Box, Cylinder, Part, Pos, Rot

from components import esp32_s3_devkitc1 as E
from components import heatset_insert_m3x6 as M3

from . import head, params as P, plate

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# ------------------------------------------------------------------ chosen --

WALL = 2.4
"""CHOSEN. Six perimeters, as the head. Opaque, and stiff under a fingertip."""

FLOOR_T = 2.4
"""CHOSEN. The base's floor ring."""

FOOT_RELIEF = 0.4
"""CHOSEN, and the number that makes the foot safe to have. A foot coplanar with
the port face would share the stop with the port land, and a print that came
out a tenth proud would lift the port off the sample. Standing the foot 0.4 mm
above the port face makes the port land the only stop when the puck is square;
the foot only touches down once the puck has tilted, which caps the tilt. See
check()."""

HEAD_CLEAR = 0.5
"""CHOSEN. Radial clearance between the collar and the head. The collar guides;
the plate's spigot locates. Two things locating one part fight, so this must
exceed the play of the two spigots between the base and the head; see check()."""

COLLAR_TOP = 10.0
"""CHOSEN. Height of the collar that guides the head. It must stop well below
where the LED bores break out of the head's wall, or it closes in on the LED
leads. See check()."""

LEAD_ROOM = head.LEAD_ROOM
LEAD_R = head.LEAD_R

CASE_CLEAR = 1.0
"""CHOSEN. Air between a board and the case wall."""

STACK_GAP = 2.0
"""CHOSEN. Air between the detector's STEMMA QT socket and the ESP32 above it,
and between the tallest part on the ESP32 and the lid."""

UNDERSIDE_ROOM = 5.0
"""CHOSEN. Air between the plate and the ESP32's underside, where wires are
soldered into the header pads from below and bent away. With no headers this is
the only thing that sets how low the board can sit, besides the detector's
socket."""

BOSS_WALL = 2.0
"""CHOSEN. Wall around an M3 insert. Five perimeters at 0.4 mm."""

M3_CLEAR_D = 3.6
"""CHOSEN. Clearance hole for M3, 0.3 mm a side: wider than the play of any joint
a screw passes through, so the screw never touches a hole wall and never
locates anything. See check()."""

M3_HEAD_D = 6.0
M3_HEAD_H = 3.4
"""CHOSEN. Counterbore in the foot for an ISO 4762 M3 socket head (5.5 mm across,
3 mm tall) with print clearance. The head sits fully inside it, so nothing of
the screw reaches the plane the foot is relieved from."""

INSERT_INTERFERENCE = head.INSERT_INTERFERENCE
"""The same 0.4 mm the head's M2 inserts use; see head.py."""

POST_N = 4
"""CHOSEN. Four posts, not three. The board lies along X and fills a band across
the middle of the puck, and the only places midway between two LEDs that are
also outside that band come in fours."""

LID_PROUD = 0.5
"""CHOSEN by Jared, 2026-10-01 ("Proud 0.5"). The lid lands on the rim's step, so
one printed part sets its height rather than a stack of four, and its top stands
this far above the rim. A deliberate reveal hides the small difference between
the rim's height and the lid's thickness that flush would show."""

KEY_ANGLE = 0.0
KEY_W = 6.0
KEY_T = 2.0
KEY_H = 2.5
"""CHOSEN. One tab under the lid's edge, at +X opposite the USB opening, 6 wide,
2 radial and 2.5 deep. It drops into a notch cut through the inner half of the
rim's step only, so nothing of it shows from outside. It is what clocks the lid;
without it the screws would."""

KEY_CLEAR = 0.1
"""CHOSEN. Tangential clearance a side between the key and its notch: the lid's
clocking play."""

CRUSH = 0.3
"""CHOSEN. The lid now lands on the rim, so its bosses must not also land on the
tray at a fixed height, or the two would fight through the print's tolerance.
Each boss face stands CRUSH above the tray, on three radial ribs printed CRUSH
into it. A stack up to CRUSH short still clamps; up to CRUSH long, the boss face
meets the tray just as the lid lands."""

POST_SPIGOT_D = 6.4
POST_SPIGOT_ENGAGE = 2.0
SPIGOT_CLEAR = plate.SPIGOT_CLEAR
"""CHOSEN. A tube rising from each post through the plate's ear and
POST_SPIGOT_ENGAGE into the tray's standoff, with the screw's clearance through
its middle. It locates the plate and the tray on the base."""

LAP_CLEAR = 0.15
"""CHOSEN. Radial clearance between the lid disc and the rim's outer half. The
rebate is half a wall deep, so the seam is not a straight line of sight in."""

TRAY_T = 2.0
RAIL_W = 5.0
"""CHOSEN. Tray thickness and rail width. The rails run along the board outside
its footprint, so nothing of the tray sits under the header pads, where wires
are soldered."""

PAD_RISE = 1.0
"""CHOSEN. The corner pads stand this far above the tray, so the board touches
the tray only at its corners and nothing underneath it is pressed on."""

FENCE_T = 0.8
FENCE_CLEAR = 0.3
"""CHOSEN. The L-shaped fences at each corner that locate the board sideways:
two perimeters thick, with print clearance to the board edge."""

USB_PLUG_W = 12.5
USB_PLUG_H = 7.5
"""CHOSEN. Opening for one USB-C plug's overmould. Sized for common cables; a fat
one will not fit.

Plugging straight into the board's own receptacle is an exception to the house
rule of panel-mount bulkheads, made on purpose: the one USB-C bulkhead in the
components library, the PENGLIN coupler, needs a 21.9 mm hole and stands 29.9 mm
into the case, and a 44.8 mm puck has no room for it."""

NATIVE_USB_SIDE = 1
"""ESTIMATE. Which of the board's two USB-C receptacles is the ESP32-S3's native
USB port: +1 for +Y, -1 for -Y, with the USB end towards -X. The components
library gives only their spacing. Check against the silkscreen before printing;
flipping it is a sign change here and moves nothing else."""

USB_REACH = 6.5
"""CHOSEN. How far behind the outside of the wall a USB-C receptacle's mouth may
sit and still take a plug. About the plug's insertion depth."""

# ---------------------------------------------------------------- estimates --
# The components library has the DevKitC-1's outline and nothing standing on
# it. Each of these is owed a caliper reading of a bare board.

ESP_ABOVE = 3.5
"""ESTIMATE. Height of the tallest part on the board's top: the module can,
the buttons or the USB-C receptacles."""

USB_Z = 1.6
"""ESTIMATE. Height of a USB-C receptacle's centre above the PCB."""

USB_RECEPT_W = 8.94
USB_RECEPT_L = 7.35
"""ESTIMATE. Footprint of each USB-C receptacle, from the common mid-mount part.
The receptacles are assumed centred either side of the board's centreline, at
USB_C_CENTRES_APART."""

CORNER_FREE = 3.0
"""ESTIMATE. How far in from each short end the board is free of parts on both
faces, top and bottom, outside the header pad rows. The pads and pegs that
hold the board live in this strip."""

# ----------------------------------------------------------------- derived --

HEAD_R = P.BODY_OD / 2
BOSS_R = (M3.OD - INSERT_INTERFERENCE) / 2 + BOSS_WALL
SEAT_Z = P.PLATE_Z
"""DERIVED. The posts end where the plate sits: the plate's ears are the joint
inside the case. The seam outside is at the rim."""

PLATE_TOP = P.PLATE_Z + plate.PLATE_T


def led_breakout_z() -> float:
    """Lowest height at which an LED bore breaks out of the head's outer wall."""
    run = HEAD_R - P.LED_RING_R
    axis_z = P.LED_Z + run * math.tan(math.radians(P.ILLUM_ANGLE))
    return axis_z - (P.LED_SEAT_D / 2) / math.cos(math.radians(P.ILLUM_ANGLE))


def board_layout() -> tuple[float, float]:
    """(inner radius the board forces, x of the board's USB edge).

    The DevKitC-1 lies along X with its USB edge towards -X, as near the wall as
    it will go so a cable reaches it. The antenna overhangs the far edge, so the
    board plus antenna is not a rectangle and not centred: the smallest circle
    that holds it is found by searching over where the USB edge sits.
    """
    half_w = E.PCB_W / 2
    ant_half = E.ANTENNA_W / 2

    def need(x_usb: float) -> float:
        far = x_usb + E.LENGTH_WITH_ANTENNA
        pcb_far = x_usb + E.PCB_L
        return max(
            math.hypot(x_usb, half_w),
            math.hypot(pcb_far, half_w),
            math.hypot(far, ant_half),
        ) + CASE_CLEAR

    lo, hi = -E.LENGTH_WITH_ANTENNA, 0.0
    for _ in range(200):  # golden-section on a convex function
        a = hi - (hi - lo) / 1.618
        b = lo + (hi - lo) / 1.618
        if need(a) < need(b):
            hi = b
        else:
            lo = a
    x_usb = (lo + hi) / 2
    return need(x_usb), x_usb


def inner_r() -> float:
    """The case's inner radius: the largest of what the board, the LED leads and
    the posts each demand."""
    board_r, _ = board_layout()
    lead_r = HEAD_R + LEAD_ROOM * math.cos(math.radians(P.ILLUM_ANGLE)) + LEAD_R
    return max(board_r, lead_r)


R_IN = inner_r()
R_OUT = R_IN + WALL
POST_R = R_IN - BOSS_R - 0.3
"""DERIVED. The posts stand on the floor just clear of the wall, so the lid's
bosses above them, which hang down inside the same wall, clear it too."""


def post_angles() -> list[float]:
    """Four angles midway between LEDs and clear of the board's band."""
    step = 360.0 / P.LED_N
    band = E.PCB_W / 2 + CASE_CLEAR + BOSS_R
    ok = [
        step * (k + 0.5)
        for k in range(P.LED_N)
        if abs(POST_R * math.sin(math.radians(step * (k + 0.5)))) > band
    ]
    if len(ok) < POST_N:
        raise ValueError(f"only {len(ok)} post positions clear the board; need {POST_N}")
    return ok[:POST_N]


def post_positions() -> list[tuple[float, float]]:
    return [(POST_R * math.cos(math.radians(a)), POST_R * math.sin(math.radians(a)))
            for a in post_angles()]


def esp_z() -> float:
    """Underside of the DevKitC-1's PCB. Whichever is higher: clear of the
    detector's socket, or clear of the plate by the wiring room."""
    from .case import detector_top

    return max(detector_top() + STACK_GAP, PLATE_TOP + UNDERSIDE_ROOM)


def tray_top() -> float:
    """Top of the tray's rails, which is what the lid's bosses bear on. The
    corner pads rise PAD_RISE above it to the board."""
    return esp_z() - PAD_RISE


def peg_w() -> float:
    """Width of the strip along each long edge that the lid's pegs may press.

    At the USB end the receptacles reach nearly to the board's edge, so the
    peg has to fit outside them.
    """
    usb_edge = E.USB_C_CENTRES_APART / 2 + USB_RECEPT_W / 2
    return E.PCB_W / 2 - usb_edge - 0.2


def corners() -> list[tuple[float, float, float, float]]:
    """(x_min, x_max, y_min, y_max) of the four corner strips the board is
    held by, in head coordinates."""
    x0 = board_x0()
    x1 = x0 + E.PCB_L
    w = peg_w()
    half = E.PCB_W / 2
    out = []
    for xa, xb in ((x0, x0 + CORNER_FREE), (x1 - CORNER_FREE, x1)):
        for sy in (-1, 1):
            ya, yb = sorted((sy * (half - w), sy * half))
            out.append((xa, xb, ya, yb))
    return out


def lid_inner_top() -> float:
    return esp_z() + E.THICKNESS + ESP_ABOVE + STACK_GAP


def lid_top() -> float:
    return lid_inner_top() + WALL


def rim_top() -> float:
    return lid_top() - LID_PROUD


def board_x0() -> float:
    return board_layout()[1]


# ------------------------------------------------------------------- parts --

def _cyl(r: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0) -> Part:
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=_MIN)


def _ring(r_in: float, r_out: float, z0: float, z1: float) -> Part:
    return _cyl(r_out, z0, z1) - _cyl(r_in, z0 - 1.0, z1 + 1.0)


def base() -> Part:
    """Floor ring, collar, wall with its half of the lap, and the posts."""
    z0 = FOOT_RELIEF
    bore = HEAD_R + HEAD_CLEAR
    floor = _ring(bore, R_OUT, z0, z0 + FLOOR_T)
    collar = _ring(bore, bore + WALL, z0 + FLOOR_T - 0.5, COLLAR_TOP)
    # One wall from the foot to the rim. Its inner half stops at the lid's
    # underside, a step the lid lands on; the outer half rises to the rim.
    step = lid_inner_top()
    wall = _ring(R_IN, R_OUT, z0 + FLOOR_T - 0.5, step)
    rim = _ring(R_IN + WALL / 2, R_OUT, step - 0.5, rim_top())
    part = floor + collar + wall + rim

    spigot_top = PLATE_TOP + POST_SPIGOT_ENGAGE
    for x, y in post_positions():
        part = part + _cyl(BOSS_R, z0 + FLOOR_T - 0.5, SEAT_Z, x, y)
        part = part + _cyl(POST_SPIGOT_D / 2, SEAT_Z - 0.5, spigot_top, x, y)
        # The screw goes up through the post; its head sits in the foot.
        part = part - _cyl(M3_CLEAR_D / 2, z0 - 1.0, spigot_top + 1.0, x, y)
        part = part - _cyl(M3_HEAD_D / 2, z0 - 1.0, z0 + M3_HEAD_H, x, y)

    part = part - usb_opening()
    return part - key_notch()


def _key_frame(part: Part) -> Part:
    return Rot(0, 0, KEY_ANGLE) * part


def key_notch() -> Part:
    """The notch the lid's key drops into: through the inner half of the step
    only, trimmed to the circle so no corner bites the outer half."""
    step = lid_inner_top()
    r0, r1 = R_IN - 1.0, R_IN + WALL / 2
    box = _key_frame(Pos((r0 + r1) / 2, 0, step - KEY_H - 0.3) * Box(
        r1 - r0, KEY_W + 2 * KEY_CLEAR, KEY_H + 0.3 + 1.0, align=_MIN))
    return box & _cyl(r1, 0, lid_top() + 10.0)


def usb_opening() -> Part:
    """The cutter for the one-plug USB-C opening, through the wall at -X."""
    z_usb = esp_z() + E.THICKNESS + USB_Z
    y_usb = NATIVE_USB_SIDE * E.USB_C_CENTRES_APART / 2
    # Long enough in X to get through the wall where it curves in at the
    # opening's edges, not only on the axis.
    y_far = abs(y_usb) + USB_PLUG_W / 2
    depth = R_OUT - math.sqrt(R_IN ** 2 - y_far ** 2) + 2.0
    return Pos(-R_OUT - 1.0 + depth / 2, y_usb, z_usb) * Box(
        depth + 2.0, USB_PLUG_W, USB_PLUG_H, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )


def puck_plate() -> Part:
    """The detector plate with an ear out to each post."""
    part = plate.detector_plate()
    reach = R_IN - 0.3
    for a in post_angles():
        ear = Rot(0, 0, a) * Pos((HEAD_R - 1.0 + reach) / 2, 0, 0) * Box(
            reach - HEAD_R + 1.0, 2 * BOSS_R, plate.PLATE_T, align=_MIN
        )
        part = part + ear
    # Trim the ear ends to the inside of the wall, keeping the spigot below.
    part = part & Pos(0, 0, -10.0) * Cylinder(reach, plate.PLATE_T + 10.0, align=_MIN)
    for x, y in post_positions():
        part = part - Pos(x, y, -1.0) * Cylinder(
            POST_SPIGOT_D / 2 + SPIGOT_CLEAR, plate.PLATE_T + 2.0, align=_MIN)
    return part


def tray() -> Part:
    """Two rails outside the board, a cross-beam under each short end carrying
    corner pads and fences, and four standoff tubes down to the plate's ears.

    Nothing of the tray is under the board except the two end strips, so the
    header pads along both long edges are open underneath for soldering, and
    the middle is open for the detector's cable and the LED wires to come up.
    """
    z0, z1 = tray_top() - TRAY_T, tray_top()
    zb = esp_z()
    x0 = board_x0()
    x1 = x0 + E.PCB_L
    xc = (x0 + x1) / 2
    half = E.PCB_W / 2
    rail_y = half + FENCE_CLEAR + FENCE_T + RAIL_W / 2
    span = 2 * (rail_y + RAIL_W / 2)

    part = None
    for sy in (-1, 1):
        rail = Pos(xc, sy * rail_y, z0) * Box(E.PCB_L + 2 * FENCE_T, RAIL_W, TRAY_T, align=_MIN)
        part = rail if part is None else part + rail
    for xa, xb in ((x0, x0 + CORNER_FREE), (x1 - CORNER_FREE, x1)):
        part = part + Pos((xa + xb) / 2, 0, z0) * Box(xb - xa, span, TRAY_T, align=_MIN)

    # Corner pads up to the board, and an L of fence outside each corner.
    for xa, xb, ya, yb in corners():
        part = part + Pos((xa + xb) / 2, (ya + yb) / 2, z1 - 0.5) * Box(
            xb - xa, yb - ya, PAD_RISE + 0.5, align=_MIN)
        sx = -1 if xa == x0 else 1
        sy = 1 if ya > 0 else -1
        x_out = (x0 - FENCE_CLEAR - FENCE_T / 2) if sx < 0 else (x1 + FENCE_CLEAR + FENCE_T / 2)
        y_out = sy * (half + FENCE_CLEAR + FENCE_T / 2)
        fence_h = PAD_RISE + E.THICKNESS + 0.5
        part = part + Pos(x_out, (ya + yb) / 2, z1 - 0.5) * Box(
            FENCE_T, (yb - ya) + FENCE_CLEAR + FENCE_T, fence_h + 0.5, align=_MIN)
        part = part + Pos((xa + xb) / 2 + sx * (FENCE_CLEAR + FENCE_T) / 2, y_out, z1 - 0.5) * Box(
            (xb - xa) + FENCE_CLEAR + FENCE_T, FENCE_T, fence_h + 0.5, align=_MIN)

    for x, y in post_positions():
        # A link from the post across to the nearer rail, then the tube down.
        y_rail = math.copysign(rail_y, y)
        link_len = abs(y - y_rail) + RAIL_W / 2
        part = part + Pos(x, (y + y_rail) / 2, z0) * Box(RAIL_W, link_len, TRAY_T, align=_MIN)
        part = part + _cyl(BOSS_R, PLATE_TOP, z1, x, y)
    part = part & _cyl(R_IN - 0.3, z0 - 50.0, zb + 10.0)
    for x, y in post_positions():
        part = part - _cyl(M3_CLEAR_D / 2, PLATE_TOP - 1.0, z1 + 1.0, x, y)
        # The socket the post's spigot rises into.
        part = part - _cyl(POST_SPIGOT_D / 2 + SPIGOT_CLEAR, PLATE_TOP - 1.0,
                           PLATE_TOP + POST_SPIGOT_ENGAGE + 0.3, x, y)
    return part


def lid(ribs: bool = True) -> Part:
    """A flat disc in the rim's rebate with its key, bosses with inserts hanging
    down to the tray on crush ribs, and pegs for the board. Nothing passes
    through the top.

    ``ribs=False`` leaves the crush ribs off, which is the lid as it sits once
    they have crushed; check() uses it for clearances."""
    top_in, top = lid_inner_top(), lid_top()
    part = _cyl(R_IN + WALL / 2 - LAP_CLEAR, top_in, top)

    pilot_r = (M3.OD - INSERT_INTERFERENCE) / 2
    boss_end = tray_top() + CRUSH
    for x, y in post_positions():
        part = part + _cyl(BOSS_R, boss_end, top_in + 0.5, x, y)
        a = math.atan2(y, x)
        for i in range(3 if ribs else 0):
            # Drawn as printed, reaching CRUSH into the tray.
            t = a + i * 2 * math.pi / 3
            rr = (pilot_r + BOSS_R) / 2
            part = part + Pos(x + rr * math.cos(t), y + rr * math.sin(t), tray_top() - CRUSH) * Rot(
                0, 0, math.degrees(t)) * Box(BOSS_R - pilot_r, 0.8, 2 * CRUSH + 0.5, align=_MIN)
        # Insert pilot from the boss's end. Blind: it stops a wall short of
        # the top so the face stays whole.
        depth = min(M3.LENGTH + 0.5, top - WALL / 2 - boss_end)
        part = part - _cyl(pilot_r, tray_top() - 1.0, boss_end + depth, x, y)

    # Pegs that press the board's corners down onto the tray's pads.
    board_top = esp_z() + E.THICKNESS
    for xa, xb, ya, yb in corners():
        part = part + Pos((xa + xb) / 2, (ya + yb) / 2, board_top) * Box(
            xb - xa, yb - ya, top_in - board_top + 0.5, align=_MIN)

    # The key, hanging under the disc's edge into the rim's notch.
    r0, r1 = R_IN - 1.0, R_IN - 1.0 + KEY_T
    tab = Pos((r0 + r1) / 2, 0, top_in - KEY_H) * Box(r1 - r0, KEY_W, KEY_H + 0.5, align=_MIN)
    return part + (_key_frame(tab) & _cyl(r1, 0, top + 10.0))


def esp32() -> Part:
    """A bare DevKitC-1 as an envelope: outline and antenna from the components
    library; what stands on it from the estimates above. The parts envelope
    stops CORNER_FREE short of each end and inside the peg strips, which is
    exactly the claim those estimates make, so check() tests it."""
    x0, z = board_x0(), esp_z()
    xc = x0 + E.PCB_L / 2
    pcb = Pos(xc, 0, z) * Box(E.PCB_L, E.PCB_W, E.THICKNESS, align=_MIN)
    ant = Pos(x0 + E.PCB_L + E.ANTENNA_OVERHANG / 2, 0, z) * Box(
        E.ANTENNA_OVERHANG + 0.5, E.ANTENNA_W, E.THICKNESS, align=_MIN)
    keep_w = E.PCB_W - 2 * peg_w() - 0.4
    parts_top = Pos(xc, 0, z + E.THICKNESS - 0.2) * Box(
        E.PCB_L - 2 * CORNER_FREE, keep_w, ESP_ABOVE + 0.2, align=_MIN)
    part = pcb + ant + parts_top
    # The USB-C receptacles sit at the very end, inside the corner strip but
    # between the pegs.
    for sy in (-1, 1):
        part = part + Pos(x0 + USB_RECEPT_L / 2, sy * E.USB_C_CENTRES_APART / 2,
                          z + E.THICKNESS - 0.2) * Box(
            USB_RECEPT_L, USB_RECEPT_W, ESP_ABOVE + 0.2, align=_MIN)
    return part


def lead_keepouts() -> Part:
    return head.lead_keepouts()


PRINTED = ("puck_base", "puck_plate", "puck_tray", "puck_lid")
FAMILIES = PRINTED + ("esp32_board",)


def _explode() -> float:
    return float(os.environ.get("SPECTRA_EXPLODE", "0") or 0)


def parts() -> dict[str, Part]:
    return {
        "puck_base": base(),
        "puck_plate": Pos(0, 0, P.PLATE_Z) * puck_plate(),
        "puck_tray": tray(),
        "puck_lid": lid(),
        "esp32_board": esp32(),
    }


def placed() -> list[tuple[str, Part]]:
    """The puck's own solids, placed, exploded along Z if SPECTRA_EXPLODE is set.

    The head, its board and the sample are placed by assembly.py as always; the
    base drops away below them and everything above lifts, so the stack reads
    in the order it is screwed together.
    """
    e = _explode()
    shift = {"puck_base": -e, "puck_plate": 0.0, "puck_tray": e,
             "esp32_board": 2 * e, "puck_lid": 3 * e}
    return [(name, Pos(0, 0, shift[name]) * solid) for name, solid in parts().items()]


# ------------------------------------------------------------------ checks --

def _overlap(a: Part, b: Part) -> float:
    hit = a & b
    return 0.0 if hit is None else sum(s.volume for s in hit.solids())


def check() -> list[tuple[str, bool, str]]:
    ps = parts()
    body = head.body()
    out = []
    for name in PRINTED:
        n = len(ps[name].solids())
        out.append((f"{name} is one solid", n == 1, f"{n} solid(s)"))

    lid_part = ps["puck_lid"]
    top = max(f.center().Z for f in lid_part.faces())
    top_faces = [f for f in lid_part.faces() if abs(f.center().Z - top) < 1e-6]
    holes = sum(len(f.inner_wires()) for f in top_faces)
    out.append(("the lid's top is unbroken", len(top_faces) == 1 and holes == 0,
                f"{len(top_faces)} top face(s), {holes} hole(s) through it"))

    body_top = ps["puck_base"].bounding_box().max.Z
    out.append(("the seam is at the rim, the lid standing proud of it",
                math.isclose(lid_top() - body_top, LID_PROUD, abs_tol=1e-6),
                f"rim z={body_top:.2f}, lid top z={lid_top():.2f}; the lid lands on the "
                f"rim's step at z={lid_inner_top():.2f}, so the rim sets its height"))

    # The joint aligns the lid by itself: seated it touches nothing of the base;
    # turned past its play, the key strikes the notch.
    seated_lid = lid(ribs=False)
    r_key = R_IN - 1.0 + KEY_T / 2
    play = math.degrees(KEY_CLEAR / r_key)
    turned = _overlap(Rot(0, 0, 2 * play + 0.1) * seated_lid, ps["puck_base"])
    out.append(("the key alone clocks the lid", turned > 1e-3,
                f"turned {2 * play + 0.1:.2f}deg, the key strikes its notch ({turned:.3f} mm^3)"))
    v = _overlap(_ring(R_IN + WALL / 2, R_OUT, 0.0, lid_top() + 1.0), key_notch())
    out.append(("the key's notch does not show from outside", v < 1e-6,
                f"notch in the rim's outer half: {v:.3f} mm^3"))

    hit = ps["puck_lid"] & ps["puck_tray"]
    depth = 0.0 if hit is None or not hit.solids() else hit.bounding_box().size.Z
    out.append(("the crush ribs, and only they, reach into the tray",
                math.isclose(depth, CRUSH, abs_tol=1e-3) and _overlap(seated_lid, ps["puck_tray"]) < 1e-3,
                f"ribs printed {depth:.2f} into the tray: the stack may be +/-{CRUSH:g} out "
                f"and the lid still lands and clamps"))

    # Fasteners do not index: with every joint at the limit of its play, no
    # screw touches the wall of a hole it passes through.
    m3_room = (M3_CLEAR_D - 3.0) / 2
    lid_play = math.hypot(LAP_CLEAR, KEY_CLEAR * POST_R / r_key)
    out.append(("no M3 screw touches a hole wall",
                lid_play + SPIGOT_CLEAR < m3_room,
                f"lid play at the screw {lid_play:.2f} + tray play {SPIGOT_CLEAR:g}; "
                f"holes clear an M3 by {m3_room:.2f}"))
    # The plate on the head, and the tray on the posts, align by their spigots.
    turned = _overlap(Rot(0, 0, 1.0) * ps["puck_plate"], body)
    out.append(("the plate's spigot clocks it on the head", turned > 1e-3,
                f"turned 1deg, the key arc strikes a web ({turned:.3f} mm^3)"))
    moved = 2 * SPIGOT_CLEAR
    hit = min(_overlap(Pos(moved * math.cos(math.radians(a)), moved * math.sin(math.radians(a)), 0)
                       * ps[name], ps["puck_base"])
              for name in ("puck_plate", "puck_tray") for a in (0, 90))
    out.append(("the posts' spigots locate the plate and the tray", hit > 1e-3,
                f"shifted {moved:g} either way, each strikes a spigot (least {hit:.3f} mm^3)"))

    m2_play = plate.spigot_play_at(head.PLATE_SCREW_R)
    m2_room = (head.PLATE_SCREW_CLEAR_D - 2.0) / 2
    out.append(("no M2 screw touches a hole wall", m2_play < m2_room,
                f"plate play on the head at the screw {m2_play:.2f}; holes clear an M2 by {m2_room:.2f}"))
    head_play = SPIGOT_CLEAR * (1 + HEAD_R / POST_R) + plate.spigot_play_at(HEAD_R)
    out.append(("the collar guides the head and never locates it", head_play < HEAD_CLEAR,
                f"head play against the base {head_play:.2f}; collar clears it by {HEAD_CLEAR:g}"))

    heads_ok = FOOT_RELIEF + M3_HEAD_H <= SEAT_Z and M3_HEAD_H >= 3.0
    out.append(("screw heads sit inside the foot", heads_ok,
                f"counterbore {M3_HEAD_H:g} deep for a 3 mm socket head"))

    low = min(ps[n].bounding_box().min.Z for n in PRINTED)
    out.append(("the port land is the only stop", low > 0.0,
                f"lowest case point z={low:.2f}, port face z=0"))

    lever = R_OUT - P.PORT_LAND_OD / 2
    tilt = math.degrees(math.atan2(FOOT_RELIEF, lever))
    out.append(("the foot catches a tilt inside the ruled tolerance",
                tilt < P.ILLUM_ANGLE_TOL,
                f"foot touches down at {tilt:.2f}deg; ruled +/-{P.ILLUM_ANGLE_TOL:g}deg"))

    out.append(("collar stops below the LED breakout",
                COLLAR_TOP < led_breakout_z(),
                f"collar top z={COLLAR_TOP:g}, LED bores break out from z={led_breakout_z():.2f}"))

    keep = lead_keepouts()
    for name in PRINTED:
        v = _overlap(ps[name], keep)
        out.append((f"{name} leaves the LED leads room", v < 1e-6, f"overlap {v:.3f} mm^3"))

    solids = {**{n: ps[n] for n in PRINTED}, "head": body, "esp32": ps["esp32_board"]}
    solids["puck_lid"] = seated_lid  # its ribs reach into the tray on purpose
    if plate.available():
        from build123d import Pos as _P

        solids["as7341"] = _P(0, 0, PLATE_TOP) * plate.as7341_board()
    names = list(solids)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = _overlap(solids[a], solids[b])
            out.append((f"{a} clear of {b}", v < 1e-3, f"overlap {v:.3f} mm^3"))

    _, x_usb = board_layout()
    reach = R_OUT - abs(x_usb)
    out.append(("a USB-C plug reaches the board", reach <= USB_REACH,
                f"receptacle mouth {reach:.2f} behind the outer wall; plug reaches {USB_REACH:g}"))
    return out


def screw_length() -> tuple[float, float]:
    """Shortest and longest M3 that clamps the stack without bottoming out.

    From the counterbore floor in the foot up to the lid boss's end, plus at
    least 3 mm into the insert and less than its length."""
    grip = tray_top() + CRUSH - (FOOT_RELIEF + M3_HEAD_H)
    return grip + 3.0, grip + M3.LENGTH - 0.5


def print_ready() -> dict[str, Part]:
    """Every part to print, turned to its print orientation and set on z = 0.

    The base and the head print foot down, as modelled. The plate, the tray and
    the lid print upside down: the plate on its top with the spigot standing up,
    the tray on its flat top with the standoffs standing up, the lid on its top
    face with the bosses standing up, so none needs support.
    """
    flip = Rot(180, 0, 0)
    raw = {
        "head": head.body(),
        "puck_base": base(),
        "puck_plate": flip * puck_plate(),
        "puck_tray": flip * tray(),
        "puck_lid": flip * lid(),
    }
    return {name: Pos(0, 0, -p.bounding_box().min.Z) * p for name, p in raw.items()}


def export(out_dir) -> list:
    """STEP for Fusion and STL for the slicer, one pair per printed part."""
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
    fails = 0
    print(f"puck v1: {2 * R_OUT:.1f} dia x {lid_top():.1f} tall above the port face "
          f"(plus the {P.LIP_PROUD:g} lip)")
    print(f"  inner radius {R_IN:.2f}, posts at r={POST_R:.2f}, angles "
          f"{', '.join(f'{a:g}' for a in post_angles())}")
    lo, hi = screw_length()
    print(f"  4 x M3 socket head, {lo:.1f} to {hi:.1f} mm long; "
          f"4 x M3x6 inserts in the lid bosses, 3 x M2x4 in the head rim\n")
    for name, ok, detail in check():
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {name}  {detail}")
    print("\n  [est] ESP_ABOVE, USB_Z, USB_RECEPT_W/L, CORNER_FREE — caliper a bare DevKitC-1")
    return fails


if __name__ == "__main__":
    import sys

    if "--export" in sys.argv:
        from pathlib import Path

        dest = Path(__file__).resolve().parents[2] / "export" / "puck"
        for path in export(dest):
            print(f"wrote {path.relative_to(dest.parents[1])}")
    raise SystemExit(report())
