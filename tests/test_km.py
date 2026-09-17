"""Tests for the Kubelka-Munk model.

Everything here is a property the maths must hold rather than a number copied out
of a table, because there is no reference implementation to copy from and a planted
value would only assert that the code still does what it did. The properties are
the ones that catch a wrong K-M: the two forms have to agree in the opaque limit,
the drawdown solve has to return what was planted, and mixing has to be additive in
the right quantity.
"""

import math

import pytest

from spectra import km


class TestSaunderson:
    @pytest.mark.parametrize("r", [0.05, 0.1, 0.35, 0.6, 0.9, 0.97])
    def test_round_trips(self, r):
        assert km.to_measured(km.to_internal(r)) == pytest.approx(r, abs=1e-12)

    def test_preserves_order(self):
        readings = [0.05, 0.2, 0.5, 0.9]
        corrected = [km.to_internal(r) for r in readings]
        assert corrected == sorted(corrected)

    def test_is_not_a_scale_factor(self):
        # The correction lightens most of the range and darkens the very bottom of
        # it, crossing over near 0.067 for the default constants. That is why it
        # cannot be folded into a gain, and why it cannot be left out and apologised
        # for later: it reshapes the curve rather than shifting it.
        assert km.to_internal(0.5) > 0.5
        assert km.to_internal(0.05) < 0.05

    def test_a_reading_below_the_front_surface_is_impossible(self):
        # Nothing can read darker than k1, so such a reading clamps rather than
        # going negative. In practice it means the stray-light budget is blown.
        assert km.to_internal(km.K1_DEFAULT / 2) == 0.0

    def test_floor_is_the_front_surface(self):
        # A perfect absorber still returns k1, which is why a light trap and not a
        # black tile is what measures an instrument's stray light.
        assert km.to_measured(0.0) == pytest.approx(km.K1_DEFAULT)
        assert km.to_internal(km.K1_DEFAULT) == 0.0

    def test_bias_grows_toward_black(self):
        # Uncorrected K/S error is small for a light sample and large for a dark one.
        def err(r):
            return abs(
                km.ks_from_reflectance(r) - km.ks_from_reflectance(km.to_internal(r))
            )

        assert err(0.03) > err(0.5) > err(0.85)


class TestOpaqueForm:
    @pytest.mark.parametrize("r", [0.01, 0.05, 0.2, 0.5, 0.8, 0.99])
    def test_round_trips(self, r):
        assert km.reflectance_from_ks(km.ks_from_reflectance(r)) == pytest.approx(
            r, abs=1e-12
        )

    def test_limits(self):
        assert km.ks_from_reflectance(1.0) == 0.0
        assert km.ks_from_reflectance(0.0) == math.inf
        assert km.reflectance_from_ks(0.0) == 1.0
        assert km.reflectance_from_ks(math.inf) == 0.0

    def test_monotone(self):
        values = [km.ks_from_reflectance(r) for r in (0.9, 0.7, 0.5, 0.3, 0.1)]
        assert values == sorted(values)


class TestTwoFlux:
    @pytest.mark.parametrize("ks", [0.0, 0.05, 0.5, 4.0, 40.0])
    @pytest.mark.parametrize("ground", [0.0, 0.4, 0.9])
    def test_opaque_limit_matches_the_simple_form(self, ks, ground):
        # A thick enough film forgets its ground. This is the join between the two
        # forms, and if it ever fails one of them is wrong. A non-absorbing film
        # converges slowly, at 1/(S*X), which is why the finite case needs a big
        # number and the exact case needs math.inf.
        assert km.reflectance_over(ks, 1e6, ground) == pytest.approx(
            km.reflectance_from_ks(ks), abs=1e-5
        )
        assert km.reflectance_over(ks, math.inf, ground) == pytest.approx(
            km.reflectance_from_ks(ks), abs=1e-12
        )

    def test_a_clear_film_shows_its_ground(self):
        for ground in (0.05, 0.5, 0.95):
            assert km.reflectance_over(0.0, 1e-9, ground) == pytest.approx(
                ground, abs=1e-6
            )

    def test_no_absorption_over_black_is_pure_scattering(self):
        # K = 0 over a perfect trap reduces to S*X / (S*X + 1).
        for sx in (0.2, 1.0, 5.0):
            assert km.reflectance_over(0.0, sx, 0.0) == pytest.approx(sx / (sx + 1.0))

    def test_thicker_film_hides_more(self):
        readings = [km.reflectance_over(0.6, sx, 0.9) for sx in (0.1, 0.5, 2.0, 10.0)]
        assert readings == sorted(readings, reverse=True)

    def test_black_ground_is_always_darker(self):
        for ks in (0.1, 1.0, 10.0):
            for sx in (0.3, 1.5, 6.0):
                assert km.reflectance_over(ks, sx, 0.0) < km.reflectance_over(
                    ks, sx, 0.85
                )


