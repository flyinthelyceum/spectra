# The case

What holds the head in a hand. Nothing here is designed yet; this is the research
the design should start from, three massing studies drawn around the real parts,
and the order to do the CAD and rendering in.

    .venv/bin/python -m spectra.cad.case                           # sizes and checks
    .venv/bin/python -m spectra.cad.viewer --cases --out export/cases.html

## What the market already settled

Every handheld contact colorimeter solves the same problem: a flat port pressed
square onto a sample, a light seal, a calibration standard that travels with it.
They make three different bets on form.

| Device | Form | Size | Geometry, sensor | Calibration | What to take from it |
|---|---|---|---|---|---|
| [Nix Mini 3][nix] | Cube-ish puck, metal | 40 × 40 × 25 mm | 31-channel sensor, 2 white LEDs, 13 mm samples | Separate tile | How small a puck can get when the head is small |
| [Nix Spectro 2][nix] | Puck, metal | 60 × 60 × 45 mm | 31 ch, 8 LEDs incl. violet and UV; 5 mm or 2 mm aperture | Ceramic tile | The closest size to this head. Aperture swaps by jig |
| [Datacolor ColorReader Spectro][dc] | Torch / pen | 30 dia × 105 mm | **8-channel, 45/0**, 6 mm aperture | Compact tile | The nearest thing on the market to this instrument. Held like a marker |
| [Variable Spectro 1][var] | Puck with a phone app | — | d/0, 8 mm aperture | Tile | Same port size as ours |
| [X-Rite ColorMunki][munki] | Palm body with a rotating dial | — | Spectro | **Tile built in**: turn the dial to a calibration position | Standards that cannot be left at home |
| [Konica Minolta CM-17d][km17] | Vertical grip, one hand | — | Lab spectro, camera viewfinder | **Cradle holds the zero box and the white cap** | A dock that is also the calibration ritual |

Two findings from that table carry weight here.

**The ColorReader Spectro is the reference, not the Nix.** It is an 8-channel
45/0 instrument with a small port, which is exactly Stage 1. It is a torch because
a 45/0 ring is round and axial, and everything else can line up behind it.

**The good devices carry their standards.** `OPTICAL_HEAD.md` rules dark, black
and white before every session. A case that parks on the PTFE tile when it is put
down, and has the light trap as its second station, makes that ritual the default
rather than a chore. The CM-17d cradle and the ColorMunki dial are two versions of
the same idea. This is the strongest single design idea in the research and it
applies to any of the three forms.

## Three massing studies

`spectra/cad/case.py` draws each as a hollow shell around the real head (44.5 mm
dia × 24 mm plus the lip), the real detector stack, and the ESP32-S3 DevKitC-1 and
SSD1306 from the components library. The shell is massing, not a part: no split
line, no fasteners, no bosses. Sizes are what the parts force.

| Concept | Overall, mm | Reference | Held |
|---|---|---|---|
| `puck` | 74.5 dia × 64.5 | Nix Spectro 2, 60 × 60 × 45 | Fingertip on top, load straight down the axis |
| `torch` | 51.3 dia × 103.6 | ColorReader, 30 dia × 105 | Like a fat marker |
| `palm` | 122.5 × 51.3 × 38.9 | i1Pro / ColorMunki | Palm on the body, broad foot coplanar with the port |

What the models show that a sketch would not:

- **The DevKitC-1, not the head, sets the puck.** It is 62.74 mm long, lies flat,
  and its diagonal makes the puck 74.5 mm across against the head's 44.5. A
  thumb-sized controller board would bring the puck down near the Nix Spectro 2.
  That is a board choice, not a CAD problem, and it is an order, so it waits for
  the lane.
- **The torch is the head's own diameter.** 51 mm is the head plus clearance and
  wall; both boards stand edge-on inside it. It cannot get thinner than the LED
  ring, so it is fatter than the ColorReader by the ring.
- **The palm is the only one with a foot.** Its whole underside is coplanar with
  the port face, so it resists rocking on a sample in a way the other two do not.
  It is also the only one with somewhere natural for a display.
- **There is a battery in every concept and none on the BOM.** The head as
  specified is tethered by USB. A handheld is a battery decision; the cell is an
  estimate (`CELL_L/W/T`) so the concepts are not flattered by leaving it out.

Rules each concept is checked against, in `case.check()` and `tests/test_cad.py`:
the port face is the stop, so no case geometry goes below z = 0; the case never
touches the head; every board fits inside its shell; the shell is one solid.

