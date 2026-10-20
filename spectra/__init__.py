"""Measured reflectance of physical samples, and the models over them.

`km` is the first model and depends on nothing. The colour maths under it moved
here from grow-lab's `tools/color/` at stage 0: `colorimetry` (XYZ/Lab, sRGB,
Bradford adaptation, ΔE00 and ΔE76), `cgats`, `fit_profile`, `check_profile`, all
standard library only, and `sample_chart`, which needs Pillow (the `capture` extra).
The three command-line modules are run as `python -m spectra.<name>` and are not
imported here, so running one does not first import it as a package attribute.
Capture and library modules arrive with the instrument; see docs/ROADMAP.md for what
is built and what is not.
"""

from . import km

__all__ = ["km"]
