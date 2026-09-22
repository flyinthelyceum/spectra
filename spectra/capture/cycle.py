"""The measurement cycle: dark, white, sample, reflectance. Hardware-agnostic.

Everything here talks to `hw.Sensor` and `hw.Lamp` through their Protocols, never
to `adafruit_as7341` or `adafruit_tlc59711` directly, so the same code runs against
the real hardware on a Pi and against the fakes on the Mac. A reading here is
always the average of `n` sensor reads taken after the lamp has settled; each of
the `n` raw reads is checked for saturation as it comes in; an average would not
saturate the same way a real read does, so the check runs before averaging, not
after.
"""

from __future__ import annotations

import time
from dataclasses import fields

from .hw import Channels, Lamp, Sensor

__all__ = [
    "SETTLE_S_DEFAULT",
    "SaturationError",
    "dark",
    "white",
    "sample",
    "reflectance",
]

# How long to wait after a lamp change before trusting a read. Not measured on any
# hardware yet; it is here so a session started under this value can be told apart
# from one started under a value that was actually characterised on the bench.
# ESTIMATE.
SETTLE_S_DEFAULT = 0.2

# F-channel field names, in wavelength order, for the reflectance calculation.
# `clear` and `nir` are recorded but have no reflectance: they are not narrowband
# enough to divide by a white reference and call the result a reflectance.
_F_FIELDS = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8")


class SaturationError(RuntimeError):
    """A channel read at or above 90% of full scale. The read is thrown away.

    A saturated channel is not a large number, it is a wrong number: the ADC has
    clipped and the true count is unknown. Averaging it in would make every
    reflectance that depends on it wrong in a way that does not show up as noise.
    """


def _saturation_floor(sensor: Sensor) -> float:
    return 0.9 * sensor.full_scale


def _check_saturation(sensor: Sensor, channels: Channels) -> None:
    floor = _saturation_floor(sensor)
    for name in _F_FIELDS + ("clear", "nir"):
        value = getattr(channels, name)
        if value >= floor:
            raise SaturationError(
                f"channel {name} read {value}, at or above 90% of full scale "
                f"({sensor.full_scale}). Lower the gain and read again."
            )


def _average(sensor: Sensor, n: int) -> Channels:
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n}")
    totals = {f.name: 0.0 for f in fields(Channels)}
    for _ in range(n):
        reading = sensor.read()
        _check_saturation(sensor, reading)
        for f in fields(Channels):
            totals[f.name] += getattr(reading, f.name)
    # Channels is a dataclass of ints (raw ADC counts); round the average back to
    # one rather than widen the type just for this intermediate value.
    return Channels(**{name: round(total / n) for name, total in totals.items()})


def dark(sensor: Sensor, lamp: Lamp, n: int, settle_s: float = SETTLE_S_DEFAULT) -> Channels:
    """Lamp off, settle, `n` reads averaged. The detector's own floor."""
    lamp.off()
    time.sleep(settle_s)
    return _average(sensor, n)


def white(
    sensor: Sensor,
    lamp: Lamp,
    channel: int,
    level: float,
    n: int,
    settle_s: float = SETTLE_S_DEFAULT,
) -> Channels:
    """Lamp on, settle, `n` reads averaged. Caller has the white reference on the port.

    For 1a the white reference is the ColorChecker's white patch (patch 19), ruled
    2026-09-22. The PTFE tile is a 1d item.
    """
    lamp.set(channel, level)
    time.sleep(settle_s)
    return _average(sensor, n)


def sample(
    sensor: Sensor,
    lamp: Lamp,
    channel: int,
    level: float,
    n: int,
    settle_s: float = SETTLE_S_DEFAULT,
) -> Channels:
    """Lamp on, settle, `n` reads averaged. Caller has the sample on the port."""
    lamp.set(channel, level)
    time.sleep(settle_s)
    return _average(sensor, n)


def reflectance(sample_ch: Channels, dark_ch: Channels, white_ch: Channels) -> tuple[float, ...]:
    """`(S - D) / (W - D)` per F channel, in f1..f8 order.

    A non-positive denominator means the white reference read no brighter than
    dark on that channel, which is a broken measurement (LED off, wrong port,
    saturated white clipped down by something upstream), not a value with a
    reflectance near infinity. That is an error, not a NaN or a silent clamp.
    """
    out = []
    for name in _F_FIELDS:
        s = getattr(sample_ch, name)
        d = getattr(dark_ch, name)
        w = getattr(white_ch, name)
        denom = w - d
        if denom <= 0:
            raise ValueError(
                f"channel {name}: white ({w}) is not above dark ({d}); "
                "cannot compute a reflectance"
            )
        out.append((s - d) / denom)
    return tuple(out)
