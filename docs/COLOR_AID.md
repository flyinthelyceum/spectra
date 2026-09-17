# Color-aid 314

**In hand.** The full Color-aid set, 314 silkscreened papers, numbered 001–314 and
identified on the reverse of every sheet except black and white.

They are not pigments and they never enter the pigment library. Paper cannot be
mixed, a Color-aid sheet has no pigment index, and its K/S describes a screen ink on
a substrate rather than anything that will ever come out of a tube. A Color-aid row
in a table whose schema means "this is how it behaves in a mixture" would be a lie
told in the schema rather than in a number.

What they are instead is the best characterisation target available here, and a
better one than a ColorChecker for everything except absolute accuracy.

## What is in the set

Counts below are off the manufacturer's Sixth Edition booklet (2006) and reconcile
two independent ways, so they are read rather than remembered.

| Block | Numbers | Count |
|---|---|---|
| Hues and tints | 001–112 | 112 (24 hues + 88 tints) |
| EX | 113–122 | 10 |
| LT | 123–134 | 12 |
| Gray | 135–153 | 19 (17 grays, plus BLACK 135 and WHITE 153) |
| DS | 154–158 | 5 |
| Shades and pastels | 159–306 | 148 (42 shades, 106 pastels) |
| LP | 307–314 | 8 |

Sliced the other way, the booklet counts 34 vivid, 100 tints, 47 shades, 114
pastels, 17 grays, black and white. Both cuts sum to 314 and agree block by block,
which is what makes the block expansions below trustworthy: EX is extra-vivid, LT
light tint, DS deep shade, LP light pastel. Those four expansions are arithmetic
inference from the two reconciling cuts, not quoted from the booklet.

**24 hue symbols**, each appearing as `<hue>-HUE` and then as ladders. R, RO, O, YO,
Y, YG, G, BG, C, B, BV, V, RV, M, with `w` (warm) and `c` (cool) variants filling the
circle out to 24: Rw, Rc, Yw, Yc, YGw, YGc, Gw, Gc, Bw, Bc. Codes read as
`R-T2` (red, tint two), `YGw-P4-1` (warm yellow-green, pastel four, one).

**Two facts from the booklet that matter more than the counts:**

- **GRAY 4 (number 141) is stated at 18% reflectance**, offered as a photographer's
  gray card. It is the only quasi-reference value anywhere in the set.
- **The set drifts.** "The colors are matched closely to a standard, but periodically
  minor adjustments may be made." And on lightfastness: a slight yellowing of the oil
  in the vehicle is unavoidable and "over time may especially affect the pale violets
  and blues." That is a dated, falsifiable prediction about these exact papers.

## What they are good for

### Hue coverage the chart does not have

grow-lab's `docs/COLOR_MEASUREMENT.md` says it plainly: a 24-patch ColorChecker "has
nothing near the edge of the gamut. High-chroma pigment is exactly where a 3×3
fitted to it is weakest." Thirty-four vivid papers spread over 24 hue symbols is
exactly that gap. They cannot calibrate anything, because no reference values exist
for them. They can test everything.

### The ladders are a reference that needs no reference values

This is the strongest reason to own them for this build. Within a hue family the
tint ladder T1→T4, the shade ladder S1→S4 and the pastel steps were built to run
evenly. So the structure itself is the standard:

- An instrument that reads a tint ladder non-monotonically in L\* has a bug.
- An instrument whose hue angle wanders along a ladder that should hold hue has a
  channel or an LED problem, and which way it wanders says which one.
- The 19-step gray ladder tests the dark end, which is where the head's stray-light
  flare term bites. A gray ladder that reads compressed at the bottom *is* the flare
  term made visible, and the compression measures it.

None of that requires a purchased standard or a certified value. It is an acceptance
test that can run the day the head first powers up, against paper already on the
shelf.

### A transfer standard between the two instruments

The asymmetry is the point. 314 flat matte papers are the flatbed's ideal subject:
several per pass, fast, and flatness is what a scanner wants. They are the head's
worst case: one at a time, hand-pressed against an 8 mm port, and a full set is
hours of handling that gets abandoned somewhere around swatch ninety.

So use each for what it is good at:

1. Scan all 314 on the profiled flatbed, with the ColorChecker in **every** pass and
   neither it nor the subject moving between them.
2. Measure a spanning subset on the head, around thirty: one per hue symbol, the
   gray ladder, and the vivid papers at the gamut edge.
3. The shared readings characterise head-against-flatbed agreement across real hue
   coverage rather than across 24 clustered patches.
4. The flatbed's 314 then stands as a working catalogue the head never had to grind
   through, with a known relationship to the head.

**Sizing decides whether this is an afternoon.** At 3"×4.5" roughly six papers plus
the chart fit a V600 pass, so the set is about fifty scans. At 6"×9" it is one or two
per pass and the full set stops being viable; scan a spanning subset instead.

### Metameric pairs, free and real

The flatbed's lamp and the head's narrowband LED sweep are radically different
illuminants. Any pair of papers that agree under one and part company under the
other is a metameric pair sitting in the drawer. `COLOR_MEASUREMENT.md` says the
scanner "cannot see this coming," and it is right: one instrument cannot. Two can.
With 114 pastels and dense near-neighbours, such pairs exist in this set.

### A fade series, for the cost of running it again

The booklet predicts that the pale violets and blues yellow first. Measure the set
now, re-measure in a year, and that is either confirmed with a number or it is not.
It costs one re-run, it makes every reading dated rather than permanent, and it
turns a static asset into a series.

## What they are not for

- **Not accuracy.** No published spectral or colorimetric reference data for
  Color-aid papers was found in a search of the vision-science literature and the
  manufacturer's own materials. Absent that, a ΔE00 measured against Color-aid is a
  statement about precision, coverage, linearity and cross-instrument agreement. It
  is not a statement about accuracy, and someone will quote it as one unless this
  paragraph exists.
- **Not a replacement for the ColorChecker.** That order still gates the Stage 1a
  acceptance rows in `ROADMAP.md`, and grow-lab's first real scanner validation.
- **Not library material.** See the top of this file.
- **Not a batch to run before the protocol is proven.** Twenty-four papers, one per
  hue, then decide whether the rest earns the handling.

## Publication, worth deciding rather than discovering

This repo is public. The booklet asserts copyright over the collection and its
arrangement and objects specifically to "cross reference to these materials."
Measurements of physical objects one owns are facts, and a list of facts carries no
copyright of its own; the selection and arrangement of 314 colours plausibly does,
and a complete table keyed to their codes reproduces that arrangement. The
measurements are worth publishing and the aggregate results certainly are. Whether
the full 314-row table goes in this repo or stays local is a call to make
deliberately, before the table exists rather than after.

## Where this goes next

Nothing here is blocked by the HOLD lane. The flatbed exists, the profiling workflow
exists in grow-lab, and the only purchase involved is the ColorChecker that was
already on the list. The head's acceptance tests, when the head exists, gain the
ladder checks above at no cost.
