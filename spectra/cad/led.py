"""The eight 5 mm LEDs, how each one reaches its bore, and where it stops.

    python -m spectra.cad.led                         # the insertion report
    .venv/bin/python -m spectra.cad.viewer --head-assembly   # see it

Jared printed the head on 2026-10-21 and could see the slotted holes in its rim
but not how an LED gets into one. The answer is geometry, so it is computed here
from the same solid that was printed rather than described:

- Each bore runs from the emitter point on the cavity wall outward and upward at
  45 degrees, and its axis leaves the head through the TOP RIM FACE. The bore's
  mouth is the slanted slot on the rim, which just breaks through the outer edge.
- An LED goes in from the rim side, dome first, tilted 45 degrees with its back
  leaning outward, and slides down the bore axis toward the cavity.
- It stops when its 5.8 mm flange, which the 5.2 mm bore cannot pass, lands on
  the head's outer top edge. ``seat()`` finds that stop by moving the LED's swept
  envelope along the axis against ``head.body()``; nothing here is placed by eye.

The plate goes on after, and its notches clear the seated flange and leads.

The LED solid is the nominal T-1 3/4 outline, not a measured part. The
components library has no LED yet; when one is measured there, the numbers
below are replaced by an import, the same way the plate takes the AS7341's.
"""

from __future__ import annotations

import math
import os
from functools import lru_cache

from build123d import Align, Axis, Box, Location, Part, Polyline, Pos, Rot, ThreePointArc, Vector
from build123d import make_face, revolve

from . import head, params as P

# ------------------------------------------------------- the lamp, nominal --

BODY_D = 5.0  # lint: not-a-measurement
"""ESTIMATE. Body diameter of a T-1 3/4 lamp, the nominal package outline."""

FLANGE_D = 5.8  # lint: not-a-measurement
FLANGE_T = 1.0  # lint: not-a-measurement
"""ESTIMATE. The rim at the lamp's base. Wider than LED_SEAT_D, so it is what
stops the lamp in its bore. Drawn round; the real flange has a flat on the
cathode side, which only makes it narrower there."""

LENGTH = 8.6  # lint: not-a-measurement
"""ESTIMATE. Dome tip to the underside of the flange."""

LEAD_L = 25.0  # lint: not-a-measurement
LEAD_W = 0.5  # lint: not-a-measurement
LEAD_PITCH = 2.54  # lint: not-a-measurement
"""ESTIMATE. Leads as bought, before they are trimmed and soldered. Drawn straight
along the bore axis, which is how the lamp is pushed in."""

DOME_R = BODY_D / 2
"""DERIVED. A hemispherical dome on the body."""

OUT_CLEAR = 6.0
"""CHOSEN. How far above the rim face the lowest point of an LED starts its
travel in the viewer: far enough that the whole lamp is visibly outside."""

PLATE_CLEAR = 4.0
"""CHOSEN. How far above the seated flanges the plate's spigot starts its travel
in the viewer."""


def shown() -> bool:
    """Whether the assembly places the LEDs. Off unless SPECTRA_LEDS is set: the
    as-bought leads stand 25 mm out of the head and would run through every case
    concept, which is not a picture of anything built."""
    return os.environ.get("SPECTRA_LEDS", "").strip() not in ("", "0")


def _profile(top: float, flange: bool = True) -> Part:
    """The lamp revolved about +Z, dome tip at the origin, flange at the back.
    Without the flange, the body's diameter runs on to ``top``."""
    s = math.sin(math.radians(45.0))
    z_fl = LENGTH - FLANGE_T
    r_back = FLANGE_D / 2 if flange else BODY_D / 2
    arc = ThreePointArc((0, 0, 0), (DOME_R * s, 0, DOME_R * (1 - s)), (DOME_R, 0, DOME_R))
    pts = [(DOME_R, 0, DOME_R), (BODY_D / 2, 0, z_fl), (r_back, 0, z_fl),
           (r_back, 0, top), (0, 0, top), (0, 0, 0)]
    # Without the flange the step is a zero-length edge, which the kernel refuses.
    pts = [p for k, p in enumerate(pts) if k == 0 or p != pts[k - 1]]
    rest = Polyline(*pts)
    return revolve(make_face([arc, rest]), axis=Axis.Z)


