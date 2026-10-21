"""The printed optical head: body, port, compliant lip, baffle, LED seats.

    python -m spectra.cad.head        # build it, report solids and volume

One part, printed top rim down in black PETG, no supports (see
`puck.print_ready()` for why not port face down). The lip and the collection tube
are features of that one part rather than separate pieces, because a light seal
made of two pieces has a joint, and a joint at the port is a light leak.

Chamfers are cut with rotated box cutters rather than kernel fillets, which is
the printed-case discipline already in use on this system: a kernel fillet on a
thin printed wall is a failure waiting for a geometry kernel to find it, and a
cutter is a shape you can see in the render.
"""

from __future__ import annotations

import math

from build123d import Align, Cylinder, Part, Pos, Rot

from components import heatset_insert_m2x4 as M2

from . import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

# ------------------------------------------------- fastening the plate on --

INSERT_INTERFERENCE = 0.4
"""CHOSEN. Diametral interference of a heat-set pilot against the insert's
knurl OD, in the middle of the 0.30-0.50 mm the components library gives for
these inserts. Sized from OD, never from the vendor's label."""

PLATE_SCREW_N = 3
"""CHOSEN. Three M2 screws hold the detector plate down on the head's top rim.
Three define a plane; a fourth would only fight it. Until these existed nothing
held the plate on at all, which is nothing holding the detector square to the
collection axis."""

PLATE_SCREW_R = (P.LED_RING_R + P.BODY_OD / 2) / 2
"""DERIVED. Middle of the solid rim between the cavity wall and the outside."""

PLATE_SCREW_CLEAR_D = 2.6
"""CHOSEN. Clearance hole for M2 through the plate: 0.3 mm a side, more than the
plate's spigot lets it move (see `plate.spigot_play_at()`), so the screws clamp
the plate and never locate it. Jared, 2026-10-01: fasteners fasten, they do not
index."""


def plate_screw_angles() -> list[float]:
    """Where the plate screws go: each exactly midway between two LEDs.

    Midway is the farthest any point on the rim can be from an LED bore, and
    the bores break out through this same rim. Spread as evenly as the LED
    count allows.
    """
    step = 360.0 / P.LED_N
    picks = sorted({round(i * P.LED_N / PLATE_SCREW_N) % P.LED_N for i in range(PLATE_SCREW_N)})
    return [step * (k + 0.5) for k in picks]


def plate_screw_positions() -> list[tuple[float, float]]:
    return [
        (PLATE_SCREW_R * math.cos(math.radians(a)), PLATE_SCREW_R * math.sin(math.radians(a)))
        for a in plate_screw_angles()
    ]


# ------------------------------------------------------------ the LED leads --

LEAD_ROOM = 8.0
"""CHOSEN. How far an LED's sealed back, its leads and their solder joints stand
out of the head along the bore axis. Nothing mounted on or around the head may
occupy it."""

LEAD_CLEAR = 0.3
"""CHOSEN. Radial air between an LED's sealed back and anything round it: the
flange's counterbore in the head and the notch in the plate. Enough for PETG to
print a hole a little small and still slip over the heat-shrink."""

LEAD_R = P.LED_FLANGE_D / 2 + P.LED_SEAL_T + LEAD_CLEAR
"""DERIVED. Radius of the keepout round each LED's axis, and of the counterbore
that carries it into the head: the flange, the heat-shrink sealed over it, and
LEAD_CLEAR. It was the bore plus 0.5 until 2026-10-21, which cleared a bare 5.8
flange by 0.20 a side and a sealed one by nothing. Rests on the nominal flange
and the seal wall, both ESTIMATE."""

FLARE_ANGLE = 15.0
"""CHOSEN. Half angle of the cone the bore opens into the cavity through, from
where the lamp's body starts (P.LED_DOME_T) inward, so the dome sits in air.
The bore was a plain cylinder cut from the emitter point, which left a wedge of
cavity wall across half its end: 53% of each LED's axial light struck it. A
plain cylinder started at the same place and run into the cavity clears the
axial rays but still takes 0.2% of the light from the dome's flanks to the edge
of the port; 6 degrees takes none, with the lamp seated half a millimetre either
side of nominal too. 15 is the margin on that, measured by led.port_view()
rather than assumed."""


def lead_exit() -> float:
    """Distance along the bore axis, from the emitter, at which the axis leaves
    the head: through the outer wall or through the top face, whichever comes
    first. With 3 mm LEDs at LED_Z 14 it was the wall; with the ruled 5 mm set at
    LED_Z 18 it is the top face, under the detector plate."""
    s, c = math.sin(math.radians(P.ILLUM_ANGLE)), math.cos(math.radians(P.ILLUM_ANGLE))
    return min((P.BODY_H - P.LED_Z) / s, (P.BODY_OD / 2 - P.LED_RING_R) / c)


