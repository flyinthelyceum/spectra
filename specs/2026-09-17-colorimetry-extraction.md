# Stage 0: move the colour maths out of grow-lab

**Status:** specified, not started. Blocked by the HOLD lane (`docs/DECISIONS.md`).
**Shape:** one branch, one PR per repo, two PRs total. Neither is merged by an agent.

## Why

grow-lab PR #73 (2026-09-16) added a complete, tested colour-measurement workflow:
CIE conversions, a CIEDE2000 asserted against all thirty-four Sharma, Wu and Dalal
test pairs, a CGATS reader, a chart sampler, a scanner profile fitter with honest
cross-validated error, and a scorer. About 1,300 lines with 800 lines of tests.

None of it is about growing plants. Its own `__init__` says so: "Colour-measurement
tooling for the bench. Not part of the station runtime." grow-lab needs it for one
job, sampling the Weston dial face off a scan, and this repo needs all of it as the
floor under everything. Two copies is the failure this system has already had once,
when a cloud session invented a second measurement registry inside a project repo
during the first hour of the `components` library's existence.

This is the same move `components` made out of `fabrication`, one week later and for
the same reason.

## What moves

| From `grow-lab` | To `spectra` |
|---|---|
| `tools/color/colorimetry.py` | `spectra/colorimetry.py` |
| `tools/color/cgats.py` | `spectra/cgats.py` |
| `tools/color/sample_chart.py` | `spectra/sample_chart.py` |
| `tools/color/fit_profile.py` | `spectra/fit_profile.py` |
| `tools/color/check_profile.py` | `spectra/check_profile.py` |
| `tests/unit/test_color.py` | `tests/test_colorimetry.py` |
| `tests/unit/test_color_fit.py` | `tests/test_fit_profile.py` |
| `tools/color/__init__.py` | folded into `spectra/__init__.py` |

`docs/COLOR_MEASUREMENT.md` **stays in grow-lab.** It is a scanner workflow written
for that bench and it reads correctly there. Its command lines change from
`python tools/color/x.py` to `python -m spectra.x`, and its Files table points here.

`MODEL_KIND` in `fit_profile.py` is the string `"growlab-color-model/1"` and is
written into every saved model. Changing it silently invalidates models already on
disk. Keep the old string readable and write the new one; the fitter should accept
both.

## What grow-lab gets back

A dependency, the same way it already takes `components`:

```
spectra @ git+https://github.com/flyinthelyceum/spectra.git@main
```

In an optional `color` extra, not in the base dependency list: the Pi runtime has no
business carrying it. Pillow moves with `sample_chart` into this repo's `capture`
extra and comes out of grow-lab's base list if nothing else there uses it — check
before removing, it is also used elsewhere.

## Done test

- `spectra`: `.venv/bin/python -m pytest tests/ -q` green, including the thirty-four
  Sharma/Wu/Dalal pairs, which must still pass unmodified. If those drift, the metric
  is broken rather than imprecise.
- `grow-lab`: its full suite green with `tools/color/` deleted and the extra installed.
- `grep -r "tools/color" grow-lab` returns only history, not code or live docs.
- Every command line in grow-lab's `docs/COLOR_MEASUREMENT.md` runs as written.
- A fitted model JSON written before the move still loads after it.

## Verify

```sh
# in spectra
.venv/bin/python -m pytest tests/ -q
# in grow-lab
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m spectra.check_profile --help
```

## Not in this spec

The library schema, the capture code, the head CAD, and any use of `km.py` against a
real measurement. Stage 0 moves working code and changes nothing about what it does.
