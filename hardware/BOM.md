# BOM

Stock-level quantities, not a wiring diagram. "In hand" means on the shelf, not
budgeted.

| Item | Est. | Stage | Note |
|---|---|---|---|
| AS7341 breakout | in hand | 1 | Its own board out of back stock, not the one cased on the station. Shared hardware means unmounting, re-seating and re-calibrating between sessions, and a calibration that has to be redone before every use quietly stops being done. |
| ESP32 | in hand | 1 | |
| PETG, black | in hand | 1 | Head, detector plate, light trap |
| Sintered PTFE white tile | $40–80 | 1 | The one part not worth improvising |
| Narrowband LEDs, 7 wavelengths | $15–25 | 1 | 405 / 450 / 505 / 530 / 590 / 625 / 660 nm, a few of each |
| Constant-current LED driver or MOSFET array | $10–20 | 1 | Constant current: brightness must not drift with supply |
| ColorChecker Classic | $70–100 | 1 | Shared with the scanner workflow, not an extra. Gates acceptance in both repos. |
| Black/white drawdown cards | $10–20 | 1 | Two grounds under one film is how K and S come apart for a transparent pigment |
| Drawdown bar | $30–60 | 1 | Thickness never has to be known, only repeated. One bar, every film. |
| Titanium white, artist grade | ~$20 | 1 | For tints as a check on prediction; one tube, consistent across every measurement |
| Digital scale, 0.01 g | $20–30 | 1 | Ratios by mass. Mixing by eye makes the model meaningless. |
| Hamamatsu C12880MA | ~$200 | 2 | Only after the gap is measured |
| ADC and clean analogue front end | $20–40 | 2 | The C12880MA's readout deserves better than a bare GPIO |

Stage 1 is about $190 of new parts. The drawdown bar and cards are the addition
over the original brief, and they buy the only honest route to K and S for the
saturated organics, which are the pigments the whole project is about.

**Dimensions are not recorded here.** Measured physical dimensions live in
[`flyinthelyceum/components`](https://github.com/flyinthelyceum/components), one
writer, written with `python -m components measure`. `as7341_breakout` currently
reads `CALIPER needed` on every row; the head plate is blocked on those calipers.
