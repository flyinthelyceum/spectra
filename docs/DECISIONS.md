# Decisions

Dated rulings, one line of why each. A cloud session reading this repo cold sees
the decisions in the code but not the reasoning behind them; that is what this file
is for.

## 2026-09-17 — the founding set

**The optical head is the instrument; the detector is a module.** Everything hard
about a spectrophotometer is the head: fixed sample distance, 45/0 geometry, stray
light kept out, the same geometry presented to a reference tile and to a paint-out.
Get it right once and it is right forever. The detector mounts on one plate behind
one connector, so an AS7341 now and a Hamamatsu C12880MA later see the same head,
the same samples and the same tiles. This makes the upgrade falsifiable: the
improvement is a measured number, not a claim.

**Stage 1 is not a throwaway.** Every calibration procedure, reference tile and
line of capture code carries forward. Only the driver changes.

**The model is built before the instrument.** Kubelka-Munk, Saunderson, the
drawdown solve and mixing need no hardware and no cured paint. If the maths is
wrong, that is found out for free rather than after a two-week cure. `spectra/km.py`
and its tests are the first commit for this reason.

**Saunderson correction is mandatory, not optional.** Measured reflectance off a
cured film is not the internal reflectance Kubelka-Munk operates on: some light
reflects at the air/binder boundary without meeting a pigment particle, and some
light heading out is turned back in. 45/0 discards the specular lobe and removes
neither term. Without the correction, K/S carries a bias that grows as the sample
darkens, which is precisely the saturated organics. The cost of leaving it out is
not a slightly wrong number, it is that the six-pigment test in `ROADMAP.md` would
show the phthalos missing badly, that would read as "the AS7341 is the limit," and
$200 would be spent on a detector that does not fix it. `k1` and `k2` are
parameters everywhere because the right `k1` under 45/0 with the specular excluded
has to be fitted against a chart, not assumed from the normal-incidence Fresnel
value.

**Masstone plus tint is replaced by a black/white drawdown.** The familiar opaque
K-M form assumes an optically thick film. Quinacridone and phthalo masstones are
not optically thick, so that form measures the ground along with the paint.
Separating K from S by tinting with titanium white is also badly conditioned for
transparent organics: white's scattering dominates and the mass ratio has enormous
leverage down at 1:50. Reading one film over a black ground and a white one gives
K and S separately, which two-constant mixture prediction needs anyway. Tints stay
in the protocol as a check on the prediction, not as the route to K and S.

**Thickness never needs to be known, only repeated.** S and the film thickness X
appear only as the product S*X, so everything is in units of "per film" and mixing
is valid as long as every film in a comparison came off the same drawdown bar. This
turns "buy a micrometer-calibrated applicator" into "use the same bar every time."

**Stage 1 curve recovery is a fit, not an inversion.** Sequential narrowband
illumination gives 56 numbers instead of 8 and does sidestep the AS7341's supplied
calibration matrix, which is the real gain. But "two of the three terms are known
from calibration" needs each LED's emission *spectrum*, not its nominal peak, and
at Stage 1 there is no instrument here that can measure an LED spectrum; the
C12880MA is the thing that could. So Stage 1 trades a known-bad matrix for seven
assumed emission curves. Lab accuracy is unaffected, because the ColorChecker test
constrains the LED-times-channel product empirically and that is all Lab needs.
Curve recovery is a regularised fit against assumed basis functions and should be
described that way in code and in comments.

**Public, name `pigment`.** (Renamed `spectra` the same day, entry at the end.) Public because CI on GitHub-hosted runners and cloud
sessions are unauthenticated, and a private dependency needs a deploy token wired
into every runner and sandbox — the exact blocker found in the `components` review
one week ago. Nothing here is sensitive. Named for the data rather than the device,
because the library and the model outlive the detector, and to sit parallel to
`components`. No LICENSE file, matching `components` and `grow-lab`; revisit if
anyone asks to use it.

**CAD lives in this repo, not in `fabrication`.** Jared's call, 2026-09-17, against
a recommendation to keep one CAD spine. One argument for the split turned out to be
weaker than stated: the build123d doc-grounding PreToolUse hook was archived during
the 2026-09-16 accretion audit and now fires nowhere, so keeping head CAD in
`fabrication` would not have inherited it. If this repo authors build123d, it needs
vendored pinned docs of its own and a repo-local grounding step. That is a ROADMAP
item, not a global hook.

