# spectra — working agreement

Measured reflectance of physical samples, and the models over them. Read
`docs/CHARTER.md`, `docs/DECISIONS.md` and `docs/ROADMAP.md` before doing anything;
they carry rulings whose reasoning is not reconstructible from the code.

**Verify:** `.venv/bin/python -m pytest tests/ -q`. Paste the output in the PR.

## The rules that are not obvious

- **The measurement layer stays general.** A reading is a curve, a date, a
  calibration state and an instrument config. What the sample is made of is an
  optional field set chosen by its kind, never a column in the core. A field only
  one material has, in the core table, is a bug — it is how this repo would quietly
  become an oil-paint pipeline, which it was briefly written as and is not.
  `docs/MEASUREMENT.md`.
- **Kubelka-Munk is one model over the store, not the reason for it.** `km.py`
  depends on nothing and knows nothing about pigments. Keep it that way.
- **Saunderson before Kubelka-Munk, always.** Measured reflectance is not the
  internal reflectance the equations operate on. Skipping it biases K/S in a way
  that grows toward black, which is where the interesting pigments live. Any code
  path that calls `ks_from_reflectance` on a raw instrument reading is a bug.
- **A masstone is not automatically opaque.** Modern organics are transparent. Use
  the black/white drawdown and `solve_ks_sx`, not the opaque form, unless the film
  has been shown to hide.
- **Never type a measured number into this repo.** Physical dimensions go in
  [`flyinthelyceum/components`](https://github.com/flyinthelyceum/components) via
  `python -m components measure`, one writer, and are imported here. Pigment curves
  go in this repo's library with a provenance line, once the library exists. A
  second registry invented inside a project repo has already happened once on this
  system; do not be the second time.
- **The ROADMAP row for saturated organics has no pass threshold on purpose.** It
  is not a test the build can fail. It measures what the cheap detector costs, so a
  $200 purchase is made on evidence. Do not add a threshold to it.
- **Lane: HOLD.** See `docs/DECISIONS.md`. Model work and documentation proceed.
  Hardware, orders and head CAD wait for the reopen trigger.

## Conventions

- Standard library only in `spectra/`. Capture-side dependencies go behind the
  `capture` extra, never in the core.
- Reflectance is 0..1, per wavelength, sequences in wavelength order. Nothing in
  `km.py` knows what those wavelengths are.
- Tests assert properties the maths must hold, not numbers a previous run produced.
  A planted constant only asserts that the code still does what it did.
- Prose in this repo is written to be read by someone who was not here. Say why,
  not just what.

## Standing lines

Open a PR, never merge. Never force-push. Paste the verify output in the PR body.
State what you did not do.
