# Charter

**An instrument that measures the reflectance of a physical sample, consistently,
and a place to keep what it measured.**

That is the whole of it. Everything specific sits in a layer above.

## Two layers, and the line between them

**The measurement layer is general.** A 45/0 head, a calibration chain, a reference
tile and a light trap, a detector on a module plate, and a store of dated readings.
It knows about samples, curves, dates and calibration state. It does not know what a
sample *is*. A tube of oil paint, a Color-aid swatch, a filament chip, a glaze test
tile, a spray-can drawdown, a print proof, a dyed fabric, an anodised coupon: all the
same kind of row.

**Models sit on top, and each answers its own question.** Kubelka-Munk is the first
one and it answers a sharp question about paint. It is a module over the store, not
the reason the store exists, and a second model would not disturb it.

The line matters because fusing the two is how an instrument ends up narrower than
its hardware. It is also how one ends up useless: a general device with no defining
question is a Nix, which is an excellent instrument aimed at a question nobody asked.
Keep the question sharp and keep it in the model layer.

## What the instrument has to do

Read a flat opaque sample pressed to its port and return a reflectance curve that is
the same curve next week, on a different day, at a different temperature, after the
tile has been wiped. Consistency across time and across samples is the whole product.
Absolute accuracy is bounded by the ColorChecker and is a secondary claim.

Its envelope is the envelope of any contact colorimeter, the Nix included: flat,
opaque, pressable, light-sealed at the port. Curved objects, pile fabrics, wet films,
anything across the room, anything transmissive: out of scope for the head, and some
of those are in scope for the profiled flatbed instead.

## The first model: mixing

**What will this pigment do when it is mixed?** Not "what colour is this tube" — the
eye reads a tube faster and better than any handheld device, and always will. High
chroma is what makes the question sharp, because a saturated pigment loses chroma in
a mixture far faster than intuition predicts and the loss is not symmetric.

- **Mixture prediction.** From two measured tubes, compute the mixing line before
  touching paint, including where on that line the chroma falls off a cliff.
- **The reachable colour solid.** For a chosen palette, the whole set of colours
  obtainable from it, and more usefully its holes. Every limited palette has a region
  it cannot reach and almost nobody knows where theirs is.
- **Substitution.** Which cheaper or less toxic pigment lands in the same place, and
  the part a swatch card never tells you: where it stops matching.

Kubelka-Munk needs things a general measurement does not: a masstone and a drawdown,
a cure interval, a pigment index. Those are fields this model asks for. They are not
columns every sample carries. See `MEASUREMENT.md`.

## Other models, named so nobody re-derives the need for them

Not built, not scheduled, and listed only so the store is not shaped in a way that
forbids them: matching a target against measured samples already in the library;
batch-to-batch drift on any material that ships in lots; fade series on anything
dated and re-measured; agreement between two instruments over the same samples.

## Non-goals

**Matching against a commercial paint database.** That is what handheld colorimeters
are optimised for and they are good at it. Solving for the mixture of *measured*
samples that lands nearest a target is a different job and is in scope.

**Scanner and camera profiling.** Done already, in grow-lab's
`docs/COLOR_MEASUREMENT.md`. This repo builds on it and does not repeat it.

**A general-purpose colour-science library.** The conversions, the metric and the
profiling maths are one implementation, moving here from grow-lab, and they are good
enough. Nothing here competes with a real colour stack.
