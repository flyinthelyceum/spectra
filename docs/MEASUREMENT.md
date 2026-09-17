# The measurement layer

Nothing in this file knows what a sample is made of. That is deliberate and it is the
load-bearing decision in the repo: the head reads reflectance off a surface, and what
the surface happens to be is a fact recorded beside the reading rather than a
different kind of reading.

## What a measurement is

Every reading carries these, and a reading missing any of them is not kept:

| Field | Why |
|---|---|
| Sample id | Stable, this repo's own, never a maker's code alone |
| Curve | Reflectance, or the raw grid it was derived from, with the wavelength basis |
| Date | Materials move. Every reading is dated or it is not a reading. |
| Calibration state | Which dark, black and white cycle it sits under, and the tile's own id |
| Instrument config | Detector, LED set, integration times, firmware or code version |
| Geometry | 45/0 and the port used, so a later head does not silently mix in |

Everything else is a property of the sample, held beside it, optional, and never
assumed present.

## Sample kinds

A kind names which optional fields apply and which models can read the row. It does
not change how the reading was taken.

| Kind | Fields it adds | Model that reads it |
|---|---|---|
| `paint` | **Colour Index name** (PB29, PY74), binder, maker, product name, masstone or drawdown, ground, cure days | Kubelka-Munk |
| `swatch` | Set name, the set's own code, sheet size | Instrument checks, matching |
| `filament` | Material, maker, lot, nozzle temperature, print orientation | Batch drift, matching |
| `coating` | Product, applicator, substrate, coats | Matching, drift |
| `textile`, `print`, `substrate` | Whatever that material actually has | Matching |

Adding a kind is adding a row to this table and a field set. It is not a schema
migration and it must never become one. A kind that needs the core table changed is a
sign the core table has picked up something specific to one material.

## What this makes possible that a paint-only store does not

- The Color-aid 314 set as 314 first-class rows rather than a special case
  (`COLOR_AID.md`). Its ladders still work as an instrument check; that is now a
  property of the set, not the reason it is in the library.
- Filament colour by maker and lot, which nothing else on this system records and
  which varies enough to matter on a multi-part print.
- The 3D Studio Color Doctrine's six Montana colours measured off the physical cans
  and compared against the six hexes the doctrine specifies. Those hexes govern every
  studio artifact, on screen and in print, and whether the paint matches them has
  never been measured.
- Two instruments over the same samples, which is what catches an error neither can
  see alone.

## The rule that keeps it general

**A field that only one material has does not go in the core.

**On `paint`: the Colour Index name is the identity; the product name is not.**
Two sources fifty years apart say the same thing. Hiler 1942: "Yellow ochre is not
yellow at all except in name … may be any one of a dozen or more dirty grayed down
oranges." Bradley 1890: pigment names "all depend on the process of manufacture and
the mediums with which they are mixed." A reading filed under "Winsor & Newton
Yellow Ochre" identifies a purchase, not a pigment. File it under PY43 and keep the
product name alongside. `artiscreation.com` is the lookup. Okumura's 2005 database
carries exactly this pair of fields, which is the third independent arrival at it.
See `docs/PRIOR_ART.md`.

**Geometry and illuminant are not optional, and have not been since 1950.** Judd,
NBS Circular 478, p.48-49: a reported colour measurement must state the illuminant,
and "the manner of illumination and viewing must also be included in the report."
The core fields above already require both. That is a standing requirement of the
field, not a preference of this repo.** If a model needs
something, the model's kind carries it. Kubelka-Munk needs a cure interval; a
Color-aid swatch does not have one and must not carry an empty column for it.
