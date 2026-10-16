"""SPECTRA full LED test: all eight channels, one at a time, against the AS7341.

Per channel: step gain down from 64x until nothing saturates, read dark and lit
(5 reads each), report lit minus dark per band, the peak band, and brightness
normalised to 1x gain so a dim LED shows up whatever gain it landed on.
Run from the repo root on the machine the board is plugged into:
    python scripts/ledtest.py          # all eight
    python scripts/ledtest.py 4 5      # just these
Writes ledtest-<time>.json in the current directory.
"""
import json, sys, time
from datetime import datetime
from spectra.capture import serial_hw as s

K = ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "clear", "nir")
NAMES = ["f1 415", "f2 445", "f3 480", "f4 515", "f5 555", "f6 590", "f7 630", "f8 680", "clear", "nir"]
# channel: (output, LED, AS7341 bands its peak may land in)
CH = {
    0: ("R3", "white C513A", {"f5", "f6", "f7"}),
    1: ("G3", "400 UV MT5400", {"f1"}),
    2: ("B3", "460 blue WP7113QBC", {"f2", "f3"}),
    3: ("R2", "501 cyan HLMP-CE34", {"f3", "f4"}),
    4: ("G2", "565 green WP7113SGC", {"f5"}),
    5: ("B2", "590 yellow WP7113SYCK", {"f6"}),
    6: ("R1", "625 red WP7113SEC", {"f7"}),
    7: ("G1", "660 deep red WP7113SRD", {"f7", "f8"}),
}
only = [int(a) for a in sys.argv[1:]] or list(CH)

S, L = s.connect("auto")


def avg(n=5):
    rows = [tuple(getattr(r, k) for k in K) for r in (S.read() for _ in range(n))]
    return [sum(c) / n for c in zip(*rows)]


results = {}
try:
    for ch in only:
        out, label, want = CH[ch]
        for gain in (7, 6, 5, 4, 3, 2, 1):
            S.configure(gain, 29, 599)
            L.off(); time.sleep(0.3)
            dark = avg()
            L.set(ch, 1.0); time.sleep(0.3)
            lit = avg()
            L.off()
            if max(lit) < 0.9 * S.full_scale:
                break
        diff = [l - d for l, d in zip(lit, dark)]
        pk = max(range(8), key=lambda i: diff[i])
        x = 2 ** (gain - 1)                      # gain code n = 2^(n-1)x
        per1x = diff[pk] / x
        ok_band = K[pk] in want
        sat = max(lit) >= 0.9 * S.full_scale
        verdict = "OK" if ok_band and not sat and per1x > 20 else "CHECK"
        why = [w for w, bad in (("wrong peak band", not ok_band), ("saturated at lowest gain", sat), ("very dim", per1x <= 20)) if bad]
        results[ch] = dict(output=out, led=label, gain_code=gain, gain_x=x, full_scale=S.full_scale,
                           peak=NAMES[pk], peak_per_1x=round(per1x, 1), clear=round(diff[8]),
                           verdict=verdict, why=why, diff=dict(zip(K, [round(v) for v in diff])))
        print(f"\nch{ch} {out} {label}  gain {x}x  peak {NAMES[pk]}  {per1x:.0f}/1x  clear {diff[8]:.0f}  {verdict} {', '.join(why)}")
        for n, v in zip(NAMES, diff):
            print(f"  {n:8}{v:9.0f}")
finally:
    L.off()
    print("\nall off")

print("\nch  out  LED                       peak     per-1x  verdict")
for ch, r in results.items():
    print(f"{ch:<3} {r['output']:4} {r['led']:25} {r['peak']:8} {r['peak_per_1x']:7.0f}  {r['verdict']} {', '.join(r['why'])}")
fn = f"ledtest-{datetime.now():%Y%m%d-%H%M%S}.json"
json.dump(results, open(fn, "w"), indent=1)
print("saved", fn)
