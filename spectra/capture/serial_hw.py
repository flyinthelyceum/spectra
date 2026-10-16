"""The sensor and the lamp, through an ESP32 on a USB cable.

The ESP32 runs `firmware/circuitpython/code.py`, which answers one line per
command on CircuitPython's data serial channel. These two classes speak that
protocol and satisfy `hw.Sensor` and `hw.Lamp`, so `cycle.py`, `session.py` and
the CLI run unchanged on whatever computer the cable is plugged into. That is the
whole design: the measurement lives here, tested; the board only does what Blinka
did on the Pi. Ruled 2026-10-06 (`docs/DECISIONS.md`).

`pyserial` is imported inside `open_port` and `find_port`, so `import
spectra.capture` still works without the `capture` extra installed.
"""

from __future__ import annotations

from typing import Protocol

from .hw import Channels, check_integration, full_scale

__all__ = ["PROTOCOL", "ESPRESSIF_VID", "Link", "SerialSensor", "SerialLamp", "open_port", "find_port", "connect"]

PROTOCOL = "SPECTRA ESP32 1"
"""What the firmware answers to `ID`. Changes when the command set does."""

ESPRESSIF_VID = 0x303A
"""USB vendor ID CircuitPython reports on the ESP32-S3 DevKitC-1 builds
(`mpconfigboard.mk` in the CircuitPython port). Used to try likely ports first."""

TIMEOUT_S = 5.0
"""ESTIMATE. Longest wait for one reply line. A READ is two integrations, each
under `hw.MAX_PASS_MS` (1 s) or refused, so the board answers within about 2 s."""


class Transport(Protocol):
    """The half of `serial.Serial` used here; a test can stand in for it."""

    timeout: float | None

    def write(self, data: bytes) -> int | None: ...

    def readline(self) -> bytes: ...


class Link:
    """One command out, one reply back. `ERR` replies and silence both raise."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def ask(self, line: str, timeout: float = TIMEOUT_S) -> str:
        self._t.timeout = timeout
        # On the console channel a boot or status line can be waiting; drop it so
        # it is not read as the reply.
        if hasattr(self._t, "reset_input_buffer"):
            self._t.reset_input_buffer()
        self._t.write((line + "\n").encode())
        raw = self._t.readline()
        if not raw.endswith(b"\n"):
            raise TimeoutError(f"no reply to {line.split()[0]!r} within {timeout} s; is code.py running?")
        reply = raw.decode("utf-8", "replace").strip()
        if reply.startswith("ERR"):
            raise RuntimeError(f"ESP32: {reply[3:].strip()} (sent {line!r})")
        return reply


class SerialSensor:
    """The AS7341 on the ESP32. Gain codes as `hw.RealSensor`: 0 (0.5x) to 10 (512x)."""

    def __init__(self, link: Link) -> None:
        self._link = link
        # The library's own defaults, which the firmware leaves in place until
        # the first CFG. Kept so `full_scale` is right before `configure`.
        self._atime = 100
        self._astep = 999

    def configure(self, gain: int, atime: int, astep: int) -> None:
        if not 0 <= gain <= 10:
            raise ValueError(f"gain code must be 0-10 (0.5x-512x), got {gain}")
        check_integration(atime, astep)
        self._link.ask(f"CFG {gain} {atime} {astep}")
        self._atime = atime
        self._astep = astep

    def read(self) -> Channels:
        reply = self._link.ask("READ")
        words = reply.split()
        if len(words) != 11 or words[0] != "CH":
            raise RuntimeError(f"ESP32: expected CH and ten counts, got {reply!r}")
        f1, f2, f3, f4, f5, f6, f7, f8, clear, nir = (int(w) for w in words[1:])
        return Channels(f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, f6=f6, f7=f7, f8=f8, clear=clear, nir=nir)

    @property
    def full_scale(self) -> int:
        return full_scale(self._atime, self._astep)


class SerialLamp:
    """The TLC59711 on the ESP32. Channel 0 is the white LED, as `hw.RealLamp`."""

    def __init__(self, link: Link) -> None:
        self._link = link

    def set(self, channel: int, level: float) -> None:
        if not 0 <= channel < 12:
            raise ValueError(f"channel must be 0-11, got {channel}")
        if not 0.0 <= level <= 1.0:
            raise ValueError(f"level must be 0..1, got {level}")
        self._link.ask(f"SET {channel} {round(level * 65535)}")

    def off(self) -> None:
        self._link.ask("OFF")


def open_port(device: str) -> Transport:
    import serial

    return serial.Serial(device, 115200, timeout=TIMEOUT_S)


def _answers(transport: Transport) -> bool:
    try:
        return Link(transport).ask("ID", timeout=1.0) == PROTOCOL
    except (TimeoutError, RuntimeError):
        return False


def find_port() -> str:
    """The serial port the firmware answers `ID` on.

    CircuitPython shows two ports, the REPL console and the data channel, and the
    OS numbers them differently on every machine. Asking is the one test that
    does not depend on how a given OS names them. Espressif's ports go first.
    """
    from serial.tools import list_ports

    ports = sorted(list_ports.comports(), key=lambda p: p.vid != ESPRESSIF_VID)
    for p in ports:
        try:
            t = open_port(p.device)
        except OSError:
            continue
        try:
            if _answers(t):
                return p.device
        finally:
            t.close()
    raise RuntimeError(
        "no port answered ID. Is the cable in the port marked USB, is code.py on "
        "CIRCUITPY with its drivers, and has the board finished booting?"
    )


def connect(device: str) -> tuple[SerialSensor, SerialLamp]:
    """Sensor and lamp on one link. `device` is a port path, or `auto`."""
    transport = open_port(find_port() if device == "auto" else device)
    link = Link(transport)
    got = link.ask("ID")
    if got != PROTOCOL:
        raise RuntimeError(f"{device} answered {got!r}, not {PROTOCOL!r}: wrong port or old code.py")
    return SerialSensor(link), SerialLamp(link)
