"""The printed optical head: body, port, compliant lip, baffle, LED seats.

    python -m spectra.cad.head        # build it, report solids and volume

One part, printed port-face-down in black PETG. The lip and the collection tube
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

from . import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _led_bore_length() -> float:
    """How long an LED bore has to be to break out through the body wall.

    Measured along the beam, from the emitter plane at the cavity wall to past
    the outside of the body. Derived, never typed: change the body diameter and
    the bores still break out.
    """
    radial = P.BODY_OD / 2 - P.LED_RING_R
    return radial / math.cos(math.radians(P.ILLUM_ANGLE)) + 1.0


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


def _led_bores() -> Part:
    """The eight angled bores, as one cutting tool."""
    length = _led_bore_length()
    tool = None
    for i in range(P.LED_N):
        a = 360.0 * i / P.LED_N
        # Rot(0, +45, 0) sends +Z to the OUTWARD beam direction in +X, so the
        # bore runs from the emitter plane outwards through the wall. Rot about
        # Z then walks it around the ring.
        bore = (
            Rot(0, 0, a)
            * Pos(P.LED_RING_R, 0, P.LED_Z)
            * Rot(0, P.ILLUM_ANGLE, 0)
            * Cylinder(P.LED_SEAT_D / 2, length, align=_MIN)
        )
        tool = bore if tool is None else tool + bore
    return tool


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
    for i in range(P.WEB_N):
        a = 360.0 * i / P.WEB_N
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

    # The LED bores.
    part = part - _led_bores()

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
