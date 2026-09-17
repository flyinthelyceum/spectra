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
wrong, that is found out for free rather than after a two-week cure. `pigment/km.py`
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

**Public, name `pigment`.** Public because CI on GitHub-hosted runners and cloud
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
