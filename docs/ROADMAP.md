# Roadmap

Each stage has one number, and the stage is not finished until the number exists.

| Stage | Build | Usable output |
|---|---|---|
| 0 | Colour maths extracted from grow-lab; grow-lab consumes it | Both repos green on their own suites |
| 1a | Head printed, AS7341 mounted, white LED only, dark/black/white cycle | Reads the ColorChecker. Gives the repeatability number. |
| 1b | LED ring, sequential capture, per-LED integration time | 56 numbers per sample. Coarse reflectance curves. |
| 1c | The general store: sample ids, dated readings, calibration state, sample kinds | A library that takes any flat opaque sample |
| 1c+ | The `paint` kind: pigment index, masstone and drawdown protocol | The tubes on hand, measured |
| 1d | K/S extraction, mixture prediction, the six-pigment test | Predictions, scored. And the Stage 2 decision, made on data. |
| 2 | C12880MA on the same plate, broadband source | The same library re-measured, against the same tiles |

Stage 1a is a weekend. 1d is where the interesting work is and it is mostly
software, which is why `spectra/km.py` exists before any of the hardware does.

## What done looks like

| Stage | Test | Passes at |
|---|---|---|
| 0 | Both suites green, no colour code left duplicated in two repos | Green, and one copy |
| 1a | Ten readings of one paint-out, head lifted and replaced between each | Spread under 0.5 ΔE00 |
| 1a | ColorChecker's 24 patches, scored by `check_profile.py` | Mean under 2.0 ΔE00, max under 5.0 |
| 1a | Head against the profiled flatbed, same 24 patches | Agreement inside the sum of their error bars |
| 1a | A Color-aid tint ladder and a shade ladder, one hue family each | L\* monotone, hue angle steady along the ladder |
| 1a | The Color-aid 19-step gray ladder | No compression at the dark end beyond the measured stray-light term |
| 1b | A pigment with a known steep edge, measured twice a week apart | Curves overlay within the noise floor |
| 1c | Three sample kinds in the store, none of them special-cased in the core | A Color-aid swatch and a tube are the same kind of row |
| 1c+ | Every tube read masstone and drawdown, pigment index recorded | The paint library is complete, not partial |
| 1d | Six pigments, 50/50 predictions against actual mixes | Broad-curve pairs inside 3 ΔE00 |
| 1d | The same test on the saturated organics | **No threshold. This number is the Stage 2 decision.** |
| 2 | The library re-measured on the C12880MA, same tiles | The organics now inside 3 ΔE00 too |

The row that matters most is the second 1d row and it has no pass threshold on
purpose. It is not a test the build can fail. It measures how much the cheap
detector is costing, and its only job is to make the $200 decision on evidence.
Anyone who adds a threshold to it has broken the instrument's reason for being
staged. Write that test before building the head, so the decision is specified
before the moment arrives and cannot be argued into or out of.

The six pigments: two earths, two cadmiums, two saturated organics. Predict each
pair at 50/50 from K/S, mix them for real, score the prediction in ΔE00. If the
earths land inside 3 and the organics land past 8, that gap is the purchase order.

## Known holes

- **No ColorChecker in hand.** It gates the 1a acceptance rows *and* grow-lab's
  first real scanner validation. One order unblocks both. The Color-aid 314 set is
  on the shelf and covers hue range, linearity and agreement, but carries no
  reference values, so it cannot stand in for the chart on accuracy.
- **Publishing the 314-row table is undecided**, and the decision is cheaper before
  the table exists than after. Same file.
- **`as7341_breakout` needs one number: `PCB_W`.** An earlier version of this line
  said the board was unmeasured on every row. That was wrong — it was read from a
  memory file dated 2026-09-14, a day before the board was actually calipered. The
  source is `components/as7341_breakout.py`, and as of 2026-09-15 every row except
  `PCB_W` carries `CALIPER 2026-09-15 JR`. Only the detector plate is blocked, and
  only because the sensor's offset across the board is measured from the edge whose
  distance `PCB_W` supplies. `spectra/cad/plate.py` raises with that message and
  `assembly.py` omits the plate; the rest of the head builds and renders. Take one
  caliper reading and write it with `python -m components measure`.
- **Saunderson `k1` is unfitted.** The default is a normal-incidence Fresnel value,
  not a measurement of this head. It should be fitted against the chart once the
  head exists, and the fitted value recorded here. Okumura 2005 fits k1 ≈ 0.03–0.04
  and k2 = 0.6 per pigment, which is where our defaults land — but his Carbon Black
  goes to k1 = 0, k2 = 0.4, so treat the pair as fittable rather than constant.
  `docs/PRIOR_ART.md`.
- **Stage 1d has a number to be judged against now.** Okumura 2005 reports mean
  ΔE00 2.21 and max 8.48 predicting secondary mixtures with two-constant K-M
  (worst: blue and yellow into green), against 0.11–0.51 for fitting a tint ladder
  to itself. Our acceptance should be stated against the prediction figure, not the
  fitting one. It is not yet written into the acceptance table because the
  measurement geometry differs — see the +3% note in `docs/PRIOR_ART.md`.
- ~~**build123d grounding.**~~ CLOSED 2026-09-17. The archived hook fires nowhere,
  so the pinned v0.11.1 docs are vendored into `docs/build123d/` (72 files, commit
  recorded in `SOURCE_COMMIT.txt`). Read the file that covers what you are about to
  write, before you write it.
- **Cure interval.** Two weeks is proposed and not yet fixed. It must be settled
  before the first paint-out, because changing it later invalidates everything
  measured under the old convention. Record the date with every reading regardless.
