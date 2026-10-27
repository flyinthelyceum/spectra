# SPECTRA calibration adapter: recommended plan (2026-10-26)

Labels: MEASURED = Jared's calipers. MIC = measured in the as-printed CAD (GROUND_puck.md). FROM-PHOTO = scaled off IMG_4937 (about ±5%). DATASHEET (source). ASSUMED. CHOSEN = a design value I picked. Derived numbers say "derived".

## Recommendation (3 sentences)

No snap-on adapter can make the Mini chart readable in its case. The puck itself hits the case: its 54.5 mm face and 79.4 mm base (MIC) run into the 2.82 mm rim or the 7.37 mm hinge (MEASURED) at every one of the 24 patches, and anything clipped onto the puck only raises it further. Buy the full-size ColorChecker Classic, a flat card with roughly 40 mm patches and the same 24 reference values, and print one snap-on collar for it. The collar blocks room light, carries aiming marks and stops the puck rocking. Park the Mini until a CAD check shows whether a narrow-nosed calibration head is worth building.

## Why the three concepts died, in one paragraph

All three (nest the case, snap-on nose, flip the chart) needed the card out of the case. The card is glued in (GROUND_chart, UPDATE 15:16). In the case, the lowest the port can get is 1.81 above a patch: the 1.2 lip (MIC) resting on the 0.61 rib grid (MEASURED). At that height the face sits 1.01 below the rim and 5.56 below the hinge. The nearest walls are 13 to 19 mm from column 4 and about 15 mm from column 1, inside the face radius of 27.25 (FROM-PHOTO against MIC). Columns 2 and 3 clear the face but not the base. The base underside is 2.21 above the patch (MIC + MEASURED), and it reaches over the hinge (7.37) and the rim (2.82). Session data agree. Column 1, next to the hinge, read 0.1–0.2× expected. Column 2 read 0.3–0.5×. Patch 13 read 1.1×. Raising the puck clear of the walls (3.8 mm or more) cuts the signal to about 0.3× (derived), and white is already only 7.5% of full scale with exposure maxed. The wall problem is on the puck itself, so a fixture cannot fix it.

## Primary plan: full-size ColorChecker Classic + snap-on collar