def lead_start() -> float:
    """Where the keepout begins along the axis: far enough inside the exit that
    the whole bore mouth is covered, wherever the axis comes out."""
    return lead_exit() - P.LED_SEAT_D / 2


def lead_reach() -> tuple[float, float]:
    """(radius, height) the keepouts reach out to, for whatever has to clear
    them."""
    s, c = math.sin(math.radians(P.ILLUM_ANGLE)), math.cos(math.radians(P.ILLUM_ANGLE))
    t = lead_start() + LEAD_ROOM
    return P.LED_RING_R + t * c + LEAD_R * s, P.LED_Z + t * s + LEAD_R * c


def lead_keepouts() -> Part:
    """The space each LED's sealed back and leads occupy, along its bore, from
    where the bore leaves the head.

    The bores are aimed at the port, so they climb at 45 degrees and break out
    of the head under or through its top rim. The leads therefore come out
    beneath whatever sits on the rim. That is the detector plate, and it is why
    the plate is notched at every LED.
    """
    tool = None
    for i in range(P.LED_N):
        a = 360.0 * i / P.LED_N
        k = (Rot(0, 0, a) * Pos(P.LED_RING_R, 0, P.LED_Z) * Rot(0, P.ILLUM_ANGLE, 0)
             * Pos(0, 0, lead_start()) * Cylinder(LEAD_R, LEAD_ROOM, align=_MIN))
        tool = k if tool is None else tool + k
    return tool


def _plate_insert_pilots() -> Part:
    """Heat-set pilots for the plate screws, down into the rim from the top."""
    depth = M2.LENGTH + 0.5
    r = (M2.OD - INSERT_INTERFERENCE) / 2
    tool = None
    for x, y in plate_screw_positions():
        pilot = Pos(x, y, P.BODY_H - depth) * Cylinder(r, depth + 1.0, align=_MIN)
        tool = pilot if tool is None else tool + pilot
    return tool


def _led_bore_length() -> float:
    """How long an LED bore has to be to break out through the body wall.

    Measured along the beam, from the emitter plane at the cavity wall to past
    the outside of the body. Derived, never typed: change the body diameter and
    the bores still break out.
    """
    radial = P.BODY_OD / 2 - P.LED_RING_R
    return radial / math.cos(math.radians(P.ILLUM_ANGLE)) + 1.0


def flare_reach() -> float:
    """How far the flare runs back into the cavity from the emitter point,
    along the axis: until even its outermost generator, the one nearest the
    port face, has left the wall, plus a millimetre. Derived from the inequality
    that puts that generator inside the cavity radius."""
    a = math.radians(P.ILLUM_ANGLE)
    s, c = math.sin(a), math.cos(a)
    k = math.tan(math.radians(FLARE_ANGLE))
    r0 = P.LED_SEAT_D / 2 + P.LED_DOME_T * k
    return c * r0 / (s - c * k) + 1.0


def led_axis_positions() -> list[tuple[float, float, float]]:
    """Emitter centre of each LED, in head coordinates.

    Every one of them aims at the port centre by construction: the ring radius
    is derived from the emitter height through the ruled 45 degrees, so there is
    no aiming step and nothing to get wrong per-LED.
    """
    out = []
    for i in range(P.LED_N):
        a = math.radians(360.0 * i / P.LED_N)
        out.append((P.LED_RING_R * math.cos(a), P.LED_RING_R * math.sin(a), P.LED_Z))
    return out


def _led_bore() -> Part:
    """One LED's bore in its own frame: the emitter point at the origin, +Z
    out along the axis through the wall.

    Three coaxial cuts, from the cavity outward:

    - a cone, FLARE_ANGLE either side, opening from where the lamp's body
      starts back into the cavity, so the dome sits in open air and nothing of
      the head is in its light;
    - the LED_SEAT_D bore the coupon chose, which grips the body, out to the
      shoulder at P.LED_SHOULDER_T;
    - a counterbore of LEAD_R, the sealed flange plus clearance, from the
      shoulder out through the rim. The flange cannot pass the bore, so it lands
      on the shoulder, and the tip lands at the emitter point.
    """
    from build123d import Cone

    k = math.tan(math.radians(FLARE_ANGLE))
    t0, reach = P.LED_DOME_T, flare_reach()
    r_b = P.LED_SEAT_D / 2
    flare = Pos(0, 0, -reach) * Cone(r_b + (t0 + reach) * k, r_b, t0 + reach, align=_MIN)
    # Each cut runs half a millimetre into the next, inside it, so the three
    # fuse into one tool rather than meeting on a shared face.
    bore = Pos(0, 0, t0 - 0.5) * Cylinder(r_b, P.LED_SHOULDER_T - t0 + 1.0, align=_MIN)
    outer = _led_bore_length() + P.LED_LENGTH
    counter = Pos(0, 0, P.LED_SHOULDER_T) * Cylinder(LEAD_R, outer - P.LED_SHOULDER_T, align=_MIN)
    return flare + bore + counter


