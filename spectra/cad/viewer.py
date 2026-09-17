#!/usr/bin/env python3
"""Turn the optical head into a self-contained 3D viewer page.

    .venv/bin/python -m spectra.cad.viewer                    # the LED beam sweep
    .venv/bin/python -m spectra.cad.viewer --variant "Long tube=BAFFLE_L:26"

The page is one HTML file: every part tessellated and embedded, three.js
inlined, no server, no network.

Ported from `workbench/bench/viewer.py`, which was itself ported from grow-lab.
The pattern is not re-derived here. What is new is the RAY overlay, and it is
the reason this page exists rather than a set of rendered angles: `OPTICAL_HEAD.md`
calls 45/0 "the single most important mechanical decision in the build", and the
question it turns on — does the specular lobe leave at 45 degrees and miss the
collection tube, and does the lit spot overfill the collected one — is a question
about light, not about shape. No render of the solids alone can answer it. The
rays are computed in `assembly.rays()` from `params` and drawn here; the page
shows the optics the geometry actually implies, not an illustration of them.

That overlay is the equivalent of the bench viewer's seated view: the one thing
you cannot learn from six fixed camera angles.

Each variant is built in a subprocess with its ``SPECTRA_*`` knobs set, so the
kernel sees a clean ``params`` module every time.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from array import array
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

OUT = REPO / "export"

# Material and role for each part FAMILY, keyed by _family() of the assembly's
# placed names.
#
# The palette is the fabrication house register, not the 3D Studio Color
# Doctrine. The Doctrine governs studio artifacts — placards, guides, course
# pages — and this is not one: it is a personal bench instrument in black PETG,
# which is the register the growlab enclosure and the CNC station already use.
# Transparent's light ground, ghosted glass, and ONE red that earns its place.
#
# Here the one red is spent on the specular ray, in the template rather than in
# this table. That is the correct place for it: the specular lobe is the single
# thing in this whole build that must not reach the detector, which makes it the
# only thing on the page that is about consequence.
#
# What a single flat material per solid CANNOT show is the matte black interior,
# which is most of the optical design. Read the render for proportion and for
# where the light goes. Read OPTICAL_HEAD.md for the surface finish.
MATERIALS = {
    # Printed here, black PETG, port face down.
    "head_body": dict(label="Head body (port, baffle, LED seats)", colour="#26282A",
                      opacity=1.0, metalness=0.04, group="printed"),
    "detector_plate": dict(label="Detector plate", colour="#303336",
                           opacity=1.0, metalness=0.04, group="printed"),
    "light_trap": dict(label="Light trap — the black reference", colour="#141618",
                       opacity=1.0, metalness=0.02, group="printed"),
    "tile_holder": dict(label="White tile holder", colour="#33373B",
                        opacity=1.0, metalness=0.04, group="printed"),
    # Bought, or measured elsewhere. Not ours to cut.
    "as7341_board": dict(label="AS7341 breakout (components lib)", colour="#3C4147",
                         opacity=1.0, metalness=0.45, group="reference"),
    "ptfe_tile": dict(label="Sintered PTFE white, >97%", colour="#F2F3F0",
                      opacity=1.0, metalness=0.0, group="reference"),
    "sample_card": dict(label="Sample at the port", colour="#D8D4CC", accent=True,
                        opacity=1.0, metalness=0.0, group="reference"),
}


# The sweep the page opens on is LED_HALF_ANGLE, because it is the one estimate
# the geometry actually rests on: it decides the lit spot, and the lit spot has
# to overfill the port. 8 degrees FAILS that constraint and 30 passes easily, so
# the three variants are a picture of how much the unchosen LED matters. None of
# them move a single triangle — the meshes are identical and pooled — which is
# what makes a three-variant default free.
DEFAULT_VARIANTS = [
    ("LED 15\u00b0 (assumed)", {"SPECTRA_LED_HALF_ANGLE": "15"}),
    ("LED 8\u00b0 (narrow)", {"SPECTRA_LED_HALF_ANGLE": "8"}),
    ("LED 30\u00b0 (wide)", {"SPECTRA_LED_HALF_ANGLE": "30"}),
]


def _family(name: str) -> str:
    """The part family a placed solid belongs to: its name with the instance
    indices dropped.

    ``rib_0`` and ``rib_3`` are one part cut four times; ``drawer_1_side_0`` is a
    drawer side. The viewer colours and toggles families, not instances, so the
    materials table stays the size of the DESIGN rather than the size of the
    assembly. Change the rib count or add a drawer tier and the table is still
    right; add a genuinely new kind of part and the test fails until it is
    given a material, which is the point of the test.
    """
    return "_".join(part for part in name.split("_") if not part.isdigit())


def families() -> list[str]:
    """Every part family in the assembly, in placement order."""
    from . import assembly

    out: list[str] = []
    for name, _ in assembly.all_placed():
        fam = _family(name)
        if fam not in out:
            out.append(fam)
    return out


def _dump(out_path: Path, tolerance_mm: float, angular: float) -> None:
    """Child process: build the head at the current knobs and write meshes.

    Millimetres throughout, z = 0 at the port face. Nothing is converted
    anywhere in this file and the page labels everything mm.
    """
    from . import assembly
    from . import params as P

    placed = assembly.all_placed()

    # One buffer pair per family: the instances of a family are concatenated,
    # with each block's indices shifted by the vertices already in it.
    verts_of: dict[str, array] = {}
    idx_of: dict[str, array] = {}
    for name, solid in placed:
        fam = _family(name)
        pos = verts_of.setdefault(fam, array("f"))
        idx = idx_of.setdefault(fam, array("I"))
        vs, tris = solid.tessellate(tolerance_mm, angular)
        base = len(pos) // 3
        pos.extend(c for v in vs for c in (v.X, v.Y, v.Z))
        idx.extend(base + i for t in tris for i in t)

    meshes = {}
    for fam, pos in verts_of.items():
        idx = idx_of[fam]
        if sys.byteorder == "big":
            pos.byteswap()
            idx.byteswap()
        meshes[fam] = {
            "positions": base64.b64encode(pos.tobytes()).decode(),
            "indices": base64.b64encode(idx.tobytes()).decode(),
            "triangles": len(idx) // 3,
        }

    boxes = [s.bounding_box() for _, s in placed]
    bbox = {
        "min": [min(b.min.X for b in boxes), min(b.min.Y for b in boxes), min(b.min.Z for b in boxes)],
        "max": [max(b.max.X for b in boxes), max(b.max.Y for b in boxes), max(b.max.Z for b in boxes)],
    }

    # The constraint report travels with the render. A page that shows a head
    # which fails its own optics and does not say so is worse than no page.
    checks = [
        {"name": n, "ok": ok, "detail": d} for n, ok, d in P.constraints()
    ]

    variant = {
        "label": os.environ.get("SPECTRA_VARIANT_LABEL", f"LED {P.LED_HALF_ANGLE:g}deg"),
        "accent": "#D8D4CC",
        "rays": assembly.rays(),
        "datums": assembly.datums(),
        "optics": assembly.optics(),
        "checks": checks,
        "failing": sum(1 for c in checks if not c["ok"]),
        "bbox": bbox,
        "meshes": meshes,
    }
    out_path.write_text(json.dumps(variant))


def build_variants(specs: list[tuple[str, dict]], tolerance_mm: float, angular: float) -> list[dict]:
    variants = []
    for n, (label, knobs) in enumerate(specs):
        tmp = OUT / f"_variant_{n}.json"
        env = {**os.environ, **knobs, "SPECTRA_VARIANT_LABEL": label}
        subprocess.run(
            # -m, not the file path: this module uses relative imports, and a
            # file run as __main__ has no package to resolve them against.
            [sys.executable, "-m", "spectra.cad.viewer",
             "--dump", str(tmp), "--tolerance", str(tolerance_mm), "--angular", str(angular)],
            env=env, check=True, cwd=str(REPO),
        )
        variants.append(json.loads(tmp.read_text()))
        tmp.unlink()
        tris = sum(m["triangles"] for m in variants[-1]["meshes"].values())
        print(f"{label} ({' '.join(f'{k}={v}' for k, v in knobs.items()) or 'defaults'}): {tris} triangles")
    return variants


def _parse_variant(spec: str) -> tuple[str, dict]:
    """'Label=KEY:VAL,KEY:VAL' → (label, {SPECTRA_KEY: VAL, …}).

    Only the knobs wired through params._knob() are live: LED_HALF_ANGLE,
    BAFFLE_L, COLLECT_D, LED_Z. Anything else parses fine, sets an environment
    variable nobody reads, and gives you N identical variants with no error —
    the same trap grow-lab's viewer documents and workbench inherited.
    """
    label, _, knobs = spec.partition("=")
    env = {}
    for kv in filter(None, knobs.split(",")):
        k, _, v = kv.partition(":")
        env[f"SPECTRA_{k.strip().upper()}"] = v.strip()
    return label.strip(), env


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


THREE_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
THREE_CACHE = OUT / "_three.min.js"
THREE_TAG = f'<script src="{THREE_URL}"></script>'


def _three_js() -> str | None:
    """three.js source, cached beside the output. None if it cannot be had.

    The page is advertised as one file you open in a browser with nothing
    installed, and a CDN tag makes that false: offline it opens as a blank page
    with two console errors and no canvas. Inlining costs ~600 KB and makes the
    claim true. It also keeps the page publishable as an Artifact, where an
    external script src is blocked outright.
    """
    if THREE_CACHE.exists():
        return THREE_CACHE.read_text()
    try:
        import urllib.request

        with urllib.request.urlopen(THREE_URL, timeout=30) as r:
            src = r.read().decode()
        THREE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        THREE_CACHE.write_text(src)
        return src
    except Exception as exc:  # noqa: BLE001 — falling back is the point
        print(f"could not fetch three.js ({exc}); falling back to the CDN tag, "
              "which means this file needs a network to open")
        return None


def pool_geometry(variants: list[dict]) -> dict:
    """Share identical buffers between variants, and leave each variant holding
    keys into the pool instead of its own copy.

    The default sweep is a COLOUR sweep: three variants in which every triangle
    is identical and one hex value is not. Carrying three copies of the bench to
    say that tripled the page for nothing — 6 MB where 2 does the same job. A
    knob that moves geometry still pays for it; a knob that only moves paint is
    now free, which is what lets the accent sweep be the default at all.
    """
    geometry: dict[str, dict] = {}
    for v in variants:
        keys = {}
        for fam, md in v["meshes"].items():
            key = hashlib.sha1((md["positions"] + md["indices"]).encode()).hexdigest()[:12]
            geometry.setdefault(key, md)
            keys[fam] = key
        v["meshes"] = keys
    return geometry


def render_html(variants: list[dict]) -> str:
    template = (Path(__file__).resolve().parent / "viewer_template.html").read_text()
    payload = json.dumps({
        "sha": _git_sha(),
        "materials": MATERIALS,
        "geometry": pool_geometry(variants),
        "variants": variants,
    })
    html = template.replace("/*__SPECTRA_DATA__*/null", payload)
    src = _three_js()
    if src is not None:
        assert THREE_TAG in html, "the three.js script tag moved; inlining would silently no-op"
        html = html.replace(THREE_TAG, f"<script>{src}</script>")
    return html


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baffle-lengths", type=float, nargs="+",
                    help="build a BAFFLE_L sweep instead of the LED beam sweep")
    ap.add_argument("--variant", action="append", default=[], metavar="LABEL=KNOB:VAL,...",
                    help="an explicit variant, e.g. 'Wide port=COLLECT_D:6'; repeatable")
    ap.add_argument("--tolerance", type=float, default=0.12, help="tessellation tolerance, mm")
    ap.add_argument("--angular", type=float, default=0.2, help="angular tolerance, radians")
    ap.add_argument("--dump", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--out", type=Path, default=OUT / "viewer.html")
    args = ap.parse_args(argv)

    if args.dump:
        _dump(args.dump, args.tolerance, args.angular)
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    if args.variant:
        specs = [_parse_variant(v) for v in args.variant]
    elif args.baffle_lengths:
        specs = [(f"{h:g}mm tube", {"SPECTRA_BAFFLE_L": f"{h:g}"}) for h in args.baffle_lengths]
    else:
        specs = DEFAULT_VARIANTS
    variants = build_variants(specs, args.tolerance, args.angular)
    html = render_html(variants)
    args.out.write_text(html)
    rel = args.out.relative_to(REPO) if args.out.is_relative_to(REPO) else args.out
    print(f"wrote {rel}  ({len(html) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
