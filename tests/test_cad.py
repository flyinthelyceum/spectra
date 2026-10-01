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

        for part in (trap.cavity(), trap.ptfe_tile()):
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
        assert "sample_card" in names
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

    def test_materials_cover_the_puck_exactly(self, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_CASE", "puck-v1")
        from spectra.cad import assembly, viewer

        built = set(viewer.families())
        gated = set(assembly.omitted_families())
        assert set(viewer.MATERIALS) == built | gated
        assert built & gated == set()


# ------------------------------------------------------ the calibration dock --

class TestDock:
    """The dock presents each standard to the port exactly as a sample would
    be presented: port face on the standard, nothing else touching, square
    inside the ruled tolerance. Every check in dock.check() is one of those."""

    def test_every_dock_check_holds(self):
        b123d("build123d")
        from spectra.cad import dock

        failed = [(n, d) for n, ok, d in dock.check() if not ok]
        assert not failed, failed

    def test_the_lip_never_carries_the_puck(self):
        # Nobody presses in the dock, so a lip that landed would hold the port
        # off the standard. The floor must sit below the lip's reach.
        b123d("build123d")
        from spectra.cad import dock

        assert dock.WELL_DEPTH > P.LIP_PROUD
        assert P.LIP_ID / 2 - dock.CUP_CLEAR > max(dock.TILE_PEDESTAL_R, dock.TRAP_LAND_R)

    def test_off_centre_seating_keeps_the_port_on_its_standard(self):
        b123d("build123d")
        from spectra.cad import dock

        worst = P.PORT_D / 2 + dock.CUP_CLEAR
        assert worst < P.TILE_D / 2
        assert worst < P.TRAP_MOUTH_D / 2

    def test_a_thin_tile_is_caught_by_the_check_not_the_printer(self, monkeypatch):
        # A tile face below its pedestal is two stops, and the check must say so.
        b123d("build123d")
        from spectra.cad import dock

        monkeypatch.setattr(dock, "TILE_PROUD", -0.2)
        failed = {n for n, ok, _ in dock.check() if not ok}
        assert "white: the tile is the only stop" in failed

    def test_the_cup_follows_the_puck(self):
        b123d("build123d")
        from spectra.cad import dock, puck

        assert dock.R_CUP > puck.R_OUT
        assert dock.PITCH >= 2 * dock.R_CUP + dock.DOCK_WALL - 1e-9

    def test_the_dock_trap_is_the_standalone_trap(self):
        # One cone, shared: the dock bores trap.cavity() rather than its own.
        b123d("build123d")
        from spectra.cad import trap

        from build123d import Pos

        from spectra.cad import dock

        c = trap.cavity()
        bb = c.bounding_box()
        assert bb.max.Z == pytest.approx(0.0, abs=1e-6)
        assert bb.min.Z == pytest.approx(-P.TRAP_L, abs=1e-6)
        # Nothing of the dock stands inside the cone at the trap station.
        hit = dock.body() & (Pos(dock.PITCH, 0, 0) * c)
        assert hit is None or sum(s.volume for s in hit.solids()) < 1e-6

    @pytest.mark.parametrize("where", ["white", "trap"])
    def test_materials_cover_the_docked_puck_exactly(self, where, monkeypatch):
        b123d("build123d")
        monkeypatch.setenv("SPECTRA_CASE", "puck-v1")
        monkeypatch.setenv("SPECTRA_DOCK", where)
        from spectra.cad import assembly, viewer

        built = set(viewer.families())
        gated = set(assembly.omitted_families())
        assert set(viewer.MATERIALS) == built | gated
        assert built & gated == set()

    def test_an_unknown_station_is_refused(self, monkeypatch):
        b123d("build123d")
        from spectra.cad import dock

        monkeypatch.setenv("SPECTRA_DOCK", "grey")
        with pytest.raises(ValueError):
            dock.station()
