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

## 2026-09-22 — three rulings from Jared, and one stale claim retired

**The first run measures matte black PLA prints, not paint-outs.** Jared: "skip
paint out on the first run. we can get good data from matte black pla prints." A
printed chip is flat, opaque, pressable and light-sealed at the port, which is the
whole envelope the head asks for, and it exists the day the head does. So Stage 1a's
repeatability and ladder rows run on printed chips and Color-aid, and the first
`paint` reading moves to 1c+. Consequence: **the cure interval no longer gates the
head print.** It still has to be fixed before the first paint-out, for the same
reason as before, and it stays in the known holes as deferred rather than open.

**The measured Color-aid table is public.** Jared: "public whenever possible. I like
the idea of community work even if I never do it." The 314-row table goes in this
repo when it exists. Color-aid's booklet asserts rights over the collection and
objects to cross-referencing; his measurements are facts about objects he owns, and
the table cites the collection rather than reproducing it. Decided before the table
exists, which is when it was cheapest.

**The LED part is being specified from datasheets.** `LED_HALF_ANGLE = 15` in
`spectra/cad/params.py` is still an ESTIMATE about a part not yet chosen. A
datasheet sweep across the seven wavelengths and white is in progress; the number
hardens to a datasheet figure, and the 8/15/30 sweep in the viewer is re-run
against it, before anything is printed.

**`as7341_breakout.PCB_W` was calipered on 2026-09-17** (`PCB_W = 17.78  # CALIPER
2026-09-17 JR` in `components/as7341_breakout.py`). `plate.missing()` returns an
empty list, `detector_plate()` builds, and `tests/test_cad.py:134` skips itself with
"board is fully measured; nothing to gate." Four documents in this repo, the memory
file and the Todoist task all still said it was the one missing number. They were
quoting each other. Retired in this commit; the source of truth for measurement
state is the components repo and nothing here.

### A fourth ruling, later the same day: no PTFE tile for Stage 1a

Jared, on the order list: the sintered PTFE tile "seems exorbitantly expensive.
what is it and how critical is it?" The answer is that it is not critical at 1a.
Every 1a number is a ratio, sample over white, and a ratio does not care what the
white's absolute reflectance is, only that it holds still and is roughly flat
across the band. The ColorChecker white patch is matte, has published
per-wavelength reflectance near 90%, and is already on order. So the tile moves
from 1a to 1d, where absolute reflectance and agreement with another instrument
start to matter. Ruled "do it" 2026-09-22.

Two things worth keeping from the same exchange. A print shop cannot lend a white
reference; the one in a handheld spectrophotometer is a ceramic tile built into
the instrument. The better ask of a print shop is ten minutes with that
instrument on our chips, which is ground truth for the whole head. And the BOM
line "the one part not worth improvising" was wrong for this stage; it was true of
absolute work and was written before the stages were separated.

Ordered 2026-09-22: ColorChecker Classic, Adafruit 1455 driver, matte black PLA.

### Fifth ruling, same day: the LED set, and the geometry that follows from it

Jared: "I don't have a pure white led. let's rule on everything and I'll order
all LEDs now. Is 5.3 the way to go?"

**Bore.** Yes. Every part in the set is a 5 mm lamp, so `LED_SEAT_D` becomes one
knob at 5.3, CHOSEN. FDM holes print small, so a coupon at 5.2 to 5.6 is printed
first and the knob set to the bore that holds by friction. The tube, plate and
trap are unchanged; the body grows from 44.5 to 54.6 mm across.

**Half angle.** `LED_HALF_ANGLE` drops from the 15 degree estimate to 10, CHOSEN
from datasheets: four of the Kingbright parts list a 20 degree viewing angle. The
narrowest LED is the one that can underfill the port, so it is the number the
geometry is checked against; the wider ones only make that constraint easier.

**Height.** At 10 degrees `LED_Z` 14 underfills the port by a millimetre. 18 is
the only value that passes: 16 still underfills, 20 puts the LED seats through
the detector plate. Margins at 18 are +0.98 mm on overfill and +1.76 mm on plate
clearance, both real but thin, and the viewer should be re-run at 8/10/12 degrees
before the print in case a batch runs narrower than its datasheet.

**The set.** Two changes to the seven colours. The 530 (WP7113ZGCK, real peak
515) sat 14 nm from the 505 (real peak 501) and left a 75 nm hole between 515 and
590; it is replaced by the WP7113SGC at 565, which brings the largest gap in the
ring down to 64 nm (501 to 565). The 660 was a LEDSupply part with no datasheet
and a 50 degree beam; it is replaced by the Kingbright WP7113SRD/J4, 660 nm peak,
30 degree beam, from a Kingbright datasheet. (First written as the /D suffix,
which Jared found obsolete at Digi-Key while ordering; the /J4 is the current
sort of the same lamp. His proposed substitute, Würth 151051RS11000, is a 650 nm
peak with a 30 nm bandwidth and 30 mcd, too close to the 630 and too dim, so no.) The 590 and 625 move
from their 3 mm packages to the 5 mm siblings (WP7113SYCK/J3, WP7113SEC/J3). Real
peaks around the ring: 400, 460, 501, 565, 590, 630, 660, plus the white. This
is a tiling of the band, not an alignment to the AS7341 channels; with narrow
sources the LED is the resolution and the channels are the cross-check.

**Stage 1a.** The white (Cree C513A) is on the same order, so 1a is no longer
waiting on the bins. The PTFE tile holder in `spectra/cad/trap.py` stays in the
model and prints at 1d with the tile.

### Sixth ruling, same day: Stage 1a reads through a Pi, not the ESP32

The BOM had an ESP32 in hand and no firmware. Nothing in the repo read the sensor
at all. The shortest path to a number is a spare Pi (Jared: "there is a spare
pi") running the Adafruit CircuitPython libraries for the AS7341 and the TLC59711
under Blinka, so the capture code is ordinary Python in this package, tested on
the Mac against fakes and run unchanged on the Pi. The ESP32 buys nothing at 1a
except firmware to write. grow-lab's own AS7341 driver is not reused: it is async,
bound to grow-lab's models, and grow-lab already depends on this repo, so the
import would be circular. Spec: `specs/2026-09-22-capture-1a.md`.

