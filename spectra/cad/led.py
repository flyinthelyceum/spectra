"""The eight 5 mm LEDs, how each one reaches its bore, and where it stops.

    python -m spectra.cad.led                         # the insertion report
    .venv/bin/python -m spectra.cad.viewer --head-assembly   # see it

Jared printed the head on 2026-10-21 and could see the slotted holes in its rim
but not how an LED gets into one. The answer is geometry, so it is computed here
from the same solid that was printed rather than described:

- Each bore runs from the emitter point on the cavity wall outward and upward at
  45 degrees, and its axis leaves the head through the TOP RIM FACE. The bore's
  mouth is the slanted slot on the rim, which widens into the flange's
  counterbore and breaks through the outer edge.
- An LED goes in from the rim side, dome first, back already sealed in black
  heat-shrink, tilted 45 degrees with its back leaning outward, and slides down
  the bore axis toward the cavity.
- It stops when its 5.8 mm flange, which the 5.2 mm bore cannot pass, lands on
  the shoulder at the foot of the counterbore. ``seat()`` finds that stop by
  moving the LED's swept envelope along the axis against ``head.body()``;
  nothing here is placed by eye. The shoulder is where it is so that the dome
  tip lands on the emitter point the optics in `params` assume.

The plate goes on after, and its notches clear the sealed backs and leads.

Until 2026-10-21 there was no counterbore: the flange stopped on the head's
outer top edge with the tip 3.15 short of the cavity, a wedge of cavity wall
across half the bore's end took 53% of each LED's axial light, and a web took
26% more of LED 0's. ``check()`` now holds the opposite of each.

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

BODY_D = P.LED_BODY_D
FLANGE_D = P.LED_FLANGE_D
FLANGE_T = P.LED_FLANGE_T
LENGTH = P.LED_LENGTH
"""ESTIMATE, all four: the nominal T-1 3/4 outline, which lives in `params`
since the head is cut to it (the flange's counterbore and the shoulder it lands
on). The flange is wider than LED_SEAT_D, so it is what stops the lamp; LENGTH
runs from the dome tip to the flange's back face."""

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

SEAL_BACK = 3.0
"""CHOSEN. How far the heat-shrink runs back over the lead roots behind the
flange: enough to close the back, short of where the leads are soldered. Only
the clearance checks use it."""


def shown() -> bool:
    """Whether the assembly places the LEDs. Off unless SPECTRA_LEDS is set: the
    as-bought leads stand 25 mm out of the head and would run through every case
    concept, which is not a picture of anything built."""
    return os.environ.get("SPECTRA_LEDS", "").strip() not in ("", "0")


