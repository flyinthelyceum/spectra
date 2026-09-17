# pigment

Measured spectral reflectance of artists' pigments, and the model that says what
they do in a mixture.

A colour wheel tells you where a paint sits. It does not tell you what happens
when you mix it, and that is the only question worth an instrument. A saturated
pigment loses chroma in a mixture far faster than intuition predicts, the loss is
not symmetric — cadmium red into phthalo green does not travel the same road as
phthalo green into cadmium red — and which pairs stay clean is a spectral fact
about those two pigments that is invisible in the tube.

This repo holds three things, in order of how long they last:

1. **The model.** Kubelka-Munk over reflectance curves: absorption and scattering
   separated, mixtures predicted before any paint is touched, and a palette's
   reachable colours computed as a shape with holes in it. Pure standard library,
   in `pigment/`. Built and tested. Needs no hardware.
2. **The library.** Measured curves for real tubes, indexed by pigment number
   (PB15:3, PY74, PR108) rather than by whatever the maker printed on the label.
   Not started; it needs the instrument.
3. **The instrument.** A printed 45/0 optical head with a detector on a module
   plate, so the cheap sensor and the good one see the same geometry and the same
   reference tiles. Specified, not built. See `docs/ROADMAP.md`.

## Why this repo exists separately

It is `components` for colour. [`flyinthelyceum/components`](https://github.com/flyinthelyceum/components)
is the one-writer public repo of measured part dimensions, where every number
carries a provenance line and no project ever types a caliper reading of its own.
The same discipline fits a pigment: one writer, a provenance line on every curve,
consumers that import rather than restate.

## Start here

```sh
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/ -q
```

That is the verify command. It runs in well under a second and needs nothing
installed beyond pytest.

| Path | What it is |
|---|---|
| `pigment/km.py` | Kubelka-Munk, Saunderson, the drawdown solve, mixing. The prize. |
| `docs/CHARTER.md` | The one question the instrument answers, and the two it does not. |
| `docs/DECISIONS.md` | Every ruling so far, dated, one line of why each. |
| `docs/ROADMAP.md` | The stages, and the single number each one has to produce. |
| `docs/OPTICAL_HEAD.md` | 45/0 geometry, the reference tiles, the calibration chain. |
| `hardware/BOM.md` | Stock-level quantities. Not a wiring diagram. |
| `process/BENCH_LOG.md` | What actually happened at the bench. The human is the test runner. |

## Where the colour maths lives

The CIE conversions, the CIEDE2000 metric and the scanner profiling workflow were
built first, in [`flyinthelyceum/grow-lab`](https://github.com/flyinthelyceum/grow-lab)
under `tools/color/` and `docs/COLOUR_MEASUREMENT` — see that repo's
`docs/COLOR_MEASUREMENT.md`. They do not belong to a grow lab and they are the
floor this repo stands on, so moving them here is stage 0: `specs/2026-09-17-colorimetry-extraction.md`.
Until that lands, nothing here converts a curve to Lab, and nothing here should
copy code out of grow-lab to pretend otherwise.