def lamp() -> Part:
    """One LED, leads included, in its own frame: dome tip at the origin, the
    back and leads along +Z."""
    part = _profile(LENGTH)
    for x in (-LEAD_PITCH / 2, LEAD_PITCH / 2):
        # Half a millimetre into the flange, so the lamp is one solid.
        part = part + Pos(x, 0, LENGTH - 0.5) * Box(
            LEAD_W, LEAD_W, LEAD_L + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part


def envelope(reach: float = 80.0) -> Part:
    """Everything the lamp passes through on its way in, from far outside to
    where its tip is now. A lamp that only gets wider toward its back sweeps a
    solid that is its own profile carried out to ``reach``: the flange's
    cylinder behind the flange, the body's in front of it."""
    return _profile(reach)


# ------------------------------------------------------------- the bores --

def _sc() -> tuple[float, float]:
    a = math.radians(P.ILLUM_ANGLE)
    return math.sin(a), math.cos(a)


def angle(i: int) -> float:
    return 360.0 * i / P.LED_N


def location(i: int, tip: float) -> Location:
    """LED i's frame with its dome tip ``tip`` mm along the bore axis from the
    emitter point, +Z pointing out of the bore. The same chain of placements
    `head._led_bores()` cuts the bore with."""
    return (Rot(0, 0, angle(i)) * Pos(P.LED_RING_R, 0, P.LED_Z)
            * Rot(0, P.ILLUM_ANGLE, 0) * Pos(0, 0, tip))


def point(i: int, t: float, v: float = 0.0, w: float = 0.0) -> tuple[float, float, float]:
    """A point in head coordinates, ``t`` along LED i's bore axis from the
    emitter point, offset ``v`` across it in the radial plane (positive is
    outward and down) and ``w`` tangentially."""
    s, c = _sc()
    a = math.radians(angle(i))
    x, y, z = P.LED_RING_R + t * s + v * c, w, P.LED_Z + t * c - v * s
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z)


def direction(i: int) -> tuple[float, float, float]:
    """Unit vector along LED i's bore axis, out of the head."""
    s, c = _sc()
    a = math.radians(angle(i))
    return (s * math.cos(a), s * math.sin(a), c)


def _vol(shape) -> float:
    return 0.0 if shape is None else sum(s.volume for s in shape.solids())


@lru_cache(maxsize=None)
def seat(i: int) -> float:
    """Where LED i stops, as the dome tip's distance along the bore axis from
    the emitter point.

    Found by bisection on the swept envelope against the head as printed: the
    smallest tip position at which everything the lamp has passed through on the
    way in is still clear of the head. The envelope only shrinks as the lamp is
    withdrawn, so the overlap is monotone and bisection is sound.
    """
    body = head.body()
    env = envelope()
    lo, hi = -P.LED_SEAT_D, _bore_length()
    if _vol(body & (location(i, hi) * env)) > 1e-6:
        raise RuntimeError(f"LED {i} cannot reach its bore from outside the head at all")
    for _ in range(16):
        mid = (lo + hi) / 2
        if _vol(body & (location(i, mid) * env)) > 1e-6:
            lo = mid
        else:
            hi = mid
    return hi


def _bore_length() -> float:
    return head._led_bore_length()


def contact(i: int) -> tuple[float, float]:
    """(radius, height) of the head material the flange lands on: the centre of
    what the envelope would cut a twentieth of a millimetre deeper."""
    hit = head.body() & (location(i, seat(i) - 0.05) * envelope())
    c = hit.center()
    return math.hypot(c.X, c.Y), c.Z


def mouth() -> dict:
    """The slot the bore leaves on the rim face, derived from params.

    A 45 degree bore of diameter d meets a horizontal face as an ellipse d wide
    and d / cos 45 long, centred where the axis crosses the face. The outer end
    of that ellipse lies past the head's outside wall, so the slot is open
    there: that is the nick in the outer edge.
    """
    s, c = _sc()
    r_axis = P.LED_RING_R + (P.BODY_H - P.LED_Z) * s / c
    half_long = (P.LED_SEAT_D / 2) / c
    r_out = P.BODY_OD / 2
    k = min(1.0, (r_out - r_axis) / half_long)
    # Along the bore's lower generator, where it passes through the outer wall.
    t_wall = (r_out - P.LED_RING_R) / s - (P.LED_SEAT_D / 2)
    z_wall = P.LED_Z + t_wall * c - (P.LED_SEAT_D / 2) * s
    return {
        "r_inner": r_axis - half_long,
        "r_axis": r_axis,
        "r_outer_edge": r_out,
        "width": P.LED_SEAT_D,
        "edge_gap_w": P.LED_SEAT_D * math.sqrt(max(0.0, 1 - k * k)),
        "edge_gap_depth": P.BODY_H - z_wall,
        "axis_exit_t": head.lead_exit(),
    }