### The target
- Card 203 × 292 mm, 4 × 6 grid, 24 patches (DATASHEET: [Calibrite / Vistek listing](https://www.vistek.ca/store/446619/calibrite-colorchecker-classic)). Patches "slightly under 2 in (5.1 cm)" (DATASHEET: [Wikipedia](https://en.wikipedia.org/wiki/ColorChecker)). Planning value: patch about 40 mm (ASSUMED, caliper on arrival).
- No walls, no ribs. The 21 mm lip (MIC) lands fully on one flat patch, so the port sits 1.2 above it. That is the same standoff as every sample reading today, so calibration and measurement match with no correction.
- Same 24-patch reference values as the Mini, so cccal's reference data and the patch-19 white anchor carry over.
- Cost and lead time are not checked. This purchase is Jared's decision.

### Part 1: collar (the snap-on adapter). The only part you need to print.
One ring that grips the base. Matte black PLA (on hand), PETG if the grip fingers crack.

| Parameter | Value | Label / source |
|---|---|---|
| Collar inner diameter | `79.37 + FIT` | 79.37 MIC; `FIT` from coupon, start +0.25 diametral (CHOSEN) |
| Wall | 2.0 | CHOSEN |
| Grip height on base | z 0.4 to z 12, 6 slots cut from the top to make fingers | CHOSEN |
| Bottom ring (seat + light skirt) | flat annulus, r 34.0 to r 41.8, z −0.9 to z +0.4 (1.3 thick) | CHOSEN |
| What sets its height | top of bottom ring presses up against the base foot at z 0.4 | 0.4 = `FOOT_RELIEF`, MIC |
| Skirt gap to the card | 0.3 (bottom at z −0.9, card face at z −1.2) | CHOSEN; −1.2 = lip, MIC |
| Inner edge r 34.0 | clears the head body (r 27.25) by 6.75 | MIC |
| Aiming ticks | 4 notches on the outer rim at 0/90/180/270°, each with a white first layer (AMS), plus matching white vertical lines up the outside of the collar | CHOSEN |
| Optional feet (print only if the reseat test fails) | 3 bumps under the bottom ring at r 40, 120° apart, tip at z −1.10 (0.10 above the card) | CHOSEN, see "Tilt" |

- **Print:** bottom ring down on smooth PEI, fingers up. The ring's underside then has the flattest surface the X1C makes, and nothing overhangs. Estimate 1 h 15 min (ASSUMED).
- **No cable clip.** A clip on the puck still passes cable pull into the puck. Instead, hang the USB-C cable from above (lamp arm or a hook) with a slack loop, so it leaves the port at z 38.5 (MIC) with no sideways pull.

### How aiming is solved
- Tolerance is huge on this card. The collected spot has radius 2.8 (MIC/derived). On a 40 mm patch (ASSUMED) the port centre can be anywhere within about 17 mm of the patch centre (derived: 20 − 2.8).
- The four white ticks show the port axis from outside the puck. Line two of them up with the middle of the patch column and the other two with the middle of the row. The patch edges stay visible past the collar, because the collar (r 41.8) covers less than the gap to the next patch centre plus half a patch. You are aiming at a 34 mm target, not a 6 mm one.
- Lift and place only. Never slide the puck across the card: it scratches the patch paint.

### Light-tightness
- The puck face covers r 27.25. The collar skirt adds a black wall at r 34–41.8, 0.3 above the card. Room light now has to travel about 14 mm through a 0.3–1.2 mm gap (derived).
- **Test before trusting it:** puck on black patch 24, LEDs off, read with room lights on and with them off. If the difference is above 0.2% of white, drape a dark cloth over the puck. Do not design a bigger hood unless that fails.

### Tilt
- On a flat card the lip ring seats by gravity. Today's seated white repeated within 0.5–1.5% even on the rib grid (session evidence).
- **Gate:** 10 lift-and-reseat reads on patch 19. Pass if the spread is 1% or less per LED channel.
- **If it fails,** print the 3-foot version. Feet 0.10 above the lip plane at r 40, against the lip edge at r 10.5, limit rock to atan(0.10/29.5) ≈ 0.2° (derived). That is under 1% at 2–4% per degree (GROUND_puck).
- Why the feet are not in v1: the CAD's free rock of 3.1° (MIC) only shows up when something pushes the puck sideways, and the hung cable takes away the main push. Add feet only if the test says so.

### Print plan
1. **Fit coupon first (about 30 min total, ASSUMED):** three short collar rings, 6 mm tall with the full bottom ring, at `FIT` +0.15 / +0.25 / +0.35. Checks:
   - the ring slides onto the base and grips without rocking;
   - with the puck on glass, a 0.25 feeler passes under the skirt all the way round and a 0.35 does not (this confirms the 0.3 gap and that the base foot really sits 1.6 above the lip plane, MIC);
   - the ticks read square to the USB-C opening.
2. **Full collar** at the winning `FIT`, about 1 h 15 min.
3. **Feet version** only if the reseat gate fails: same file with `FEET=True`.

## cccal.py changes (branch claude/project-thread-esjrdg; do not edit until approved)

1. **Layout table with `--layout`.** Prompts name the patch by position on the physical target, in plain words.
   - `classic` (full card, landscape): row 1 = patches 1–6 left to right, row 4 = 19–24, so white 19 is bottom row, far left. Today's line 171 prompt is already correct for this layout.
   - `mini-case` (kept for later): column 1 bottom→top = 1..6, beside the hinge; column 2 = 7..12; column 3 = 13..18; column 4 = 19..24. So white 19 is bottom-right and black 24 top-right. Example prompt: "Patch 10, column 2 from the hinge, 4th up: purple."
2. **Double read on every patch.** Read, then prompt "lift and reseat", then read again. If any LED's peak differs by more than 2% between the two, prompt a third reseat. Keep the two reads that agree and record all three.
3. **Flush stray Enter.** Call `termios.tcflush(sys.stdin, termios.TCIFLUSH)` immediately before every `input()` in `ask()`. Also ignore an Enter that arrives less than 1.5 s after the prompt, so a held or double Enter can't read the wrong patch.
4. **Wrong-patch check.** After each patch, compare its per-LED pattern (relative to white) with the expected ordering, for example patch 15 (red) must peak on the red LED and the greys 19→24 must fall in that order. If it doesn't match, re-prompt the same patch. Do not use a plain 2× brightness window: neighbouring greys differ by only about 1.6×.
5. **Record the setup in the output:** `target: classic|mini-case`, `adapter: collar-v1|collar-v1-feet`, `standoff_mm: 1.2`. Never mix calibrations with different tags.
6. **Reseat gate at the start:** read patch 19 twice with a lift between. Stop if they differ by more than 1.5%.
7. **Dark read at the start and the end** (already done at both). Add optional `--dark-each` for a lights-on stray check after each placement.

Session time: 31 placements, patches read twice, about 20 s per read (ASSUMED from cccal exposure steps) plus about 5 s to seat. Roughly 22–25 min (ASSUMED).

## Branches

**A. Card does come out after all** (Jared wasn't sure and didn't have it with him). The answer barely changes. A loose 64 × 108 card (DATASHEET BabelColor) with about 12 mm patches at about 15 mm pitch (FROM-PHOTO) puts the lip across neighbouring patches. Standoff is 1.2 if the ribs belong to the case, or 1.81 if they belong to the card. Aim tolerance is about ±3 mm, which needs a pegged tray (Concept A's tray: blind holes on the patch grid, one peg under the port), and the card has to sit flush in a frame so the 79 mm base has something to rest over. That is 3 parts and calipered pitch, against 1 part for the full card. Still buy the full card. Use the loose Mini only if the purchase is refused.

**B. Keep the Mini in its case (no purchase).** The only route is a calibration-only head with a narrow nose. Keep the optics exactly as they are (LED throw 25.46 at 45°, port 8.0, MIC). Taper the outside of the head to a 45° cone that follows the LED ray envelope, outer surface roughly r ≈ z + 6 above the sample (derived). Raise the base so it sits at least about 9 above the patch (derived). Replace the lip with a square key, about 11.4–11.7 wide, that drops into the patch window and rests on the rib grid. That holds the port 1.2 above the patch and aims itself to ±0.3. This is a new head and base, not a snap-on.
- **Before any CAD:** run the build123d check in `~/projects/spectra/.venv`. It must clear 2.82 at the rim distance and 7.37 at the hinge distance for columns 1 and 4. Column 1 is marginal (about 18 mm to the hinge edge against a cone radius of about 17.9 at 7.37, FROM-PHOTO + derived).
- **Free first step:** fold the white panel fully back behind the chart and caliper the hinge top above the patch surface. If it drops below about 1.6, the hinge stops being an obstacle.
- **Interim, no print:** do not fit a calibration to the in-case data you already have. Tag it as partial.

## Residual risks still standing
- Full-card patch size and border are not measured (40 mm is ASSUMED from "slightly under 2 in"). Even at 30 mm the aim tolerance is still about ±12 mm (derived), so the plan holds, but caliper on arrival.
- Lip flatness is not measured. The rim-down print leaves a possible seam blob on the lip tip (GROUND_puck). The 10-reseat gate catches it, and the feet are the fix.
- The skirt gap assumes the card lies within 0.3 of flat under the collar. A bowed card makes the skirt touch, which lifts the puck. Check with a straightedge on arrival, and tape the card corners flat.
- Ambient light is not measured. The lights on/off dark test decides whether a cloth is needed.
- The white LED is at 7.5% of full scale with exposure maxed. Signal on the full card equals today's sample point (1.2 standoff), so nothing gets worse, but nothing gets better either.
- 1.2 standoff is the instrument's as-built point, not its design point (0). Calibration and samples now match, which is what matters. Fixing the design point is a head change, out of scope.
- The Mini stays unusable for calibration until branch B is checked.

## Numbers still needed, each tied to what it sets

| # | Measure | How | Sets |
|---|---|---|---|
| 1 | Printed base OD at z 2–10 | caliper, 3 angles | collar `FIT` (start value; the coupon decides) |
| 2 | Base foot height above glass, lip on glass | feeler stack under the base edge, 4 points | bottom-ring Z and 0.3 skirt gap (MIC says 1.6) |
| 3 | Lip rock on glass | press the rim at 4 points, feeler under the lip | whether feet are needed in v1 |
| 4 | Full card: patch edge, gap, border to the first patch | caliper on arrival | aim tolerance; confirms the 40 mm ASSUMED |
| 5 | Full card: thickness and bow | caliper; straightedge + feeler across the diagonal | skirt gap margin |
| 6 | (Branch A) does the Mini card release; if so `CARD_L/W/T`, and are the ribs on the card | try it; caliper | tray pocket, standoff 1.2 vs 1.81 |
| 7 | (Branch B) hinge top above patch with the case folded back | caliper | whether the hinge stays an obstacle |
| 8 | (Branch B) column 1 centre to hinge inner edge; column 4 centre to rim inner edge; rows 1 and 6 to top and bottom walls, plus those wall heights | caliper, or a square-on photo with a ruler at patch height | cone-nose clearance check |
| 9 | (Branch B) patch window edge and corner radius; pitch over 3 spans (columns) and 5 spans (rows) | caliper | key size; confirms no pitch error builds up |

Nothing was edited, committed or printed. Only this file was written.
