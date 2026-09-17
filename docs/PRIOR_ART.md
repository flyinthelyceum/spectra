# Prior art

Jared has kept a science-based colour library on Drive since 2021 — 26 texts from
1868 to 2016, plus an annotated bibliography he wrote himself. It was read against
this repo's charter on 2026-09-17. This file is what came back that changes
something here.

**Provenance, stated plainly.** The annotated bibliography was read directly. The
26 sources were read by four subagents working from the PDFs, each instructed to
mark VERIFIED (read it, with a page) or INFERRED. Page citations below are theirs
and have not been independently re-checked against the PDFs. Treat a page number
here as a pointer to go look, not as a quotation this repo vouches for. Where two
independent readers agreed, that is noted, because it is worth more.

Folder: `Color Nerd Library` on Drive. Everything in it is public domain or made
free by the author.

---

## The finding that matters most

**Jared wrote this project's thesis in his own bibliography, years ago.** On
[artistpigments.org](https://artistpigments.org/), a database of colorimetric
readings of commercial paints with a Kubelka-Munk mixing tool:

> "which gives a generally good idea, but **does not, in my opinion, adequately
> account for the effects of pigment transparency/opacity**"

That sentence is the reason `spectra/km.py` has `solve_ks_sx` and a black/white
drawdown rather than only the opaque form. The critique came first; the code is
the answer to it. Nobody connected the two until now.

It is corroborated from an unexpected direction. Okumura 2005 — the closest thing
to prior art for this entire repo — ran into exactly that wall and did not have
the fix:

- His pipeline is the **opaque-limit** K-M equation throughout. He states the
  general two-flux equation and then declines to use it, because "paint
  researchers sometimes meet difficulty in measuring the thickness of an actual
  paint layer" (p.8).
- Several pigments — Hansa Yellow Opaque, the phthalos — **stayed translucent at
  the standard 10 mil drawdown**, forcing uncontrolled thicker films (p.51).
- He names this as the cause of his worst results in the conclusions (p.107).

Spectra's two-flux solve over a known black/white ground does not need the opaque
assumption at all. **This is the strongest available argument for prioritising
stage 1d**, and it came from a 2005 thesis and a bibliography note, not from us.

---

## The single most relevant source

**Okumura 2005, *Developing a Spectral and Colorimetric Database of Artist Paint
Materials*.** RIT M.S. thesis, 191 pages, Center for Imaging Science, advisor Roy
S. Berns. Native digital text, not a scan.

It is prior art for close to the whole of this repo, and it should be read before
stage 1 hardware is ordered. What it gives us:

| Thing | Value | Bearing |
|---|---|---|
| Saunderson constants | k1 ≈ 0.03–0.04, k2 = 0.6, fitted per pigment (p.53) | **Empirical provenance for `km.py`'s defaults**, which were chosen from general literature. Carbon Black is the outlier at k1=0, k2=0.4 |
| Two- vs one-constant K-M | two-constant mean ΔE00 < 1.0 for all 13 paints; one-constant 1.18–4.83, max 20.87 (Table V, p.53) | Justifies `mix_two_constant` as the default rather than the convenience |
| Mixture *prediction* error | mean ΔE00 2.21, max 8.48 over 27 secondary mixtures, worst blue+yellow→green (Table X, p.70) | **The number stage 1d should be judged against.** Fitting a ladder to itself gives 0.11–0.51; predicting a mixture is an order worse |
| Wavelength grid | 360–750 nm, 10 nm, 40 bands | What this field considers normal resolution |
| Drawdown practice | LENETA opacity chart, 10 mil (254 µm) gap, 6 cm/s, ASTM D2805 | A protocol to copy rather than invent. Belongs in the BOM |
| Geometry recommendation | "using the 45/0 geometry … will be the best way for the Kubelka-Munk solution" (p.15–16) | Independent support for our head |
| Geometry actually used | integrating sphere, diff/8°, SPIN and SPEX | His dataset is **not** directly comparable to ours |
| Cross-geometry fudge | "+3% flat spectral reflectance" to simulate diff/0 SPIN from 45/0 (p.166) | Needed if we ever compare our readings to his |
| White reference | PTFE | Same as ours |
| Record schema | raw `{header, label, wave, data}` kept **separate** from fitted `{colKandS, whKandS, K1andK2, de00, RMS}` (Tables C-I, C-III) | **He independently arrived at our measurement-layer / model-layer split.** Convergent evidence the architecture is right |
| Identity fields | Paint Name, **C.I. Name** (e.g. "PY 74"), Pigment Name | See the schema change below |
| Sample prep | palette-knife SOP from GOLDEN's own staff (Appendix G) | Adoptable when `kind: paint` gets a prep protocol |
| Out of scope for him too | fluorescent, metallic, pearlescent | Not a gap unique to us |

His Chapter 6 (gamut rendering) and much of Chapter 7 (gloss) are display-gamut
work — the thing our charter excludes. Even the closest prior art treats that as
separate, later work.

---

## What the library changes about this repo

### 1. A `paint` sample needs a Colour Index code, not a product name

Hiler 1942, p.5–6: *"Yellow ochre is not yellow at all except in name … an
accidentally prominent unstandardized pigment which may be any one of a dozen or
more dirty grayed down oranges."* Bradley 1890, p.70, independently: names like
vermilion and carmine are scientifically worthless because "they all depend on the
process of manufacture and the mediums with which they are mixed."

Two sources fifty years apart, saying a product name does not identify a pigment.
Okumura's schema already carries the fix: a **C.I. generic name** (PB29, PY74)
alongside the marketing name. `artiscreation.com`, in Jared's own bibliography, is
the lookup. `docs/MEASUREMENT.md` has been updated.

### 2. Geometry and illuminant are required metadata, and have been since 1950

Judd 1950 (NBS Circular 478), p.48–49: a reported colour measurement must state
the illuminant, and "the manner of illumination and viewing must also be included
in the report."

`MEASUREMENT.md` already requires both. That is now a 75-year-old standard
requirement rather than our preference, and should be cited as such.

### 3. 45/0 is independently validated across 55 years

Judd 1950, p.5–6: *"The angular conditions recommended for the colorimetry of
opaque specimens are that the light shall strike the specimen at 45° and that the
specimen shall be viewed along the perpendicular to its surface."* Okumura 2005,
p.15–16, names the same geometry as best for K-M. The two do not cite each other
on this point. `docs/OPTICAL_HEAD.md` was reasoned from first principles and
landed on the standard.

### 4. ΔE00 cannot be the acceptance test for pigment identification

Cohen 1995, p.52: matrix R is "symmetrical, order k, rank 3, and idempotent." Any
reflectance curve of k bands splits into a 3-dimensional *fundamental* — everything
human vision transmits — and a (k−3)-dimensional *residual*, or metameric black,
which is physically real and perceptually invisible.

The consequence is sharp and it bites a feature we have not built yet. **A ΔE00
comparison is by construction blind to the residual.** Two chemically different
mixtures can match to ΔE00 < 0.5 and still have visibly different curves. So:

- For colour *reproduction*, ΔE00 is the right measure.
- For pigment *identification*, comparison must happen on the raw curve. Never
  after a round trip through XYZ or Lab.

This is also the cleanest theoretical statement of why the charter stores the
curve rather than a Lab triple. If reproducing human appearance were the only goal,
three numbers would provably suffice.

### 5. A reading is a point in time, not a fact about a pigment

Two independent routes to the same conclusion:

- **Fading.** Hiler 1942 organises around lightfastness; his period benchmark is
  "the permanence of a good Rose Madder" as the minimum for calling a colour
  lightfast (p.51, citing Doerner). A fugitive pigment's curve changes.
- **Coating.** Okumura found GOLDEN's MSA gloss varnish contains a UV stabiliser
  producing a measurable absorption increase at 360–450 nm between varnished and
  unvarnished specimens of the same paint (p.94). The pigment did not change; the
  reading did.

Open question, not yet ruled: does re-measuring the same physical sample over time
belong in the model as a series, or is each reading a standalone fact? The `date`
field already exists. Nothing consumes it as a series.

---

## The adversarial finding

**Nothing in the library validates eight channels.** Three sources converge on
roughly 10 nm as the working resolution for pigment-level colorimetry: Okumura's
40-band grid, Judd's 5–20 nm summation guidance, and the ~31-passband convention
noted around Cohen. Okumura's own pigment discrimination relies on resolving
Cobalt Blue's 430 nm peak from Cerulean's at 460 — a 30 nm gap. Stage 1 has gaps
up to 55 nm and sees nothing past 660 nm.

Judd is blunter still about the closest period analogue. Photoelectric three-filter
colorimeters showed chromaticity errors "frequently larger than 0.02 in x or y,"
which he says "limits the usefulness of these filters to the measurement of colour
differences between nonmetameric or slightly metameric pairs" (p.22–23).

**This confirms `OPTICAL_HEAD.md` rather than contradicting it.** That document
already says eight broad channels cannot carry K/S for high-chroma pigments and
that sequential narrowband illumination "converts a coarse instrument into a
better coarse instrument." The library says the same thing from three directions.

The honest framing to carry forward: **Stage 1 is a differential instrument.** It
is trustworthy for repeatability, for tracking one sample over time, and for
telling apart pigments that are not near-metameric. Stage 2 is the one that
reaches the resolution this literature treats as baseline. That is an argument for
building Stage 1 — you cannot measure the error bars without it — and against
publishing Stage 1 numbers as pigment identifications.

One partial counterweight: Küppers 1978, p.142–143, argues three-filter
tristimulus devices are inaccurate *relative to scanning spectral photometers*,
which is an argument for more bands over three, not for eight over forty.

---

## Historical claims worth pointing the instrument at

These are the falsifiable ones. Every author below made a claim about specific,
still-purchasable pigments, and none had an instrument as good as the one in this
repo's roadmap.

**Rood 1879, *Modern Chromatics*.** The strongest. A working experimental
physicist who published numbers.

- Luminosity by rotating-disc photometry, white = 100 (p.47–48): English
  Vermilion 25.7, Pale chrome-yellow 80.3, Pale emerald-green 48.6, Cobalt-blue
  35.4, Ultramarine 7.6. He corrected for his black disc reflecting 5.2% rather
  than zero.
- Dominant wavelength by Rutherfurd six-prism spectroscope (p.51): Vermilion 6290 Å,
  Red lead 6061, Pale chrome-yellow 5820, Emerald-green 5234, Prussian-blue 4899,
  Cobalt-blue 4790, genuine Ultramarine 4735, artificial Ultramarine 4472.
- A quantified mixture claim (p.152): "Chrome-yellow (the pale variety) and
  ultramarine-blue … give an excellent white, and emerald-green and vermilion give
  a yellowish or orange tint."

**Brown 1913, *The Painter's Palette*.** A 24-pigment table (p.22) giving each a
hue degree 0–360 and an intensity percentage, explicitly describing "their
performance in opaque mixture, on the average" rather than their appearance — e.g.
Cadmium 330–360° at 100%, English Vermilion 265° at 85%, Ivory Black 60° at 18%.
Derived on a self-built Maxwell-disc rig whose value scale he published as
percentages (4, 9½, 16½, 25½, 35¾, 48, 62¾, 78¾).

**Benson 1868.** The densest set of unmeasured, falsifiable mixture claims:
"Vermilion and Emerald Green compound an Olive-green … Emerald Green and Cobalt
Blue, a dark Seagreen … Cobalt Blue and Vermilion, a Purple" (p.28), plus three
claimed neutral-grey pairs (p.29) and a 27-entry palette vetted for permanence
(p.69). He measured nothing.

**Bradley 1890, *Color in the School-Room* — the ancestor of the Color-aid set.**
Milton Bradley manufactured the coloured papers, with J.H. Pilsbury as his
scientist, competing against Prang for the same school market. Two things matter:

- **A proportional notation**: `WR5743` means 57 parts white to 43 parts standard
  red, "as determined by the Maxwell disks when rotated on the wheel" (p.65–66).
  A physical mixture spec, not a name.
- **Two testable identity claims** (p.81): his orange is "a nearer match to the
  pure orange of the spectrum than can possibly be made from any red and yellow
  pigments," and his blue is "pure ultramarine, which is recognized as the nearest
  possible match to the spectrum blue that can be found in pigments."

See `docs/COLOR_AID.md`. Bradley is why measuring that 314-swatch set is a
continuation of something rather than a novelty.

**Maxwell-Evans 1961** (*J. Photographic Science* 9:243–246). Actual
spectrophotometry, and a general claim we could test this year: Maxwell's 1861 red
cloth "had a secondary reflectance band in the ultra-violet as do most red cloths
available today," from "a systematic study of a considerable number of red-dyed
materials." Our 405 nm LED is the relevant channel and `OPTICAL_HEAD.md` already
puts it there to catch optical brighteners. Whether the AS7341 has usable response
that far down needs checking before this is treated as in range.

**Munsell 1905.** Pigment pairs balanced on a Maxwell disc to read neutral, with
the balance recorded numerically — Venetian red against viridian at 3¾ parts to 6
(p.77–79). He also built and sold a photometer ($50, patented 1901, used at MIT,
p.134). The historical ancestor of the black/white drawdown solve: two materials,
mixed in known proportion, read against a reference.

---

## What is in the library and is not relevant

Saying so plainly, so nobody reads them twice hoping.

- **Joblove & Greenberg 1978** (HSL/HSV) and **Smith & Lyons 1996** (HWB) are
  display colour-picker maths. Smith & Lyons disqualify themselves in their own
  text (p.5): these models "are not perception-based … not to be confused with
  such systems as Munsell, CIE, and Ostwald."
- **Nemcsics, Coloroid** is a colour-*harmony* notation built from 70,000
  observers' aesthetic judgements. Precisely the category the charter excludes.
- **Allen 1937** is harmony pedagogy with hand-coloured cardboard wheels. No
  pigments named, no measurement.
- **Carry van Biema summary (2003)** is biography, not doctrine.
- **Patrick 1915** is a Munsell curriculum article; useful only as evidence of how
  far Munsell's physical standard had spread.
- **Kerr 2005** is worth keeping open as a formula reference for the XYZ→Lab/Luv
  chain, and nothing else.
- **Martínez-Verdú 2007** and **Service 2016** bound what surface colours can
  theoretically and actually reach. Useful background; see the note below.

### On gamut, since it bears on the Color-aid question

Service 2016 defines Pointer's gamut as an empirical envelope over ~4,000 real
surface colours, sitting well inside the theoretical MacAdam limit everywhere
except red and yellow at low-to-middle lightness (p.4). The practical consequence:
**measuring the 314 Color-aid swatches will not produce new gamut science** — that
general question is answered and published. It will characterise that specific set,
which is unmeasured. Worth knowing before the effort is framed as a discovery.

Pointer's Table 2, via Service, is the reference data if a physical-plausibility
check on K-M predictions is ever wanted: a predicted mixture outside Pointer's
gamut is probably a bad prediction rather than an exotic pigment.

---

## Not in the library, but in the bibliography, and worth having

From Jared's own online-resources list:

- **artistpigments.org** — colorimetric readings of commercial paints plus a K-M
  mixing tool. The closest live comparable to what this repo would produce, and
  the thing whose opacity handling he criticised. Read before designing the store.
- **artiscreation.com (The Color of Art)** — the Colour Index lookup. The
  authority behind the C.I. field described above.
- **Munsell Color Science Lab educational resources** (RIT) — CIE and Pointer
  datasets.
- **Mixbox** (Sochorová & Jamriška) — a K-M pigment-mixing simulator in OKLab.
  Prior art for the model layer specifically.