def grip(i: int = 1, radius_extra: float = 0.15, n: int = 72) -> list[tuple[float, float]]:
    """(t, fraction) of the bore wall that is head material, along the axis.

    The bore coupon that chose LED_SEAT_D was a block with closed bores; in the
    head the bore is open to the cavity at its inner end and to the rim at its
    outer end, so the lamp is gripped all round over a short length only.
    """
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN

    inside = BRepClass3d_SolidClassifier(head.body().wrapped)
    r = P.LED_SEAT_D / 2 + radius_extra
    out = []
    t = 0.0
    while t <= _bore_length():
        k = 0
        for j in range(n):
            inside.Perform(gp_Pnt(*point(i, t, r * math.cos(2 * math.pi * j / n),
                                         r * math.sin(2 * math.pi * j / n))), 1e-7)
            k += inside.State() == TopAbs_IN
        out.append((round(t, 2), k / n))
        t += 0.25
    return out


@lru_cache(maxsize=None)
def aperture(i: int, step: float = 0.2) -> dict:
    """What fraction of LED i's light, leaving the seated dome parallel to the
    bore axis, strikes the head before it reaches the height where the
    collection tube begins, and what it strikes.

    A geometric measure of the bore as an aperture, not photometry: a real lamp
    sends a cone, not parallel rays. But a ray cast here that hits the head is
    light the optics in `params` assume reaches the port.
    """
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector

    hit_test = IntCurvesFace_ShapeIntersector()
    hit_test.Load(head.body().wrapped, 1e-7)
    s, c = _sc()
    tip = seat(i)
    t_end = (P.BAFFLE_Z0 - 0.5 - P.LED_Z) / c
    back = gp_Dir(*(-x for x in direction(i)))
    r_max = BODY_D / 2 - 0.05
    m = int(r_max / step)
    grid = [(a * step, b * step) for a in range(-m, m + 1) for b in range(-m, m + 1)
            if (a * step) ** 2 + (b * step) ** 2 <= r_max ** 2]
    hits = {"bore end": 0, "web": 0, "collection tube": 0, "other": 0}
    for v, w in grid:
        # Every ray starts in the air of the bore, so its first crossing of the
        # head's surface is where it enters material.
        hit_test.Perform(gp_Lin(gp_Pnt(*point(i, tip, v, w)), back), 0.0, tip - t_end)
        if hit_test.NbPnt() == 0:
            continue
        k = min(range(1, hit_test.NbPnt() + 1), key=hit_test.WParameter)
        q = hit_test.Pnt(k)
        r = math.hypot(q.X(), q.Y())
        if r < P.BAFFLE_OD / 2 + 0.1:
            hits["collection tube"] += 1
        elif r >= P.LED_RING_R - 0.05:
            hits["bore end"] += 1
        elif q.Z() > P.LED_Z - 0.05:
            hits["web"] += 1
        else:
            hits["other"] += 1
    n = len(grid)
    return {"rays": n, "blocked": sum(hits.values()) / n,
            "by": {k: v / n for k, v in hits.items() if v}}


def placed() -> list[tuple[str, Part]]:
    """The eight LEDs, seated, as (name, solid). Empty unless ``shown()``."""
    if not shown():
        return []
    one = lamp()
    return [(f"led_{i}", location(i, seat(i)) * one) for i in range(P.LED_N)]


def travel() -> float:
    """How far back along its axis each LED starts in the viewer, from the
    inequality that puts the lamp's lowest point OUT_CLEAR above the rim face.
    The dome's lowest point, tilted 45 degrees, sits DOME_R * (sqrt 2 - 1)
    below its tip."""
    s, c = _sc()
    dip = DOME_R * (math.sqrt(2) - 1)
    t_start = (P.BODY_H + OUT_CLEAR - P.LED_Z) / c + dip
    return max(t_start - seat(i) for i in range(P.LED_N))


def plate_travel() -> float:
    """How far above its seat the plate starts in the viewer: its spigot's
    underside PLATE_CLEAR above the highest point of any seated flange."""
    from . import plate

    s, c = _sc()
    t_back = seat(0) + LENGTH
    flange_top = P.LED_Z + t_back * c + (FLANGE_D / 2) * s
    return flange_top + PLATE_CLEAR - (P.PLATE_Z - plate.SPIGOT_H)