class TestDrawdownSolve:
    WHITE_GROUND = 0.92

    @pytest.mark.parametrize("ks", [0.02, 0.3, 2.0, 15.0, 120.0])
    @pytest.mark.parametrize("sx", [0.25, 1.0, 3.0, 9.0])
    def test_recovers_what_was_planted(self, ks, sx):
        r_black = km.reflectance_over(ks, sx, 0.0)
        r_white = km.reflectance_over(ks, sx, self.WHITE_GROUND)
        got_ks, got_sx = km.solve_ks_sx(r_black, r_white, self.WHITE_GROUND)

        # The readings always come back, whatever the conditioning: the solve has
        # to reproduce the film it was given.
        assert km.reflectance_over(got_ks, got_sx, 0.0) == pytest.approx(
            r_black, abs=1e-6
        )
        assert km.reflectance_over(got_ks, got_sx, self.WHITE_GROUND) == pytest.approx(
            r_white, abs=1e-6
        )

        # The planted pair only comes back while the film still shows its ground.
        # Past hiding there is no thickness left to recover and the honest answer
        # is an infinite S*X, so the grid deliberately runs off that edge.
        contrast = r_white - r_black
        if contrast < 1e-3:
            # Past hiding the ground stops showing through, so S*X is no longer
            # identifiable and the solve says so by running to infinity. K/S is
            # still pinned by the black reading, so that much is still recovered.
            assert got_ks == pytest.approx(ks, rel=0.05)
            return
        assert got_ks == pytest.approx(ks, rel=1e-4, abs=1e-7)
        assert got_sx == pytest.approx(sx, rel=1e-3, abs=1e-6)

    def test_hiding_film_reports_infinite_thickness(self):
        r = km.reflectance_from_ks(1.5)
        got_ks, got_sx = km.solve_ks_sx(r, r, self.WHITE_GROUND)
        assert got_ks == pytest.approx(1.5, rel=1e-9)
        assert got_sx == math.inf

    def test_transparent_masstone_is_not_its_opaque_reading(self):
        # The finding this whole function exists for: read a thin quinacridone-like
        # film over white and treat it as opaque, and the K/S is wrong by a lot.
        ks, sx = 2.0, 0.25
        r_white = km.reflectance_over(ks, sx, self.WHITE_GROUND)
        naive = km.ks_from_reflectance(r_white)
        assert naive < ks / 3

    def test_rejects_swapped_grounds(self):
        with pytest.raises(ValueError, match="swapped"):
            km.solve_ks_sx(0.4, 0.1, self.WHITE_GROUND)

    @pytest.mark.parametrize("bad", [0.0, 1.0, -0.2, 1.5])
    def test_rejects_impossible_readings(self, bad):
        with pytest.raises(ValueError):
            km.solve_ks_sx(bad, 0.5, self.WHITE_GROUND)


