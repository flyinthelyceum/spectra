"""The two reference standards: the light trap's cone and the PTFE white tile.

    python -m spectra.cad.trap

`OPTICAL_HEAD.md` rules that the black reference is a light trap and not a black
tile, because a trap reads nearer zero than any black surface and is what
actually measures the head's stray light. The white is a bought sintered-PTFE
disc.

Both live in the calibration dock (`dock.py`), which presents each at the port
at the same standoff the sample sees. There used to be a standalone printed trap
and a separate tile holder here as well; the dock made both redundant and they
were removed on 2026-09-30 rather than kept as two more parts to print and
reconcile. What remains is what the dock is built from.
"""

from __future__ import annotations

from build123d import Align, Cone, Cylinder, Part, Pos

from . import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def cavity() -> Part:
    """The trap: a deep cone that swallows what enters it, as a cutting tool,
    mouth at z = 0 and apex below.

    The geometry is the whole mechanism: a ray entering at the mouth strikes the
    cone wall at a shallow angle and is reflected further in rather than back
    out, so it has to survive many grazing bounces to escape. Matte black PETG
    takes a large bite at each one. Depth is what makes it work, which is why
    TRAP_L is long relative to the mouth.
    """
    return Pos(0, 0, -P.TRAP_L) * Cone(
        bottom_radius=0.001, top_radius=P.TRAP_MOUTH_D / 2, height=P.TRAP_L, align=_MIN
    )


def ptfe_tile() -> Part:
    """The bought disc. Reference only — nothing here is ours to make."""
    return Pos(0, 0, 0) * Cylinder(P.TILE_D / 2, P.TILE_T, align=_MIN)


def report() -> int:
    bad = 0
    for name, part in (("trap cavity", cavity()), ("PTFE tile", ptfe_tile())):
        n = len(part.solids())
        print(f"{name}: {n} solid(s), volume {part.volume / 1000:.2f} cm^3")
        if n != 1:
            print(f"  FAIL: {name} is not a single solid")
            bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(report())
