"""Every number the optical head is built from, and the constraints between them.

    python -m spectra.cad.params

Millimetres and degrees throughout. Z is up. **z = 0 is the port face** — the
plane the sample is pressed against — with the head occupying z > 0 and the
sample below at z < 0. That choice is not cosmetic: `OPTICAL_HEAD.md` rules that
the part prints port-face-down, so the model's Z and the printer's Z are the
same direction and the face that must come out flat is the face on the bed.

Three kinds of number live here and they are labelled:

``RULED``
    Written down in ``docs/OPTICAL_HEAD.md`` before any CAD existed. Changing one
    here without changing it there makes the document a lie. Change the document.
``DERIVED``
    Computed from ruled numbers. Not a decision; arithmetic. Never type one in.
``CHOSEN``
    A decision this file makes because the document left it open. Each carries
    the reason. These are the ones to argue with.
``ESTIMATE``
    Not measured and not ruled: a stand-in good enough to draw with, with the
    real value still owed. Parameterised so the part builds and the constraint
    report says what is resting on a guess.
"""

from __future__ import annotations

import math
import os

UNIT = "mm"


def _knob(name: str, default: float) -> float:
    """A parameter the viewer may sweep, read from the environment at import.

    Only the handful of numbers worth comparing side by side are wired this way.
    Reading at import is why the viewer builds each variant in its own
    subprocess: a module already imported keeps the value it was imported with.
    """
    raw = os.environ.get(f"SPECTRA_{name}")
    return default if raw is None else float(raw)

# ---------------------------------------------------------------- the port ---

PORT_D = 8.0
"""RULED. Sample port aperture. Small enough to sit inside a paint-out, large
enough to average brushwork."""

PORT_LAND_W = 1.5
"""CHOSEN. Width of the flat land ringing the port. This is the hard stop the
sample bottoms out against, so it wants to be wide enough not to emboss a soft
drawdown and narrow enough that a curled card still seats."""

# ---------------------------------------------------------- the light seal ---

LIP_T = 0.8
"""CHOSEN. Wall of the compliant lip. Thin enough to flex at PETG's stiffness,
thick enough to survive a 0.4mm nozzle at two perimeters."""

LIP_PROUD = 1.2
"""CHOSEN, and the one place where two ruled requirements pull against each
other. The document rules both a *compliant lip* at the port and a *fixed
hard-stopped standoff*. A lip that seals must stand proud of the port face; a
stop that is fixed must be the port face itself. So the lip stands 1.2mm proud
and is designed to be crushed: it touches first, seals the room light out, and
keeps collapsing until the sample lands on the port land, which is the stop. The
compliance is the travel, not the standoff."""

LIP_OD_EXTRA = 5.0
"""CHOSEN. How far the lip reaches beyond the port land. Enough skirt to seal
against a sample that is not quite flat."""

# ------------------------------------------------------------- collection ---

COLLECT_D = _knob("COLLECT_D", 4.0)
"""CHOSEN, bounded by a ruled constraint: "aperture smaller than the lit spot".
Half the port diameter leaves the collected spot well inside the lit one, so an
alignment shift moves the spot around inside a uniformly lit field instead of
off its edge. Bigger would gather more light and spend the margin that makes the
reading insensitive to where exactly the sample sits."""

BAFFLE_WALL = 1.6
"""CHOSEN. Four perimeters at 0.4mm. The tube is the part that must not be
translucent — PETG at two perimeters passes visible light, and a glowing baffle
is a flare term that calibration cannot see."""

BAFFLE_Z0 = 6.0
"""CHOSEN, and it is set by the illumination rather than by the collection.

The first value tried here was 2.0, on the reasoning that the tube should start
just above the port land. That is wrong, and wrong in a way a render would have
shown only if someone thought to look down the right axis. At 45 degrees the
incoming beam is at radius r = z for every height z, so at z = 2 the beam is
only 2mm off the optical axis — inside the 3.6mm outer radius of the tube. The
tube would have stood directly in the illumination path and shadowed the port
with its own collection optics.

The condition is BAFFLE_OD/2 < BAFFLE_Z0: the tube must be thinner than the
height at which it starts. 6.0 clears 3.6 with room. Below the tube the
collection path is open air, which costs nothing — the tube is the aperture
stop wherever it begins."""

BAFFLE_L = _knob("BAFFLE_L", 18.0)
"""CHOSEN. Length of the collection tube. It sets the angular acceptance and the
size of the collected spot, and it lifts the detector plate clear of the LED
seats. See check()."""

