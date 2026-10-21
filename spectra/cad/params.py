"""Every number the optical head is built from, and the constraints between them.

    python -m spectra.cad.params

Millimetres and degrees throughout. Z is up. **z = 0 is the port face** — the
plane the sample is pressed against — with the head occupying z > 0 and the
sample below at z < 0. It was chosen when the head was to print port face down,
so the model's Z and the printer's Z would agree. The head now prints top rim
down (2026-10-05, `OPTICAL_HEAD.md`: the lip held the port face off the bed and
the tube started in mid-air), so the printer's Z is the model's flipped; the
datum is unchanged.

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
stop wherever it begins.

That condition is for the beam's centre line. The beam is a 5 mm dome wide, and
its upper edge passes the tube's foot at r = BAFFLE_Z0 - 2.5 / cos 45 = 2.46,
inside it: the tube takes 8.7% of each LED's axial rays, all bound for the far
rim of the port, and 0.5% of the light bound for the collected spot
(`led.remaining()`, measured 2026-10-21). Clearing the whole beam needs this
above 7.14, and with PLATE_Z held that shortens the tube and grows the collected
spot outward into the port floor's shadow (FLOOR_T). Tried at 7.2 on the solid:
the tube's share goes to nothing and the floor's share of the bigger collected
spot rises from 5.8% to 9.2%. Left at 6."""

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

LED_Z = _knob("LED_Z", 18.0)
"""CHOSEN. Height of the LED emitter plane above the port face. It trades two
things against each other: lower puts the emitters closer, which is brighter and
lights a smaller spot; higher lights a bigger spot and makes the head fatter.
18mm is the smallest value at which the narrowest LED in the chosen set (10
degree half angle) still overfills the port with a whole millimetre of margin;
14mm passed only under the old 15 degree estimate. Ruled 2026-09-22. See
check()."""

LED_SEAT_D = _knob("LED_SEAT_D", 5.2)  # lint: not-a-measurement
"""CHOSEN by the bore coupon, 2026-10-05. Bore for a 5mm (T-1 3/4) through-hole
LED. Every LED in the ruled set is 5mm (2026-09-22), so one bore serves the ring.
FDM holes print small, so a coupon of 45 degree bores at 5.2 to 5.6 was printed
on Jared's printer, and 5.2 was the smallest the LED entered fully by hand and
stayed in when turned over and tapped. This is the CAD value that prints a
gripping bore on that printer and filament, not a diameter anyone measured; a
different printer reruns the coupon. It was the smallest bore offered, so the
true optimum may sit below it; 5.2 grips, which is the test."""

LED_SEAT_L = 6.0
"""CHOSEN. The length of 45 degree bore, from the emitter point, that the body is
sized to wrap with a full WALL outside it (see BODY_OD), and the length the
09-22 plate-clearance margin was ruled on. It was first written as how deep the
LED sits, which it never set: the lamp stops where its flange lands, and that
is LED_SHOULDER_T. Left at 6 so the body, and the puck base built round it,
keep their size."""

LED_BODY_D = 5.0  # lint: not-a-measurement
LED_FLANGE_D = 5.8  # lint: not-a-measurement
LED_FLANGE_T = 1.0  # lint: not-a-measurement
LED_LENGTH = 8.6  # lint: not-a-measurement
"""ESTIMATE. The nominal T-1 3/4 outline: a 5.0 body under a hemispherical dome,
a 5.8 x 1.0 flange at the base, 8.6 from the dome tip to the flange's back face.
Not a measured part: the components library has no LED yet. The head is now
cut to it (the flange's counterbore and the shoulder it lands on), so when one
is measured there these become an import and the head follows. The real flange
has a flat on the cathode side, which only makes it narrower there."""

LED_SEAL_T = 0.6  # lint: not-a-measurement
"""ESTIMATE. Wall of the black heat-shrink sealed over each LED's back, flange
included, before the LED goes in (`OPTICAL_HEAD.md` rules the seal). The BOM's
~6 mm 2:1 sleeve recovers to about 0.6 wall where nothing holds it open, and is
thinner over the 5.8 flange, which does; this takes the thick end. Sizes the
flange's counterbore and the plate's notches."""

LED_HALF_ANGLE = _knob("LED_HALF_ANGLE", 10.0)
"""CHOSEN from datasheets, 2026-09-22. The narrowest half-intensity angle in the
ruled LED set: Kingbright WP7113QBC/D, WP7113SGC, WP7113SYCK/J3 and WP7113SEC/J3
all list a 20 degree viewing angle (2 x theta-half), so theta-half is 10. The
rest are wider (HLMP-CE34 about 15, WP7113SRD/J4 15, C513A white 27.5, MT5400-UV
about 30) and a wider beam only makes the overfill constraint easier. The
narrowest LED is the binding case, so it is the number the geometry is checked
against. `hardware/BOM.md` carries the part list."""

# ----------------------------------------------------------------- the body --

WALL = 2.4
"""CHOSEN. Six perimeters. Opaque, and stiff enough that pressing a sample
against the port does not flex the optical path."""

