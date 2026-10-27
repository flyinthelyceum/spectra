**SPECTRA adapter: ground truth from the as-printed CAD**

Sources: as-printed tree `0641d42` (PR #14 merged with #15), exported to `/private/tmp/claude-501/-Users-jared/ea9ef439-5f23-47cd-9bf6-fb754cbc8d1d/scratchpad/adapter/src`. I ran the build123d code with `~/projects/spectra/.venv`. The probe script is `.../scratchpad/adapter/measure.py`. Labels: MIC = MEASURED-IN-CAD, DS = DATASHEET (source given), ASM = ASSUMED.

**1. Which version is the printed one, and branch discrepancies**
- **Head:** the PR #15 design. Memory note 10-22 says the printed mesh matches `0641d42` exactly. That commit is on `origin/claude/project-thread-sb1xhy` and `viewer-led-path`.
- **Base:** the #9 export (`work_puck_v2`, about 48 mm tall). `puck.py` at 0641d42 differs from `calibration-dock-0fxwut` only in a docstring and the `led_breakout_z` formula.
- **The worktree branch I was pointed at, `claude/project-thread-esjrdg`,** still carries the pre-#15 head CAD: no `led.py`, `LED_SEAT_D` 5.3. Do not design from it.
- **A dock already exists, unprinted (ASM),** in `origin/claude/calibration-dock-0fxwut:spectra/cad/dock.py`. It has white and trap cups, and its cup radius and well depth are driven from the puck. An adapter should reuse its parameterisation.

**Geometry (z = 0 is the port face, sample below)**
- **Puck outer diameter:** 79.37 (MIC; `R_OUT` 39.68). Base height runs from z 0.40 to 48.45, and the lid top is at z 48.95 (MIC).
- **Head body:** 54.49 diameter, z −1.2 to 24.0 (MIC).
- **Measuring face:**
  - Flat disc, 54.5 diameter, at z 0 (MIC).
  - Port is 8.0 diameter, on the axis, centred in the puck (MIC; `PORT_D`, ruled).
  - Port land is 11.0 OD (MIC).
  - The port's cavity side is bevelled at 45°, leaving a 0.8 straight land (MIC; `PORT_BEVEL_LAND`).
- **Lip:** a ring 21.0 OD / 19.4 ID (wall 0.8) standing **1.2 proud, down to z −1.2. It is the lowest point of the whole assembly** (MIC; slab z −1.3 to 0 contains only the 21-diameter ring).
- **Base foot:** relieved 0.4 above the port face (MIC; `FOOT_RELIEF`).
- **Other features on the face:** the M3 socket-head counterbores are recessed into the foot. The LED bores break out of the head wall only above z 21.87 (MIC), so nothing breaks the face.
- **USB-C opening:** through the wall at −X, centred at z 38.5, 12.5 × 7.5 (MIC).
- **Print orientation:** the head prints rim-down, so the port face and lip are top surfaces. The face is the top skin over a bridged cavity ceiling. The base prints foot-down (MIC docstring, `puck.print_ready`).

**2. ColorChecker Classic physical dimensions**
- **Card:** 203 × 292 mm (DS: [calibrite.com product page](https://calibrite.com/us/product/colorchecker-classic/)). BabelColor gives 20.4 × 29.0 cm ([babelcolor.com](https://babelcolor.com/colorchecker.htm)).
- **Grid:** 4 × 6, 24 patches (DS: [Wikipedia](https://en.wikipedia.org/wiki/ColorChecker)).
- **Patch size:** Wikipedia says "slightly under 2 in (5.1 cm)". That figure probably describes the older 13 × 9 in card. Pitch is bounded by 292/6 ≈ 48.7 and 203/4 ≈ 50.8 (derived from DS).
  - Patch ≈ 40 mm, gap ≈ 6–9 mm black, border ≈ 10 mm: **ASM. No source I could reach gives patch, gap, border or thickness. Caliper all four.**
- **Card thickness:** ASM 1–2 mm, plus the protective sleeve. The sleeve may bow the card.
- **For reference if Jared actually has the small card:** Passport and Classic Mini are 6.4 × 10.8 cm (DS: BabelColor), so pitch is ≤ 18 mm. Confirm which card is in hand. "Small patches, narrow gaps" fits a 40 mm patch under a 79 mm puck, but check anyway.

**3. Optical constraints at the design point (sample at z 0)**
- LED throw 25.46 mm (MIC).
- Lit beam minor axis 8.98 and major axis 12.70 (MIC, resting on `LED_HALF_ANGLE` 10°, from the WP7113 DS 20° viewing angle).
- Collected spot 5.33 diameter (MIC: 4.0 aperture, plate at z 24, tube 18 long). That leaves 1.33 of play inside the port.
- Specular acceptance is ±6.3° against 43° worst case (MIC).

**As-built point (sample at z −1.2, on the lip):**
- Each LED's beam centre lands 1.2 off the axis on the far side, because 45° gives an offset equal to the standoff (derived).
- The port shadow of each LED shifts by the same 1.2, so the region lit by all 8 LEDs has radius 4 − 1.2 = 2.8.
- The collected spot radius becomes 2 × 25.2/18 = 2.8. **Margin is zero.** At design it was 1.33 (derived).
- Irradiance falls as 1/throw² for every LED: (25.46/27.16)² = 0.88, so −12%, and the light is scarce already (derived).

**Sensitivity** (derived, first order):
- **Standoff:** about −11% per mm. Beyond 1.2 mm, port vignetting is added, which is non-linear.
- **Tilt about the port centre:** cos(45 ± θ) gives ±1.75% per degree per LED. Each band is driven by one LED, so opposite LEDs do not cancel.
- **Tilt pivoting on the lip edge (r 10.5):** this also lifts the port centre about 0.18 mm per degree, roughly −2% per degree more. Net is about 2–4% per degree per channel.
- **Patch margin:** the spot needs the port centre within about 40/2 − 2.8 ≈ 17 mm of the patch centre (ASM 40 mm patch).
- Seating error of a few percent fits tilt. **The observed 0.1×–1.1× swings and the white reading at 7% do not fit tilt.** They fit the port sitting over the black gap or a neighbouring patch, or a gross lift (inference).
- An adapter must keep the sample at z −1.2 exactly, as the lip sets it. Moving it to z 0 needs the lip removed or crushed. Any standoff it adds costs about 11% per mm. It also must not bring anything inside the 45° light cone below the port: r < 4 + h at depth h.

**4. Why the puck rocks** (ranked, inference from the CAD)
1. **It stands on a 21 mm ring under a 79 mm, ~49 mm-tall body.**
   - The CAD check "foot catches tilt at 0.67°" ignores the lip. It levers from the land edge with 0.4 relief.
   - Actually the foot sits 1.6 above the sample (0.4 + 1.2), and the pivot is at r 10.5. That gives free rock of atan(1.6/29.18) = **3.1°, which exceeds the ruled ±2°** (MIC + derived). This is a flaw in the model's own check.
2. **The lip was designed to crush (PETG compliance), but the material is matte black PLA (ASM, per the BOM order).** A 0.8 × 1.2 ring loaded axially barely compresses, so the port land never becomes the stop.
3. **USB-C cable torque at z 38.5 on one side (−X)** acts on a 10.5 mm lever, so it biases the tilt toward one side.
4. **The lip tip is the last top layers of a rim-down print.** Seam blobs or stringing on a 0.8 wall make it a non-flat ring. The face is a bridged top skin and can pillow.
5. **The chart's sleeve or card bowing** (ASM). A 21 mm ring will find any curvature.

Elephant foot is not a face cause, because the face is the top of the print. It would only matter on the base foot, and that foot is 1.6 mm clear.