**Lane: HOLD until the 2026-09-23 FINISH cut.** The autumn roadmap allows three
open FINISH items outside course ops and already carries seven, with a cut dated
09-23. Model work and documentation proceed now because they cost nothing physical.
Hardware, orders and the head wait. Reopen trigger: the 09-23 cut lands.

**Stage 0 is an extraction, not a rewrite.** grow-lab's `tools/color/` is tested
colour maths that does not belong to a grow lab, including a CIEDE2000 asserted
against all thirty-four Sharma, Wu and Dalal pairs. It moves here and grow-lab
consumes it, the same move `components` made out of `fabrication`. Copying it would
create the second registry this system already learned about the hard way. See
`specs/2026-09-17-colorimetry-extraction.md`.

## 2026-09-17 — the Color-aid 314 set

**It is a characterisation target, not library material.** Jared owns the full
Color-aid set. Paper cannot be mixed and a silkscreened sheet has no pigment index,
so nothing from it enters the paint library; putting it there would make the
schema claim something false about every row in it. It goes in its own place, as
measured Lab and reflectance with no K/S. Full reasoning in `COLOR_AID.md`.

**Its value is that its structure is a standard with no reference values attached.**
The tint, shade and pastel ladders within a hue family were built to run evenly, and
the gray scale has 19 steps. An instrument that reads a ladder non-monotonically, or
that lets hue angle wander along one, has a fault, and no certified value was needed
to find it. That makes ladder checks a Stage 1a acceptance test that costs nothing
and can run the day the head powers up.

**Precision and coverage, never accuracy.** A search of the vision-science
literature and the manufacturer's own materials turned up no published spectral or
colorimetric reference data for these papers, and the booklet says the set is
periodically readjusted. A ΔE00 against Color-aid therefore says something about
repeatability, hue coverage, linearity and cross-instrument agreement, and nothing
about accuracy. It does not displace the ColorChecker order.

**The two instruments split the work by what each is good at.** 314 flat matte
papers are the flatbed's ideal subject and the head's worst workload, so the flatbed
takes the set and the head takes a spanning subset, with the shared readings tying
them together. Recorded because the reverse is the obvious and wrong instinct.

**Publication is an open decision, deliberately raised early.** The repo is public;
the booklet asserts rights over the collection and its arrangement and objects to
cross-referencing it. The measurements are facts about objects Jared owns. A
complete table keyed to their codes is closer to their arrangement. Decide before
the table exists.

## 2026-09-17 (later) — the scope was too narrow, and it was the documents not the hardware

Jared, reading the founding set back: the inspiration was a device that gave broad,
consistent data on all kinds of colour, and this had been written down as an oil-paint
map. He was right, and the correction is worth recording precisely because the two
halves were in different states.

**The hardware was never narrow.** A Nix is a contact device: flat, opaque,
light-sealed at a small port. That is the same envelope as the 45/0 head, so nothing
measurable with a Nix is out of reach here. At Stage 2 the C12880MA returns 288 pixels
where a Nix returns three numbers, which is strictly more general than the thing that
inspired the build. 45/0 is not a narrowing either: it is what makes a glossy surface
measurable at all, and loosening it buys noise rather than reach.

**The documents were narrow, and that is the real defect.** The founding charter said
the instrument existed to answer one question. The roadmap's storage stage said
"pigment index, masstone and drawdown protocol." An agent building against those would
produce a paint pipeline and nothing else, because that is what they asked for. The
brief this repo came from opened the same way, and the review it got went after the
physics and left the scope alone.

**The fix is a line, not a loosening.** The measurement layer is general and the models
sit on top. `km.py` already had this shape — it depends on nothing and knows nothing
about pigments — so no code changed. `CHARTER.md` was rewritten, `MEASUREMENT.md` is
new, and the rule is now in `CLAUDE.md` where a cold session reads it.

**What is deliberately not loosened.** The sharp question stays, in the model layer.
A general instrument with no defining question is exactly the failure the founding
charter named in the Nix: a good device pointed at a question nobody asked. Dropping
the question to gain generality would trade one failure for the other.

**Open, and Jared's call: the repo name.** `pigment` names the first model rather than
the thing. The honest parallel is `components` — a bare plural noun naming the measured
data — which for this would be `spectra`. Renaming is free today with one merged PR and
no consumers, and it is not free later.

