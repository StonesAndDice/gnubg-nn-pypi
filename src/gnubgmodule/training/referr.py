"""Score a net's move choices and cube decisions against real rollout data.

A Python 3 port of the original ``gnubg-nn`` project's ``scripts/train/
referr.py`` (Python 2, ``pygnubg``-only), retargeted at :mod:`gnubg_nn`.
The benchmark file format is unchanged -- the same ``.bm`` rollout files
published at https://alpha.gnu.org/gnu/gnubg/nn-training/ (see
:mod:`gnubg_nn.training.download`) work here directly, one line per
labeled decision:

* ``o <position_key> <p_win> <p_win_gammon> <p_win_backgammon>
  <p_lose_gammon> <p_lose_backgammon>`` -- a cube decision, labeled with
  the rollout-derived probability vector for that position.
* ``m <position_key> <die1> <die2> <best_move_key> [<alt_move_key>
  <alt_loss> ...]`` -- a move decision, labeled with the rollout-ranked
  best move and each alternative's equity loss relative to it.

Lines starting with anything else (``s``/``r`` settings/seed echoes, the
same format :func:`gnubg_nn.rollout` itself would produce) are skipped, not
treated as errors -- the real benchmark files interleave them with the
``o``/``m`` lines being scored.
"""

from __future__ import annotations

import sys
from typing import NamedTuple, TextIO, Tuple, Union

import gnubg_nn


class BenchmarkError(NamedTuple):
    """Mean error over a benchmark file's labeled decisions.

    :ivar move_error: Mean equity lost per move decision by playing the
        net's own 0-ply best move instead of the rollout-labeled one.
        ``0.0`` if the file had no ``m`` lines.
    :ivar double_error: Mean equity lost per cube decision where the net's
        double/no-double call disagreed with the rollout label. ``0.0`` if
        the file had no ``o`` lines.
    :ivar take_error: Mean equity lost per cube decision where the net's
        take/pass call disagreed with the rollout label. ``0.0`` if the
        file had no ``o`` lines.
    """

    move_error: float
    double_error: float
    take_error: float


def _match_equity(values: Tuple, selector: Tuple) -> float:
    """Pick one of ``values``'s three match-equity fields, choosing which
    one by ``selector``'s own double/take verdict.

    ``evaluate_cube_decision(..., i=1, ...)`` returns ``(double, take,
    too_good, no_double_equity, double_take_equity, double_pass_equity)``.
    Port of the original ``referr.py``'s own ``matchEqutiy(i, l)``: taking
    *two* decision tuples (not one) is deliberate -- ``values`` supplies
    the equity numbers, ``selector`` supplies which action's equity to
    read off it, and the two calls in :func:`_score_cube_line` pass
    different combinations (see there). Collapsing this to a single
    tuple, which an earlier version of this port did, silently makes the
    reported error always zero -- both "sides" of the comparison end up
    reading the exact same field.
    """
    double, take = selector[0], selector[1]
    if not double:
        return values[3]
    if take:
        return values[4]
    return values[5]


def _score_cube_line(fields: list) -> Tuple[float, float]:
    """Return ``(double_loss, take_loss)`` for one ``o`` benchmark line's
    fields (already split, ``fields[0] == 'o'``)."""
    # evaluate_cube_decision() takes the raw position-key string directly
    # (or a 26-int AnalyzeBoard) -- NOT the 2x25 Board shape best_move()/
    # classify() use, so this is intentionally not decoded via
    # board_from_position_key() the way _score_move_line() decodes its
    # position.
    position_key = fields[1]
    rollout_probabilities = [float(x) for x in fields[2:]]

    gnubg_nn.set.score(7, 7)  # money-play equivalent: symmetric match score
    net_decision = gnubg_nn.evaluate_cube_decision(position_key, n=0, i=1)
    label_decision = gnubg_nn.evaluate_cube_decision(
        position_key, n=0, i=1, p=tuple(rollout_probabilities)
    )
    gnubg_nn.set.score(0, 0)

    if label_decision[0:3] == net_decision[0:3]:
        return 0.0, 0.0

    # Both values come from the rollout label's own equity numbers --
    # only the *selector* (which of the three fields to read) differs:
    # "if we'd taken the net's action, what would the label's own model
    # say the equity is" vs. "what does the label's model say about its
    # own preferred action".
    net_equity = _match_equity(values=label_decision, selector=net_decision)
    label_equity = _match_equity(values=label_decision, selector=label_decision)
    error = abs(label_equity - net_equity)

    double_loss = error if net_decision[0] != label_decision[0] else 0.0
    take_loss = error if net_decision[1] != label_decision[1] else 0.0
    return double_loss, take_loss


def _score_move_line(fields: list) -> float:
    """Return the equity loss for one ``m`` benchmark line's fields
    (already split, ``fields[0] == 'm'``)."""
    position_key, die1, die2 = fields[1], int(fields[2]), int(fields[3])
    labeled_moves = fields[4:]

    position = gnubg_nn.board_from_position_key(position_key)
    _moves, chosen_key, *_rest = gnubg_nn.best_move(position, die1, die2, 0, b=1)

    if chosen_key == labeled_moves[0]:
        return 0.0
    if chosen_key in labeled_moves:
        # Alternatives are stored as (key, loss) pairs after the best move.
        return float(labeled_moves[labeled_moves.index(chosen_key) + 1])
    # Chosen move wasn't among the labeled alternatives at all -- charge
    # the worst recorded loss, same fallback the original referr.py uses.
    return float(labeled_moves[-1])


def benchmark_error(path_or_file: Union[str, TextIO], verbose: bool = False) -> BenchmarkError:
    """Score the currently active net (see :func:`gnubg_nn.net_use`)
    against a rollout benchmark file.

    :param path_or_file: Path to a ``.bm`` benchmark file, or an already-
        open text file/iterable of lines (matching the original's own
        "accepts a path or a file object" flexibility).
    :param verbose: Print a ``c``/``m`` progress marker to stderr every
        5000 cube/move decisions scored.
    :returns: A :class:`BenchmarkError`.
    """
    cube_positions = 0
    double_error_total = 0.0
    take_error_total = 0.0

    move_positions = 0
    move_error_total = 0.0

    if isinstance(path_or_file, str):
        handle: TextIO = open(path_or_file)  # noqa: SIM115 -- closed below
        should_close = True
    else:
        handle = path_or_file
        should_close = False

    try:
        for line in handle:
            if not line or line.isspace():
                continue
            tag = line[0]
            fields = line.split()

            if tag == "o":
                double_loss, take_loss = _score_cube_line(fields)
                double_error_total += double_loss
                take_error_total += take_loss
                cube_positions += 1
                if verbose and cube_positions % 5000 == 0:
                    print("c", end="", file=sys.stderr)

            elif tag == "m":
                move_error_total += _score_move_line(fields)
                move_positions += 1
                if verbose and move_positions % 5000 == 0:
                    print("m", end="", file=sys.stderr)
    finally:
        if should_close:
            handle.close()

    if move_positions == 0:
        return BenchmarkError(0.0, 0.0, 0.0)
    if cube_positions == 0:
        return BenchmarkError(move_error_total / move_positions, 0.0, 0.0)
    return BenchmarkError(
        move_error_total / move_positions,
        double_error_total / cube_positions,
        take_error_total / cube_positions,
    )


__all__ = ["BenchmarkError", "benchmark_error"]
