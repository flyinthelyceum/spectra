"""Measured reflectance of physical samples, and the models over them.

`km` is the first model and depends on nothing. Capture and library modules arrive with
the instrument; see docs/ROADMAP.md for what is built and what is not.
"""

from . import km

__all__ = ["km"]