class TestMixing:
    def test_single_constant_is_additive_in_ks(self):
        assert km.mix_ks([1.0, 5.0], [0.5, 0.5]) == pytest.approx(3.0)
        assert km.mix_ks([1.0, 5.0], [0.25, 0.75]) == pytest.approx(4.0)

    def test_concentrations_are_normalised(self):
        assert km.mix_ks([1.0, 5.0], [2.0, 2.0]) == pytest.approx(
            km.mix_ks([1.0, 5.0], [0.5, 0.5])
        )

    def test_a_single_pigment_mixes_to_itself(self):
        assert km.mix_ks([3.7], [1.0]) == pytest.approx(3.7)
        ks, sx = km.mix_two_constant([3.7], [2.2], [1.0])
        assert (ks, sx) == pytest.approx((3.7, 2.2))

    def test_two_constant_weights_k_and_s_separately(self):
        # A weak-scattering colourant at half concentration with a strong-scattering
        # white: the mixture's K/S is NOT the average of the two K/S values, and the
        # gap between the two answers is the whole reason two-constant exists.
        colour_ks, colour_sx = 20.0, 0.4
        white_ks, white_sx = 0.02, 12.0
        ks, sx = km.mix_two_constant(
            [colour_ks, white_ks], [colour_sx, white_sx], [0.5, 0.5]
        )
        expected_kx = 0.5 * colour_ks * colour_sx + 0.5 * white_ks * white_sx
        expected_sx = 0.5 * colour_sx + 0.5 * white_sx
        assert ks == pytest.approx(expected_kx / expected_sx)
        assert sx == pytest.approx(expected_sx)
        naive = km.mix_ks([colour_ks, white_ks], [0.5, 0.5])
        assert naive > ks * 5

    def test_tint_moves_monotonically_toward_the_white(self):
        colour = (20.0, 0.4)
        white = (0.02, 12.0)
        lightness = []
        for c in (1.0, 0.8, 0.5, 0.2, 0.0):
            ks, _ = km.mix_two_constant(
                [colour[0], white[0]], [colour[1], white[1]], [c, 1.0 - c]
            )
            lightness.append(km.reflectance_from_ks(ks))
        assert lightness == sorted(lightness)

    @pytest.mark.parametrize(
        "args", [([1.0, 2.0], [1.0]), ([1.0], [-1.0]), ([1.0, 2.0], [0.0, 0.0])]
    )
    def test_rejects_bad_concentrations(self, args):
        with pytest.raises(ValueError):
            km.mix_ks(*args)


class TestCurves:
    def test_curve_helpers_match_the_scalars(self):
        curve = [0.08, 0.2, 0.55, 0.9]
        assert km.curve_to_internal(curve) == [km.to_internal(r) for r in curve]
        ks = km.curve_ks_from_reflectance(curve)
        assert km.curve_reflectance_from_ks(ks) == pytest.approx(curve, abs=1e-12)


class TestTheWholePath:
    def test_measured_masstone_to_predicted_mixture(self):
        """The path the instrument will actually walk, planted end to end.

        Two pigments drawn down over black and white, read as an instrument would
        read them, corrected, solved, mixed 50/50, and predicted back into a
        measured reflectance. Nothing here is a number to trust; the point is that
        every step composes and the result lands between the two parents.
        """
        white_ground = 0.92
        # The white card is measured by the same instrument as everything else, so
        # it goes through the same correction. Feeding the solver a card reflectance
        # that skipped it is a quiet source of error in exactly the transparent
        # pigments the drawdown exists for.
        white_card_reading = km.to_measured(white_ground)
        parents = [(18.0, 0.5), (0.9, 3.0)]
        measured = []
        for ks, sx in parents:
            over_black = km.to_measured(km.reflectance_over(ks, sx, 0.0))
            over_white = km.to_measured(km.reflectance_over(ks, sx, white_ground))
            measured.append((over_black, over_white))

        solved = [
            km.solve_ks_sx(
                km.to_internal(b), km.to_internal(w), km.to_internal(white_card_reading)
            )
            for b, w in measured
        ]
        for got, planted in zip(solved, parents):
            assert got == pytest.approx(planted, rel=1e-4)

        ks_mix, sx_mix = km.mix_two_constant(
            [s[0] for s in solved], [s[1] for s in solved], [0.5, 0.5]
        )
        predicted = km.to_measured(km.reflectance_over(ks_mix, sx_mix, 0.0))
        parent_readings = sorted(km.to_measured(km.reflectance_over(ks, sx, 0.0)) for ks, sx in parents)
        assert parent_readings[0] < predicted < parent_readings[1]
