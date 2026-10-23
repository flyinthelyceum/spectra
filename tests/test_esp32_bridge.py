"""The ESP32 bridge: `firmware/circuitpython/code.py` and `spectra.capture.serial_hw`.

The firmware's command handler is plain Python with its hardware behind a `Head`,
so it is loaded here and driven through a loopback in place of the USB cable. What
is asserted is that the bridge is transparent: a measurement taken through it is
the measurement taken without it, and every failure on the board arrives at the
host as an exception rather than a wrong number. Nothing here touches a real
AS7341 or TLC59711; those are proved on the bench (`process/FIRST_BUILD.md`).
"""

from __future__ import annotations

import importlib.util
from dataclasses import astuple, fields
from pathlib import Path

import pytest

from spectra.capture import cycle, hw, serial_hw

FIRMWARE = Path(__file__).resolve().parent.parent / "firmware" / "circuitpython" / "code.py"


def _load_firmware():
    spec = importlib.util.spec_from_file_location("spectra_esp32_code", FIRMWARE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # defines things only; main() is behind __name__
    return module


fw = _load_firmware()


class FakeHead:
    """The firmware's `Head`, backed by the package's own fakes."""

    def __init__(self) -> None:
        self.lamp = hw.FakeLamp()
        self.sensor = hw.FakeSensor(self.lamp)
        self.words: dict[int, int] = {}

    def configure(self, gain, atime, astep):
        self.sensor.configure(gain, atime, astep)

    def read(self):
        return astuple(self.sensor.read())

    def set(self, channel, word):
        self.words[channel] = word
        self.lamp.set(channel, word / 65535)

    def off(self):
        self.words.clear()
        self.lamp.off()


class Loopback:
    """Stands in for the USB cable: each written line is answered by `handle`."""

    def __init__(self, head, silent: bool = False) -> None:
        self.head = head
        self.silent = silent
        self.timeout = None
        self.sent: list[str] = []
        self._pending = b""

    def write(self, data: bytes) -> int:
        line = data.decode()
        self.sent.append(line.strip())
        if not self.silent:
            reply = fw.handle(line, self.head)
            if reply is not None:
                self._pending += (reply + "\n").encode()
        return len(data)

    def readline(self) -> bytes:
        out, _, rest = self._pending.partition(b"\n")
        if not _:
            return out  # no newline: what pyserial returns on timeout
        self._pending = rest
        return out + b"\n"


def _pair(head=None):
    head = head or FakeHead()
    link = serial_hw.Link(Loopback(head))
    return serial_hw.SerialSensor(link), serial_hw.SerialLamp(link), head


def test_both_ends_agree_on_the_protocol_and_the_gain_table():
    assert fw.PROTOCOL == serial_hw.PROTOCOL
    assert tuple(fw.GAIN_NAMES) == hw.RealSensor._GAIN_NAMES


def test_a_measurement_through_the_bridge_is_the_measurement_without_it():
    """Same dark, white and sample, same reflectance, to the last count."""
    sensor, lamp, _ = _pair()
    direct_lamp = hw.FakeLamp()
    direct_sensor = hw.FakeSensor(direct_lamp)
    for s in (sensor, direct_sensor):
        s.configure(8, 100, 999)
    # The wire carries a 16-bit word, so the direct run is given the level that
    # word stands for; anything else would compare quantisation, not the bridge.
    half = round(0.5 * 65535) / 65535
    results = []
    for s, l, level in ((sensor, lamp, 0.5), (direct_sensor, direct_lamp, half)):
        d = cycle.dark(s, l, 3, settle_s=0)
        w = cycle.white(s, l, 0, 1.0, 3, settle_s=0)
        x = cycle.sample(s, l, 0, level, 3, settle_s=0)
        results.append((d, w, x, cycle.reflectance(x, d, w)))
    assert results[0] == results[1]


def test_every_channel_survives_the_wire_in_order():
    head = FakeHead()
    sensor, _, _ = _pair(head)
    names = [f.name for f in fields(hw.Channels)]
    # Distinct values per channel, so a swapped pair cannot pass.
    head.read = lambda: tuple(1000 + 7 * i for i in range(len(names)))
    got = sensor.read()
    assert [getattr(got, n) for n in names] == [1000 + 7 * i for i in range(len(names))]


def test_lamp_level_maps_onto_the_full_pwm_word_and_keeps_order():
    sensor, lamp, head = _pair()
    words = []
    for level in (0.0, 0.25, 0.5, 0.75, 1.0):
        lamp.set(3, level)
        words.append(head.words[3])
    assert words[0] == 0 and words[-1] == 65535
    assert words == sorted(words) and len(set(words)) == len(words)
    lamp.off()
    assert head.words == {} and not head.lamp.is_on


def test_full_scale_follows_configure():
    sensor, _, _ = _pair()
    sensor.configure(4, 29, 599)
    assert sensor.full_scale == hw.full_scale(29, 599)


@pytest.mark.parametrize("line", ["CFG 11 100 999", "CFG 8 300 999", "SET 12 1", "SET 0 70000", "SET 0", "READ 1", "BLINK"])
def test_the_board_refuses_bad_commands_and_the_host_raises(line):
    link = serial_hw.Link(Loopback(FakeHead()))
    with pytest.raises(RuntimeError):
        link.ask(line)


@pytest.mark.parametrize("line", ["", "   ", "CFG a b c", "SET -1 -1", "\x00\xff", "READ READ READ"])
def test_handle_never_raises(line):
    reply = fw.handle(line, FakeHead())
    assert reply is None or reply.startswith(("ERR", "OK", "CH", "SPECTRA"))


def test_a_hardware_fault_on_the_board_reaches_the_host():
    class Broken(FakeHead):
        def read(self):
            raise OSError("No I2C device at address: 0x39")

    sensor, _, _ = _pair(Broken())
    with pytest.raises(RuntimeError, match="0x39"):
        sensor.read()


def test_silence_is_an_error_not_a_reading():
    link = serial_hw.Link(Loopback(FakeHead(), silent=True))
    with pytest.raises(TimeoutError):
        serial_hw.SerialSensor(link).read()


def test_host_rejects_out_of_range_values_before_sending():
    sensor, lamp, head = _pair()
    transport = sensor._link._t
    with pytest.raises(ValueError):
        sensor.configure(11, 100, 999)
    with pytest.raises(ValueError):
        lamp.set(12, 0.5)
    with pytest.raises(ValueError):
        lamp.set(0, 1.5)
    assert transport.sent == []


@pytest.mark.parametrize("atime, astep", [(255, 65534), (100, 3600), (255, 1500)])
def test_integrations_the_driver_cannot_wait_for_are_refused_at_both_ends(atime, astep):
    """The Adafruit driver waits 1 s for data; a longer pass can only error."""
    assert hw.integration_time_ms(atime, astep) >= hw.MAX_PASS_MS
    sensor, _, _ = _pair()
    with pytest.raises(ValueError):
        sensor.configure(8, atime, astep)
    assert fw.handle(f"CFG 8 {atime} {astep}", FakeHead()).startswith("ERR")


def test_the_board_lights_one_channel_at_a_time():
    """SET means this channel alone; the driver latches, so the rest are cleared."""

    class TLC:
        def __init__(self):
            self.words = [0] * 12
            self.frames = []

        def set_channel(self, i, v):
            self.words[i] = v

        def show(self):
            self.frames.append(list(self.words))

    head = object.__new__(fw.Head)
    head._tlc = tlc = TLC()
    for ch in (0, 5, 2):
        assert fw.handle(f"SET {ch} 65535", head) == "OK"
        assert [i for i, v in enumerate(tlc.frames[-1]) if v] == [ch]
    assert all(sum(1 for v in f if v) <= 1 for f in tlc.frames)
