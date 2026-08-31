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

    def test_net_load_and_use(self):
        # Reuse the package's own bundled weights file rather than
        # requiring a second, separate net asset just for this test.
        # Not os.environ["GNUBGHOME"]: the native module's own setenv()
        # call (gnubgmodule.cpp) mutates the process's real environment,
        # but Python's os.environ is a dict snapshot taken once at `os`
        # import time -- it doesn't observe env changes a C extension
        # makes afterwards. Locate the data dir the same way the module
        # itself does instead: relative to its own installed location.
        from pathlib import Path
        weights_path = str(Path(nn.__file__).parent / "data" / "gnubg.weights")

        handle_a = nn.net_load(weights_path)
        handle_b = nn.net_load(weights_path)
        self.assertIsNotNone(handle_a)
        self.assertIsNotNone(handle_b)

        nn.net_use(handle_a)
        probs_a = nn.probabilities(self.board, 0)

        nn.net_use(handle_b)
        probs_b = nn.probabilities(self.board, 0)

        # Same underlying weights file loaded via two independent handles
        # must evaluate identically.
        self.assertEqual(probs_a, probs_b)

        # Switching back to the first handle must reproduce the same
        # result again (no state corruption from the intervening switch).
        nn.net_use(handle_a)
        probs_a_again = nn.probabilities(self.board, 0)
        self.assertEqual(probs_a, probs_a_again)

    def test_net_use_rejects_non_handle(self):
        with self.assertRaises(TypeError):
            nn.net_use("not a handle")

    def test_net_load_rejects_missing_file(self):
        with self.assertRaises(RuntimeError):
            nn.net_load("/nonexistent/path/gnubg.weights")

    def test_net_use_survives_handle_going_out_of_scope(self):
        # Regression test for a real use-after-free this exposed during
        # development: net_use() must keep its own strong reference to
        # whichever handle it makes active, since the caller's own
        # reference (here, the `handle` local below) can be garbage
        # collected the moment this function returns to its caller --
        # without net_use() holding on, the capsule's destructor frees
        # the C-level net while it's still the globally active one, and
        # the NEXT evaluation call segfaults (not this one -- that's
        # what made it easy to miss: it only crashed a few calls later,
        # classic use-after-free timing, confirmed by finding it broke
        # test_unit.py tests that ran strictly after unrelated net_use()
        # calls elsewhere in the suite).
        import gc
        from pathlib import Path

        weights_path = str(Path(nn.__file__).parent / "data" / "gnubg.weights")

        def make_and_activate():
            handle = nn.net_load(weights_path)
            nn.net_use(handle)
            # No reference to `handle` survives this function returning.

        make_and_activate()
        gc.collect()  # force collection now rather than waiting on it

        board = nn.board_from_position_id(self.board_id)
        # If the fix regresses, this is the call that segfaults -- a
        # crash here kills the whole test process, not just this test,
        # so there's no assertion to make beyond "this didn't crash".
        result = nn.probabilities(board, 0)
        self.assertEqual(len(result), 5)

    # Optional: trainer object test (uncomment if stable)
    # def test_trainer(self):
    #     t = nn.trainer({"pos": self.board, "n": 0})
    #     self.assertIsNotNone(t)

if __name__ == '__main__':
    unittest.main()
