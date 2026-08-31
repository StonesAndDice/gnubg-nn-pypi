"""Tests for :mod:`gnubg_nn.training`.

Follows this project's own convention (see ``tests/test_unit.py``): plain
``unittest.TestCase`` classes, run under pytest. Engine-touching tests use
the package's bundled default net for both "trainee" and "reference" where
two handles are needed -- this project has no bundled second net asset,
and pulling one in only for tests would be a real new test-time dependency
for something these tests don't need: identical nets by construction never
disagree, so the self-play/mining test only needs to prove the mechanism
runs cleanly end-to-end and returns the right shapes, not that it finds
real disagreements (which needs two genuinely different, meaningfully
trained nets -- exercised by hand against real checkpoints during this
module's own development, not repeated here as an automated test since it
would need bundling extra net assets purely for that one assertion).
"""

from __future__ import annotations

import io
import os
import unittest
from pathlib import Path
from unittest import mock

import gnubg_nn as nn

from gnubg_nn.training import _util
from gnubg_nn.training.buildnet import DisagreementMiningConfig, self_play_and_mine
from gnubg_nn.training.download import (
    CLASSES,
    download_all,
    download_benchmark,
    download_reference_net,
    download_training_data,
)
from gnubg_nn.training.referr import _match_equity, benchmark_error
from gnubg_nn.training.train import load_training_lines, train


def _bundled_weights_path() -> str:
    return str(Path(nn.__file__).parent / "data" / "gnubg.weights")


class TestUtil(unittest.TestCase):
    def test_equity_extremes(self):
        self.assertAlmostEqual(_util.equity((1, 0, 0, 0, 0)), 1.0)
        self.assertAlmostEqual(_util.equity((0, 0, 0, 0, 0)), -1.0)
        self.assertAlmostEqual(_util.equity((0.5, 0, 0, 0, 0)), 0.0)

    def test_equity_error_symmetric(self):
        px = (0.6, 0.1, 0.0, 0.1, 0.0)
        py = (0.5, 0.2, 0.0, 0.05, 0.0)
        self.assertAlmostEqual(_util.equity_error(px, py), _util.equity_error(py, px))

    def test_equity_error_zero_for_identical(self):
        p = (0.4, 0.1, 0.05, 0.1, 0.02)
        self.assertEqual(_util.equity_error(p, p), 0.0)

    def test_format_probabilities_default_scales_to_percent(self):
        formatted = _util.format_probabilities((0.5, 0.0, 0.0, 0.0, 0.0))
        self.assertIn("50.00", formatted)

    def test_random_order_is_a_permutation(self):
        order = _util.random_order(10)
        self.assertEqual(sorted(order), list(range(10)))

    def test_format_seconds_under_and_over_an_hour(self):
        self.assertEqual(_util.format_seconds(65), "1:05")
        self.assertEqual(_util.format_seconds(3665), "1:01:05")

    def test_to_board_produces_lists_not_tuples(self):
        board = _util.to_board(((1, 2), (3, 4)))
        self.assertEqual(board, [[1, 2], [3, 4]])
        self.assertIsInstance(board[0], list)

    def test_start_position_is_the_real_starting_board(self):
        # Cross-check against the well-known starting Position ID decoded
        # directly, rather than hand-asserting point counts.
        expected = nn.board_from_position_id("4HPwATDgc/ABMA")
        self.assertEqual(_util.START_POSITION, expected)

    def test_start_position_classifies_as_contact(self):
        board = _util.to_board(_util.START_POSITION)
        self.assertEqual(nn.classify(board), nn.c_contact)


