#!/usr/bin/env bash
# Put CircuitPython and the SPECTRA bridge on an ESP32-S3-DevKitC-1, end to end.
#
#   firmware/circuitpython/flash.sh                 # flash, install, check
#   firmware/circuitpython/flash.sh --port /dev/cu.usbmodemXXXX
#   firmware/circuitpython/flash.sh --no-flash      # files and drivers only
#
# Start with the cable in the port marked COM. The script reads the chip's flash and
# PSRAM with esptool, picks the matching CircuitPython build, flashes it, then asks
# for the one physical step: move the cable to the port marked USB. It copies
# code.py onto CIRCUITPY, installs the two drivers with circup, and
# after a press of RST asks the board for ID and one READ.
#
# First run on 2026-10-05, Jared's board: ESP32-S3 rev 0.2, 16 MB flash, 8 MB PSRAM.
# There is no N16R8 build, so it took N8R8, which runs on the larger flash.
set -euo pipefail

CP_VERSION="${CP_VERSION:-10.3.1}"   # the release the bridge was brought up on, 2026-10-15
VENV="${SPECTRA_ESP_VENV:-$HOME/.venvs/esp}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT=""
FLASH=1
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --no-flash) FLASH=0; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -x "$VENV/bin/esptool" ] || { python3 -m venv "$VENV"; "$VENV/bin/pip" -q install esptool circup pyserial; }
ESPTOOL="$VENV/bin/esptool"

ports() { ls /dev/cu.usbmodem* /dev/cu.usbserial* /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true; }

if [ "$FLASH" = 1 ]; then
  if [ -z "$PORT" ]; then
    set -- $(ports)
    [ $# -eq 1 ] || { echo "found $# serial ports; pass --port: $*" >&2; exit 1; }
    PORT="$1"
  fi
  info="$("$ESPTOOL" --port "$PORT" flash-id 2>&1)" || {
    echo "$info" | tail -3
    echo "esptool could not reach the chip. If another program (a browser tab) holds the port, close it. Otherwise hold BOOT, tap RST, release BOOT, and run again." >&2
    exit 1; }
  echo "$info" | grep -E "Chip type|Features|Detected flash size"
  flash_mb="$(echo "$info" | sed -n 's/.*Detected flash size: \([0-9]*\)MB.*/\1/p')"
  psram_mb="$(echo "$info" | sed -n 's/.*PSRAM \([0-9]*\)MB.*/\1/p')"
  case "${psram_mb:-0}:$flash_mb" in
    8:32) BOARD=n32r8 ;;
    8:*)  BOARD=n8r8 ;;
    2:*)  BOARD=n8r2 ;;
    0:16) BOARD=n16 ;;
    *)    BOARD=n8 ;;
  esac
  BIN="adafruit-circuitpython-espressif_esp32s3_devkitc_1_${BOARD}-en_US-${CP_VERSION}.bin"
  CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/spectra"; mkdir -p "$CACHE"
  [ -s "$CACHE/$BIN" ] || curl -fsSL -o "$CACHE/$BIN" \
    "https://downloads.circuitpython.org/bin/espressif_esp32s3_devkitc_1_${BOARD}/en_US/$BIN"
  echo "flashing $BIN"
  "$ESPTOOL" --port "$PORT" erase-flash | tail -1
  "$ESPTOOL" --port "$PORT" --baud 921600 write-flash -z 0x0 "$CACHE/$BIN" | grep -E "Wrote|verified"
  echo
  echo ">>> Move the cable to the port marked USB."
fi

DRIVE=""
echo "waiting for the CIRCUITPY drive"
for _ in $(seq 1 120); do
  for d in /Volumes/CIRCUITPY "/media/$USER/CIRCUITPY" "/run/media/$USER/CIRCUITPY"; do
    [ -d "$d" ] && DRIVE="$d" && break 2
  done
  sleep 2
done
[ -d "$DRIVE" ] || { echo "no CIRCUITPY drive after 4 minutes; is the cable in the port marked USB?" >&2; exit 1; }

# No boot.py: the default USB setup (console + drive) is the one macOS configures.
# A boot.py left from an older flash would bring the data channel back, so it goes.
rm -f "$DRIVE/boot.py"
cp "$HERE/code.py" "$DRIVE/" && sync
"$VENV/bin/circup" --path "$DRIVE" install adafruit_as7341 adafruit_tlc59711
echo
echo ">>> Press RST once, so code.py starts with its drivers in place."

"$VENV/bin/python" - <<'EOF'
import glob, time
import serial
deadline = time.time() + 120
while time.time() < deadline:
    for port in sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*")):
        try:
            s = serial.Serial(port, 115200, timeout=2)
            s.reset_input_buffer(); s.write(b"ID\n"); time.sleep(0.5)
            if s.readline().startswith(b"SPECTRA"):
                s.write(b"READ\n")
                print(f"bridge on {port}; READ -> {s.readline().decode().strip()}")
                raise SystemExit(0)
        except (OSError, serial.SerialException):
            pass
    time.sleep(2)
raise SystemExit("the bridge never answered ID; open the USB port at 115200 and press Ctrl-D to see why")
EOF