## The CAD and rendering order

1. **Massing, done here.** build123d plus the existing three.js viewer. Answers
   size, proportion and fit. Cheap to rerun whenever a part changes.
2. **Pick a form, then detail it.** Split line, how the head is held (above the
   LED plane, never at the port), fasteners with the heat-set inserts already in
   the components library, the USB-C opening, and the tile/trap dock. Chamfers by
   rotated box cutters, not kernel fillets, as in the head.
3. **Hold it before rendering it.** A draft print of the chosen shell in any
   filament answers grip and size better than any render. That is a print, so it
   waits for the lane to reopen.
4. **Photoreal renders, last.** `build123d.export_step` to Fusion or KeyShot,
   or `export_gltf` into Blender with a scripted Cycles scene
   (`blender -b -P render.py`) so a render is rebuilt from the model rather than
   posed by hand. Worth it for a finished form and for showing people; not worth
   it for choosing between forms, where the viewer is faster and honest about
   dimensions.

## The puck, chosen

Jared narrowed it to the puck or the palm on 2026-09-30, and the puck was taken
forward. Three reasons, in order of weight:

1. **The load goes down the optical axis.** A fingertip on top presses the port
   land flat. A palm pressed on its body loads the head off-centre and tips the
   port, which is the one error 45/0 exists to keep out. The first number the
   roadmap asks for is lift-and-replace repeatability under 0.5 ΔE00; seating is
   that number.
2. **It works on anything the lip covers.** The palm's long foot overhangs a
   small or thick sample and rocks on its edge.
3. **A round body parks on a round dock**, which is where the tile and the trap
   belong.

What the palm had that the puck gives up: a natural place for a display, and a
long foot on big flat cards. A 30 mm SSD1306 would fit on the puck's lid later.

### Two things the concepts got wrong

- **The antenna.** The concept puck sized itself to the DevKitC-1's PCB and left
  out the 6.3 mm antenna overhang. With it, and with the USB edge pulled to the
  wall so a cable reaches, the smallest circle is 74.6 mm inside, not 69.7.
- **The LED leads.** The bores climb at 45 degrees and break out of the head's
  wall from z = 20 up to just under its top rim, so the leads come out beneath
  whatever sits on the rim. The torch and palm concepts left 1 mm around the
  head, which is no room at all. The plain detector plate sat on them too, and
  is now notched at every LED (`head.lead_keepouts()`).

### Puck v1

    .venv/bin/python -m spectra.cad.puck             # checks and sizes
    .venv/bin/python -m spectra.cad.puck --export    # STEP + STL, print-oriented
    .venv/bin/python -m spectra.cad.viewer --puck    # assembled and exploded

79.4 mm across and 44.8 mm tall above the port face: a hockey puck with a lid.
Four printed parts plus the head, and seven screws.

| Part | Prints | Carries |
|---|---|---|
| Head | Port face down, as before | Now three M2x4 inserts in its top rim, midway between LEDs. Located by the plate's spigot, not the screws |
| `puck_base` | Foot down | The body: floor ring, a collar guiding the head, one wall from the foot to the rim with a step the lid lands on and a hidden key notch, the one-plug USB-C opening, four posts with locating spigots that the screws pass up through, counterbores for the screw heads in the foot |
| `puck_plate` | Upside down | The detector plate plus four ears, notched for the LED leads. A spigot ring underneath drops into the head's cavity and keys between two of its webs |
| `puck_tray` | Upside down | Holds a bare DevKitC-1 (no headers) on four corner pads inside L-shaped fences. The board has no mounting holes; the long edges stay open underneath for soldering wires to the header pads |
| `puck_lid` | Upside down | A flat disc landing on the rim's step, 0.5 mm proud of the rim, with one hidden key under its edge. Bosses with M3x6 inserts hang down to the tray on crush ribs; four pegs hold the board. Nothing passes through the top |

**The load path.** Four M3x35 screws each run up from the foot through a post and its spigot,
the plate ear and the tray standoff into an insert in the lid's boss. A finger on the lid presses the plate onto the
head's rim and the head onto the sample. The base hangs from the ears and
reaches the sample nowhere: its foot stands 0.4 mm above the port face, so the
port land is the only stop, and the foot touches down if the puck tilts 0.67°,
inside the ruled ±2°.

**The three changes from the red team** (Jared chose all three on 2026-10-01,
in the dock thread; reasoning in `red-team.md` in the project files):

- **Screws from below.** The heads sit in counterbores in the foot, where nobody
  sees them, and the top is an unbroken disc. Same screws, same load path.
