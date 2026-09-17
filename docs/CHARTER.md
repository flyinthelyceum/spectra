# Charter

**The instrument exists to answer one question: what will this pigment do when it
is mixed?**

Not "what colour is this tube." The eye reads a tube faster and better than any
handheld device, and always will. High chroma is what makes the question sharp,
because a saturated pigment loses chroma in a mixture far faster than intuition
predicts and the loss is not symmetric.

## What becomes possible once pigment is measured rather than judged

- **Mixture prediction.** From two measured tubes, compute the mixing line before
  touching paint, including where on that line the chroma falls off a cliff.
- **The reachable colour solid.** For a chosen palette, the whole set of colours
  obtainable from it, and more usefully its holes. Every limited palette has a
  region it cannot reach and almost nobody knows where theirs is.
- **Substitution.** Which cheaper or less toxic pigment lands in the same place,
  and the part a swatch card never tells you: where it stops matching.

## Non-goals

**Matching a target against a commercial paint database.** That is what handheld
colorimeters are optimised for and they are good at it. Solving for the mixture of
*your own measured tubes* that lands nearest a target is a different job and is
firmly in scope, residual reported honestly when the palette cannot reach it.

**Scanner and camera profiling.** Done already, in grow-lab's
`docs/COLOR_MEASUREMENT.md`. This repo builds on it and does not repeat it.

## Why not a Nix Pro

It is an excellent instrument pointed at a different question. It reports
colorimetric output, not spectra: it says where a colour sits, and mixture
behaviour is a property of the reflectance curve rather than of the Lab point. Two
paints that read identically under its lamp can behave completely differently in a
mixture, because the curves that produced that Lab are different shapes. A device
that only ever hands back the Lab has thrown away exactly the information the
question needs. Buying one would not have been a mistake. It would have been a
purchase that answers a question nobody was asking.
