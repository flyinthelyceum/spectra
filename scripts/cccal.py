"""SPECTRA ColorChecker calibration session: per-LED exposure, white, 24 patches.

Walks the operator through one session on a ColorChecker Classic and writes
cccal-<time>.json in the current directory. Nothing is fitted here; the JSON is
the raw record (dark, white and patch counts per LED, with the exposure each LED
ran at) and the colour model is scored from it afterwards.

Steps, each one prompted:
  1. Head on patch 19 (white). Warm-up, then each LED gets its own exposure:
     gain and integration chosen so its brightest band sits near 60% of full
     scale on the white patch. Nothing on the chart reads brighter than 19.
  2. Dark for every LED's exposure, LEDs off, head still on 19.
  3. White repeatability: lift the head and set it back on 19, five times.
  4. Patches 1 to 24 in order, one placement each.
  5. Patch 19 again, for drift over the session, then dark again.

Run from the repo root on the machine the board is plugged into:
    python scripts/cccal.py
Ctrl-C at any prompt stops cleanly; whatever was measured is still written.
"""
import json, statistics, time
from datetime import datetime
from spectra.capture import serial_hw as s
from spectra.capture.hw import full_scale, integration_time_ms, MAX_PASS_MS

F = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8")
K = F + ("clear", "nir")
LEDS = {
    0: "white C513A",
    1: "400 UV MT5400",
    2: "460 blue WP7113QBC",
    3: "501 cyan HLMP-CE34",
    4: "565 green WP7113SGC",
    5: "590 yellow WP7113SYCK",
    6: "625 red WP7113SEC",
    7: "660 deep red WP7113SRD",
}
PATCHES = {
    1: "dark skin", 2: "light skin", 3: "blue sky", 4: "foliage", 5: "blue flower",
    6: "bluish green", 7: "orange", 8: "purplish blue", 9: "moderate red", 10: "purple",
    11: "yellow green", 12: "orange yellow", 13: "blue", 14: "green", 15: "red",
    16: "yellow", 17: "magenta", 18: "cyan", 19: "white 9.5", 20: "neutral 8",
    21: "neutral 6.5", 22: "neutral 5", 23: "neutral 3.5", 24: "black 2",
}
ATIME = 29
ASTEPS = (599, 1199, 2399, 4799, 9599)  # 50 to 800 ms per pass at ATIME 29
TARGET = 0.6  # brightest band on patch 19, as a fraction of full scale
CEIL = 0.8    # above this on patch 19 the exposure is rejected
FLOOR = 0.3   # below this the gain is stepped up
SETTLE_S = 0.3
WARMUP_S = 120
N_WHITE, N_PATCH, PLACEMENTS = 5, 3, 5

S, L = s.connect("auto")
cfg_now = None


def cfg(c):
    global cfg_now
    if c != cfg_now:
        S.configure(c["gain"], ATIME, c["astep"])
        cfg_now = c


def read_avg(n):
    rows = [S.read() for _ in range(n)]
    out = {}
    for k in K:
        v = [getattr(r, k) for r in rows]
        out[k] = statistics.fmean(v)
        out[k + "_sd"] = statistics.stdev(v) if n > 1 else 0.0
    return out


def lit(ch, c, n):
    cfg(c)
    L.set(ch, 1.0)
    time.sleep(SETTLE_S)
    r = read_avg(n)
    L.off()
    return r


def dark(c, n):
    cfg(c)
    L.off()
    time.sleep(SETTLE_S)
    return read_avg(n)


def peak(r):
    return max(r[f] for f in F)


def expose(ch):
    """Pick gain and ASTEP so this LED's brightest band lands near TARGET on white."""
    probe = {"gain": 4, "astep": 599}  # 8x, 50 ms: nothing in the ring saturates here
    p = peak(lit(ch, probe, 2)) - peak(dark(probe, 2))
    per_unit = max(p, 0.5) / (2 ** (probe["gain"] - 1) * (probe["astep"] + 1))
    best = None
    for astep in ASTEPS:
        if integration_time_ms(ATIME, astep) >= MAX_PASS_MS:
            continue
        fs = full_scale(ATIME, astep)
        for g in range(10, -1, -1):
            pred = per_unit * 2 ** (g - 1) * (astep + 1)
            if pred <= TARGET * fs:
                # prefer the shortest integration that reaches the target: less drift per read
                score = (pred / fs, -astep)
                if best is None or score > best[0]:
                    best = (score, {"gain": g, "astep": astep})
                break
    c = best[1]
    for _ in range(4):  # verify against a real read; step gain to correct the prediction
        fs = full_scale(ATIME, c["astep"])
        got = peak(lit(ch, c, 2))
        if got > CEIL * fs and c["gain"] > 0:
            c = {"gain": c["gain"] - 1, "astep": c["astep"]}
        elif got < FLOOR * fs and c["gain"] < 10 and 2 * got <= CEIL * fs:
            c = {"gain": c["gain"] + 1, "astep": c["astep"]}
        else:
            break
    c["fs"] = full_scale(ATIME, c["astep"])
    c["ms"] = round(integration_time_ms(ATIME, c["astep"]), 1)
    c["peak_frac"] = round(got / c["fs"], 3)
    return c


