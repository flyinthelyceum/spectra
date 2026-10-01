# The calibration dock

Where the puck lives when it is not reading a sample, and where its two standards
live. One printed part: two cups side by side, a PTFE white tile in one and the
light trap in the other. The puck parks on the white.

    .venv/bin/python -m spectra.cad.dock             # checks and sizes
    .venv/bin/python -m spectra.cad.dock --export    # STEP + STL, print-oriented
    .venv/bin/python -m spectra.cad.viewer --dock    # the puck on each station

167.9 × 85.2 × 48 mm, sized entirely from the puck and the standards. Nothing has
been printed. The model is `spectra/cad/dock.py`; this file is why it is shaped the
way it is.

## What it is for

`OPTICAL_HEAD.md` rules dark, black and white before every session, and no sample
reading kept without them. A calibration that needs the tile fetched from a drawer
is a calibration that stops being done, which the BOM already says about the
detector. The dock makes the ritual the default: when the puck is not on a sample
it is on one of its standards, and the session starts by lifting it one cup over.

    dark    puck on the trap, LEDs off      the detector's floor, in real darkness
    black   puck on the trap, LEDs on       the head's stray light
    white   puck on the tile, LEDs on       full scale
    ...     samples
    park    puck back on the tile

## What the market already settled

Every serious handheld treats its white standard as part of the instrument, not an
accessory, and keeps it covered.

| Device | Where the standards live | Taken from it |
|---|---|---|
| [X-Rite i1Pro][i1pro] | A base plate with the white tile at its tip, serial-paired to the meter. The meter is also initialised on it, because the base blocks light from the aperture | The tile and the instrument are one unit. Resting on the standard doubles as the dark |
| [Konica Minolta CM-700d][cm700d] | White cap CM-A177, paired by number; zero-calibration box CM-A182 | "Invert it so that the White Calibration Plate is not exposed to ambient light or dust"; the plate "may become discolored if left exposed to light". Calibrate at the temperature you measure at |
| [Konica Minolta CM-17d][km17] | A cradle holding the zero box and the white cap | A dock that is the calibration ritual. The direct model for this one |
| [X-Rite ColorMunki][munki] | Tile inside a rotating dial | Standards that cannot be left behind, at the cost of a moving part at the port |

Three things carried over. **Pair the tile to the head** and never swap it: its
reading *is* the white, and it is what makes next week's curve comparable to this
week's. **Keep it covered**, which parking the puck on it does for free. **The
dark belongs somewhere dark**; the CM-700d's instructions have you point the port
at nothing for a metre, and a cup with a light trap in it is better than that.

What was not carried over is the dial. The first version of this file argued
that a rotating standard would put its height on a detent. That was wrong, and
the red team on 2026-09-30 caught it: a turntable's height is set by the disc
resting on its floor, and the detent only sets where it stops sideways, which
the tile has 1.85 mm of margin for. The real reason is plainer. A dial is a
mechanism, two more parts and a bearing surface, bought to save one lift of the
puck. Two fixed cups have nothing to wear.

## The PTFE tile, and one thing to know before buying it

Labsphere, who make Spectralon, [recommend 7 mm as the minimum thickness for
optimum reflectance][spectralon-design]: thinner sections are translucent, so a 3 mm
disc partly reads whatever is behind it. `params.TILE_T` is an estimate of 3 mm.

That changes two things. The tile's backing becomes part of the reference, so the
pocket floor behind it is plain black PETG, never glued, never changed once the
tile has been calibrated against. And if there is a choice at purchase, **buy the
thickest disc offered, 7 mm or more.** The dock follows TILE_T, so the only cost is
reprinting it.