# ----------------------------------------------------------- illumination ---

ILLUM_ANGLE = 45.0
"""RULED. Degrees from the surface normal. The whole geometry."""

ILLUM_ANGLE_TOL = 2.0
"""RULED. The plus-or-minus the document allows."""

LED_N = 8
"""RULED as "a ring of LEDs, even count". Eight is what the illumination table
asks for: seven narrowband peaks (405, 450, 505, 530, 590, 625, 660) plus one
white LED kept in the ring as a sanity channel."""

LED_Z = _knob("LED_Z", 14.0)
"""CHOSEN. Height of the LED emitter plane above the port face. It trades two
things against each other: lower puts the emitters closer, which is brighter and
lights a smaller spot; higher lights a bigger spot and makes the head fatter.
14mm is the smallest value that still overfills the port with the beam estimate
below and a whole millimetre of margin. See check()."""

LED_SEAT_D = 3.2
"""ESTIMATE. Bore for a 3mm through-hole LED plus print clearance. The LED part
number is not chosen, so this is a stand-in. Owed: the real emitter package."""

LED_SEAT_L = 6.0
"""ESTIMATE. How deep the LED sits in its bore. Long enough to aim it; the real
number follows the real LED."""

LED_HALF_ANGLE = _knob("LED_HALF_ANGLE", 15.0)
"""ESTIMATE, and the single load-bearing guess in this file. Datasheet-typical
half-intensity angle for a narrow 3mm LED. It decides the lit spot size, which
decides whether the beam overfills the port, which is one of the three
constraints this geometry exists to satisfy. A wide-angle LED (30 degrees plus)
makes the spot larger and the constraint easier; a water-clear narrow one
(8 degrees) could fail it. Measure or specify before printing."""

# ----------------------------------------------------------------- the body --

WALL = 2.4
"""CHOSEN. Six perimeters. Opaque, and stiff enough that pressing a sample
against the port does not flex the optical path."""

FLOOR_T = 2.0
"""CHOSEN. Thickness of the port face — the plate the sample presses against and
the one surface printed directly on the bed. Thin enough that the port bore is a
short tunnel rather than a long one, thick enough not to flex under a thumb."""

WEB_N = 3
WEB_T = 2.0
WEB_H = 6.0
"""CHOSEN. The collection tube is an island in the middle of an open cavity and
has to be held by something. Three radial webs from tube to wall do it. They sit
in the top WEB_H of the body, above the LED plane, because below that height
they would be standing in the illumination — the same mistake BAFFLE_Z0
documents, and the reason the ray view is worth building."""

# ------------------------------------------------------------- the standards --

TILE_D = 12.7
"""CHOSEN. Half an inch of sintered PTFE. The document rules "10mm or larger";
half-inch discs are what is actually sold."""

TILE_T = 3.0
"""ESTIMATE. Thickness of the PTFE disc. PTFE must be thick enough to be
optically deep or it reads the holder behind it; 3mm is the usual minimum and
the real number comes with the part."""

TRAP_L = 30.0
"""CHOSEN. Length of the light-trap cone. Long and narrow beats short and wide:
a ray entering at the port has to survive many grazing bounces to get back out,
and each bounce on matte black PETG costs it most of what is left."""

TRAP_WALL = 2.0
"""CHOSEN. Same opacity argument as the baffle."""

# ------------------------------------------------------------------ derived --

_TAN_ILLUM = math.tan(math.radians(ILLUM_ANGLE))
_SIN_ILLUM = math.sin(math.radians(ILLUM_ANGLE))
_COS_ILLUM = math.cos(math.radians(ILLUM_ANGLE))

PORT_LAND_OD = PORT_D + 2 * PORT_LAND_W
"""DERIVED. Outer diameter of the flat the sample bottoms out on."""

LIP_OD = PORT_LAND_OD + 2 * LIP_OD_EXTRA
LIP_ID = LIP_OD - 2 * LIP_T
"""DERIVED. The lip is a thin skirt standing on a circle well outside the port
land, not a thick collar around it: it has to bend, and a 5mm-thick ring of PETG
does not bend. So the skirt diameter is LIP_OD and its wall is LIP_T, and the
flat land the sample actually stops against is the separate, rigid PORT_LAND_OD
inside it."""

BAFFLE_OD = COLLECT_D + 2 * BAFFLE_WALL
"""DERIVED."""

