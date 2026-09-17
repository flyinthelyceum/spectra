"""The two reference standards: the light trap and the white tile holder.

    python -m spectra.cad.trap

`OPTICAL_HEAD.md` rules that the black reference is a light trap and not a black
tile, because a trap reads nearer zero than any black surface and is what
actually measures the head's stray light. That is the part built here.

The white is a bought sintered-PTFE disc; what is built here is the holder that
presents it at the port at the same standoff the sample sees. Presenting the
white at a different height from the sample would put a geometry difference
inside the calibration, which is the one place it cannot be corrected out.
"""

from __future__ import annotations

from build123d import Align, Cone, Cylinder, Part, Pos

from . import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def light_trap() -> Part:
    """A deep cone that swallows what enters it.

    The geometry is the whole mechanism: a ray entering at the mouth strikes the
    cone wall at a shallow angle and is reflected further in rather than back
    out, so it has to survive many grazing bounces to escape. Matte black PETG
    takes a large bite at each one. Depth is what makes it work, which is why
    TRAP_L is long relative to the mouth.
    """
    outer = Pos(0, 0, 0) * Cylinder(P.TRAP_OD / 2, P.TRAP_L, align=_MIN)
    # Cone bored from the top face down to a point. Apex at the bottom.
    cavity = Pos(0, 0, 0) * Cone(
        bottom_radius=0.001, top_radius=P.TRAP_MOUTH_D / 2, height=P.TRAP_L, align=_MIN
    )
    return outer - cavity


def tile_holder() -> Part:
    """A disc with a recess the PTFE tile drops into, face flush with the top."""
    body = Pos(0, 0, 0) * Cylinder(
        P.TILE_HOLDER_OD / 2, P.TILE_T + P.TRAP_WALL, align=_MIN
    )
    recess = Pos(0, 0, P.TRAP_WALL) * Cylinder(
        P.TILE_D / 2 + 0.15, P.TILE_T + 1.0, align=_MIN
    )
    return body - recess


def ptfe_tile() -> Part:
    """The bought disc. Reference only — nothing here is ours to make."""
    return Pos(0, 0, 0) * Cylinder(P.TILE_D / 2, P.TILE_T, align=_MIN)


def report() -> int:
    bad = 0
    for name, part in (("light trap", light_trap()),
                       ("tile holder", tile_holder()),
                       ("PTFE tile", ptfe_tile())):
        n = len(part.solids())
        print(f"{name}: {n} solid(s), volume {part.volume / 1000:.2f} cm^3")
        if n != 1:
            print(f"  FAIL: {name} is not a single solid")
            bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(report())