def _profile(top: float, flange: bool = True, sealed: bool = False) -> Part:
    """The lamp revolved about +Z, dome tip at the origin, flange at the back.
    Without the flange, the body's diameter runs on to ``top``. Sealed, the
    flange and everything behind it are LED_SEAL_T fatter: the heat-shrink,
    trimmed flush with the flange's front face."""
    s = math.sin(math.radians(45.0))
    z_fl = LENGTH - FLANGE_T
    r_back = (FLANGE_D / 2 + (P.LED_SEAL_T if sealed else 0.0)) if flange else BODY_D / 2
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
    solid that is its own profile carried out to ``reach``: the sealed flange's
    cylinder behind the flange, the body's in front of it. Sealed, because that
    is how it goes in."""
    return _profile(reach, sealed=True)


def sealed_back() -> Part:
    """The heat-shrink over one LED's back, in the lamp's frame: from the
    flange's front face to SEAL_BACK behind its back face, LED_SEAL_T thick
    over the flange. Drawn as a plain cylinder that wide, which is fatter than
    the sleeve once it has shrunk onto the leads."""
    from build123d import Cylinder

    z0 = LENGTH - FLANGE_T
    return Pos(0, 0, z0) * Cylinder(FLANGE_D / 2 + P.LED_SEAL_T, FLANGE_T + SEAL_BACK,
                                    align=(Align.CENTER, Align.CENTER, Align.MIN))


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

    In the bore's radial plane a point is (t along the axis, v across it,
    outward and down), and the rim face and the outer wall are lines in that
    plane. The slot starts where the bore's upper generator crosses the rim
    face, widens where the shoulder's plane does, and is open through the outer
    wall from where the counterbore's lower generator crosses it: that is the
    nick in the outer edge.
    """
    s, c = _sc()
    r_b, r_c = P.LED_SEAT_D / 2, head.LEAD_R
    dz = P.BODY_H - P.LED_Z

    def on_rim(t, v):  # radius at which (t, v) lies, for a point on the rim face
        return P.LED_RING_R + t * s + v * c

    t_in = (dz - r_b * s) / c                      # bore's upper generator meets the rim
    v_sh = (P.LED_SHOULDER_T * c - dz) / s         # shoulder plane meets the rim
    r_out = P.BODY_OD / 2
    # Counterbore's lower generator through the outer wall.
    t_wall = (r_out - P.LED_RING_R - r_c * c) / s
    z_wall = P.LED_Z + t_wall * c - r_c * s
    # Across the counterbore where the rim face meets the outer wall.
    v_edge = (r_out - P.LED_RING_R) * c - dz * s
    return {
        "r_inner": on_rim(t_in, -r_b),
        "r_shoulder": on_rim(P.LED_SHOULDER_T, v_sh),
        "r_axis": P.LED_RING_R + dz * s / c,
        "r_outer_edge": r_out,
        "width": P.LED_SEAT_D,
        "counter_d": 2 * r_c,
        "edge_gap_w": 2 * math.sqrt(max(0.0, r_c * r_c - v_edge * v_edge)),
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


ROUND_LED = ("bore", "web", "other")
"""What `aperture()` and `port_view()` count against the head round an LED: the
bore, flare and cavity wall it sits in, and the webs. Each must take nothing."""

VIEWED = (0, 1)
"""The LEDs `port_view()` is run on. Every bore is the same cut and the webs sit
every 90 degrees from 22.5, so each even LED sees the head LED 0 sees and each
odd one its mirror image; `aperture()`, which is cheap, runs on all eight and
shows it."""

BEYOND = ("collection tube", "port floor")
"""What they report but do not count: parts of the collection geometry and the
port, which this module does not set. See `remaining()`."""


@lru_cache(maxsize=None)
def _hits():
    """One ray-surface intersector loaded with the head, shared by every cast."""
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector

    x = IntCurvesFace_ShapeIntersector()
    x.Load(head.body().wrapped, 1e-7)
    return x


def _first(p, q) -> str | None:
    """What of the head the segment from p to q enters first, or None.

    Every cast starts in air, so its first crossing of the head's surface is
    where it enters material. Named by where that crossing is."""
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt

    d = [q[k] - p[k] for k in range(3)]
    n = math.sqrt(sum(x * x for x in d))
    x = _hits()
    x.Perform(gp_Lin(gp_Pnt(*p), gp_Dir(*(a / n for a in d))), 1e-6, n - 1e-6)
    if x.NbPnt() == 0:
        return None
    h = x.Pnt(min(range(1, x.NbPnt() + 1), key=x.WParameter))
    r, z = math.hypot(h.X(), h.Y()), h.Z()
    if z <= P.FLOOR_T + 0.01:
        return "port floor"  # the floor beside the port, or the port's own bore
    if r < P.BAFFLE_OD / 2 + 0.1 and z >= P.BAFFLE_Z0 - 0.01:
        return "collection tube"
    if r >= P.LED_RING_R - 0.05:
        return "bore"
    if z > P.PLATE_Z - P.WEB_H - 0.05:
        return "web"
    return "other"


def _shares(hits: dict, n: int) -> dict:
    return {"blocked": sum(hits.get(k, 0) for k in ROUND_LED) / n,
            "by": {k: v / n for k, v in hits.items() if k is not None and v}}


def _disk(r: float, step: float) -> list[tuple[float, float]]:
    m = int(r / step)
    return [(a * step, b * step) for a in range(-m, m + 1) for b in range(-m, m + 1)
            if (a * step) ** 2 + (b * step) ** 2 <= r * r]


@lru_cache(maxsize=None)
def aperture(i: int, step: float = 0.2) -> dict:
    """What fraction of LED i's light, leaving the seated dome parallel to the
    bore axis, strikes the head on its way to the sample plane, and what it
    strikes.

    A geometric measure of the bore as an aperture, not photometry: a real lamp
    sends a cone, not parallel rays. But a ray cast here that hits the head is
    light the optics in `params` assume reaches the port. ``blocked`` counts
    only ROUND_LED; ``by`` names everything, BEYOND included.

    The first version stopped each ray on a plane square to the axis, level
    with z = 5.5 only on the axis itself. The rays from the dome's upper edge
    stopped above 7 mm, short of the collection tube they were about to hit.
    These run to z = 0.
    """
    s, c = _sc()
    tip = seat(i)
    d = direction(i)
    grid = _disk(BODY_D / 2 - 0.05, step)
    hits: dict = {}
    for v, w in grid:
        p = point(i, tip, v, w)
        run = p[2] / c
        h = _first(p, tuple(p[k] - d[k] * run for k in range(3)))
        hits[h] = hits.get(h, 0) + 1
    return {"rays": len(grid), **_shares(hits, len(grid))}


def _dome(i: int, rings: int = 3, around: int = 8) -> list[tuple[float, float, float]]:
    """Points a fiftieth of a millimetre proud of LED i's seated dome: the tip,
    and rings out to 85 degrees down its flank."""
    tip = seat(i)
    r = DOME_R + 0.02
    out = [point(i, tip - 0.02)]
    for a in range(1, rings + 1):
        th = math.radians(85.0 * a / rings)
        for b in range(around):
            ph = 2 * math.pi * b / around
            out.append(point(i, tip + DOME_R - r * math.cos(th),
                             r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph)))
    return out


