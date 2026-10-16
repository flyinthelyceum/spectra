"""One capture session is one directory: `session.json` plus `readings.csv`.

`session.json` carries everything a later reader needs to reproduce or distrust
the numbers: when it started, what code and hardware settings produced it, and the
dark and white references every reflectance in the session is divided against.
`readings.csv` is one row per sample read, raw counts and reflectance together, so
a reader never has to recompute a reflectance to check it.
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import hw

__all__ = [
    "READINGS_HEADER",
    "SESSION_FILENAME",
    "READINGS_FILENAME",
    "create",
    "load",
    "dark_channels",
    "white_channels",
    "append_reading",
    "read_rows",
    "check_instrument",
]

GEOMETRY = "45/0"
"""The head's illumination/viewing geometry (`docs/OPTICAL_HEAD.md`). Recorded so a
later head with another geometry cannot silently extend this session."""

WAVELENGTH_BASIS = "AS7341 F1-F8, nominal centres " + ", ".join(f"{nm}" for nm in hw.F_CHANNEL_NM) + " nm"
"""What the eight reflectance columns are. Nominal channel centres, not a measured
response; the eight-channel fitter is a later stage."""

WHITE_REFERENCE = "ColorChecker patch 19"
"""The Stage 1a white, ruled 2026-09-22. The PTFE tile is a 1d item and will have
its own id when it exists."""

SESSION_FILENAME = "session.json"
READINGS_FILENAME = "readings.csv"

_CHANNEL_FIELDS = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "clear", "nir")
_F_FIELDS = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8")

READINGS_HEADER = (
    ["sample_id", "ts"]
    + list(_CHANNEL_FIELDS)
    + [f"r_{name}" for name in _F_FIELDS]
)


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _git_sha() -> str | None:
    """HEAD of the checkout this module was loaded from, or None.

    Asked of the directory holding this file, never the operator's working
    directory: running the CLI from inside some other repository must not record
    that repository's commit as the code that took the reading. The answer is
    used only if that checkout's top level really contains this file, so an
    installed copy sitting inside an unrelated repo also gives None. An install
    with no checkout at all is normal, so None is not an error.
    """
    here = Path(__file__).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(here.parent), "rev-parse", "--show-toplevel", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    lines = result.stdout.split()
    if len(lines) != 2:
        return None
    top, sha = Path(lines[0]).resolve(), lines[1]
    if (top / "spectra" / "capture" / here.name).resolve() != here:
        return None
    return sha


def _spectra_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version("spectra")
    except (ImportError, PackageNotFoundError):
        return "unknown"


def create(
    directory: str | Path,
    *,
    gain: int,
    atime: int,
    astep: int,
    lamp_channel: int,
    lamp_level: float,
    settle_s: float,
    n: int,
    dark: hw.Channels,
    white: hw.Channels,
    instrument: dict[str, Any],
    notes: str = "",
) -> dict[str, Any]:
    """Write `session.json` and an empty `readings.csv` for a new session.

    `directory` must not already hold a session; this never overwrites one, so a
    typo in a directory name cannot quietly erase a dark/white pair that took a
    minute to collect.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    session_path = directory / SESSION_FILENAME
    if session_path.exists():
        raise FileExistsError(f"{session_path} already exists; start a new directory")

    record: dict[str, Any] = {
        "started": _timestamp(),
        "spectra_version": _spectra_version(),
        "git_sha": _git_sha(),
        "instrument": {
            **instrument,
            "geometry": GEOMETRY,
            "wavelength_basis": WAVELENGTH_BASIS,
        },
        "white_reference": WHITE_REFERENCE,
        "sensor": {
            "gain": gain,
            "atime": atime,
            "astep": astep,
            "integration_time_ms": hw.integration_time_ms(atime, astep),
        },
        "lamp": {"channel": lamp_channel, "level": lamp_level},
        "settle_s": settle_s,
        "n": n,
        "dark": asdict(dark),
        "white": asdict(white),
        "notes": notes,
    }
    session_path.write_text(json.dumps(record, indent=2) + "\n")

    readings_path = directory / READINGS_FILENAME
    if not readings_path.exists():
        with readings_path.open("w", newline="") as f:
            csv.writer(f).writerow(READINGS_HEADER)

    return record


def load(directory: str | Path) -> dict[str, Any]:
    """Read `session.json` back."""
    session_path = Path(directory) / SESSION_FILENAME
    return json.loads(session_path.read_text())


def check_instrument(record: dict[str, Any], instrument: dict[str, Any]) -> None:
    """Refuse to extend a session from a different instrument than took its
    dark and white. A sample read on real hardware against a fake white, or on
    one board against another's dark, divides by the wrong references and
    produces a plausible, wrong reflectance. Every key the caller passes must
    match what the session recorded; a session with no record is refused too.
    """
    recorded = record.get("instrument")
    if not recorded:
        raise ValueError("session has no instrument record; start a new session with this code")
    for key, value in instrument.items():
        if recorded.get(key) != value:
            raise ValueError(
                f"session was taken with {key}={recorded.get(key)!r}, this run is {key}={value!r}; "
                "start a new session rather than mix references"
            )


def dark_channels(record: dict[str, Any]) -> hw.Channels:
    return hw.Channels(**record["dark"])


def white_channels(record: dict[str, Any]) -> hw.Channels:
    return hw.Channels(**record["white"])


def append_reading(
    directory: str | Path,
    sample_id: str,
    channels: hw.Channels,
    reflectance: tuple[float, ...],
) -> None:
    """Append one row to `readings.csv`. `reflectance` is f1..f8 order, 8 values."""
    if len(reflectance) != len(_F_FIELDS):
        raise ValueError(f"expected {len(_F_FIELDS)} reflectance values, got {len(reflectance)}")
    readings_path = Path(directory) / READINGS_FILENAME
    row = [sample_id, _timestamp()]
    row += [getattr(channels, name) for name in _CHANNEL_FIELDS]
    row += list(reflectance)
    with readings_path.open("a", newline="") as f:
        csv.writer(f).writerow(row)


def read_rows(directory: str | Path) -> list[dict[str, str]]:
    """All rows of `readings.csv`, as written (strings; the caller converts)."""
    readings_path = Path(directory) / READINGS_FILENAME
    with readings_path.open(newline="") as f:
        return list(csv.DictReader(f))
