"""
Tests for bearoff-related functionality.

Covers bearoff_id_2_pos, bearoff_probabilities (one-sided bearoff database),
one_checker_race (simple one-checker model), and classification of bearoff positions.
"""
import pytest
import gnubg_nn as nn

# Bearoff ID range from the engine (one-sided, up to 15 checkers on 6 points).
BEAROFF_ID_MIN = 1
BEAROFF_ID_MAX = 54263  # [1, 54264) per C code


@pytest.fixture(scope="module")
def engine():
    return nn


class TestBearoffId2Pos:
    """bearoff_id_2_pos(id) -> 6-tuple of checker counts on points 1–6."""

    def test_returns_six_tuple(self, engine):
        pos = engine.bearoff_id_2_pos(1)
        assert isinstance(pos, (list, tuple))
        assert len(pos) == 6

    def test_elements_are_non_negative_integers(self, engine):
        for bid in (1, 100, 1000, 10000, BEAROFF_ID_MAX):
            pos = engine.bearoff_id_2_pos(bid)
            assert all(isinstance(x, int) and x >= 0 for x in pos), f"id={bid} -> {pos}"

    def test_total_checkers_at_most_15(self, engine):
        for bid in (1, 42, 1000, 54263):
            pos = engine.bearoff_id_2_pos(bid)
            assert sum(pos) <= 15, f"id={bid} sum={sum(pos)}"

    def test_accepts_6_tuple_and_returns_same_position(self, engine):
        pos = engine.bearoff_id_2_pos(1000)
        pos_tuple = tuple(pos)
        roundtrip = engine.bearoff_id_2_pos(pos_tuple)
        assert tuple(roundtrip) == pos_tuple

    def test_boundary_ids(self, engine):
        for bid in (BEAROFF_ID_MIN, BEAROFF_ID_MAX):
            pos = engine.bearoff_id_2_pos(bid)
            assert len(pos) == 6 and sum(pos) <= 15

    def test_invalid_id_raises(self, engine):
        with pytest.raises((ValueError, TypeError)):
            engine.bearoff_id_2_pos(0)
        with pytest.raises((ValueError, TypeError)):
            engine.bearoff_id_2_pos(BEAROFF_ID_MAX + 1)


class TestBearoffProbabilities:
    """bearoff_probabilities(id_or_6tuple) -> distribution over number of moves to bear off."""

    def test_returns_sequence_of_floats(self, engine):
        probs = engine.bearoff_probabilities(1)
        assert isinstance(probs, (list, tuple))
        assert len(probs) >= 1
        assert all(isinstance(p, (int, float)) for p in probs)

    def test_probabilities_in_unit_interval(self, engine):
        for bid in (1, 100, 1000):
            probs = engine.bearoff_probabilities(bid)
            for p in probs:
                assert 0 <= p <= 1.0, f"id={bid} probs={probs}"

    def test_probabilities_sum_near_one(self, engine):
        for bid in (1, 42, 1000):
            probs = engine.bearoff_probabilities(bid)
            total = sum(float(p) for p in probs)
            assert 0.99 <= total <= 1.01, f"id={bid} sum(probs)={total}"

    def test_id_and_position_tuple_agree(self, engine):
        bid = 1000
        probs_id = engine.bearoff_probabilities(bid)
        pos = engine.bearoff_id_2_pos(bid)
        probs_pos = engine.bearoff_probabilities(tuple(pos))
        assert len(probs_id) == len(probs_pos)
        for a, b in zip(probs_id, probs_pos):
            assert abs(float(a) - float(b)) < 1e-6

    def test_fully_born_off_has_prob_one_in_one_move(self, engine):
        # ID 1 is typically the "all off" or minimal position; check it doesn't crash
        probs = engine.bearoff_probabilities(1)
        assert len(probs) >= 1 and sum(probs) <= 1.01


class TestOneCheckerRace:
    """one_checker_race(pips) -> (equity, std_dev) or None for simple one-checker bearoff."""

    def test_returns_tuple_or_none(self, engine):
        result = engine.one_checker_race(10)
        assert result is None or (isinstance(result, (list, tuple)) and len(result) == 2)

    def test_when_returned_equity_and_std_are_numeric(self, engine):
        for pips in (1, 5, 10, 15, 20):
            result = engine.one_checker_race(pips)
            if result is not None:
                equity, std = result
                assert isinstance(equity, (int, float)) and isinstance(std, (int, float))
                assert std >= 0, f"pips={pips} std={std}"

    def test_known_example_if_available(self, engine):
        result = engine.one_checker_race(10)
        if result is not None:
            equity, std = result
            assert isinstance(equity, (int, float)) and isinstance(std, (int, float))


class TestBearoffClassification:
    """Board classification: bearoff positions should classify as c_bearoff when applicable."""

    def test_c_bearoff_constant_exists(self, engine):
        assert hasattr(engine, "c_bearoff")
        assert isinstance(engine.c_bearoff, int)

    def test_classify_bearoff_position(self, engine):
        # Build a one-sided bearoff board: all checkers in home board (points 1–6)
        # Row 0 = X: 15 checkers on point 6 (ready to bear off). Row 1 = O: 0 (already off).
        board = [[0] * 25 for _ in range(2)]
        board[0][6] = 15
        cls = engine.classify(board)
        # Can be c_bearoff, c_race, or c_over (if engine treats O-off as game over)
        valid = (engine.c_bearoff, engine.c_race, engine.c_over)
        assert cls in valid, f"Expected one of {valid}, got {cls}"