FLOOR_T = 2.0
"""CHOSEN. Thickness of the port face — the plate the sample presses against and
the one surface printed directly on the bed. Thin enough that the port bore is a
short tunnel rather than a long one, thick enough not to flex under a thumb.

Short is not nothing. A 45 degree ray reaching the sample at x crossed the
floor's top at x + FLOOR_T, so an LED's axial rays cannot reach the band of the
port within FLOOR_T of the edge nearest it: the floor itself takes 18.9% of
them, and 5.9% of the light bound for the collected spot, whose near edge lies
in that shadow (`led.remaining()`, measured 2026-10-21). A 45 degree chamfer
on the port's cavity side, leaving 0.8 of floor at the port's edge, took the
collected spot's share to nothing when tried on the solid, with the aperture,
the land and the datum unchanged. Not cut: the port is ruled, and this is
Jared's to change."""

PORT_BEVEL_LAND = 0.8
"""CHOSEN (Jared, 2026-10-21). Height of straight port bore kept at the sample
face before a 45 degree bevel opens the port toward the cavity. The aperture the
sample sees is still PORT_D, so the measured area does not change; the bevel only
takes the floor's edge out of the light bound for the collected spot."""

WEB_N = 4
WEB_T = 2.0
WEB_H = 6.0
"""CHOSEN. The collection tube is an island in the middle of an open cavity and
has to be held by something. Four radial webs from tube to wall do it, each
midway between two LEDs (WEB_ANGLE0). They sit in the top WEB_H of the body,
above the LED plane, because below that height they would be standing in the
illumination — the same mistake BAFFLE_Z0 documents, and the reason the ray view
is worth building.

There were three, at 0/120/240, until 2026-10-21. With LEDs every 45 degrees
that put web 0 square in front of LED 0, which lost 26% of its light to it, and
three webs cannot all sit between LEDs on an eight-ring. Four can: WEB_N must
divide LED_N, and check() holds it."""

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
"""DERIVED. Where the back of LED_SEAT_L of bore lands; this is what sets the
body size."""

LED_SHOULDER_T = LED_LENGTH - LED_FLANGE_T
"""DERIVED from the nominal lamp (ESTIMATE). Distance along the bore, from the
emitter point, of the shoulder the flange's front face lands on: the lamp's own
tip-to-flange length, so a seated lamp's dome tip is AT the emitter point and
LED_THROW is the throw it actually has. Until 2026-10-21 there was no shoulder:
the flange stopped on the head's outer top edge, the tip 3.15 short of the
cavity, and the throw was 28.6, not 25.5."""

LED_DOME_T = LED_BODY_D / 2
"""DERIVED from the nominal lamp (ESTIMATE). Where the hemispherical dome ends
and the cylindrical body starts, along the bore from the tip. The bore grips
the body from here back; in front of it the bore flares open, so nothing of the
head is round the dome."""

WEB_ANGLE0 = 180.0 / LED_N
"""DERIVED. Azimuth of the first web: midway between LED 0 and LED 1. The rest
follow every 360/WEB_N."""

BODY_OD = 2 * (LED_SEAT_R_OUT + LED_SEAT_D / 2 + WALL)
"""DERIVED. The body is as big as the LED ring makes it and no bigger."""

PLATE_Z = BAFFLE_Z0 + BAFFLE_L
"""DERIVED. The detector plate sits on the top of the collection tube, which is
what puts the sensor on the optical axis looking down it."""

BODY_H = PLATE_Z
"""DERIVED. The body ends where the plate begins."""

LIT_BEAM_D = 2 * LED_THROW * math.tan(math.radians(LED_HALF_ANGLE))
"""DERIVED from the chosen half angle. Beam diameter at the sample, measured across the
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
        f"LED_HALF_ANGLE={LED_HALF_ANGLE:g}deg, the narrowest LED in the ruled set",
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

    # 7. Every web midway between two LEDs, never in front of one. Three webs on
    #    an eight-ring put one square in an LED's beam; see WEB_N.
    out.append((
        "the webs stand between LEDs",
        LED_N % WEB_N == 0,
        f"{WEB_N} webs from {WEB_ANGLE0:g}deg every {360 / WEB_N:g}deg, LEDs every "
        f"{360 / LED_N:g}deg; each web {WEB_ANGLE0:g}deg from its nearest LED",
    ))

    return out


def estimates() -> list[tuple[str, float, str]]:
    """Numbers that are stand-ins, and what is owed for each."""
    return [
        ("LED_HALF_ANGLE", LED_HALF_ANGLE,
         "decides the lit spot; specify the LED or measure the beam before printing"),
        ("LED_SEAT_D", LED_SEAT_D, "follows the chosen LED package"),
        ("LED_LENGTH", LED_LENGTH, "nominal T-1 3/4 outline, with LED_BODY_D, LED_FLANGE_D and "
         "LED_FLANGE_T; sets the shoulder the flange lands on, so the tip lands at the "
         "emitter point only as well as this is right. Measure one into components"),
        ("LED_SEAL_T", LED_SEAL_T, "heat-shrink wall over the LED back; sizes the counterbore "
         "and the plate notches"),
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