## 2026-09-17 (later still) — renamed `pigment` to `spectra`

`pigment` named the first model rather than the thing the repo holds, which was the
same narrowing the entry above corrects. `spectra` is the bare plural noun naming the
measured data, exactly parallel to `components`: that repo holds measured dimensions
of parts, this one holds measured curves off surfaces.

**`chroma` was considered and rejected on its meaning.** Chroma is a colorimetric
coordinate, C\* = sqrt(a\*^2 + b\*^2) in CIELAB: one scalar derived from a colour's
position. The founding argument here is that colorimetric output discards the
reflectance curve and that mixture behaviour lives in the curve rather than in the Lab
point. Naming the repo after one coordinate of the representation it exists to see past
would have been the one word in colour science most precisely wrong. It is also the
quantity the paint work is about *losing*, so it re-narrowed to paint besides.

`albedo` was the other candidate, accurate and more evocative, rejected as a stretch:
it implies broadband and hemispherical where this is spectral and 45/0 directional.

Done while the repo was one day old with two merged PRs and no consumers. GitHub keeps
a redirect from the old name, but nothing should rely on it.

## 2026-09-17 — the head is drawn, and the viewer draws light as well as shape

**Lane note.** `docs/ROADMAP.md` and `CLAUDE.md` both put head CAD behind the
09-23 reopen. Jared asked for the viewer directly and then said go. He is
overriding his own lane; saying so rather than pretending the lane allowed it.
Nothing was ordered and nothing was printed.

**The CAD spine lives in this repo**, per the ruling on 2026-09-17 that everything
goes in the new repo. `spectra/cad/` holds `params`, `head`, `plate`, `trap`,
`assembly`, `viewer`. build123d 0.11.1 on Python 3.13, behind a `cad` extra so the
core stays standard-library-only. The pinned docs are vendored into
`docs/build123d/` because the doc-grounding hook was archived on 09-16 and fires
nowhere.

**The viewer is a port, and gained one thing.** `spectra/cad/viewer.py` and its
template come from `workbench/bench/viewer.py`, itself ported from grow-lab. The
pattern was not re-derived. What is new is a **ray overlay**: `assembly.rays()`
returns the illumination path, the specular lobe, the collection cone and the three
circles on the sample plane, computed from `params` alone, and the page draws them.

That is not decoration. `OPTICAL_HEAD.md` calls 45/0 the single most important
mechanical decision in the build, and whether the specular lobe clears the
collection tube is a question about light, which no render of solids can answer.
Looking at it is check 7 in the spec and it is the only check that is not runnable.
It was run: the section view shows the beam arriving at 45 degrees, the red
specular ray leaving at 45 on the far side, and the tube standing well clear.

**The palette is the fabrication house register, not the 3D Studio Color
Doctrine.** The Doctrine governs studio artifacts. This is a bench instrument in
black PETG, which is the register the growlab enclosure and the CNC station
already use: Transparent's light ground, ghosted glass, one red. The single red is
spent on the specular ray, because that ray is the one thing in the build that must
not reach the detector — which is exactly the Doctrine's own rule that red means
consequence, applied in the right register.

### Two errors this entry exists to record

**The collection tube was first drawn starting 2mm above the port face**, which put
it inside the illumination. At 45 degrees the beam is at radius r = z, so at z = 2
it is 2mm off axis and the 3.6mm-radius tube is standing in it. Caught in the
constraint arithmetic before anything was drawn. The condition is now a test:
`BAFFLE_OD/2 < BAFFLE_Z0 * tan(ILLUM_ANGLE)`, and `BAFFLE_Z0` is 6.0.

**The acceptance angle was first computed as `atan(COLLECT_D / BAFFLE_L)`**, which
answers a different question — whether any ray at that angle can traverse the tube
from somewhere — and overstates the acceptance by a factor of two. The figure that
matters is for a ray from the sample reaching a detector on the axis:
`atan(COLLECT_D/2 / BAFFLE_L)`, which is 6.3 degrees rather than 12.5. The
conservative form is in `params`.

Both are in the docstrings at the point of use, not only here.

### What is still resting on a guess

`LED_HALF_ANGLE = 15` is an estimate and the geometry rests on it: it decides the
lit spot, which must overfill the port. The viewer opens on a three-way sweep of
it, and the 8-degree variant **fails its own constraint and says so on the page**.
Specify the LED before printing.

