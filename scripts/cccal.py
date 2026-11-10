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
  3. White repeatability: lift the head and set it back on 19, five times. The
     first two must agree within 1.5% or the session asks for a reseat; three
     failed tries stop it, because nothing after that can be trusted.
  4. Patches 1 to 24 in order. Each patch is read, lifted and reseated, and read
     again; if any LED's peak differs by more than 2% a third read is taken.
     Each patch is also checked against what it should look like (the red patch
     peaks on a red LED, each grey is darker than the one before), and a patch
     that fails is asked for again, so a misplaced puck is caught at the chart.
  5. Patch 19 again, for drift over the session, then dark again.

Run from the repo root on the machine the board is plugged into:
    python scripts/cccal.py                      # full card, no adapter
    python scripts/cccal.py --adapter collar-v1  # tag the run with what was fitted
    python scripts/cccal.py --dark-each          # LEDs-off read after every placement
Ctrl-C at any prompt stops cleanly; whatever was measured is still written.

Lift and place only. Never slide the puck across the card: it scratches the patches.
"""
import argparse, json, statistics, sys, termios, time
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
ORD = ("1st", "2nd", "3rd", "4th", "5th", "6th")


def where_classic(n):
    """Full card, landscape, patch 1 top left, white 19 bottom left."""
    row, col = (n - 1) // 6 + 1, (n - 1) % 6 + 1
    return "row %d from the top, %s from the left" % (row, ORD[col - 1])


def where_mini_case(n):
    """Classic Mini glued in its hinged case, hinge on the left."""
    col, up = (n - 1) // 6 + 1, (n - 1) % 6 + 1
    return "column %d from the hinge, %s up" % (col, ORD[up - 1])


LAYOUTS = {"classic": where_classic, "mini-case": where_mini_case}

# Which LEDs a patch's strongest return may come from, relative to white. Only the
# patches whose colour leaves no doubt; the rest are checked by the reseat alone.
# LED numbers as in LEDS: 1 400, 2 460, 3 501, 4 565, 5 590, 6 625, 7 660.
PEAK_ON = {
    3: {1, 2, 3}, 6: {2, 3, 4}, 7: {6, 7}, 8: {1, 2}, 9: {6, 7}, 12: {5, 6, 7},
    13: {1, 2}, 14: {3, 4}, 15: {6, 7}, 16: {5, 6, 7}, 17: {1, 2, 6, 7}, 18: {2, 3},
}
GREYS = (19, 20, 21, 22, 23, 24)

ATIME = 29
ASTEPS = (599, 1199, 2399, 4799, 9599)  # 50 to 800 ms per pass at ATIME 29
TARGET = 0.6  # brightest band on patch 19, as a fraction of full scale
CEIL = 0.8    # above this on patch 19 the exposure is rejected
FLOOR = 0.3   # below this the gain is stepped up
SETTLE_S = 0.3
WARMUP_S = 120
N_WHITE, N_PATCH, PLACEMENTS = 5, 3, 5
RESEAT_TOL = 0.02   # two reads of one patch agree if every LED's peak is within this
GATE_TOL = 0.015    # the first two white placements must agree this closely
GATE_TRIES = 3
PATCH_TRIES = 3     # placements before a patch that fails its check is recorded anyway
ENTER_GUARD_S = 1.5

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--layout", choices=sorted(LAYOUTS), default="classic")
ap.add_argument("--adapter", default="none", help="what is fitted to the puck, e.g. collar-v1")
ap.add_argument("--standoff", type=float, default=1.2, help="port face above the patch, mm (the lip)")
ap.add_argument("--port", default="auto")
ap.add_argument("--dark-each", action="store_true", help="LEDs-off read after every placement, room lights as they are")
args = ap.parse_args()
where = LAYOUTS[args.layout]

try:
    S, L = s.connect(args.port)
except RuntimeError:
    time.sleep(2)  # a board that has just rebooted can miss the first ID
    S, L = s.connect(args.port)
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
    """Prompt and wait for Enter. Keys pressed before the prompt, or within
    ENTER_GUARD_S of it, are thrown away, so a held or doubled Enter cannot read
    the wrong patch."""
    print("\n>>> " + msg + "  [Enter] ", end="", flush=True)
    t0 = time.time()
    while True:
        if sys.stdin.isatty():
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        sys.stdin.readline()
        if time.time() - t0 >= ENTER_GUARD_S:
            return
        t0 = time.time()
        print("    (too quick; set the puck down, then Enter) ", end="", flush=True)


def placement(label, patch, n):
    t0 = time.time()
    rec = {"label": label, "patch": patch, "t": t0, "leds": {}}
    print("    reading %s: LED" % label, end="", flush=True)  # a placement runs ~1-2 min; show it is alive
    for ch, c in EXP.items():
        rec["leds"][ch] = lit(ch, c, n)
        print(" %d" % ch, end="", flush=True)
    if args.dark_each:
        rec["dark"] = {ch: dark(c, 1) for ch, c in EXP.items()}
        print(" dark", end="", flush=True)
    rec["dur_s"] = round(time.time() - t0, 1)
    print(" (%.0f s)" % rec["dur_s"])
    return rec


def rel(rec, white):
    """Per LED: its strongest white band, on this placement, as a fraction of white."""
    out = {}
    for ch, r in rec["leds"].items():
        w, d = white[ch], DARK0[ch]
        k = max(F, key=lambda f: w[f] - d[f])
        out[ch] = (r[k] - d[k]) / max(w[k] - d[k], 1e-9)
    return out


def worst_gap(a, b):
    """Largest per-LED peak difference between two placements, as a fraction."""
    return max(abs(peak(a["leds"][ch]) - peak(b["leds"][ch])) / max(peak(a["leds"][ch]), peak(b["leds"][ch]), 1e-9)
               for ch in a["leds"])


def show(rec, white):
    """One line: per LED, its peak band as a fraction of the session's white."""
    r = rel(rec, white)
    print("    %s  (%.0f s)" % ("  ".join("%d:%.2f" % (ch, v) for ch, v in r.items()), rec["dur_s"]))


