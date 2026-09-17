"""Measured pigment spectra, and the model that says what they do in a mixture.

`km` is the model and depends on nothing. Capture and library modules arrive with
the instrument; see docs/ROADMAP.md for what is built and what is not.
"""

from . import km

__all__ = ["km"]