## 2026-09-17 — the colour library was read against the charter

Jared has kept a science-based colour library on Drive since 2021: 26 texts,
1868 to 2016, plus his own annotated bibliography. It was read against the
charter. `docs/PRIOR_ART.md` is the result and the detail is there, not here.

Four things changed in this repo because of it:

1. **A `paint` reading is identified by its Colour Index name**, with the product
   name alongside. Hiler 1942 and Bradley 1890 independently say a product name
   does not identify a pigment; Okumura's 2005 database carries both fields.
   `docs/MEASUREMENT.md`.
2. **ΔE00 cannot be the acceptance test for pigment identification.** Cohen 1995
   proves any k-band curve splits into a rank-3 fundamental and a (k−3)-dimensional
   residual that human vision cannot see. ΔE00 is blind to the residual by
   construction, so two chemically different mixtures can match to ΔE00 < 0.5 and
   have visibly different curves. Identification must compare raw curves, never a
   round trip through XYZ or Lab. This is also the cleanest statement of why the
   charter stores the curve.
3. **Stage 1 is a differential instrument.** Three sources converge on ~10nm as
   working resolution; Judd's verdict on the closest period analogue is that such
   devices are good for differences between non-metameric pairs and not for
   absolute work. This confirms what `OPTICAL_HEAD.md` already said rather than
   contradicting it, and it is an argument for building Stage 1 — you cannot
   measure the error bars without it — and against publishing Stage 1 numbers as
   identifications.
4. **Okumura 2005 is prior art for most of this repo** and should be read before
   stage 1 hardware is ordered. He independently arrived at the same
   measurement-layer / model-layer split. He also hit the opacity wall that
   `solve_ks_sx` exists to get around, and did not have the fix.

**The finding worth keeping:** Jared's own bibliography says artistpigments.org's
Kubelka-Munk tool "does not, in my opinion, adequately account for the effects of
pigment transparency/opacity." That is this project's thesis, written years before
the repo, and `km.py`'s drawdown solve is the answer to it.