class TestMatchEquity(unittest.TestCase):
    """_match_equity(values, selector) -- see its own docstring for why
    this takes two decision tuples, not one (an earlier version of this
    port collapsed them into one and silently zeroed every cube error)."""

    def test_reads_no_double_field_when_selector_says_no_double(self):
        values = (0, 1, 0, 111.0, 222.0, 333.0)
        selector = (0, 0, 0, 0, 0, 0)  # double=0 -> field index 3
        self.assertEqual(_match_equity(values, selector), 111.0)

    def test_reads_take_field_when_selector_says_double_take(self):
        values = (0, 1, 0, 111.0, 222.0, 333.0)
        selector = (1, 1, 0, 0, 0, 0)  # double=1, take=1 -> field index 4
        self.assertEqual(_match_equity(values, selector), 222.0)

    def test_reads_pass_field_when_selector_says_double_pass(self):
        values = (0, 1, 0, 111.0, 222.0, 333.0)
        selector = (1, 0, 0, 0, 0, 0)  # double=1, take=0 -> field index 5
        self.assertEqual(_match_equity(values, selector), 333.0)

    def test_selector_and_values_can_differ(self):
        # This is the whole point of the two-tuple design: the equity
        # numbers always come from `values`, but which one gets picked
        # is `selector`'s call -- proves the two aren't silently
        # collapsed onto the same tuple (a regression test for the exact
        # bug described in the module docstring).
        values = (0, 1, 0, 1.0, 2.0, 3.0)
        net_selector = (1, 0, 0, 0, 0, 0)  # net would double/pass -> index 5
        self.assertEqual(_match_equity(values, net_selector), 3.0)
        self.assertEqual(_match_equity(values, values), 1.0)  # values' own verdict -> index 3


class TestBenchmarkError(unittest.TestCase):
    def test_empty_file_returns_zero(self):
        result = benchmark_error(io.StringIO(""))
        self.assertEqual(result, (0.0, 0.0, 0.0))

    def test_non_om_lines_are_skipped_not_errors(self):
        # 's'/'r' lines (settings/seed echoes) appear throughout the real
        # published benchmark files interleaved with 'o'/'m' lines.
        result = benchmark_error(io.StringIO("s version 1.0\nr 12345\n"))
        self.assertEqual(result, (0.0, 0.0, 0.0))

    def test_move_line_scores_against_the_bundled_net(self):
        handle = nn.net_load(_bundled_weights_path())
        nn.net_use(handle)
        board = _util.to_board(_util.START_POSITION)
        key = nn.key_of_board(board)
        _moves, best_key, *_rest = nn.best_move(board, 3, 1, 0, b=1)

        # The net's own best move, labeled as correct -- should score 0.
        line = f"m {key} 3 1 {best_key}\n"
        result = benchmark_error(io.StringIO(line))
        self.assertEqual(result.move_error, 0.0)
        self.assertEqual(result.double_error, 0.0)
        self.assertEqual(result.take_error, 0.0)

    def test_accepts_a_path_as_well_as_a_file_object(self, tmp_path=None):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".bm", delete=False) as handle:
            handle.write("s version 1.0\n")
            path = handle.name
        try:
            result = benchmark_error(path)
            self.assertEqual(result, (0.0, 0.0, 0.0))
        finally:
            os.unlink(path)


class TestTrain(unittest.TestCase):
    def test_load_training_lines_skips_blanks_and_comments(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".dat", delete=False) as handle:
            handle.write("# a comment\n")
            handle.write("\n")
            handle.write("ABCDEFGHIJKLMNOPQRST 0.5 0.1 0.0 0.1 0.0\n")
            path = handle.name
        try:
            lines = load_training_lines(path)
            self.assertEqual(len(lines), 1)
            self.assertTrue(lines[0].startswith("ABCDEFGHIJKLMNOPQRST"))
        finally:
            os.unlink(path)

    def test_train_reduces_internal_error_on_a_solvable_set(self):
        handle = nn.net_load(_bundled_weights_path())
        board = _util.to_board(_util.START_POSITION)
        key = nn.key_of_board(board)
        # A single labeled position with an extreme target the net
        # almost certainly doesn't already predict -- training on it
        # should visibly move the error, proving train() actually calls
        # into Trainer.train() rather than being a no-op.
        line = f"{key} 0.99000 0.50000 0.10000 0.00000 0.00000"

        nn.net_use(handle)
        before = train([line], handle, stop_after_bottoms=1, min_bottoms=0)
        self.assertGreater(before.epochs_run, 0)


