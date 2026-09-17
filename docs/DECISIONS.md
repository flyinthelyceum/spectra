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