**Open, and not ruled here:** whether re-measuring the same physical sample over
time belongs in the model as a series. Both fading (Hiler) and coating chemistry
(Okumura's UV stabiliser shifting 360–450nm) say a reading is a point in time, not
a permanent fact. The `date` field exists; nothing consumes it as a series.

## 2026-09-30 — case concepts, as massing

Jared asked what CAD and rendering could mock up a case, with the Nix as the only
reference. `docs/CASE.md` holds the research and `spectra/cad/case.py` draws three
massing studies (puck, torch, palm) around the real head and the measured boards.

**Lane note.** The 09-17 release covered the head CAD. A case is the same spine and
costs nothing physical, and Jared asked for it directly, so it proceeds on the same
footing. Nothing was printed or ordered. The draft print that would answer grip
and size is a print, and waits for the reopen.

**The Nix is not the right reference.** The Datacolor ColorReader Spectro is an
8-channel 45/0 instrument with a small port, which is Stage 1 almost exactly, and
it is a torch. The Nix is a 31-channel device whose head is smaller than ours.

**Not ruled here:** the form, the controller board (the DevKitC-1 is what makes the
puck 74.5 mm across), the battery (none is on the BOM), and whether the PTFE tile
and light trap become a dock the instrument parks on.

## 2026-09-30 (later) — the puck, and two things fitting it turned up

Jared narrowed the case to the puck or the palm and asked for help choosing. The
puck was taken forward because a press on its top goes straight down the optical
axis, it seats on anything the lip covers, and it parks on a round dock. Reasons in
full in `docs/CASE.md`. `spectra/cad/puck.py` is version one: base, plate with ears,
board tray, lid, four M3 and three M2 screws.

**The detector plate was never fastened to anything.** It sat on the head's rim
and the drawing implied it stayed there. The head now carries three M2 heat-set
inserts in that rim, midway between LEDs, and the plate is screwed down. This is
a head change made for the case's sake, and it would have been needed without one.

**The plate sat on the LED leads.** The bores are aimed at the port, climb at 45
degrees, and break out of the head's wall just under the rim. The leads come out
underneath the plate. The plate is now notched at every LED against
`head.lead_keepouts()`, and a test holds it. Nobody would have seen this until
the first LED was soldered.

**The foot stands 0.4 mm clear of the port face on purpose.** Coplanar would make
the foot share the stop with the port land. Relieved, the port land is the only
stop, and the foot touches down after 0.67 degrees of tilt, inside the ruled ±2.

Nothing printed or ordered. The draft print waits for the lane.

**Later the same day: bare board.** Jared has DevKitC-1s with and without headers
soldered and asked to design for the best case. The tray now holds a headerless
board by its four corners, the long edges open underneath for soldering, and
the lid drops from 48.0 to 44.8 mm. A headered board no longer fits v1.

## 2026-09-30 — the calibration dock

Jared asked for the dock that goes with the puck. `docs/DOCK.md` has the research
and the reasoning; the rulings are these.

**Two fixed cups, not a dial.** The ColorMunki puts its tile on a rotating dial.
A dial is a mechanism bought to save one lift of the puck; two cups have nothing
to wear. (This entry first said a dial would put the tile's height on a detent.
It would not: a turntable's height is set by its floor. Corrected the same day
by the red team, `docs/DOCK.md`.) The puck parks on the white, which keeps the tile
covered, as Konica Minolta's own manuals insist.

**The lip is given nowhere to land in the dock.** Nobody presses a docked puck,
and a lip standing on the dock would hold the port face off the tile. The station
floors are sunk below the lip's reach and the cup keeps the light out instead. The
lip sits outside the port face, so leaving it uncrushed is optically nothing.

**One stop per station, as on the puck.** The tile stands 0.3 mm proud of its
pedestal so the PTFE is the only thing the head touches; the trap's stop is its
own wall. The dock bores `trap.cavity()` rather than a second cone.

**Buy a thick tile.** Labsphere gives 7 mm as the minimum Spectralon thickness for
full reflectance; `TILE_T` estimates 3. A thin tile reads its backing, so the
pocket floor behind it is part of the reference and never changes. The BOM line
now says so, before the purchase rather than after it.

**Lane.** CAD only, under the head-CAD release. Nothing printed or bought.

**Subtracted, same day.** The standalone printed light trap and the separate
tile holder in `trap.py` predate the dock and do the dock's job worse. Both were
deleted, with their viewer materials and the loose staging beside the head.
`trap.py` keeps the cone and the tile, which is what the dock is built from.
## 2026-10-01 — the puck takes the red team's three no-new-parts changes

The dock thread red-teamed the puck and Jared chose "All three" on its decision
card. Screws now drive up from the foot into inserts in the lid's bosses, so the
top is unbroken. The seam moved to the rim: one wall from foot to rim, the lid a
flat disc. The USB opening fits one plug, at the native receptacle, and the
panel-mount bulkhead rule is broken there on purpose because the only bulkhead in
the library does not fit. Sealing the LED backs is now ruled in
`OPTICAL_HEAD.md`: the bores open into the case, so without it the case is part of
the optics, which nobody decided. The smoked acrylic top was not chosen.

**The rim stays at 16 mm.** With the puck's seam moved to its top edge, the
cup rim is the only horizontal line on a docked puck, so it was not raised to
hide a seam (red team finding C). It clears the narrowed USB opening by 18.75 mm.

**Later the same day: second red team.** The round-one claim that sealed LEDs make
the head light-tight by itself overclaimed: only the LED end is sealed, the
detector end has no ruled seal, and the board's own LEDs are inside the case.
`OPTICAL_HEAD.md` now says it is unproven until a Stage 1a dark test with a torch
at the USB opening. `CASE.md` gained the upside-down assembly order and a firmware
rule: USB-Serial-JTAG for the host link, never TinyUSB, so the enclosed buttons
are never needed. Reasoning in `red-team-2.md` in the project files.

**Later the same day: fasteners fasten, they do not index.** Jared's rule, in the
dock thread: "the lid to body joint should align without bolts." Before this the
screws clocked the lid, located the tray on its posts, and located the plate on
the head. Now the lid lands on the rim's step, 0.5 mm proud (Jared chose "Proud
0.5" on the dock thread's card), centred by the rebate and clocked by one hidden
key; spigots on the posts locate the plate and tray; a keyed spigot ring under
the plate locates the head. Screw holes widened (M3 3.6, M2 2.6) so no screw
touches a wall at any joint's full play, and crush ribs under the lid bosses
absorb the stack now that the rim sets the lid's height. `puck.check()` asserts
each of these.