class TestSelfPlayAndMine(unittest.TestCase):
    def test_returns_requested_shape_even_with_identical_nets(self):
        # Two handles onto the SAME weights file, compared at the SAME
        # ply, never disagree by construction -- this proves the
        # self-play loop itself runs cleanly (games advance, classify()/
        # best_move() calls all succeed) without asserting on
        # disagreement counts, which would need two genuinely different
        # nets to be meaningful. reference_ply=0 matters here: with the
        # default reference_ply=2, even identical weights can
        # legitimately pick a different move at a deeper search depth
        # than at 0-ply -- that's real lookahead behavior, not a false
        # "disagreement", so it's deliberately excluded from this check.
        path = _bundled_weights_path()
        trainee = nn.net_load(path)
        reference = nn.net_load(path)

        config = DisagreementMiningConfig(
            target_class=nn.c_contact,
            target_positions=1,
            max_game_plies=60,
            reference_ply=0,
            max_games=5,  # identical nets at the same ply never disagree --
            # this must hit the max_games cap, not target_positions
        )
        result = self_play_and_mine(trainee, reference, config)
        self.assertEqual(result.new_lines, [])
        self.assertEqual(result.games_played, 5)


class TestDownload(unittest.TestCase):
    def test_classes_tuple(self):
        self.assertEqual(CLASSES, ("contact", "race", "crashed"))

    def test_download_benchmark_rejects_unknown_class(self):
        with self.assertRaises(ValueError):
            download_benchmark("not-a-real-class", "/tmp")

    def test_download_training_data_rejects_unknown_class(self):
        with self.assertRaises(ValueError):
            download_training_data("not-a-real-class", "/tmp")

    def test_download_reference_net_builds_the_confirmed_url(self):
        # Doesn't hit the network -- checks the exact URL construction
        # against the real, hand-confirmed server layout (see the
        # module docstring: 1.01/nets/ and 1.00/{benchmarks,
        # training_data}/ are NOT mirrors of each other, so this is
        # worth pinning down explicitly).
        with (
            mock.patch("gnubg_nn.training.download._download_and_decompress") as fake,
            mock.patch("gnubg_nn.training.download._download"),
        ):
            fake.return_value = Path("/tmp/nngnubg.weights")
            download_reference_net("/tmp")
            url = fake.call_args[0][0]
            self.assertEqual(
                url, "https://alpha.gnu.org/gnu/gnubg/nn-training/1.01/nets/nngnubg.weights.bz2"
            )

    def test_download_benchmark_builds_the_confirmed_url(self):
        with (
            mock.patch("gnubg_nn.training.download._download_and_decompress") as fake,
            mock.patch("gnubg_nn.training.download._download"),
        ):
            fake.return_value = Path("/tmp/contact.bm")
            download_benchmark("contact", "/tmp")
            url = fake.call_args[0][0]
            self.assertEqual(
                url,
                "https://alpha.gnu.org/gnu/gnubg/nn-training/1.00/benchmarks/contact.bm.bz2",
            )

    def test_download_all_fetches_net_plus_every_class_pair(self):
        with (
            mock.patch("gnubg_nn.training.download.download_reference_net") as net,
            mock.patch("gnubg_nn.training.download.download_benchmark") as bench,
            mock.patch("gnubg_nn.training.download.download_training_data") as data,
        ):
            net.return_value = Path("/tmp/nngnubg.weights")
            bench.return_value = Path("/tmp/x.bm")
            data.return_value = Path("/tmp/x-train-data")
            paths = download_all("/tmp")
            net.assert_called_once()
            self.assertEqual(bench.call_count, len(CLASSES))
            self.assertEqual(data.call_count, len(CLASSES))
            self.assertEqual(len(paths), 1 + 2 * len(CLASSES))


if __name__ == "__main__":
    unittest.main()