@lru_cache(maxsize=None)
def port_view(i: int, step: float = 0.6) -> dict:
    """What the head takes of the light from LED i's dome to the port: every
    segment from a point on the seated dome to a point on the port's disk on
    the sample plane, first hit named, tallied for the whole port and for the
    collected spot inside it.

    `aperture()` only sends light along the axis. The dome is 5 mm across and
    the port 8, so light reaches the edge of the port from the dome's flanks
    several degrees off axis, and that is the light a bore cut square, or a
    flare too narrow, would clip. This is the proof the flare is wide enough,
    rather than the assumption that it is.
    """
    src = _dome(i)
    port = _disk(P.PORT_D / 2, step)
    spot2 = (P.COLLECTED_SPOT_D / 2) ** 2
    every: dict = {}
    spot: dict = {}
    n_spot = 0
    for p in src:
        for x, y in port:
            h = _first(p, (x, y, 0.0))
            every[h] = every.get(h, 0) + 1
            if x * x + y * y <= spot2:
                spot[h] = spot.get(h, 0) + 1
                n_spot += 1
    n = len(src) * len(port)
    return {"segments": n, "port": _shares(every, n), "spot": _shares(spot, n_spot)}


def remaining() -> list[tuple[str, str]]:
    """What still stands in the light, beyond the head round the LED, with the
    reason it is left. Reported, never counted: neither is this module's to
    change."""
    def worst(part):
        return (max(aperture(i)["by"].get(part, 0) for i in range(P.LED_N)),
                *(max(port_view(i)[k]["by"].get(part, 0) for i in VIEWED) for k in ("port", "spot")))

    tube, port = worst("collection tube"), worst("port floor")
    s, c = _sc()
    # The axial beam's inner edge is at r = z tan(ILLUM) - (dome radius) / cos(ILLUM).
    need = (P.BAFFLE_OD / 2 + (BODY_D / 2) / c) / (s / c)
    return [
        ("the collection tube",
         f"takes {tube[0]:.1%} of each LED's axial beam, {tube[1]:.1%} of its light to the "
         f"port and {tube[2]:.1%} of its light to the collected spot: the dome's upper edge, "
         f"bound for the far rim. Clearing it needs BAFFLE_Z0 above {need:.2f} (now "
         f"{P.BAFFLE_Z0:g}), which with the plate where it is grows the collected spot into the "
         f"port floor's shadow: tried at 7.2, the floor's share of it went from 5.8% to 9.2%. "
         f"Left: see BAFFLE_Z0"),
        ("the port's own floor",
         f"takes {port[0]:.1%} of each LED's axial beam, {port[1]:.1%} of its light to the "
         f"port and {port[2]:.1%} of its light to the collected spot: the {P.FLOOR_T:g} mm "
         f"floor round the port, bevelled at 45 degrees down to a {P.PORT_BEVEL_LAND:g} mm "
         f"land at the sample face (Jared, 2026-10-21). What it still takes misses the "
         f"collected spot. Left: the aperture at the sample is ruled; see PORT_BEVEL_LAND"),
    ]


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
                f"swept envelope, back sealed, clear of the head for all {P.LED_N}"))

    # The seat is where the optics say the emitter is, or every number in
    # params that rests on LED_THROW is about a different instrument.
    off = max(abs(seat(i)) for i in range(P.LED_N))
    out.append(("every LED seats where the optics put it", off < 0.05,
                f"dome tip within {off:.2f} of the emitter point on all {P.LED_N}; throw to the "
                f"port {P.LED_THROW + seat(0):.2f}, the LED_THROW the overfill check rests on"))

    # Without its flange the lamp would go a millimetre deeper and still touch
    # nothing: the flange stops it, not the body jamming in the bore.
    bare = _profile(80.0, flange=False)
    narrow = [i for i in range(P.LED_N) if _vol(body & (location(i, seat(i) - 1.0) * bare)) > 1e-6]
    out.append(("the flange is what stops it", not narrow,
                f"flange front {seat(0) + LENGTH - FLANGE_T:.2f} along the axis, on the shoulder at "
                f"r={contact(0)[0]:.2f} z={contact(0)[1]:.2f}"))

    one, sleeve = lamp(), sealed_back()
    keep = head.lead_keepouts()
    loose = sum(_vol((location(i, seat(i)) * sleeve) - keep) for i in range(P.LED_N))
    out.append(("the lead keepout holds each sealed back", loose < 1e-6,
                f"sealed back outside the keepout: {loose:.3f} mm^3"))

    sealed_r = FLANGE_D / 2 + P.LED_SEAL_T
    clear = head.LEAD_R - sealed_r
    plate_at = Pos(0, 0, P.PLATE_Z) * plate.detector_plate()
    hit = sum(_vol(plate_at & (location(i, seat(i)) * (one + sleeve))) for i in range(P.LED_N))
    out.append(("the plate's notches clear the sealed backs and leads", hit < 1e-6 and clear > 0,
                f"overlap {hit:.3f} mm^3; notch radius {head.LEAD_R:.2f} round a {FLANGE_D / 2:.2f} "
                f"flange sealed to {sealed_r:.2f}: {clear:.2f} a side "
                f"({head.LEAD_R - FLANGE_D / 2:.2f} bare)"))

    axial = max(aperture(i)["blocked"] for i in range(P.LED_N))
    viewed = max(port_view(i)["port"]["blocked"] for i in VIEWED)
    by = aperture(0)["by"]
    out.append(("nothing round an LED stands in its beam", axial == 0 and viewed == 0,
                f"bore, flare and webs take {axial:.1%} of each seated dome's axial rays (all "
                f"{P.LED_N}) and {viewed:.1%} of its light to the port (LEDs "
                f"{', '.join(map(str, VIEWED))}); past them, the collection tube takes "
                f"{by.get('collection tube', 0):.1%} of the axial rays and the port's floor "
                f"{by.get('port floor', 0):.1%}, both named in remaining()"))
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
        "flare": head.FLARE_ANGLE,
        "throw_assumed": P.LED_THROW,
        "throw_seated": P.LED_THROW + tip,
        "seal_t": P.LED_SEAL_T,
        "notch_clear": head.LEAD_R - FLANGE_D / 2 - P.LED_SEAL_T,
        "notch_clear_bare": head.LEAD_R - FLANGE_D / 2,
        "lead_room_left": head.lead_start() + head.LEAD_ROOM - (tip + LENGTH),
        "lamp": {"body_d": BODY_D, "flange_d": FLANGE_D, "length": LENGTH, "lead_l": LEAD_L},
        "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in check()],
        "remaining": [{"name": n, "detail": d} for n, d in remaining()],
    }