Handling, from [Labsphere's care guide][spectralon-care]: clean gloves, never a
finger on the face; kept covered except in use; dust blown off with clean air, and
real soiling sanded off under running water with 220–240 grit waterproof paper
until the surface is hydrophobic. Sanding means the tile comes out, so it sits in
a clearance pocket with a notch on one side for a fingernail under its edge,
rather than pressed in and pried out.

## Four decisions the shape follows from

**1. The lip gets nowhere to land.** On a sample, a finger crushes the lip until
the port face lands. In the dock nobody presses, and the puck's weight alone may
not crush it; a lip standing on the dock would hold the port face off the tile, a
standoff error in the one reading that cannot have one. So each station's floor is
sunk `LIP_PROUD + LIP_CLEAR` (2.0 mm) below the stop plane and the lip hangs in
air. The lip was only ever a light seal, and it sits outside the port face, so
leaving it uncrushed changes nothing optical.

**2. The cup is the light seal instead.** The puck drops into a cup 0.5 mm larger
in radius and 16 mm deep. Room light has to go down that gap, across under the
puck and up past the hanging lip to reach the port, and the head's face is sitting
flat on the tile or the trap's land besides. The rim stays 18.75 mm below the puck's
USB-C opening, so the cable clears it whichever way the puck is turned; there is
no slot and no key, and any rotation seats. With the puck's seam moved to its top
edge, the rim is the only horizontal line on a docked puck, which is why it was
not raised to 24 mm to hide a seam.

**3. One stop per station.** At the white station the tile stands 0.3 mm proud of
its pedestal and is the only thing the head touches. Flush with plastic around it
would be two stops at one height, and the printer would decide which one won. At
the trap station the stop is the trap's own wall, an annulus around the mouth,
the same wall thickness the trap was designed with. The trap *is*
`trap.cavity()`, the one cone in the repo. The standalone printed trap and the
separate tile holder that came before the dock were deleted rather than kept
as two more parts to print and reconcile.

**4. The foot catches a tilt, as it does on a sample.** A ledge under the puck's
foot ring sits 0.2 mm below the stop plane. The foot stands 0.6 mm above it, so it
touches down only if the puck tips, at 1.03°, inside the ruled ±2°. On a sample the
same foot catches at 0.67°.

## What `dock.check()` holds

All fifteen pass and `tests/test_cad.py` holds them. The kernel ones lower the
puck a tenth of a millimetre and confirm nothing of the dock is in the way but the
stop:

- the dock is one solid
- white: the tile is the only stop; trap: the land is the only stop
- the puck seats in either cup without touching it; the tile clears its pocket
- with the puck pushed hard against the cup, the port still sees only PTFE
  (reaches r = 4.5 on a 6.35 tile) and only the trap mouth (r = 5.0)
- the lip clears both pedestals and the well floor; the head's rim cannot reach
  the ledge
- the foot catches a tilt inside ±2° at both stations
- the cup rim clears the USB-C plug; the tile pocket stays inside the body

`test_a_thin_tile_is_caught_by_the_check_not_the_printer` sinks the tile below its
pedestal and confirms the check fails, so the stop check is known to bite.

**Tile thickness window.** The dock holds for a tile from 0.30 mm thinner than
TILE_T (then the pedestal becomes the stop) to 0.56 mm thicker (then the foot's
tilt cap passes 2°). A real tile outside that window is a reprint with TILE_T
updated, not a shim.

## Resting on estimates, and what moves it

- **TILE_T.** The pocket depth, and so the tile's height, is the estimate. Record
  the real thickness through `components measure` when the disc arrives.
- **The puck's remaining board heights.** They move the lid and the USB-C opening, which
  moves the margin over the cup rim (18.75 mm with the headerless board). The cup radius follows the puck's
  outer radius, which the heights do not change.

## Not decided, or not done

- **The cable can tip the puck.** A USB cable pulling sideways at the plug, 38.5 mm
  up, works on a lever about six times longer than the one the puck's weight
  has about the edge of the tile (6.35 mm). That is arithmetic, not a measurement
  of any real cable. The foot catches it inside tolerance, but a tilted white is a worse white
  than a square one. Leave the cable slack over the rim. If that proves fiddly, the
  fix is a cable channel in the dock's back wall or two small magnets pulling the
  puck down, and the magnets would be a change to the puck, which is not this
  file's to make.
- **The puck's weight** is not known until it is printed and populated, so whether
  it seats on the tile without a nudge is a first-print question. Pressing it once
  when docking costs nothing and is the same motion as reading a sample.
- **Firmware.** Nothing reads the calibration automatically when the puck is
  docked; the order above is a procedure. Detecting the dock (a reed switch and a
  magnet, or simply a white reading that matches the last one) is later work.
- **Rubber feet, a label on each cup, cosmetic chamfers.** Not modelled. Feet are a
  bought part and wait for the lane with everything else.
- **Material.** Printed solid it is 559 g of PETG; at a normal infill it is a
  fraction of that, and the mass is welcome, since a heavy dock does not follow the
  puck when it is lifted.

[i1pro]: https://www.portrait.com/resource-center/x-rite-i1pro-and-i1pro-2-guides/
[cm700d]: https://www.konicaminolta.com/instruments/download/instruction_manual/color/pdf/cm-700d_instruction_eng.pdf
[km17]: https://fineeng.eu/konica-minolta-to-launch-the-cm-17d-a-vertical-portable-spectrophotometer-for-high-accuracy-colour-measurement-in-any-situation/
[munki]: https://www.northlight-images.co.uk/x-rite-colormunki-photo-review/
[spectralon-design]: https://www.labsphere.com/wp-content/uploads/2021/09/Spectralon-Design-and-Machining-Guidelines.pdf
[spectralon-care]: https://www.labsphere.com/wp-content/uploads/2021/09/Spectralon-Standards-Care-and-Handling-Guidelines.pdf