- **Seam at the rim.** The body is one wall from foot to rim and the lid is a flat
  disc in the rim's rebate, so the only line on the outside is the lid's edge.
- **One-plug USB opening**, 12.5 × 7.5 mm, at the native USB-C receptacle only,
  instead of 25.9 mm across both. Which receptacle is native is `NATIVE_USB_SIDE`,
  owed a look at the silkscreen. Plugging into the board's own receptacle breaks
  the house rule of panel-mount bulkheads, on purpose: the library's one USB-C
  bulkhead, the PENGLIN coupler, needs a 21.9 mm hole and stands 29.9 mm into the
  case, and there is no room for it.

**Fasteners fasten; they do not index.** Jared's rule, 2026-10-01: every joint
aligns by its own geometry, and the screws only clamp. Everything is located
from the base:

| Joint | Located by | Play |
|---|---|---|
| Lid on body | The rim's rebate centres it, one key under its edge (opposite the USB opening, invisible from outside) clocks it, and it lands on the rim's step, so one printed part sets its height | 0.15 radial, 0.1 at the key |
| Plate and tray on the posts | A tube rising from each post through the plate's ear and 2 mm into the tray's standoff | 0.1 |
| Head under the plate | A spigot ring under the plate, broken by the head's three webs, one arc tight between two of them | 0.1 |
| Board in the tray | The corner fences, as before | 0.3 |

Every M3 hole is now 3.6 mm and every M2 hole 2.6 mm, wider than the joint's
play at that screw, and `check()` proves it. The lid lands 0.5 mm proud of the
rim (Jared chose "Proud 0.5"): a deliberate reveal that hides the small
difference between the rim's height and the lid's thickness. Because the lid
now lands on the rim, its bosses would fight the rim through the stack of four
prints; three crush ribs under each boss, printed 0.3 mm into the tray, let the
stack be 0.3 mm out either way and still clamp. The collar's clearance went to
0.5 mm so it only ever guides.

**Seal the LED backs** with black heat-shrink or black silicone before the head
goes in. The bores open into the case and the USB opening lets room light in, so
an unsealed clear LED passes it into the head. `OPTICAL_HEAD.md` now rules it.

**Assemble it upside down.** With the screws coming from below, the stack builds
into the lid: lid face down on the bench, the board on its pegs, then the tray,
then the plate with the head on it, then the base lowered over everything, and
the four screws driven straight down. Built right way up, the stack is loose until
it is turned over.

**Firmware must leave the native USB port alone.** The BOOT and RESET buttons are
now under an unbroken lid, four screws away. esptool resets the ESP32-S3 into
download mode over its built-in USB-Serial-JTAG without a button, but only while
the firmware does not take the port over. So the host link uses USB-Serial-JTAG
and never TinyUSB; otherwise every reflash means opening the case.

`puck.check()` asserts all of that, plus: every part one solid, nothing within
the LED lead keepouts, no part intersecting another or a board, the collar below
the LED breakout, and a USB-C plug able to reach the receptacle. `tests/test_cad.py`
holds it.

**Designed for a bare board.** Jared has DevKitC-1s with and without headers
and asked for the best case, which is without: soldered headers would stand
about 8.5 mm below the board and push the lid up by 3.2 mm, and the tray would
have to hold the board by its header plastic. A headered board does not fit v1.

**Resting on estimates.** The components library has the DevKitC-1's outline
and nothing standing on it. Owed from one caliper session on a bare board: the
tallest part on top (`ESP_ABOVE`, sets the lid height), the USB-C receptacle
centre height and footprint (sets the opening), and the parts-free strip at
each short end (`CORNER_FREE`, where the pads and pegs grip).

## Not decided

The controller board: a thumb-sized one would bring the puck toward the Nix
Spectro 2's 60 mm, and is an order, so it waits for the lane. The battery, and
whether there is one. The dock for the tile and trap. Chamfers and the lid's
finish, which are cosmetic and come after the first print is held.

[nix]: https://www.nixsensor.com/color-sensor-comparison/
[dc]: https://www.datacolor.com/business-solutions/product/colorreader-spectro/
[var]: https://variableinc.com/product/spectro-1-professional-color-measurement/
[munki]: https://www.northlight-images.co.uk/x-rite-colormunki-photo-review/
[km17]: https://fineeng.eu/konica-minolta-to-launch-the-cm-17d-a-vertical-portable-spectrophotometer-for-high-accuracy-colour-measurement-in-any-situation/
