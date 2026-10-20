"""Tests for `spectra.capture`.

No test here imports `adafruit_as7341` or `adafruit_tlc59711`; `hw.RealSensor` and
`hw.RealLamp` import those lazily inside their constructors and are not exercised
by this suite at all. What is tested is the maths in `cycle.py`, the session round
trip, and the CLI end to end against `hw.FakeSensor`/`hw.FakeLamp`, all of which is
provable without any hardware. `RealSensor`/`RealLamp` are validated on the Pi.
"""

from __future__ import annotations

import csv
import subprocess
import sys

import pytest

from spectra.capture import cycle, hw, session


class _StubSensor:
    """A sensor that always returns the same reading. For the saturation test."""

    def __init__(self, reading: hw.Channels, full_scale_value: int = 65535) -> None:
        self._reading = reading
        self._full_scale = full_scale_value

    def configure(self, gain: int, atime: int, astep: int) -> None:
        pass

    def read(self) -> hw.Channels:
        return self._reading

    @property
    def full_scale(self) -> int:
        return self._full_scale


class _StubLamp:
    def set(self, channel: int, level: float) -> None:
        pass

    def off(self) -> None:
        pass


class TestHwFormulas:
    def test_full_scale_caps_at_16_bit(self):
        # (255+1) * (65534+1) is far above 65535 and must clip there.
        assert hw.full_scale(255, 65534) == 65535

    def test_full_scale_below_cap(self):
        assert hw.full_scale(atime=9, astep=9) == 100

    def test_integration_time_scales_with_atime_and_astep(self):
        # (99+1) * (999+1) * 2.78us = 278000us = 278ms
        assert hw.integration_time_ms(99, 999) == pytest.approx(278.0)


class TestReflectance:
    def _channels(self, value: int) -> hw.Channels:
        return hw.Channels(
            f1=value, f2=value, f3=value, f4=value, f5=value, f6=value, f7=value, f8=value,
            clear=value, nir=value,
        )

    def test_formula_is_sample_minus_dark_over_white_minus_dark(self):
        dark_ch = self._channels(10)
        white_ch = self._channels(110)
        sample_ch = self._channels(60)
        result = cycle.reflectance(sample_ch, dark_ch, white_ch)
        assert len(result) == 8
        assert result == pytest.approx((0.5,) * 8)

    def test_only_the_eight_f_channels_are_returned(self):
        # clear and nir do not get a reflectance; result must be exactly 8 long.
        dark_ch = self._channels(0)
        white_ch = self._channels(100)
        sample_ch = self._channels(25)
        assert len(cycle.reflectance(sample_ch, dark_ch, white_ch)) == 8

    def test_nonpositive_denominator_is_an_error_not_a_nan(self):
        dark_ch = self._channels(50)
        white_ch = self._channels(50)  # white == dark on every channel
        sample_ch = self._channels(50)
        with pytest.raises(ValueError):
            cycle.reflectance(sample_ch, dark_ch, white_ch)

    def test_white_below_dark_is_also_an_error(self):
        dark_ch = self._channels(50)
        white_ch = self._channels(40)
        sample_ch = self._channels(50)
        with pytest.raises(ValueError):
            cycle.reflectance(sample_ch, dark_ch, white_ch)


class TestSaturation:
    def test_a_channel_at_90_percent_of_full_scale_aborts(self):
        # full_scale 65535, 90% floor is 58981.5; 60000 is over it.
        reading = hw.Channels(
            f1=1, f2=2, f3=3, f4=4, f5=5, f6=6, f7=7, f8=60000, clear=9, nir=9
        )
        sensor = _StubSensor(reading, full_scale_value=65535)
        lamp = _StubLamp()
        with pytest.raises(cycle.SaturationError, match="f8"):
            cycle.dark(sensor, lamp, n=1, settle_s=0.0)

    def test_a_channel_just_under_the_floor_does_not_abort(self):
        reading = hw.Channels(
            f1=1, f2=2, f3=3, f4=4, f5=5, f6=6, f7=7, f8=58000, clear=9, nir=9
        )
        sensor = _StubSensor(reading, full_scale_value=65535)
        lamp = _StubLamp()
        result = cycle.dark(sensor, lamp, n=1, settle_s=0.0)
        assert result.f8 == 58000


class TestCycleWithFakes:
    def test_dark_turns_the_lamp_off(self):
        lamp = hw.FakeLamp()
        lamp.set(0, 1.0)
        sensor = hw.FakeSensor(lamp)
        sensor.configure(gain=8, atime=100, astep=999)
        cycle.dark(sensor, lamp, n=3, settle_s=0.0)
        assert lamp.is_on is False

    def test_white_turns_the_named_channel_on_at_the_given_level(self):
        lamp = hw.FakeLamp()
        sensor = hw.FakeSensor(lamp)
        sensor.configure(gain=8, atime=100, astep=999)
        cycle.white(sensor, lamp, channel=0, level=0.75, n=3, settle_s=0.0)
        assert lamp.channel == 0
        assert lamp.level == 0.75

    def test_lit_reads_higher_than_dark(self):
        lamp = hw.FakeLamp()
        sensor = hw.FakeSensor(lamp)
        sensor.configure(gain=8, atime=100, astep=999)
        dark_ch = cycle.dark(sensor, lamp, n=5, settle_s=0.0)
        white_ch = cycle.white(sensor, lamp, channel=0, level=1.0, n=5, settle_s=0.0)
        for name in ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"):
            assert getattr(white_ch, name) > getattr(dark_ch, name)


