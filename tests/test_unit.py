import unittest
import gnubg_nn as nn
import faulthandler
import pytest

faulthandler.enable()

class TestGnubgBindings(unittest.TestCase):
    def setUp(self):
        self.board_id = "4HPwATDgc/ABMA"
        self.board = nn.board_from_position_id(self.board_id)

    def test_board_key_roundtrip(self):
        key = nn.key_of_board(self.board)
        roundtrip = nn.board_from_position_key(key)
        self.assertEqual(self.board, [list(row) for row in roundtrip])

    def test_roll_output(self):
        d1, d2 = nn.roll()
        self.assertIn(d1, range(1, 7))
        self.assertIn(d2, range(1, 7))

    def test_bestmove_simple(self):
        d1, d2 = nn.roll()
        result = nn.best_move(self.board, d1, d2)
        self.assertIsInstance(result, tuple)

    def test_bestmove_extras(self):
        d1, d2 = nn.roll()
        result = nn.best_move(self.board, d1, d2, b=1, r=1, list=1)
        self.assertIsInstance(result, tuple)

    def test_bearoff_functions(self):
        self.assertIsInstance(nn.bearoff_id_2_pos(1000), tuple)
        self.assertEqual(len(nn.bearoff_probabilities(1000)[:5]), 5)

    def test_moves_function(self):
        result = nn.moves(self.board, 2, 3)
        self.assertIsInstance(result, tuple)

    def test_probs_function(self):
        result = nn.probabilities(self.board, 0)
        self.assertEqual(len(result), 5)

    # def test_rollout(self):
    #     result = nn.rollout(self.board_id, 1)
    #     self.assertEqual(len(result), 2)

    def test_constants_existence(self):
        constants = (
            "c_over", "c_bearoff", "c_race", "c_crashed", "c_contact",
            "p_osr", "p_bearoff", "p_prune", "p_race", "p_1srace", "p_0plus1",
            "ro_auto", "ro_over", "ro_bearoff", "ro_race",
        )
        for name in constants:
            self.assertTrue(hasattr(nn, name), f"{name} missing")

    def test_equities_module(self):
        self.assertTrue(hasattr(nn, "equities"))
        self.assertTrue(hasattr(nn.equities, "value"))
        val = nn.equities.value(2, 3)
        self.assertIsInstance(val, float)

    def test_set_submodule(self):
        nn.set.seed(42)
        nn.set.shortcuts(1)
        nn.set.osdb(0)
        nn.set.ps(1, 4, 0, 0.1)
        nn.set.score(1, 2, 0)
        nn.set.cube(2, b'X')  # just verify no exceptions raised

    def test_onecrace(self):
        result = nn.one_checker_race(10)
        self.assertIsInstance(result, tuple)

    # Optional: trainer object test (uncomment if stable)
    # def test_trainer(self):
    #     t = nn.trainer({"pos": self.board, "n": 0})
    #     self.assertIsNotNone(t)

if __name__ == '__main__':
    unittest.main()