def looks_wrong(n, r, prev_grey):
    """A reason this read is not patch n, or None. r is rel() of the read."""
    if n != 19 and min(r.values()) > 0.8:
        return "reads like the white patch (every LED above 0.8 of white)"
    if n in PEAK_ON:
        top = max((ch for ch in r if ch), key=lambda ch: r[ch])  # coloured LEDs only
        if top not in PEAK_ON[n]:
            return "brightest on LED %d (%s), expected one of %s" % (top, LEDS[top], sorted(PEAK_ON[n]))
    if n in GREYS[1:] and prev_grey is not None and r[0] > 0.9 * prev_grey:
        return "white LED reads %.2f, not darker than the grey before it (%.2f)" % (r[0], prev_grey)
    return None


def read_patch(n, label):
    """Read, lift and reseat, read again; a third read if the two disagree.
    Returns the reads and the gap between the two that agree best."""
    reads = [placement(label + "-a", n, N_PATCH)]
    ask("Lift and reseat on patch %d." % n)
    reads.append(placement(label + "-b", n, N_PATCH))
    gap = worst_gap(reads[0], reads[1])
    if gap > RESEAT_TOL:
        print("    the two reads differ by %.1f%%; one more" % (100 * gap))
        ask("Lift and reseat on patch %d again." % n)
        reads.append(placement(label + "-c", n, N_PATCH))
        gap, keep = min((worst_gap(reads[i], reads[j]), (i, j)) for i, j in ((0, 1), (0, 2), (1, 2)))
        for i, rd in enumerate(reads):
            rd["kept"] = i in keep
    else:
        for rd in reads:
            rd["kept"] = True
    return reads, gap


def mean_rel(reads, white):
    kept = [rel(rd, white) for rd in reads if rd["kept"]]
    return {ch: statistics.fmean(k[ch] for k in kept) for ch in kept[0]}


out = {
    "kind": "cccal", "version": 2, "started": datetime.now().isoformat(timespec="seconds"),
    "target": args.layout, "adapter": args.adapter, "standoff_mm": args.standoff,
    "dark_each": args.dark_each,
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
    print("SPECTRA ColorChecker session (%s, adapter %s, standoff %.1f mm)." % (args.layout, args.adapter, args.standoff))
    print("Dim the room. Hang the USB cable from above with slack so it doesn't tug the puck.")
    print("Lift and place only; never slide the puck across the card.")
    ask("Put the head on patch 19 (white, %s)." % where(19))
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

    print("  reseat gate: two placements on 19 must agree within %.1f%%" % (100 * GATE_TOL))
    first = placement("white-1", 19, N_WHITE)
    for attempt in range(GATE_TRIES):
        ask("Lift the head clear and set it back down on patch 19.")
        second = placement("white-2", 19, N_WHITE)
        gap = worst_gap(first, second)
        out["notes"].append("reseat gate try %d: %.2f%%" % (attempt + 1, 100 * gap))
        if gap <= GATE_TOL:
            print("    agree within %.2f%%" % (100 * gap))
            break
        print("    differ by %.2f%%. Check the card is flat and the cable isn't pulling." % (100 * gap))
        first = second
    else:
        out["notes"].append("reseat gate failed")
        raise SystemExit("reseat gate failed %d times: fix the seating (flat card, slack cable, or the feet) before calibrating" % GATE_TRIES)
    out["white_placements"] += [first, second]
    save()

    print("  white repeatability: %d placements on 19" % PLACEMENTS)
    for i in range(2, PLACEMENTS):
        ask("Lift the head clear and set it back down on patch 19 (%d of %d)." % (i + 1, PLACEMENTS))
        rec = placement("white-%d" % (i + 1), 19, N_WHITE)
        out["white_placements"].append(rec)
        save()
        print("    placement %d done (%.0f s)" % (i + 1, rec["dur_s"]))
    WHITE = {ch: {f: statistics.fmean(p["leds"][ch][f] for p in out["white_placements"]) for f in F} for ch in LEDS}

    prev_grey = 1.0
    for n in range(1, 25):
        for attempt in range(PATCH_TRIES):
            ask("Patch %d, %s: %s." % (n, PATCHES[n], where(n)))
            reads, gap = read_patch(n, "patch-%d" % n)
            r = mean_rel(reads, WHITE)
            why = looks_wrong(n, r, prev_grey if n in GREYS else None)
            entry = {"patch": n, "attempt": attempt + 1, "reads": reads, "reseat_gap": round(gap, 4), "check": why or "ok"}
            out["patch_reads"].append(entry)
            save()
            print("    %s  reseat %.1f%%" % ("  ".join("%d:%.2f" % (ch, v) for ch, v in r.items()), 100 * gap))
            if why is None:
                break
            print("    doesn't look like patch %d: %s" % (n, why))
            if attempt + 1 < PATCH_TRIES:
                print("    check the puck is on %s and try again." % where(n))
        else:
            out["notes"].append("patch %d kept after %d failed checks" % (n, PATCH_TRIES))
        if n in GREYS:
            prev_grey = r[0]

    ask("Back to patch 19 for the drift check (%s)." % where(19))
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
