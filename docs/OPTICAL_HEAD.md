# The optical head

45/0, because oil paint is glossy. Illuminate at 45 degrees from the surface
normal, collect along the normal. The specular lobe leaves at 45 degrees on the far
side and misses the detector, so what is measured is the colour of the pigment
rather than a reflection of the LED. This is the single most important mechanical
decision in the build. Get it wrong and every reading of a glossy surface carries a
variable amount of white, and no amount of calibration recovers it.

## The head, as specified for the first print

| Element | Spec | Why |
|---|---|---|
| Sample port | 8 mm aperture, flat, sample pressed against it | Small enough to sit inside a paint-out, large enough to average brushwork |
| Illumination | 45° ± 2°, ring of LEDs, even count | The ring cancels directional texture; one LED at 45° reads brush direction |
| Collection | 0°, baffled tube, aperture smaller than the lit spot | The lit spot must overfill the collected spot, or an alignment shift changes the reading |
| Interior | Matte black, printed, no gloss | Every internal reflection adds an unmeasurable flare term |
| Standoff | Fixed and hard-stopped, no user adjustment | Distance and signal are the same number to a detector; anything adjustable becomes an error source |
| Light seal | Compliant lip at the port | Room light at the port is the largest single error in a home-built head |
| Material | Black PETG, port face down on the bed | The one surface that must seat flat is the one printed against the bed |

Chamfers are cut with rotated box cutters rather than kernel fillets, and each half
carries a kernel test asserting it is one solid. That is the printed-case discipline
already in use elsewhere on this system; nothing new to learn.

## Reference tiles

Two, both measured every session.

- **White.** Sintered PTFE, 10 mm or larger, above 97% diffuse reflectance. The one
  part not worth improvising: barium sulphate paint and printer paper both drift,
  and paper is full of optical brighteners.
- **Black.** A light trap, not a black tile. A printed cone or a stack of razor
  blades reads nearer zero than any black surface, and it is what actually measures
  the head's stray light.

## Calibration chain

Every session starts with three readings, in this order, and no sample reading is
kept without them.

1. **Dark.** All LEDs off, full integration time. The detector's own floor, and it
   moves with temperature.
2. **Black.** The light trap at the port. Dark subtracted, what is left is the
   head's stray light: the flare term that limits how dark a pigment can be read.
3. **White.** The PTFE tile at the port. Full-scale reference for every channel and
   every LED.

Reflectance is `(sample − dark) / (white − dark)`, per channel per LED, with the
black reading kept alongside as the noise floor rather than subtracted twice.

Then, before anything is handed to `spectra.km`: **Saunderson.** The chain above
produces a measured reflectance. Kubelka-Munk operates on internal reflectance. The
step between them is not optional. See `DECISIONS.md`.

## Illumination: one colour at a time

The AS7341 gives eight channels between roughly 415 and 680 nm, plus clear and
near-IR. Eight broad overlapping channels is a coarse spectrum. The trick that
changes the arithmetic is to light the sample with one narrowband LED at a time and
read all eight channels each time: seven LEDs gives 56 numbers per sample rather
than 8, sampling the reflectance curve on a grid rather than through eight fixed
windows. Each LED gets its own integration time, so a dark pigment under a weak LED
is given longer rather than returned as noise.

| Nominal peak | Role |
|---|---|
| 405 nm | Violet. Also excites optical brighteners, which is how they get detected rather than mistaken for blue |
| 450 nm | Royal blue |
| 505 nm | Cyan. The gap most cheap LED sets leave open |
| 530 nm | Green |
| 590 nm | Amber. The yellow region where cheap white LEDs are weakest |
| 625 nm | Red |
| 660 nm | Deep red. The far edge, where phthalos and dioxazines do their most distinctive work |

One white LED stays in the ring as a sanity channel.

This sidesteps two documented AS7341 problems: the supplied calibration matrix can
misread NIR crosstalk on F1 to F8, and ams-osram's own note says colorimetric
results drift cold on warm-white sources. Neither applies when the matrix is not
used at all and raw channel counts are read against a measured LED spectrum.

**The honest limit.** "Measured LED spectrum" is doing work in that sentence that
Stage 1 cannot pay for. See `DECISIONS.md` under Stage 1 curve recovery: with no
spectrometer in the building, the LED emission curves are assumed from datasheet
nominals, so the 56-number grid supports a regularised fit rather than a true
inversion. Lab accuracy is unaffected. Curve shape is softer than the count of
numbers suggests.

## The caveat, stated plainly

Eight broad channels cannot carry K/S for high-chroma pigments, and high-chroma
pigments are the ones that matter here. A saturated modern organic has a reflectance
curve with a very steep edge: near-zero across a wide band, then a sharp rise over
perhaps 30 nm. Where that edge sits and how steep it is determines everything about
how the pigment mixes. Overlapping 20 to 50 nm windows smear it, and two pigments
whose edges differ by 15 nm can produce nearly identical channel readings and wildly
different mixing behaviour. The earths and the cadmiums, with their broad gentle
curves, come through fine.

Sequential narrowband illumination helps materially and does not fix it. Seven LEDs
sample the curve at seven places; a steep edge falling between two of them is still
invisible. It converts a coarse instrument into a better coarse instrument.

So Stage 1's honest scope: Lab measurement, pigment identification, repeatability,
the whole software and calibration chain, and K/S for broad-curve pigments. Not
trustworthy K/S for the saturated organics. That is not a reason to skip Stage 1.
It is the reason the detector is a module.

## Stage 2

The Hamamatsu C12880MA is a fingernail-sized grating spectrometer: about 288 pixels
across 340 to 850 nm, roughly 15 nm optical resolution, analogue video out with a
clocked readout, around $200. What changes is the detector plate, the driver and the
illumination sequence, since a real spectrometer would rather see everything at
once. What does not change is the head, the port, the standoff, the tiles, the
calibration procedure, the storage schema and every pigment already measured.

Three notes before ordering one. The readout is analogue and fussy: a clean clock, a
decent ADC, attention to grounding, and an ESP32 rather than a Pi alone. Wavelength
calibration is per unit, shipped as that device's own polynomial coefficients, not
transferable. And 15 nm is not a lab instrument; it is roughly ten times finer than
eight broad channels and entirely sufficient for Kubelka-Munk on artists' pigments,
which is the job.

Do not order it at the start. Order it when Stage 1's error bars have been measured
and the AS7341 has been shown to be the limit.