def ask(msg):
    input("\n>>> " + msg + "  [Enter] ")


def placement(label, patch, n):
    t0 = time.time()
    rec = {"label": label, "patch": patch, "t": t0, "leds": {}}
    for ch, c in EXP.items():
        rec["leds"][ch] = lit(ch, c, n)
    rec["dur_s"] = round(time.time() - t0, 1)
    return rec


def show(rec, white):
    """One line: per LED, its peak band as a fraction of the session's white."""
    parts = []
    for ch, r in rec["leds"].items():
        w = white[ch]
        d = DARK0[ch]
        bands = [(r[f] - d[f]) / max(w[f] - d[f], 1e-9) for f in F]
        k = max(range(8), key=lambda i: w[F[i]] - d[F[i]])
        parts.append("%d:%.2f" % (ch, bands[k]))
    print("    %s  (%.0f s)" % ("  ".join(parts), rec["dur_s"]))


out = {
    "kind": "cccal", "version": 1, "started": datetime.now().isoformat(timespec="seconds"),
    "atime": ATIME, "leds": LEDS, "patches": PATCHES, "white_ref_patch": 19,
    "exposure": {}, "dark_start": {}, "white_placements": [], "patch_reads": [],
    "white_end": None, "dark_end": {}, "notes": [],
}
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
path = "cccal-%s.json" % stamp


def save():
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)


try:
    print("SPECTRA ColorChecker session. Dim the room; the head should sit flat with no light leaking in.")
    ask("Put the head on patch 19 (white, bottom row, far left).")
    print("  warm-up: cycling all eight LEDs for %d s" % WARMUP_S)
    end = time.time() + WARMUP_S
    while time.time() < end:
        for ch in LEDS:
            L.set(ch, 1.0)
            time.sleep(1.0)
    L.off()

    print("  exposure per LED on patch 19:")
    EXP = {}
    for ch in LEDS:
        EXP[ch] = expose(ch)
        c = EXP[ch]
        print("    ch%d %-24s gain %2d  %6.1f ms  peak %.2f of full scale" % (ch, LEDS[ch], c["gain"], c["ms"], c["peak_frac"]))
    out["exposure"] = EXP
    DARK0 = {ch: dark(c, N_WHITE) for ch, c in EXP.items()}
    out["dark_start"] = DARK0
    save()

    print("  white repeatability: %d placements on 19" % PLACEMENTS)
    for i in range(PLACEMENTS):
        if i:
            ask("Lift the head clear and set it back down on patch 19 (%d of %d)." % (i + 1, PLACEMENTS))
        rec = placement("white-%d" % (i + 1), 19, N_WHITE)
        out["white_placements"].append(rec)
        save()
        print("    placement %d done (%.0f s)" % (i + 1, rec["dur_s"]))
    WHITE = {ch: {f: statistics.fmean(p["leds"][ch][f] for p in out["white_placements"]) for f in F} for ch in LEDS}

    for n in range(1, 25):
        ask("Patch %d, %s." % (n, PATCHES[n]))
        rec = placement("patch-%d" % n, n, N_PATCH)
        out["patch_reads"].append(rec)
        save()
        show(rec, WHITE)

    ask("Back to patch 19 for the drift check.")
    out["white_end"] = placement("white-end", 19, N_WHITE)
    out["dark_end"] = {ch: dark(c, N_WHITE) for ch, c in EXP.items()}
    show(out["white_end"], WHITE)
except KeyboardInterrupt:
    out["notes"].append("stopped by operator")
    print("\nstopped.")
finally:
    try:
        L.off()
    except Exception:
        pass
    out["finished"] = datetime.now().isoformat(timespec="seconds")
    save()
    print("\nwrote %s" % path)
