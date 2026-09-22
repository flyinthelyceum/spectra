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
]

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
    """`git rev-parse HEAD`, or None off a machine with no git or no repo.

    A capture session on the Pi will usually not have a git checkout of this
    package at all (it is installed with the `pi` extra), so this is optional by
    design, not a missing-error-handling gap.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


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
