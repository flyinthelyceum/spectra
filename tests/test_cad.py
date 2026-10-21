"""Tests for the optical head geometry and the viewer.

These assert properties the optics must hold, not numbers a previous run
produced. A planted constant would only assert that the code still does what it
did; these fail when the head stops being a 45/0 instrument.

build123d is an optional dependency behind the `cad` extra, so the geometry
tests skip cleanly on an install that does not have it. The pure-arithmetic
tests do not need it and never skip.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from spectra.cad import params as P

b123d = pytest.importorskip


# --------------------------------------------------------------- the optics --

class TestOpticalConstraints:
    """The three claims the 45/0 geometry exists to make."""

    def test_all_constraints_hold_at_the_shipped_numbers(self):
        failures = [(n, d) for n, ok, d in P.constraints() if not ok]
        assert failures == [], f"shipped parameters violate their own optics: {failures}"

    def test_specular_lobe_cannot_enter_the_collection_tube(self):
        # The whole reason for 45/0. The specular lobe leaves at the illumination
        # angle; the tube accepts a cone about the normal. They must not overlap,
        # even at the worst end of the ruled angular tolerance.
        worst_specular = P.ILLUM_ANGLE - P.ILLUM_ANGLE_TOL
        assert P.BAFFLE_ACCEPT_ANGLE < worst_specular

    def test_collected_spot_sits_strictly_inside_the_lit_spot(self):
        # Computed from params, never measured off a mesh: a mesh is a
        # tessellation and would make this a test of tessellation tolerance.
        assert P.COLLECTED_SPOT_D < P.LIT_SPOT_MINOR
        assert P.COLLECTED_SPOT_D < P.PORT_D

    def test_lit_footprint_is_an_ellipse_not_a_circle(self):
        # A round beam at 45 degrees lands as an ellipse stretched by 1/cos(45).
        # If these are ever equal, someone has modelled the footprint as round
        # and the overfill margin is being computed against the wrong axis.
        assert P.LIT_SPOT_MAJOR > P.LIT_SPOT_MINOR
        ratio = P.LIT_SPOT_MAJOR / P.LIT_SPOT_MINOR
        assert ratio == pytest.approx(1 / math.cos(math.radians(P.ILLUM_ANGLE)))

    def test_illumination_is_not_blocked_by_the_collection_tube(self):
        # The mistake the first draft made. At 45 degrees the beam is at radius
        # r = z, so a tube starting at height z0 must be thinner than z0.
        beam_r_at_tube_start = P.BAFFLE_Z0 * math.tan(math.radians(P.ILLUM_ANGLE))
        assert P.BAFFLE_OD / 2 < beam_r_at_tube_start

    def test_led_ring_radius_is_derived_from_the_ruled_angle(self):
        # Never typed. Every emitter aims at the port centre by construction.
        assert P.LED_RING_R == pytest.approx(
            P.LED_Z / math.tan(math.radians(P.ILLUM_ANGLE))
        )

    def test_led_count_is_even(self):
        # Ruled: an odd ring reads brush direction instead of cancelling it.
        assert P.LED_N % 2 == 0

    def test_a_narrow_led_is_caught_rather_than_passing_silently(self):
        # The estimate this design rests on. If someone fits an 8-degree LED the
        # beam stops overfilling the port, and the constraint report must say so
        # rather than the head quietly reading the edge of its own aperture.
        throw = P.LED_Z / math.sin(math.radians(P.ILLUM_ANGLE))
        narrow_minor = 2 * throw * math.tan(math.radians(8.0))
        assert narrow_minor < P.PORT_D


# ------------------------------------------------------------- the geometry --

class TestSolids:
    """Everything printed has to be one solid, or it is not printable."""

    def test_head_is_a_single_solid(self):
        b123d("build123d")
        from spectra.cad import head

        assert len(head.body().solids()) == 1

    def test_standards_are_each_a_single_solid(self):
        b123d("build123d")
        from spectra.cad import trap

        for part in (trap.light_trap(), trap.tile_holder(), trap.ptfe_tile()):
            assert len(part.solids()) == 1

    def test_head_port_face_is_the_datum(self):
        b123d("build123d")
        from spectra.cad import head

        bb = head.body().bounding_box()
        # The lip hangs below z=0 and nothing else does. The port face is the
        # stop, so the only thing under it is the thing designed to be crushed.
        assert bb.min.Z == pytest.approx(-P.LIP_PROUD, abs=1e-6)
        assert bb.max.Z == pytest.approx(P.PLATE_Z, abs=1e-6)


# --------------------------------------------------- the components boundary --

class TestComponentsBoundary:
    """The plate is gated on a measurement, and gates nothing else."""

    def test_plate_reports_what_it_is_missing(self):
        from spectra.cad import plate

        for name in plate.missing():
            assert name in plate.NEEDS, f"{name} is missing but undocumented"

    def test_a_missing_measurement_blocks_only_the_plate(self):
        b123d("build123d")
        from spectra.cad import assembly, plate

        names = {n for n, _ in assembly.all_placed()}
        assert "head_body" in names
        assert "light_trap" in names
        if plate.available():
            assert "detector_plate" in names
        else:
            assert "detector_plate" not in names

    def test_plate_raises_rather_than_guessing(self):
        from spectra.cad import plate

        if plate.available():
            pytest.skip("board is fully measured; nothing to gate")
        with pytest.raises(plate.MissingMeasurement) as exc:
            plate.detector_plate()
        # The error has to name the one writer, or the next person types the
        # number in here instead.
        assert "components measure" in str(exc.value)


# ----------------------------------------------------------------- the rays --

class TestRays:
    def test_specular_ray_leaves_on_the_far_side_at_the_illumination_angle(self):
        b123d("build123d")
        from spectra.cad import assembly

        incidents = [r for r in assembly.rays() if r["role"] == "incident"]
        speculars = [r for r in assembly.rays() if r["role"] == "specular"]
        assert incidents and len(incidents) == len(speculars)

        for inc, spec in zip(incidents, speculars):
            (ex, ey, ez), _ = inc["points"]
            _, (sx, sy, sz) = spec["points"]
            # Same angle from the normal...
            angle = math.degrees(math.atan2(math.hypot(sx, sy), sz))
            assert angle == pytest.approx(P.ILLUM_ANGLE, abs=1e-6)
            # ...and on the opposite side of it.
            assert sx == pytest.approx(-ex * (math.hypot(sx, sy) / math.hypot(ex, ey)), abs=1e-6)
            assert sy == pytest.approx(-ey * (math.hypot(sx, sy) / math.hypot(ex, ey)), abs=1e-6)
            assert sz > 0

    def test_every_ray_role_has_a_style_in_the_template(self):
        b123d("build123d")
        from pathlib import Path

        from spectra.cad import assembly

        template = (Path(__file__).resolve().parents[1]
                    / "spectra" / "cad" / "viewer_template.html").read_text()
        for role in {r["role"] for r in assembly.rays()}:
            assert f"  {role}:" in template, f"ray role {role!r} would be drawn as nothing"


# --------------------------------------------------------------- the viewer --

class TestViewer:
    def test_materials_and_families_cover_each_other_exactly(self):
        b123d("build123d")
        from spectra.cad import viewer

        # Equality, never a subset check in either direction. A new part with no
        # material would render as a grey blob; a material for a part that no
        # longer exists is a dead row in the legend. Both are failures here.
        from spectra.cad import assembly

        built = set(viewer.families())
        gated = set(assembly.omitted_families())
        assert set(viewer.MATERIALS) == built | gated
        # And the gated ones must genuinely be absent, not merely declared so.
        assert built & gated == set()

    def test_every_material_declares_a_group_the_page_renders(self):
        from spectra.cad import viewer

        for name, spec in viewer.MATERIALS.items():
            assert spec["group"] in {"printed", "reference"}, name

    def test_template_placeholder_is_present_for_substitution(self):
        from pathlib import Path

        template = (Path(__file__).resolve().parents[1]
                    / "spectra" / "cad" / "viewer_template.html").read_text()
        # render_html() replaces exactly this token; if it is renamed in one
        # place and not the other the page ships with `null` as its data and
        # fails silently in the browser.
        assert template.count("/*__SPECTRA_DATA__*/null") == 1

    def test_template_declares_a_charset(self):
        from pathlib import Path

        template = (Path(__file__).resolve().parents[1]
                    / "spectra" / "cad" / "viewer_template.html").read_text()
        # Without this the degree signs and em dashes render as mojibake when
        # the page is served over HTTP. Found by looking at it.
        assert '<meta charset="utf-8">' in template

    def test_three_js_tag_matches_what_render_html_asserts(self):
        from pathlib import Path

        from spectra.cad import viewer

        template = (Path(__file__).resolve().parents[1]
                    / "spectra" / "cad" / "viewer_template.html").read_text()
        # render_html() asserts this exact tag before inlining. If the template's
        # tag drifts, inlining silently no-ops and the page needs a network.
        assert viewer.THREE_TAG in template


# ---------------------------------------------------------- the case concepts --

class TestCaseConcepts:
    """Massing models, but the two rules they inherit from the head are real."""

    @pytest.mark.parametrize("form", ["puck", "torch", "palm"])
    def test_every_concept_holds_its_checks(self, form):
        b123d("build123d")
        from spectra.cad import case

        failed = [(n, d) for n, ok, d in case.check(form) if not ok]
        assert not failed, failed

    @pytest.mark.parametrize("form", ["puck", "torch", "palm"])
    def test_the_port_lip_still_touches_the_sample_first(self, form):
        # The case may be coplanar with the port face but never below it, so the
        # compliant lip is the lowest thing on the instrument whatever the case.
        b123d("build123d")
        from spectra.cad import case, head

        lowest_case = min(s.bounding_box().min.Z for _, s in case.placed(form))
        assert head.body().bounding_box().min.Z < lowest_case

    @pytest.mark.parametrize("form", ["puck", "torch", "palm"])
    def test_materials_cover_each_concept_exactly(self, form, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_CASE", form)
        from spectra.cad import assembly, viewer

        built = set(viewer.families())
        gated = set(assembly.omitted_families())
        assert set(viewer.MATERIALS) == built | gated
        assert built & gated == set()

    def test_an_unknown_concept_is_refused_rather_than_drawn_bare(self, monkeypatch):
        b123d("build123d")
        from spectra.cad import case

        monkeypatch.setenv("SPECTRA_CASE", "brick")
        with pytest.raises(ValueError):
            case.form()


# ---------------------------------------------------------------- the puck --

class TestPuck:
    """The detailed case. Every check in puck.check() is a property the design
    exists to hold, so the test is that all of them hold."""


    def test_head_prints_without_an_island(self):
        # Orca, 2026-10-05: port face down, the lip held the port face off the
        # bed and the collection tube began in mid-air. In its print orientation
        # every flat face looking down must be either on the bed, a pilot end
        # small enough to bridge, or the cavity ceiling, which bridges between
        # walls on every side.
        b123d("build123d")
        from spectra.cad import puck

        h = puck.print_ready()["head"]
        ceiling = None
        for f in h.faces():
            if f.normal_at(f.center()).Z < -0.99 and f.center().Z > 0.05:
                if f.area < 10.0:
                    continue
                assert ceiling is None, f"second large downward face at z={f.center().Z:.2f}"
                ceiling = f
        assert ceiling is not None
        assert len(ceiling.inner_wires()) == 1  # the port hole, nothing floating in it
    def test_every_part_stands_on_the_bed(self):
        # 2026-10-05: the tray was exported upside down, standing on its
        # corner pads alone (11 mm^2). Each printed part must put a real area
        # on the bed in its print orientation.
        b123d("build123d")
        from spectra.cad import puck

        for name, part in puck.print_ready().items():
            on_bed = sum(f.area for f in part.faces()
                         if abs(f.center().Z) < 0.01 and f.normal_at(f.center()).Z < -0.99)
            assert on_bed > 50.0, f"{name} touches the bed with {on_bed:.1f} mm^2"

    def test_every_board_on_the_bom_has_a_home(self):
        # 2026-10-05: puck v1 was drawn round the ESP32, the sensor and the
        # head, and the LED driver on the BOM had nowhere to go. Every BOM row
        # that names a board must map to a solid the puck places.
        b123d("build123d")
        from spectra.cad import puck

        bom = (Path(__file__).resolve().parent.parent / "hardware" / "BOM.md").read_text()
        items = [ln.split("|")[1].strip() for ln in bom.splitlines()
                 if ln.startswith("| ") and not ln.startswith("| Item")]
        boards = [i for i in items if re.search(r"breakout|ESP32|driver", i, re.I)]
        assert boards, "no boards found on the BOM; the parse is wrong"
        missing = [b for b in boards if b not in puck.HOUSED]
        assert not missing, f"boards with no home in the puck: {missing}"
        placed = set(puck.parts()) | {"as7341"}
        for b in boards:
            name = puck.HOUSED[b]
            assert any(name in p for p in placed), f"{b} maps to {name}, which the puck never places"

    def test_every_puck_check_holds(self):
        b123d("build123d")
        from spectra.cad import puck

        failed = [(n, d) for n, ok, d in puck.check() if not ok]
        assert not failed, failed

    def test_port_land_is_the_only_stop_and_the_foot_caps_tilt(self):
        # The foot is relieved above the port face, and by little enough that it
        # touches down before the head leaves the ruled angle tolerance.
        b123d("build123d")
        from spectra.cad import puck

        assert puck.FOOT_RELIEF > 0
        lever = puck.R_OUT - P.PORT_LAND_OD / 2
        assert math.degrees(math.atan2(puck.FOOT_RELIEF, lever)) < P.ILLUM_ANGLE_TOL

    def test_posts_sit_midway_between_leds(self):
        b123d("build123d")
        from spectra.cad import puck

        step = 360.0 / P.LED_N
        for a in puck.post_angles():
            assert math.isclose((a / step) % 1.0, 0.5)

    def test_plate_screws_miss_the_led_bores(self):
        b123d("build123d")
        from spectra.cad import head

        hit = head._plate_insert_pilots() & head._led_bores()
        assert hit is None or sum(s.volume for s in hit.solids()) < 1e-6

    def test_plain_plate_leaves_the_led_leads_room(self):
        # Found while fitting the case: the bores break out just under the rim,
        # so an un-notched plate sits on the leads.
        b123d("build123d")
        from build123d import Pos

        from spectra.cad import head, plate

        hit = (Pos(0, 0, P.PLATE_Z) * plate.detector_plate()) & head.lead_keepouts()
        assert hit is None or sum(s.volume for s in hit.solids()) < 1e-6

    def test_lead_keepouts_cover_every_bore_mouth(self):
        # The keepouts are only as good as where they start. With the 5 mm set
        # the bores leave through the top face, not the wall, and a keepout that
        # began at the wall left the plate sitting on every LED's back.
        b123d("build123d")
        import math

        from build123d import Vector

        from spectra.cad import head

        keep = head.lead_keepouts()
        t = head.lead_exit()
        s, c = math.sin(math.radians(P.ILLUM_ANGLE)), math.cos(math.radians(P.ILLUM_ANGLE))
        for i in range(P.LED_N):
            a = math.radians(360.0 * i / P.LED_N)
            r, z = P.LED_RING_R + t * c, P.LED_Z + t * s
            assert keep.is_inside(Vector(r * math.cos(a), r * math.sin(a), z))

    def test_materials_cover_the_puck_exactly(self, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_CASE", "puck-v1")
        from spectra.cad import assembly, viewer

        built = set(viewer.families())
        gated = set(assembly.omitted_families())
        assert set(viewer.MATERIALS) == built | gated
        assert built & gated == set()


# ------------------------------------------------------- the LEDs going in --

@pytest.fixture(scope="module")
def led_checks():
    b123d("build123d")
    from spectra.cad import led

    return {name: (ok, detail) for name, ok, detail in led.check()}


class TestLedInsertion:
    """How a 5 mm LED reaches its bore, checked against the printed head.

    The lamp is the nominal T-1 3/4 outline (ESTIMATE, see led.py), so these
    test the shape of the fit: that a path exists, what stops the lamp, and that
    the plate goes on over it. None of them asserts a seat depth.
    """

    def test_materials_cover_the_head_assembly_exactly(self, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_CASE", "puck-v1")
        monkeypatch.setenv("SPECTRA_LEDS", "1")
        from spectra.cad import assembly, viewer

        built = set(viewer.families())
        gated = set(assembly.omitted_families())
        assert "led" in built
        assert set(viewer.MATERIALS) == built | gated
        assert built & gated == set()

    def test_leds_are_drawn_only_when_asked(self, monkeypatch):
        b123d("build123d")
        monkeypatch.delenv("SPECTRA_LEDS", raising=False)
        from spectra.cad import assembly, led

        # Off by default, so every other page and test sees the head it saw
        # before; the coverage tests above then hold through omitted_families.
        assert led.placed() == []
        assert assembly.access() == []
        assert "led" in assembly.omitted_families()

    def test_every_access_family_is_drawn_and_coloured(self, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_CASE", "puck-v1")
        monkeypatch.setenv("SPECTRA_LEDS", "1")
        from spectra.cad import assembly, viewer

        built = set(viewer.families())
        for a in assembly.access():
            assert a["family"] in viewer.MATERIALS, a["family"]
            assert a["family"] in built, a["family"]
            assert a["travel_mm"] > 0, a["family"]

    def test_each_led_travels_its_own_bore_axis(self, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_LEDS", "1")
        from spectra.cad import assembly

        (entry,) = [a for a in assembly.access() if a["family"] == "led"]
        assert len(entry["dirs"]) == P.LED_N
        for i, d in enumerate(entry["dirs"]):
            # The LED moves INTO the head along the bore: down at the
            # illumination angle from vertical, toward the axis, at its own
            # azimuth on the ring.
            assert math.isclose(math.hypot(*d), 1.0, abs_tol=1e-9)
            assert math.isclose(math.degrees(math.acos(-d[2])), P.ILLUM_ANGLE, abs_tol=1e-6)
            az = math.radians(360.0 * i / P.LED_N)
            assert d[0] * math.cos(az) + d[1] * math.sin(az) < 0

    def test_every_led_starts_clear_of_the_head(self):
        b123d("build123d")
        from spectra.cad import head, led

        # The viewer's travel is derived from an inequality, not tuned by eye;
        # this is the inequality.
        body, one = head.body(), led.lamp()
        for i in range(P.LED_N):
            start = led.location(i, led.seat(i) + led.travel()) * one
            assert (body & start).volume < 1e-6, i

    def test_every_led_reaches_its_seat(self, led_checks):
        ok, detail = led_checks["every LED reaches its seat from outside along its bore"]
        assert ok, detail

    def test_the_flange_is_what_stops_it(self, led_checks):
        ok, detail = led_checks["the flange is what stops it"]
        assert ok, detail

    def test_the_plate_notches_clear_the_seated_leds(self, led_checks):
        ok, detail = led_checks["the plate's notches clear the seated flanges and leads"]
        assert ok, detail

    @pytest.mark.xfail(strict=True, reason=(
        "found 2026-10-21: each bore is cut from the emitter point on the cavity "
        "wall, which leaves a wedge of wall across half its end, and web 0 stands "
        "in front of LED 0. Strict, so fixing the head turns this into a failure "
        "that says to drop the mark."))
    def test_the_head_leaves_each_beam_open(self, led_checks):
        ok, detail = led_checks["the head leaves each LED's beam open"]
        assert ok, detail
