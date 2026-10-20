"""What the head is made of: a sensor and a lamp, real or fake.

Two Protocols so `cycle.py` and `session.py` never know which they are talking to.
The real classes wrap `adafruit_as7341` and `adafruit_tlc59711` and import them
inside `__init__`, not at module load, so `import spectra.capture` succeeds on a
machine without Blinka installed (this Mac, CI). The fakes make the whole package
testable without either chip.

grow-lab has its own AS7341 driver (`pi/drivers/as7341.py`). It is not used here:
it is async, bound to grow-lab's data models, and grow-lab depends on this repo, so
importing it back would be circular. Adafruit's library is the native mechanism.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, fields
from typing import Protocol

__all__ = [
    "Channels",
    "Sensor",
    "Lamp",
    "full_scale",
    "integration_time_ms",
    "RealSensor",
    "RealLamp",
    "FakeSensor",
    "FakeLamp",
]

# AS7341 F-channel centre wavelengths, in the order the datasheet and the library
# both use. Not a measurement, just naming.
F_CHANNEL_NM = (415, 445, 480, 515, 555, 590, 630, 680)


@dataclass(frozen=True)
class Channels:
    """One sensor read: the eight F channels, clear, and near-IR. Raw counts."""

    f1: int  # 415nm
    f2: int  # 445nm
    f3: int  # 480nm
    f4: int  # 515nm
    f5: int  # 555nm
    f6: int  # 590nm
    f7: int  # 630nm
    f8: int  # 680nm
    clear: int
    nir: int


def full_scale(atime: int, astep: int) -> int:
    """ADC full-scale count for the configured integration settings.

    ``(ATIME + 1) * (ASTEP + 1)``, capped at 65535 (16-bit channel registers). From
    the AS7341 datasheet (DS000504); the CircuitPython library does not expose
    this itself, so this repo owns the formula and it is unverified against a real
    part. Confirm it against an actual saturated read on the Pi before trusting the
    abort threshold at a new atime/astep.
    """
    return min(65535, (atime + 1) * (astep + 1))


def integration_time_ms(atime: int, astep: int) -> float:
    """Integration time in ms for a given ATIME/ASTEP.

    ``(ATIME + 1) * (ASTEP + 1) * 2.78`` microseconds, from the AS7341 datasheet
    (DS000504) and confirmed against the CircuitPython library's own docstring.
    Recorded in the session file so a later reader knows how long each read
    integrated for, without having to reverse the formula out of two raw settings.
    """
    return (atime + 1) * (astep + 1) * 2.78 / 1000.0


class Sensor(Protocol):
    """An AS7341, or something that reads like one."""

    def configure(self, gain: int, atime: int, astep: int) -> None:
        """Set gain, ATIME and ASTEP. Integration time follows from atime/astep."""
        ...

    def read(self) -> Channels:
        """One read of all ten channels."""
        ...

    @property
    def full_scale(self) -> int:
        """ADC full scale under the last `configure()` call. See `hw.full_scale`."""
        ...


class Lamp(Protocol):
    """A TLC59711 channel, or something that lights like one."""

    def set(self, channel: int, level: float) -> None:
        """Turn one channel on at `level`, 0 (off) to 1 (full 16-bit PWM)."""
        ...

    def off(self) -> None:
        """All channels off."""
        ...


class RealSensor:
    """Wraps `adafruit_as7341.AS7341` over the board's I2C bus.

    The gain code is the AS7341's raw AGAIN register value, 0 (0.5x) to 10
    (512x), doubling each step. This mapping to the library's `Gain` enum members
    (`GAIN_0_5X` .. `GAIN_512X`) is read off the datasheet's gain table, not
    exercised against real hardware here; confirm it reads a sane value on the Pi
    before trusting it.
    """

    _GAIN_NAMES = (
        "GAIN_0_5X",
        "GAIN_1X",
        "GAIN_2X",
        "GAIN_4X",
        "GAIN_8X",
        "GAIN_16X",
        "GAIN_32X",
        "GAIN_64X",
        "GAIN_128X",
        "GAIN_256X",
        "GAIN_512X",
    )

    def __init__(self, i2c_bus, address: int = 0x39) -> None:
        import adafruit_as7341

        self._lib = adafruit_as7341
        self._sensor = adafruit_as7341.AS7341(i2c_bus, address=address)
        self._atime = 100
        self._astep = 999

    def configure(self, gain: int, atime: int, astep: int) -> None:
        if not 0 <= gain < len(self._GAIN_NAMES):
            raise ValueError(f"gain code must be 0-10 (0.5x-512x), got {gain}")
        self._sensor.gain = getattr(self._lib.Gain, self._GAIN_NAMES[gain])
        self._sensor.atime = atime
        self._sensor.astep = astep
        self._atime = atime
        self._astep = astep

    def read(self) -> Channels:
        # `all_channels` does both SMUX passes (F1-F4, F5-F8) in one call; rolling
        # that by hand here would just be a worse copy of what the library already
        # does. clear/nir come off whichever pass ran last inside it.
        f1, f2, f3, f4, f5, f6, f7, f8 = self._sensor.all_channels
        return Channels(
            f1=f1,
            f2=f2,
            f3=f3,
            f4=f4,
            f5=f5,
            f6=f6,
            f7=f7,
            f8=f8,
            clear=self._sensor.channel_clear,
            nir=self._sensor.channel_nir,
        )

    @property
    def full_scale(self) -> int:
        return full_scale(self._atime, self._astep)


class RealLamp:
    """Wraps `adafruit_tlc59711.TLC59711` over SPI. Channel 0 is the white LED."""

    def __init__(self, spi_bus) -> None:
        import adafruit_tlc59711

        self._tlc = adafruit_tlc59711.TLC59711(spi_bus)

    def set(self, channel: int, level: float) -> None:
        if not 0 <= channel < 12:
            raise ValueError(f"channel must be 0-11, got {channel}")
        if not 0.0 <= level <= 1.0:
            raise ValueError(f"level must be 0..1, got {level}")
        self._tlc.set_channel(channel, round(level * 65535))
        self._tlc.show()

    def off(self) -> None:
        for channel in range(12):
            self._tlc.set_channel(channel, 0)
        self._tlc.show()


class FakeSensor:
    """Dark counts when the fake lamp is off, a fixed lit spectrum scaled by
    the lamp level when it is on, plus a small deterministic noise term.

    Deterministic so the repeatability report in `repeat` has something real to
    report on a machine with no sensor at all: the noise is a function of the
    read count, not of wall-clock time or an unseeded RNG, so two `--fake` runs
    of the same length produce the same spread.
    """

    # Dark counts: a handful of stray photons and read noise, nothing that looks
    # like a spectrum. CHOSEN, not measured.
    _DARK = Channels(f1=12, f2=10, f3=9, f4=11, f5=13, f6=10, f7=8, clear=40, nir=20, f8=9)
    # Full-scale spectrum shape under the white LED at level 1.0: a plausible
    # broad white curve, brighter in the middle channels the way a phosphor-
    # converted white LED actually looks. CHOSEN so the fake has a shape to test
    # reflectance against, not a claim about the real C513A. Kept well under the
    # default saturation floor (90% of 65535) so the default CLI path never trips
    # the saturation abort; the saturation test drives `cycle` with its own values.
    _LIT = Channels(
        f1=5000,
        f2=7500,
        f3=11000,
        f4=13500,
        f5=15000,
        f6=14000,
        f7=11500,
        f8=9000,
        clear=36000,
        nir=5500,
    )
    _NOISE_AMPLITUDE = 30

    def __init__(self, lamp: "FakeLamp") -> None:
        self._lamp = lamp
        self._gain = 8
        self._atime = 100
        self._astep = 999
        self._rng = random.Random(0)

    def configure(self, gain: int, atime: int, astep: int) -> None:
        self._gain = gain
        self._atime = atime
        self._astep = astep

    def read(self) -> Channels:
        level = self._lamp.level if self._lamp.is_on else 0.0
        values = {}
        for f in fields(Channels):
            dark = getattr(self._DARK, f.name)
            lit = getattr(self._LIT, f.name)
            noise = self._rng.randint(-self._NOISE_AMPLITUDE, self._NOISE_AMPLITUDE)
            value = dark + (lit - dark) * level + noise
            values[f.name] = max(0, round(value))
        return Channels(**values)

    @property
    def full_scale(self) -> int:
        return full_scale(self._atime, self._astep)


class FakeLamp:
    """Tracks which channel is on and at what level. No hardware."""

    def __init__(self) -> None:
        self.channel: int | None = None
        self.level: float = 0.0
        self.is_on: bool = False

    def set(self, channel: int, level: float) -> None:
        if not 0.0 <= level <= 1.0:
            raise ValueError(f"level must be 0..1, got {level}")
        self.channel = channel
        self.level = level
        self.is_on = level > 0.0

    def off(self) -> None:
        self.channel = None
        self.level = 0.0
        self.is_on = False