def _led_bores() -> Part:
    """The eight angled bores, as one cutting tool."""
    one = _led_bore()
    tool = None
    for i in range(P.LED_N):
        a = 360.0 * i / P.LED_N
        # Rot(0, +45, 0) sends +Z to the OUTWARD beam direction in +X, so the
        # bore runs from the emitter plane outwards through the wall. Rot about
        # Z then walks it around the ring.
        bore = Rot(0, 0, a) * Pos(P.LED_RING_R, 0, P.LED_Z) * Rot(0, P.ILLUM_ANGLE, 0) * one
        tool = bore if tool is None else tool + bore
    return tool


def web_angles() -> list[float]:
    """Azimuth of each web: midway between two LEDs, every 360 / WEB_N."""
    return [P.WEB_ANGLE0 + 360.0 * i / P.WEB_N for i in range(P.WEB_N)]


def _webs() -> Part:
    """Radial webs holding the collection tube to the body wall."""
    z0 = P.PLATE_Z - P.WEB_H
    # Bite into the tube at one end and the cavity wall at the other. A web that
    # merely reaches them shares a face with each and fuses into nothing; the
    # kernel counts that as three solids, and report() fails on it.
    bite = 0.5
    r_in = P.BAFFLE_OD / 2 - bite
    r_out = P.LED_RING_R + bite
    length = r_out - r_in
    tool = None
    for a in web_angles():
        web = (
            Rot(0, 0, a)
            * Pos(r_in + length / 2, 0, z0 + P.WEB_H / 2)
            * _box(length, P.WEB_T, P.WEB_H)
        )
        tool = web if tool is None else tool + web
    return tool


def _box(length: float, width: float, height: float) -> Part:
    from build123d import Box

    return Box(length, width, height)


def body() -> Part:
    """The whole printed head as one solid."""
    # The outer shell, standing on the port face at z = 0.
    part = Pos(0, 0, 0) * Cylinder(P.BODY_OD / 2, P.BODY_H, align=_MIN)

    # Hollow it out, leaving the port face as a floor. The cavity wall is the
    # LED ring radius, which is what puts every emitter flush with the inside.
    cavity = Pos(0, 0, P.FLOOR_T) * Cylinder(
        P.LED_RING_R, P.BODY_H - P.FLOOR_T + 1.0, align=_MIN
    )
    part = part - cavity

    # The collection tube, and the webs that hold it.
    tube = Pos(0, 0, P.BAFFLE_Z0) * Cylinder(P.BAFFLE_OD / 2, P.BAFFLE_L, align=_MIN)
    part = part + tube + _webs()

    # Bore the tube and the port. The port bore runs a millimetre past the
    # floor on both sides so the cut is clean rather than tangent.
    part = part - Pos(0, 0, P.BAFFLE_Z0 - 1.0) * Cylinder(
        P.COLLECT_D / 2, P.BAFFLE_L + 2.0, align=_MIN
    )
    part = part - Pos(0, 0, -1.0) * Cylinder(P.PORT_D / 2, P.FLOOR_T + 2.0, align=_MIN)

    # The LED bores, and the pilots the plate's inserts melt into.
    part = part - _led_bores()
    part = part - _plate_insert_pilots()

    # The compliant lip: a thin ring standing proud of the port face, printed
    # as part of the same solid. It is BELOW z = 0, which is deliberate — the
    # port face is the datum and the stop, and the lip hangs under it to be
    # crushed. See params.LIP_PROUD.
    # It overlaps the floor by half a millimetre rather than merely touching it:
    # two solids sharing one planar face are two solids as far as the kernel is
    # concerned, and report() is what catches that.
    overlap = 0.5
    lip_outer = Pos(0, 0, -P.LIP_PROUD) * Cylinder(
        P.LIP_OD / 2, P.LIP_PROUD + overlap, align=_MIN
    )
    lip_bore = Pos(0, 0, -P.LIP_PROUD - 1.0) * Cylinder(
        P.LIP_ID / 2, P.LIP_PROUD + overlap + 1.0, align=_MIN
    )
    part = part + (lip_outer - lip_bore)

    return part


def report() -> int:
    """Build the head and say what came out. Non-zero if it is not one solid."""
    part = body()
    solids = part.solids()
    bb = part.bounding_box()
    print(f"head: {len(solids)} solid(s), volume {part.volume / 1000:.2f} cm^3")
    print(f"  bbox {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
    print(f"  z from {bb.min.Z:.2f} (lip tip) to {bb.max.Z:.2f} (plate face)")
    if len(solids) != 1:
        print("  FAIL: the head must be a single solid or it is not printable")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(report())