def check() -> list[tuple[str, bool, str]]:
    """What the LED fit must hold, as (name, passed, detail)."""
    from . import plate

    body = head.body()
    env = envelope()
    out = []
    blocked = [i for i in range(P.LED_N) if _vol(body & (location(i, seat(i)) * env)) > 1e-6]
    out.append(("every LED reaches its seat from outside along its bore", not blocked,
                f"blocked: {blocked}" if blocked else
                f"swept envelope clear of the head for all {P.LED_N}"))

    # Without its flange the lamp would go a millimetre deeper and still touch
    # nothing: the flange stops it, not the body jamming in the bore.
    bare = _profile(80.0, flange=False)
    narrow = [i for i in range(P.LED_N) if _vol(body & (location(i, seat(i) - 1.0) * bare)) > 1e-6]
    out.append(("the flange is what stops it", not narrow,
                f"flange front {seat(0) + LENGTH - FLANGE_T:.2f} along the axis, on the head at "
                f"r={contact(0)[0]:.2f} z={contact(0)[1]:.2f}"))

    clear = head.LEAD_R - FLANGE_D / 2
    one = lamp()
    plate_at = Pos(0, 0, P.PLATE_Z) * plate.detector_plate()
    hit = sum(_vol(plate_at & (location(i, seat(i)) * one)) for i in range(P.LED_N))
    out.append(("the plate's notches clear the seated flanges and leads", hit < 1e-6 and clear > 0,
                f"overlap {hit:.3f} mm^3; notch radius {head.LEAD_R:.2f} round a "
                f"{FLANGE_D / 2:.2f} flange, {clear:.2f} a side"))

    worst = max(range(P.LED_N), key=lambda i: aperture(i)["blocked"])
    a = aperture(worst)
    typical = aperture((worst + 1) % P.LED_N)
    out.append(("the head leaves each LED's beam open", a["blocked"] < 0.05,
                f"of the rays leaving each seated dome along its axis, "
                f"{typical['blocked']:.0%} strike the head ("
                + ", ".join(f"{k} {v:.0%}" for k, v in typical["by"].items())
                + f"); LED {worst}: {a['blocked']:.0%} ("
                + ", ".join(f"{k} {v:.0%}" for k, v in a["by"].items()) + ")"))
    return out


def payload() -> dict:
    """The numbers the viewer's LED panel shows, and each LED's axis."""
    s, c = _sc()
    m = mouth()
    g = grip()
    full = [t for t, f in g if f > 0.999]
    half = [t for t, f in g if f >= 0.5]
    tip = seat(0)
    return {
        "family": "led",
        "n": P.LED_N,
        "axes": [{"i": i, "angle": angle(i), "emitter": point(i, 0.0), "dir": direction(i),
                  "mouth": point(i, m["axis_exit_t"]), "seat_tip": seat(i),
                  "blocked": aperture(i)["blocked"], "by": aperture(i)["by"]}
                 for i in range(P.LED_N)],
        "angle": P.ILLUM_ANGLE,
        "bore_d": P.LED_SEAT_D,
        "travel": travel(),
        "tip": tip,
        "flange_front": tip + LENGTH - FLANGE_T,
        "flange_back": tip + LENGTH,
        "back_above_rim": P.LED_Z + (tip + LENGTH) * c - P.BODY_H,
        "contact": contact(0),
        "mouth": m,
        "grip_full": [min(full), max(full)] if full else None,
        "grip_half": [min(half), max(half)] if half else None,
        "body_starts": tip + DOME_R,
        "throw_assumed": P.LED_THROW,
        "throw_seated": P.LED_THROW + tip,
        "notch_clear": head.LEAD_R - FLANGE_D / 2,
        "lead_room_left": head.lead_start() + head.LEAD_ROOM - (tip + LENGTH),
        "lamp": {"body_d": BODY_D, "flange_d": FLANGE_D, "length": LENGTH, "lead_l": LEAD_L},
        "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in check()],
    }


def report() -> int:
    p = payload()
    m = p["mouth"]
    print(f"LED fit, {P.LED_N} x T-1 3/4 (nominal {BODY_D:g} body, {FLANGE_D:g} x {FLANGE_T:g} "
          f"flange, {LENGTH:g} long) in {P.LED_SEAT_D:g} bores at {P.ILLUM_ANGLE:g} deg\n")
    print(f"  mouth on the rim face: r {m['r_inner']:.2f} to the outer edge {m['r_outer_edge']:.2f}, "
          f"{m['width']:g} wide; open through the outer wall {m['edge_gap_w']:.2f} wide, "
          f"{m['edge_gap_depth']:.2f} deep")
    print(f"  seated: dome tip {p['tip']:.2f} up the bore from the emitter point, flange front "
          f"at {p['flange_front']:.2f}, on the head at r={p['contact'][0]:.2f} z={p['contact'][1]:.2f}")
    print(f"  the back stands {p['back_above_rim']:.2f} above the rim face on the axis; "
          f"{p['lead_room_left']:.2f} of the {head.LEAD_ROOM:g} mm lead keepout is left past it")
    if p["grip_full"]:
        print(f"  bore closed all round from {p['grip_full'][0]:.2f} to {p['grip_full'][1]:.2f}; "
              f"the cylindrical body starts at {p['body_starts']:.2f}")
    print(f"  throw to the port centre {p['throw_seated']:.2f}, the optics assume {p['throw_assumed']:.2f}\n")
    fails = 0
    for c in p["checks"]:
        fails += not c["ok"]
        print(f"  [{'ok' if c['ok'] else 'FAIL'}] {c['name']}  {c['detail']}")
    return fails


if __name__ == "__main__":
    raise SystemExit(report())