def report() -> int:
    p = payload()
    m = p["mouth"]
    print(f"LED fit, {P.LED_N} x T-1 3/4 (nominal {BODY_D:g} body, {FLANGE_D:g} x {FLANGE_T:g} "
          f"flange, {LENGTH:g} long) in {P.LED_SEAT_D:g} bores at {P.ILLUM_ANGLE:g} deg, backs "
          f"sealed {P.LED_SEAL_T:g} thick\n")
    print(f"  mouth on the rim face: {m['width']:g} wide from r {m['r_inner']:.2f}, the "
          f"{m['counter_d']:.1f} counterbore from r {m['r_shoulder']:.2f} to the outer edge "
          f"{m['r_outer_edge']:.2f}; open through the outer wall {m['edge_gap_w']:.2f} wide, "
          f"{m['edge_gap_depth']:.2f} deep")
    print(f"  seated: dome tip {p['tip']:.2f} from the emitter point, flange front at "
          f"{p['flange_front']:.2f} on the shoulder at r={p['contact'][0]:.2f} z={p['contact'][1]:.2f}")
    print(f"  the back stands {p['back_above_rim']:.2f} above the rim face on the axis; "
          f"{p['lead_room_left']:.2f} of the {head.LEAD_ROOM:g} mm lead keepout is left past it")
    if p["grip_full"]:
        print(f"  bore closed all round from {p['grip_full'][0]:.2f} to {p['grip_full'][1]:.2f}, "
              f"at least half round to {p['grip_half'][1]:.2f}; the body runs from "
              f"{p['body_starts']:.2f} to the flange, the dome sits in a {p['flare']:g} deg flare")
    print(f"  throw to the port centre {p['throw_seated']:.2f}, the optics assume {p['throw_assumed']:.2f}\n")
    fails = 0
    for c in p["checks"]:
        fails += not c["ok"]
        print(f"  [{'ok' if c['ok'] else 'FAIL'}] {c['name']}  {c['detail']}")
    print()
    for r in p["remaining"]:
        print(f"  [left] {r['name']} {r['detail']}")
    return fails


if __name__ == "__main__":
    raise SystemExit(report())
