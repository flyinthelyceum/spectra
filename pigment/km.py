"""Kubelka-Munk: what a paint absorbs, what it scatters, and what a mixture does.

The whole reason the instrument exists is in this file. A reflectance curve says
where a pigment sits; it does not say what happens when you mix it, because
reflectance is not additive and CIELAB is emphatically not additive. Kubelka-Munk
turns a reflectance into two quantities that are: ``K``, absorption, and ``S``,
scattering, both per wavelength. Mix two paints and the mixture's K and S are the
concentration-weighted sums of theirs. That is the property everything else here
rests on.

Three things in this module are easy to get wrong and expensive to get wrong late.

**Saunderson.** What an instrument measures off a cured film is not what the
Kubelka-Munk equations operate on. Some light reflects at the air/binder boundary
without ever meeting a pigment particle, and some light heading back out is
reflected inward again. A 45/0 geometry throws away the specular lobe; it does not
remove either term. Skipping the correction puts a systematic bias into K/S that
grows as the sample gets darker, which is exactly where the saturated organics
live. Correct first, always: :func:`to_internal` before :func:`ks_from_reflectance`.

**Opacity.** The familiar ``K/S = (1-R)^2 / 2R`` is the infinite-thickness case. A
masstone of quinacridone or phthalo is not optically thick, so that form silently
measures the ground as well as the paint. :func:`reflectance_over` is the general
two-flux solution, and :func:`solve_ks_sx` recovers both quantities from the same
film read over a black ground and a white one.

**Thickness.** ``S`` and the film thickness ``X`` only ever appear as the product
``S*X``, so nothing here needs a thickness in microns. It needs the drawdown to be
the *same* thickness every time. Everything in this module is therefore in units of
"per film", and mixing is valid as long as every film in the comparison was drawn
down with the same bar.

Pure standard library, per wavelength, scalar in and scalar out. Curve-level
helpers take and return sequences in the same wavelength order; nothing here knows
what those wavelengths are.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

__all__ = [
    "K1_DEFAULT",
    "K2_DEFAULT",
    "to_internal",
    "to_measured",
    "ks_from_reflectance",
    "reflectance_from_ks",
    "reflectance_over",
    "solve_ks_sx",
    "mix_ks",
    "mix_two_constant",
    "curve_ks_from_reflectance",
    "curve_reflectance_from_ks",
    "curve_to_internal",
]

# Front-surface reflection at the air/binder boundary. 0.04 is the normal-incidence
# Fresnel value for a binder near n = 1.5 and is the usual starting point, NOT a
# measurement of any film in this project. Under 45/0 with the specular lobe
# excluded the effective value is lower, and the honest thing is to fit it against
# a chart rather than assume it. Treated as a parameter everywhere for that reason.
K1_DEFAULT = 0.04

# Internal diffuse reflection heading back into the film at the same boundary.
# ~0.6 for n = 1.5 under diffuse internal illumination. Much less sensitive than k1.
K2_DEFAULT = 0.6

# coth(x) is 1.0 to within double precision well before here.
_COTH_SATURATES = 20.0


def to_internal(
    r_measured: float, k1: float = K1_DEFAULT, k2: float = K2_DEFAULT
) -> float:
    """Saunderson: measured reflectance to the internal reflectance K-M wants."""
    u = r_measured - k1
    if u <= 0.0:
        return 0.0
    return u / ((1.0 - k1) * (1.0 - k2) + k2 * u)


def to_measured(
    r_internal: float, k1: float = K1_DEFAULT, k2: float = K2_DEFAULT
) -> float:
    """Saunderson, the other way: a predicted internal reflectance as it would read."""
    if r_internal <= 0.0:
        return k1
    return k1 + (1.0 - k1) * (1.0 - k2) * r_internal / (1.0 - k2 * r_internal)


def ks_from_reflectance(r_internal: float) -> float:
    """K/S from the reflectance of an optically thick film.

    Saunderson-corrected reflectance in, K/S out. A film that is not opaque needs
    :func:`solve_ks_sx` instead; using this on a transparent masstone reports the
    ground as though it were the paint.
    """
    if r_internal <= 0.0:
        return math.inf
    if r_internal >= 1.0:
        return 0.0
    return (1.0 - r_internal) ** 2 / (2.0 * r_internal)


def reflectance_from_ks(ks: float) -> float:
    """The opaque reflectance implied by a K/S. Inverse of :func:`ks_from_reflectance`."""
    if ks == math.inf:
        return 0.0
    if ks <= 0.0:
        return 1.0
    return 1.0 + ks - math.sqrt(ks * ks + 2.0 * ks)


def _b_coth_bsx(b: float, sx: float) -> float:
    """b * coth(b * S * X), with both degenerate ends handled.

    As b goes to zero the product tends to 1/(S*X), which is the no-absorption
    case; as b*S*X grows, coth saturates at 1.
    """
    if sx == math.inf:
        return b
    x = b * sx
    if x < 1e-9:
        return 1.0 / sx
    if x > _COTH_SATURATES:
        return b
    return b / math.tanh(x)


def reflectance_over(ks: float, sx: float, r_ground: float) -> float:
    """Reflectance of a film of K/S and S*X laid over a ground of reflectance r_ground.

    The general two-flux solution. All three arguments and the result are internal
    (Saunderson-corrected) reflectances. ``sx = math.inf`` gives the opaque case and
    agrees with :func:`reflectance_from_ks` for any ground.
    """
    if ks == math.inf:
        return 0.0
    a = 1.0 + ks
    b = math.sqrt(max(a * a - 1.0, 0.0))
    t = _b_coth_bsx(b, sx)
    denominator = a - r_ground + t
    if denominator <= 0.0:
        return 0.0
    return (1.0 - r_ground * (a - t)) / denominator


def solve_ks_sx(
    r_over_black: float,
    r_over_white: float,
    r_ground_white: float,
    tolerance: float = 1e-10,
) -> Tuple[float, float]:
    """Recover (K/S, S*X) from one film read over two grounds.

    This is the black/white drawdown, and it is the only honest way to measure a
    transparent pigment. All four numbers are internal reflectances: correct with
    :func:`to_internal` before calling.

    The film over white is always the lighter of the two unless it is hiding, in
    which case the pair is equal and ``S*X`` comes back as ``math.inf``.
    """
    if not 0.0 < r_over_black < 1.0:
        raise ValueError(f"r_over_black must be in (0, 1), got {r_over_black}")
    if not 0.0 < r_over_white < 1.0:
        raise ValueError(f"r_over_white must be in (0, 1), got {r_over_white}")
    if r_over_white < r_over_black - tolerance:
        raise ValueError(
            "r_over_white is below r_over_black; the readings are swapped or the "
            "grounds are not what they are labelled"
        )
    if r_over_white - r_over_black <= tolerance:
        return ks_from_reflectance(r_over_black), math.inf

    # Over a black ground the film can never be lighter than the same paint opaque,
    # so this K/S is the hard upper bound: it is the value at which S*X is infinite.
    ks_hi = ks_from_reflectance(r_over_black)

    def sx_matching_black(ks: float) -> float:
        a = 1.0 + ks
        b = math.sqrt(max(a * a - 1.0, 0.0))
        t = 1.0 / r_over_black - a  # = b * coth(b * S * X)
        if t <= 0.0:
            return math.inf
        if b < 1e-12:
            return 1.0 / t
        ratio = b / t
        if ratio >= 1.0:
            return math.inf
        return math.atanh(ratio) / b

    def residual(ks: float) -> float:
        return reflectance_over(ks, sx_matching_black(ks), r_ground_white) - r_over_white

    # residual is monotone decreasing in K/S: more absorption, less S*X needed to
    # hit the black reading, so less of the white ground shows through.
    lo, hi = 0.0, ks_hi
    if residual(hi) > 0.0:
        return hi, sx_matching_black(hi)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if residual(mid) > 0.0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tolerance:
            break
    ks = 0.5 * (lo + hi)
    return ks, sx_matching_black(ks)


def _checked_concentrations(concentrations: Sequence[float], n: int) -> List[float]:
    if len(concentrations) != n:
        raise ValueError(f"expected {n} concentrations, got {len(concentrations)}")
    if any(c < 0.0 for c in concentrations):
        raise ValueError("concentrations must not be negative")
    total = math.fsum(concentrations)
    if total <= 0.0:
        raise ValueError("concentrations must not sum to zero")
    return [c / total for c in concentrations]


def mix_ks(ks_values: Sequence[float], concentrations: Sequence[float]) -> float:
    """Single-constant mixing: the concentration-weighted sum of K/S.

    Right for self-shades and for pigments of similar scattering power. Wrong, and
    wrong in a direction that flatters the answer, for any mixture with titanium
    white in it: white's scattering is what does the work there, and a ratio cannot
    carry it. Use :func:`mix_two_constant` for anything with white.
    """
    weights = _checked_concentrations(concentrations, len(ks_values))
    return math.fsum(w * ks for w, ks in zip(weights, ks_values))


def mix_two_constant(
    ks_values: Sequence[float],
    sx_values: Sequence[float],
    concentrations: Sequence[float],
) -> Tuple[float, float]:
    """Two-constant mixing: weighted sums of K and of S, kept separate.

    Takes each pigment as the (K/S, S*X) pair :func:`solve_ks_sx` returns, and gives
    the mixture back in the same form. Valid as long as every film in the set was
    drawn down at the same thickness, because X divides out only when it is shared.
    """
    if len(sx_values) != len(ks_values):
        raise ValueError("ks_values and sx_values must be the same length")
    weights = _checked_concentrations(concentrations, len(ks_values))
    kx = math.fsum(w * ks * sx for w, ks, sx in zip(weights, ks_values, sx_values))
    sx = math.fsum(w * sx for w, sx in zip(weights, sx_values))
    if sx <= 0.0:
        return math.inf, 0.0
    return kx / sx, sx


def curve_to_internal(
    curve: Iterable[float], k1: float = K1_DEFAULT, k2: float = K2_DEFAULT
) -> List[float]:
    """Saunderson across a whole reflectance curve."""
    return [to_internal(r, k1, k2) for r in curve]


def curve_ks_from_reflectance(curve: Iterable[float]) -> List[float]:
    """K/S across a whole opaque reflectance curve."""
    return [ks_from_reflectance(r) for r in curve]


def curve_reflectance_from_ks(curve: Iterable[float]) -> List[float]:
    """Opaque reflectance across a whole K/S curve."""
    return [reflectance_from_ks(ks) for ks in curve]