LED_RING_R = LED_Z / _TAN_ILLUM
"""DERIVED, and at 45 degrees it is an identity: the ring radius equals the
emitter height. Every LED aims at the port centre by construction, so nothing
here is aimed by eye."""

LED_THROW = LED_Z / _SIN_ILLUM
"""DERIVED. Emitter to port centre along the beam."""

LED_SEAT_R_OUT = LED_RING_R + LED_SEAT_L * _COS_ILLUM
LED_SEAT_Z_OUT = LED_Z + LED_SEAT_L * _SIN_ILLUM
"""DERIVED. Where the back of an LED seat lands; this is what sets the body size."""

BODY_OD = 2 * (LED_SEAT_R_OUT + LED_SEAT_D / 2 + WALL)
"""DERIVED. The body is as big as the LED ring makes it and no bigger."""

PLATE_Z = BAFFLE_Z0 + BAFFLE_L
"""DERIVED. The detector plate sits on the top of the collection tube, which is
what puts the sensor on the optical axis looking down it."""

BODY_H = PLATE_Z
"""DERIVED. The body ends where the plate begins."""

LIT_BEAM_D = 2 * LED_THROW * math.tan(math.radians(LED_HALF_ANGLE))
"""DERIVED from an ESTIMATE. Beam diameter at the sample, measured across the
beam. Only as good as LED_HALF_ANGLE."""

LIT_SPOT_MINOR = LIT_BEAM_D
LIT_SPOT_MAJOR = LIT_BEAM_D / _COS_ILLUM
"""DERIVED. The footprint on the sample is an ellipse, not a circle: a round
beam striking at 45 degrees is stretched by 1/cos(45) along the radial
direction. The minor axis is the one that has to clear the port, because it is
the smaller one. Treating the footprint as round is the mistake this pair of
numbers exists to prevent."""

BAFFLE_ACCEPT_ANGLE = math.degrees(math.atan2(COLLECT_D / 2, BAFFLE_L))
"""DERIVED. Half-angle the collection tube accepts, for a detector on the axis
at the top of the tube: a ray may be off axis by at most the aperture radius
over the tube length. Rays steeper than this strike the tube wall instead of
the detector, which is how the specular lobe is rejected — geometrically, with
nothing relying on a black surface to absorb it.

The first version of this line used atan(COLLECT_D / BAFFLE_L), which is the
full-diameter figure and answers a different question (whether *any* ray at that
angle can traverse the tube from some starting point, not whether a ray from the
sample reaches the detector). It over-stated the acceptance by a factor of two.
The conservative half-diameter form is the one that matters here."""

COLLECTED_SPOT_D = COLLECT_D * PLATE_Z / BAFFLE_L
"""DERIVED. Diameter of the patch of sample the detector actually sees, found by
projecting the tube aperture from the detector back down to the port plane. It
is larger than the aperture itself because the detector sits above the aperture
rather than in it. This — not COLLECT_D — is the number that has to fit inside
the lit spot."""

TRAP_MOUTH_D = PORT_D + 2.0
TRAP_OD = TRAP_MOUTH_D + 2 * TRAP_WALL
TILE_HOLDER_OD = TILE_D + 2 * TRAP_WALL
"""DERIVED."""


# ------------------------------------------------------------------- checks --

