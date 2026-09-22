"""`python -m spectra.capture`: session new, session read, repeat.

The white reference for 1a is the ColorChecker's white patch (19), ruled
2026-09-22, not the PTFE tile (a 1d item). The lamp channel and level are not CLI
flags: Stage 1a only drives the white LED, channel 0 per the channel assignment in
`specs/2026-09-22-capture-1a.md`, so the choice is a constant below rather than
something an operator can get wrong by typing a number.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

from . import cycle, hw, session

# Channel 0 is the white LED (Cree C513A) per the spec's channel assignment. CHOSEN.
WHITE_LED_CHANNEL = 0
# Full level. Whether this saturates the white patch under the real LED at the
# gain chosen is exactly what the first Pi run has to check. CHOSEN, unverified.
WHITE_LED_LEVEL = 1.0

# Defaults mirror adafruit_as7341.AS7341's own constructor defaults (atime=100,
# astep=999, gain=GAIN_128X, gain code 8 in the 0-10 AGAIN scale), so an operator
# who changes nothing gets the same integration the library would pick on its own.
# CHOSEN, not characterised against the C513A or the ColorChecker.
GAIN_DEFAULT = 8
ATIME_DEFAULT = 100
ASTEP_DEFAULT = 999
# Reads averaged per measurement. Five is a guess at enough to knock down read
# noise without making every `session read` take noticeably longer. ESTIMATE.
N_DEFAULT = 5

_F_CHANNEL_LABELS = {
    f"r_f{i + 1}": f"r_f{i + 1} ({nm}nm)" for i, nm in enumerate(hw.F_CHANNEL_NM)
}


def _prompt(message: str, no_prompt: bool) -> None:
    """Wait for Enter, unless told not to. Never hangs with no stdin to read.

    A script or a test harness that runs this with stdin closed or empty gets an
    immediate EOFError from `input()`; that is treated the same as an operator who
    pressed Enter right away; a real terminal session waits for a real keypress.
    """
    if no_prompt:
        return
    try:
        input(message)
    except EOFError:
        pass


def _build_hardware(fake: bool) -> tuple[hw.Sensor, hw.Lamp]:
    if fake:
        lamp = hw.FakeLamp()
        sensor = hw.FakeSensor(lamp)
        return sensor, lamp

    # Only imported here, on the real-hardware path, so `import spectra.capture`
    # and every `--fake` run stay clean on a machine with no Blinka installed.
    import board
    import busio

    i2c = busio.I2C(board.SCL, board.SDA)
    # No MISO: the TLC59711 is write-only over SPI, per specs/2026-09-22-capture-1a.md.
    spi = busio.SPI(board.SCK, board.MOSI)
    return hw.RealSensor(i2c), hw.RealLamp(spi)


def _cmd_session_new(args: argparse.Namespace) -> int:
    sensor, lamp = _build_hardware(args.fake)
    sensor.configure(args.gain, args.atime, args.astep)

    print("Taking dark...")
    dark = cycle.dark(sensor, lamp, args.n, args.settle)

    _prompt("White reference (ColorChecker patch 19) on the port, Enter: ", no_prompt=False)
    print("Taking white...")
    white = cycle.white(sensor, lamp, WHITE_LED_CHANNEL, WHITE_LED_LEVEL, args.n, args.settle)

    session.create(
        args.dir,
        gain=args.gain,
        atime=args.atime,
        astep=args.astep,
        lamp_channel=WHITE_LED_CHANNEL,
        lamp_level=WHITE_LED_LEVEL,
        settle_s=args.settle,
        n=args.n,
        dark=dark,
        white=white,
        notes=args.notes,
    )
    print(f"Session written to {args.dir}")
    return 0


def _cmd_session_read(args: argparse.Namespace) -> int:
    record = session.load(args.dir)
    sensor, lamp = _build_hardware(args.fake)
    sensor.configure(record["sensor"]["gain"], record["sensor"]["atime"], record["sensor"]["astep"])
    n = args.n if args.n is not None else record["n"]

    _prompt("Sample on the port, Enter: ", args.no_prompt)
    sample_ch = cycle.sample(
        sensor, lamp, record["lamp"]["channel"], record["lamp"]["level"], n, record["settle_s"]
    )
    refl = cycle.reflectance(sample_ch, session.dark_channels(record), session.white_channels(record))
    session.append_reading(args.dir, args.sample_id, sample_ch, refl)
    print(f"{args.sample_id}: " + ", ".join(f"{v:.4f}" for v in refl))
    return 0


def _cmd_repeat(args: argparse.Namespace) -> int:
    record = session.load(args.dir)
    sensor, lamp = _build_hardware(args.fake)
    sensor.configure(record["sensor"]["gain"], record["sensor"]["atime"], record["sensor"]["astep"])
    n = record["n"]
    dark = session.dark_channels(record)
    white = session.white_channels(record)

    rows: list[tuple[float, ...]] = []
    for i in range(args.count):
        if i > 0:
            _prompt("Lift and replace the head, Enter: ", no_prompt=False)
        sample_ch = cycle.sample(sensor, lamp, record["lamp"]["channel"], record["lamp"]["level"], n, record["settle_s"])
        refl = cycle.reflectance(sample_ch, dark, white)
        session.append_reading(args.dir, args.sample_id, sample_ch, refl)
        rows.append(refl)

    _print_spread(rows)
    return 0


def _print_spread(rows: list[tuple[float, ...]]) -> None:
    channel_names = [f"r_f{i + 1}" for i in range(8)]
    print()
    print(f"{'channel':<16}{'mean':>10}{'stdev':>10}{'cv':>8}")
    worst_name = None
    worst_cv = -1.0
    for i, name in enumerate(channel_names):
        values = [row[i] for row in rows]
        mean = statistics.fmean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        cv = (stdev / mean) if mean != 0 else float("inf")
        label = _F_CHANNEL_LABELS[name]
        print(f"{label:<16}{mean:>10.4f}{stdev:>10.4f}{cv:>7.1%}")
        if cv > worst_cv:
            worst_cv, worst_name = cv, label

    print()
    if len(rows) < 2:
        print("Fewer than 2 reads: no spread to report.")
    else:
        print(f"Worst channel: {worst_name} (cv {worst_cv:.1%})")
    print()
    print(
        "ΔE00 spread: not reported here. It needs the eight-channel to XYZ "
        "fitter, which is the next spec, not this one."
    )


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("dir", type=Path, help="session directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m spectra.capture")
    parser.add_argument("--fake", action="store_true", help="use FakeSensor/FakeLamp instead of real hardware")
    subparsers = parser.add_subparsers(dest="command", required=True)

    session_parser = subparsers.add_parser("session", help="start or extend a capture session")
    session_sub = session_parser.add_subparsers(dest="session_command", required=True)

    new_parser = session_sub.add_parser("new", help="take dark and white, write session.json")
    _add_common(new_parser)
    new_parser.add_argument("--gain", type=int, default=GAIN_DEFAULT, help="AS7341 gain code, 0 (0.5x) to 10 (512x)")
    new_parser.add_argument("--atime", type=int, default=ATIME_DEFAULT)
    new_parser.add_argument("--astep", type=int, default=ASTEP_DEFAULT)
    new_parser.add_argument("--n", type=int, default=N_DEFAULT, help="reads averaged per measurement")
    new_parser.add_argument("--settle", type=float, default=cycle.SETTLE_S_DEFAULT, help="settle time after a lamp change, seconds")
    new_parser.add_argument("--notes", type=str, default="")
    new_parser.set_defaults(func=_cmd_session_new)

    read_parser = session_sub.add_parser("read", help="read one sample, append a row")
    _add_common(read_parser)
    read_parser.add_argument("sample_id", type=str)
    read_parser.add_argument("--n", type=int, default=None, help="override the session's averaging count")
    read_parser.add_argument("--no-prompt", action="store_true")
    read_parser.set_defaults(func=_cmd_session_read)

    repeat_parser = subparsers.add_parser("repeat", help="read the same sample `count` times and report the spread")
    _add_common(repeat_parser)
    repeat_parser.add_argument("sample_id", type=str)
    repeat_parser.add_argument("--count", type=int, default=10)
    repeat_parser.set_defaults(func=_cmd_repeat)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