class TestSessionRoundTrip:
    def _dark_and_white(self):
        dark_ch = hw.Channels(f1=10, f2=10, f3=10, f4=10, f5=10, f6=10, f7=10, f8=10, clear=10, nir=10)
        white_ch = hw.Channels(
            f1=110, f2=120, f3=130, f4=140, f5=150, f6=160, f7=170, f8=180, clear=200, nir=90
        )
        return dark_ch, white_ch

    def test_write_then_read_back_gives_the_same_numbers(self, tmp_path):
        dark_ch, white_ch = self._dark_and_white()
        directory = tmp_path / "session"
        written = session.create(
            directory,
            gain=8,
            atime=100,
            astep=999,
            lamp_channel=0,
            lamp_level=1.0,
            settle_s=0.2,
            n=5,
            dark=dark_ch,
            white=white_ch,
            notes="a test session",
        )

        record = session.load(directory)
        assert record == written
        assert session.dark_channels(record) == dark_ch
        assert session.white_channels(record) == white_ch
        assert record["sensor"]["gain"] == 8
        assert record["sensor"]["integration_time_ms"] == pytest.approx(
            hw.integration_time_ms(100, 999)
        )
        assert record["lamp"] == {"channel": 0, "level": 1.0}
        assert record["notes"] == "a test session"

    def test_refuses_to_overwrite_an_existing_session(self, tmp_path):
        dark_ch, white_ch = self._dark_and_white()
        directory = tmp_path / "session"
        session.create(
            directory, gain=8, atime=100, astep=999, lamp_channel=0, lamp_level=1.0,
            settle_s=0.2, n=5, dark=dark_ch, white=white_ch,
        )
        with pytest.raises(FileExistsError):
            session.create(
                directory, gain=8, atime=100, astep=999, lamp_channel=0, lamp_level=1.0,
                settle_s=0.2, n=5, dark=dark_ch, white=white_ch,
            )

    def test_readings_csv_starts_with_the_declared_header(self, tmp_path):
        dark_ch, white_ch = self._dark_and_white()
        directory = tmp_path / "session"
        session.create(
            directory, gain=8, atime=100, astep=999, lamp_channel=0, lamp_level=1.0,
            settle_s=0.2, n=5, dark=dark_ch, white=white_ch,
        )
        with (directory / "readings.csv").open() as f:
            header = next(csv.reader(f))
        assert header == session.READINGS_HEADER

    def test_append_reading_then_read_rows_round_trips(self, tmp_path):
        dark_ch, white_ch = self._dark_and_white()
        directory = tmp_path / "session"
        session.create(
            directory, gain=8, atime=100, astep=999, lamp_channel=0, lamp_level=1.0,
            settle_s=0.2, n=5, dark=dark_ch, white=white_ch,
        )
        sample_ch = hw.Channels(
            f1=60, f2=65, f3=70, f4=75, f5=80, f6=85, f7=90, f8=95, clear=100, nir=50
        )
        refl = cycle.reflectance(sample_ch, dark_ch, white_ch)
        session.append_reading(directory, "chip-1", sample_ch, refl)

        rows = session.read_rows(directory)
        assert len(rows) == 1
        row = rows[0]
        assert row["sample_id"] == "chip-1"
        assert int(row["f1"]) == 60
        assert float(row["r_f1"]) == pytest.approx(refl[0])
        assert float(row["r_f8"]) == pytest.approx(refl[7])


class TestCliEndToEnd:
    """Runs the real `python -m spectra.capture --fake ...` entry point.

    Subprocess, not a direct call into `main()`, because this is the same
    interface the done test in the spec runs and the same interface a human runs
    on the bench; a direct call could pass CI while the console script does not.
    stdin is closed rather than piped, which is exactly what happens when this is
    run from a non-interactive harness: `_prompt` treats the resulting EOFError as
    an operator who pressed Enter immediately.
    """

    def _run(self, *args: str, timeout: float = 30) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "spectra.capture", *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def test_session_new_then_repeat(self, tmp_path):
        session_dir = tmp_path / "s"

        new_result = self._run("--fake", "session", "new", str(session_dir))
        assert new_result.returncode == 0, new_result.stderr
        assert (session_dir / "session.json").exists()
        assert (session_dir / "readings.csv").exists()

        repeat_result = self._run(
            "--fake", "repeat", str(session_dir), "black-pla", "--count", "10"
        )
        assert repeat_result.returncode == 0, repeat_result.stderr
        assert "Worst channel" in repeat_result.stdout

        with (session_dir / "readings.csv").open() as f:
            reader = csv.reader(f)
            header = next(reader)
            data_rows = list(reader)

        assert header == session.READINGS_HEADER
        assert len(data_rows) == 10
        assert all(row[0] == "black-pla" for row in data_rows)

    def test_import_spectra_capture_needs_no_adafruit_library(self):
        result = subprocess.run(
            [sys.executable, "-c", "import spectra.capture; print('ok')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert "ok" in result.stdout
