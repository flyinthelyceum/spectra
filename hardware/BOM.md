# BOM

Stock-level quantities, not a wiring diagram. "In hand" means on the shelf, not
budgeted.

| Item | Est. | Stage | Note |
|---|---|---|---|
| AS7341 breakout | in hand | 1a | Its own board out of back stock, not the one cased on the station. Shared hardware means unmounting, re-seating and re-calibrating between sessions, and a calibration that has to be redone before every use quietly stops being done. |
| ESP32 | in hand | later | Not used for Stage 1a. Capture runs on a spare Pi with the Adafruit CircuitPython libraries under Blinka (ruled 2026-09-22, `specs/2026-09-22-capture-1a.md`). |
| PETG, black | in hand | 1 | Head, detector plate, light trap |
| PLA, matte black | ordered 2026-09-22 | 1a | The first samples. A printed chip is flat, opaque and pressable, which is the whole envelope the port asks for. Ruled 2026-09-22; confirm a spool is on the shelf. |
| Sintered PTFE white tile | $40–80 | 1d | Cut from 1a, ruled 2026-09-22. Stage 1a is ratios against a white, so the ColorChecker white patch (19, matte, published reflectance near 90%) is the reference. The tile returns when absolute reflectance or cross-instrument agreement is on the table. Uncertified sintered PTFE is enough; certified Spectralon is not needed. |
| Narrowband LEDs, 7 wavelengths, all 5 mm | ordered 2026-09-22 | 1 | Ruled set, peak / half angle from datasheets: 405 Marktech MT5400-UV (400 nm, ~30°); 450 Kingbright WP7113QBC/D (460, 10°); 505 Broadcom HLMP-CE34-Y1CDD (501, ~15°); 565 Kingbright WP7113SGC (565, 10°) replaces the 530 ZGCK, which sat 14 nm from the 501 and left a 75 nm hole to 590; 590 Kingbright WP7113SYCK/J3 (10°); 625 Kingbright WP7113SEC/J3 (10°); 660 Kingbright WP7113SRD/D (660, FWHM 20, 15°, red diffused lens) replaces the no-datasheet LEDSupply part. A few of each. |
| White LED, 5 mm | ordered 2026-09-22 | 1a | Cree C513A-MSN-CW0Z0132, 2500–2800 K, CRI 80, 27.5°. The only source Stage 1a uses. |
| Constant-current LED driver | ordered 2026-09-22 | 1 | Adafruit 1455 (TLC59711, 12 ch, 16 bit, constant current). Brightness must not drift with supply; the datasheet states line and load regulation. |
| ColorChecker Classic | ordered 2026-09-22 | 1 | Shared with the scanner workflow, not an extra. Gates acceptance in both repos. |
| Color-aid 314 full set | in hand | 1 | The characterisation target: 24 hue symbols, even tint/shade/pastel ladders, a 19-step gray scale. Tests coverage, linearity and cross-instrument agreement, none of which the 24-patch chart reaches. Not an accuracy standard and not library material — `docs/COLOR_AID.md`. |
| Black/white drawdown cards | $10–20 | 1c+ | Two grounds under one film is how K and S come apart for a transparent pigment |
| Drawdown bar | $30–60 | 1c+ | Thickness never has to be known, only repeated. One bar, every film. |
| Titanium white, artist grade | ~$20 | 1c+ | For tints as a check on prediction; one tube, consistent across every measurement |
| Digital scale, 0.01 g | $20–30 | 1c+ | Ratios by mass. Mixing by eye makes the model meaningless. |
| Hamamatsu C12880MA | ~$200 | 2 | Only after the gap is measured |
| ADC and clean analogue front end | $20–40 | 2 | The C12880MA's readout deserves better than a bare GPIO |

Stage 1 is about $190 of new parts. The drawdown bar and cards are the addition
over the original brief, and they buy the only honest route to K and S for the
saturated organics, which are the pigments the whole project is about.

**Dimensions are not recorded here.** Measured physical dimensions live in
[`flyinthelyceum/components`](https://github.com/flyinthelyceum/components), one
writer, written with `python -m components measure`. `as7341_breakout` is
fully calipered as of 2026-09-17 and the detector plate builds. (Two earlier versions
of this line claimed otherwise, each quoting a memory file rather than the source.
Read `components/as7341_breakout.py`; do not read this line for measurement state.)
