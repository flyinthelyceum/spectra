"""The head and its standards, placed, plus the optical rays as data.

    python -m spectra.cad.assembly

`all_placed()` has the same shape the workbench viewer already calls:
``list[tuple[str, Solid]]``, names without instance indices where a part is
unique. The viewer colours and toggles FAMILIES, so a name here that nothing in
`viewer.MATERIALS` covers is a test failure rather than a grey mesh.

`rays()` is the part that is not a port. It returns the illumination path, the
specular lobe and the collection cone as plain polylines, computed from
`params` alone, so the viewer draws the optics the geometry actually implies
rather than a picture of them. Seeing the specular ray leave at 45 degrees and
sail past the tube is the whole reason to render this before printing it.
"""

from __future__ import annotations

import math

from . import head, params as P, plate, trap


def datums() -> dict[str, float]:
    """Named heights, all in head coordinates with z = 0 at the port face."""
    return {
        "lip_tip": -P.LIP_PROUD,
        "port_face": 0.0,
        "floor_top": P.FLOOR_T,
        "baffle_start": P.BAFFLE_Z0,
        "led_plane": P.LED_Z,
        "plate_face": P.PLATE_Z,
    }


def all_placed(_datums=None) -> list[tuple[str, object]]:
    """Every solid in the assembly, placed, as (name, solid).

    The accessories are staged to one side rather than at the port. Only one of
    them is ever at the port at a time — that is what a calibration sequence is
    — so putting them all there would draw a machine that cannot exist.
    """
    from build123d import Pos

    out: list[tuple[str, object]] = [("head_body", head.body())]

    if plate.available():
        out.append(("detector_plate", Pos(0, 0, P.PLATE_Z) * plate.detector_plate()))
        out.append(("as7341_board",
                    Pos(0, 0, P.PLATE_Z + plate.PLATE_T) * plate.as7341_board()))

    # The sample: a card held against the port face, standing in for whatever is
    # being read. It is the thing the whole geometry is pointed at.
    from build123d import Align, Cylinder

    card = Pos(0, 0, -P.LIP_PROUD - 1.0) * Cylinder(
        P.LIP_OD / 2 + 4.0, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    out.append(("sample_card", card))

    # The two standards, staged beside the head at port height.
    stage_x = P.BODY_OD / 2 + P.TRAP_OD / 2 + 6.0
    out.append(("light_trap", Pos(stage_x, 0, -P.TRAP_L - 2.0) * trap.light_trap()))
    out.append(("tile_holder",
                Pos(-stage_x, 0, -(P.TILE_T + P.TRAP_WALL) - 2.0) * trap.tile_holder()))
    out.append(("ptfe_tile",
                Pos(-stage_x, 0, -P.TILE_T - 2.0 + P.TRAP_WALL) * trap.ptfe_tile()))
    return out


def omitted_families() -> dict[str, str]:
    """Part families deliberately left out of the assembly, and why.

    This exists so the viewer's exact-coverage test stays an EQUALITY. A part
    that is gated on a missing measurement still has a material and still has a
    row in the legend — it just has no geometry yet. Without this the test would
    have to be loosened to a subset check, and a subset check is exactly what
    lets an unlabelled part render as a grey blob.
    """
    gaps = plate.missing()
    if not gaps:
        return {}
    why = f"blocked on {', '.join(gaps)} in the components library"
    return {"detector_plate": why, "as7341_board": why}


# ------------------------------------------------------------------- optics --

def _led_points() -> list[tuple[float, float, float]]:
    return head.led_axis_positions()


def rays(pairs: int = 2) -> list[dict]:
    """Illumination, specular and collection paths as polylines.

    `pairs` is how many opposed LED pairs to draw. Drawing all eight makes a
    cone of spaghetti; two opposed pairs tell the whole story and leave the
    specular rays legible, which is the point.
    """
    out: list[dict] = []
    origin = (0.0, 0.0, 0.0)
    n = P.LED_N
    step = max(1, n // (pairs * 2))
    chosen = list(range(0, n, step))[: pairs * 2]

    for i in chosen:
        a = 2 * math.pi * i / n
        emitter = (P.LED_RING_R * math.cos(a), P.LED_RING_R * math.sin(a), P.LED_Z)

        # Incoming: emitter to the port centre.
        out.append({"role": "incident", "points": [emitter, origin]})

        # Specular: mirror the incoming direction in the sample plane. The
        # z-component flips and the lateral components carry straight on, so the
        # lobe leaves at the same 45 degrees on the OPPOSITE side. This is the
        # ray that must miss the detector, and the only one drawn in red.
        throw = P.LED_THROW
        dx, dy = -math.cos(a), -math.sin(a)
        c, s = math.cos(math.radians(P.ILLUM_ANGLE)), math.sin(math.radians(P.ILLUM_ANGLE))
        far = (dx * c * throw, dy * c * throw, s * throw)
        out.append({"role": "specular", "points": [origin, far]})

    # The collection axis, and the edges of what the tube actually accepts.
    out.append({"role": "collect_axis", "points": [origin, (0.0, 0.0, P.PLATE_Z)]})
    half = math.radians(P.BAFFLE_ACCEPT_ANGLE)
    for k in range(4):
        a = math.pi / 2 * k
        r = P.PLATE_Z * math.tan(half)
        out.append({"role": "collect_edge",
                    "points": [origin, (r * math.cos(a), r * math.sin(a), P.PLATE_Z)]})

    # The three circles on the sample plane that the whole geometry is about:
    # what is lit, what is collected, and what the port lets through. Drawn a
    # hair above z=0 so they are not z-fighting with the sample card.
    z = 0.05
    out.append({"role": "port_circle",
                "points": _ellipse(P.PORT_D / 2, P.PORT_D / 2, z)})
    out.append({"role": "lit_spot",
                "points": _ellipse(P.LIT_SPOT_MAJOR / 2, P.LIT_SPOT_MINOR / 2, z)})
    out.append({"role": "collected_spot",
                "points": _ellipse(P.COLLECTED_SPOT_D / 2, P.COLLECTED_SPOT_D / 2, z)})
    return out


def _ellipse(a: float, b: float, z: float, n: int = 72) -> list[tuple[float, float, float]]:
    """A closed polyline. The lit spot is an ellipse because a round beam at 45
    degrees lands as one; drawing it round would hide the fact."""
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        pts.append((a * math.cos(t), b * math.sin(t), z))
    return pts


def optics() -> dict:
    """Numbers the viewer puts on screen beside the render."""
    return {
        "port_d": P.PORT_D,
        "collect_d": P.COLLECT_D,
        "collected_spot_d": P.COLLECTED_SPOT_D,
        "lit_minor": P.LIT_SPOT_MINOR,
        "lit_major": P.LIT_SPOT_MAJOR,
        "illum_angle": P.ILLUM_ANGLE,
        "accept_angle": P.BAFFLE_ACCEPT_ANGLE,
        "led_n": P.LED_N,
        "plate_blocked": sorted(plate.missing()),
    }


def report() -> int:
    placed = all_placed()
    print(f"assembly: {len(placed)} placed solids")
    for name, solid in placed:
        print(f"  {name:<16} {len(solid.solids())} solid(s)  "
              f"{solid.volume / 1000:8.2f} cm^3")
    gaps = plate.missing()
    if gaps:
        print(f"\n  omitted: detector_plate, as7341_board "
              f"(blocked on {', '.join(gaps)})")
    print(f"\n  {len(rays())} rays, {len(datums())} datums")
    return 0


if __name__ == "__main__":
    raise SystemExit(report())