def constraints() -> list[tuple[str, bool, str]]:
    """Every geometric claim this head makes, as (name, passed, detail).

    These are the three things the 45/0 geometry is *for*. If one fails the head
    still builds and still renders — it is a printable object that does not do
    its job, which is exactly the thing a render alone will not tell you.
    """
    out = []

    # 1. The beam must overfill the port. If it does not, the edge of the port
    #    is darker than the middle and the reading depends on where in the
    #    aperture the sample texture happens to sit.
    out.append((
        "beam overfills the port",
        LIT_SPOT_MINOR >= PORT_D,
        f"lit minor axis {LIT_SPOT_MINOR:.2f} vs port {PORT_D:.2f} "
        f"(margin {LIT_SPOT_MINOR - PORT_D:+.2f}), resting on "
        f"LED_HALF_ANGLE={LED_HALF_ANGLE:g}deg which is an ESTIMATE",
    ))

    # 2. The collected spot must sit inside the lit one, with room to move.
    #    Note this is the PROJECTED spot, not the tube aperture: the detector
    #    sees a wider patch than the hole it looks through.
    out.append((
        "collected spot inside the lit spot",
        COLLECTED_SPOT_D < LIT_SPOT_MINOR and COLLECTED_SPOT_D < PORT_D,
        f"collected spot {COLLECTED_SPOT_D:.2f} (from a {COLLECT_D:g} aperture) "
        f"vs port {PORT_D:.2f} and lit minor {LIT_SPOT_MINOR:.2f}; "
        f"{(PORT_D - COLLECTED_SPOT_D) / 2:.2f} of sideways play all round",
    ))

    # 2b. The tube must not stand in the illumination. This is the one the first
    #     draft of this file got wrong; see BAFFLE_Z0.
    out.append((
        "illumination clears the collection tube",
        BAFFLE_OD / 2 < BAFFLE_Z0 * _TAN_ILLUM,
        f"beam is at r={BAFFLE_Z0 * _TAN_ILLUM:.2f} where the tube starts "
        f"(z={BAFFLE_Z0:g}); tube outer r={BAFFLE_OD / 2:.2f}",
    ))

    # 3. The specular lobe must miss the detector. This is the whole reason the
    #    instrument is 45/0 and not 0/0, and it is the one a render can show.
    out.append((
        "specular lobe rejected by the baffle",
        BAFFLE_ACCEPT_ANGLE < ILLUM_ANGLE - ILLUM_ANGLE_TOL,
        f"tube accepts +/-{BAFFLE_ACCEPT_ANGLE:.1f}deg, specular arrives at "
        f"{ILLUM_ANGLE:g}deg (worst case {ILLUM_ANGLE - ILLUM_ANGLE_TOL:g}deg "
        f"with the ruled tolerance); margin {ILLUM_ANGLE - ILLUM_ANGLE_TOL - BAFFLE_ACCEPT_ANGLE:.1f}deg",
    ))

    # 4. Mechanical: the plate has to clear the LED seats or it cannot be fitted.
    out.append((
        "detector plate clears the LED seats",
        PLATE_Z >= LED_SEAT_Z_OUT,
        f"plate at z={PLATE_Z:.2f}, LED seats top out at z={LED_SEAT_Z_OUT:.2f} "
        f"(margin {PLATE_Z - LED_SEAT_Z_OUT:+.2f})",
    ))

    # 5. Mechanical: the LED ring must not foul the collection tube.
    out.append((
        "LED ring clears the collection tube",
        LED_RING_R - LED_SEAT_D / 2 > BAFFLE_OD / 2,
        f"nearest LED edge at r={LED_RING_R - LED_SEAT_D / 2:.2f}, "
        f"baffle outer r={BAFFLE_OD / 2:.2f}",
    ))

    # 6. The even-count rule, which is what cancels directional texture.
    out.append((
        "LED count is even",
        LED_N % 2 == 0,
        f"{LED_N} LEDs; an odd ring reads brush direction",
    ))

    return out


def estimates() -> list[tuple[str, float, str]]:
    """Numbers that are stand-ins, and what is owed for each."""
    return [
        ("LED_HALF_ANGLE", LED_HALF_ANGLE,
         "decides the lit spot; specify the LED or measure the beam before printing"),
        ("LED_SEAT_D", LED_SEAT_D, "follows the chosen LED package"),
        ("LED_SEAT_L", LED_SEAT_L, "follows the chosen LED package"),
        ("TILE_T", TILE_T, "comes with the PTFE disc when it is bought"),
    ]


def check() -> int:
    """Print the constraint report. Exit code is the number of failures."""
    rows = constraints()
    width = max(len(name) for name, _, _ in rows)
    print(f"optical head, {UNIT}, z=0 at the port face\n")
    print(f"  port {PORT_D:g}  collection {COLLECT_D:g}  "
          f"illumination {ILLUM_ANGLE:g}+/-{ILLUM_ANGLE_TOL:g}deg x{LED_N}")
    print(f"  body {BODY_OD:.1f} dia x {BODY_H:.1f} high  "
          f"LED ring r={LED_RING_R:.1f} at z={LED_Z:.1f}\n")
    failures = 0
    for name, ok, detail in rows:
        if not ok:
            failures += 1
        print(f"  [{'ok' if ok else 'FAIL'}] {name:<{width}}  {detail}")
    print()
    for name, value, owed in estimates():
        print(f"  [est] {name} = {value:g}  — {owed}")
    print(f"\n{len(rows) - failures}/{len(rows)} constraints hold, "
          f"{len(estimates())} numbers are estimates")
    return failures


if __name__ == "__main__":
    raise SystemExit(check())
