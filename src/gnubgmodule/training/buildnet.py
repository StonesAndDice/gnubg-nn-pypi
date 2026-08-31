"""Self-play a net against a fixed reference net, mine the positions where
they disagree, and train on the disagreements.

A Python 3 port of the core algorithm in the original ``gnubg-nn``
project's ``scripts/train/buildnet.py`` (Python 2, ``pygnubg``-only),
retargeted at :mod:`gnubg_nn`, using the ``net_load``/``net_use`` handle
API added alongside this module specifically so one process can hold both
nets (the trainee and the fixed reference) at once, matching the original
script's own ``gnubg.net.get()``/``gnubg.net.set()`` pattern.

**What's ported**: self-play driven by the trainee net's own 0-ply move
choice; at each position in the target game phase, a cube-decision check
(sweeping the same 18 match scores as the original) and a single-ply
move-choice check against the reference net, with disagreements above a
threshold written out as new training positions (labeled with the
reference net's own evaluation).

**What's deliberately NOT ported**: the original's ``do1p`` branch (a
secondary, more expensive refinement that additionally compares 1-ply vs.
reference-ply move choices and expands *all* 21 replies at both resulting
positions when they disagree) and the alternate ``method_p1``/
``method_1ponly`` data-generation strategies (rarely-used experimental
alternatives to the main path, per the original's own comments). The
ported path is what this project's own training runs actually used.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Tuple

import gnubg_nn

from ._util import START_POSITION, equity, to_board

#: Match scores swept by the cube-decision disagreement check -- money
#: play (7-away/7-away) plus a spread of close-to-even and lopsided
#: scores, mirroring the original ``buildnet.py``'s own ``scores`` list.
_CUBE_CHECK_SCORES: Tuple[Tuple[int, int], ...] = tuple(
    pair
    for base in (
        (7, 7),
        (3, 3),
        (5, 5),
        (9, 9),
        (25, 25),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (2, 7),
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
        (4, 5),
        (4, 6),
        (4, 7),
        (5, 7),
    )
    for pair in ({base} if base[0] == base[1] else {base, base[::-1]})
)


@dataclass
class DisagreementMiningConfig:
    """Tuning knobs for :func:`self_play_and_mine`.

    :ivar target_class: One of ``gnubg_nn.c_contact``, ``c_race``, or
        ``c_crashed`` -- which game phase to collect training data for.
    :ivar equity_threshold: Minimum equity disagreement (on the -1..+1
        cubeless scale) between the trainee and reference net's own
        evaluation of a position before it's worth adding.
    :ivar reference_ply: Lookahead depth used for the reference net's
        "correct" move choice and evaluation. The original defaults this
        to 2 (or 1 with its own ``--use1p`` flag) -- deeper is a more
        trustworthy label at the cost of more evaluation time per
        position checked.
    :ivar target_positions: Stop once this many new positions have been
        collected.
    :ivar max_game_plies: Hang guard -- abandon a self-play game after
        this many plies even if it hasn't reached game-over (matches the
        original's implicit reliance on real games always ending; this
        makes that explicit rather than assumed).
    :ivar max_games: Hang guard -- stop after this many games even if
        ``target_positions`` was never reached. The original script had
        no equivalent: it implicitly assumed a sufficiently different
        trainee/reference pair would always keep producing
        disagreements, which doesn't hold in general (confirmed: two
        handles on the *same* weights file, or a reference_ply that
        happens to always agree with the trainee's ply, can genuinely
        never disagree, and would otherwise self-play forever).
    """

    target_class: int
    equity_threshold: float = 0.02
    reference_ply: int = 2
    target_positions: int = 1000
    max_game_plies: int = 400
    max_games: int = 10_000


@dataclass
class DisagreementMiningResult:
    """What :func:`self_play_and_mine` returns."""

    #: New ``"<position_key> <5 probabilities>"`` lines, in the exact
    #: format :func:`gnubg_nn.training.train.load_training_lines` and
    #: ``gnubg_nn.Trainer`` both expect.
    new_lines: List[str] = field(default_factory=list)
    games_played: int = 0
    elapsed_seconds: float = 0.0


def _cube_decision_disagrees(
    position_key: str, trainee_probs: Tuple[float, ...], reference_probs: Tuple[float, ...]
) -> bool:
    """True if the trainee's and reference's own cube verdicts differ at
    any of :data:`_CUBE_CHECK_SCORES`, given each side's own probability
    vector for this position (already evaluated by the caller)."""
    for us_away, them_away in _CUBE_CHECK_SCORES:
        gnubg_nn.set.score(us_away, them_away)
        try:
            trainee_decision = gnubg_nn.evaluate_cube_decision(
                position_key, n=0, i=1, p=trainee_probs
            )
            reference_decision = gnubg_nn.evaluate_cube_decision(
                position_key, n=0, i=1, p=reference_probs
            )
        except ValueError:
            # A small number of positions produce a probability vector
            # evaluate_cube_decision() rejects as internally inconsistent
            # (observed empirically against real trained nets, not just a
            # theoretical case) -- skip that one score rather than losing
            # the whole self-play game to it.
            continue
        finally:
            gnubg_nn.set.score(0, 0)
        if trainee_decision[0:3] != reference_decision[0:3]:
            return True
    return False


def self_play_and_mine(
    trainee_handle,
    reference_handle,
    config: DisagreementMiningConfig,
    *,
    already_have: Optional[Set[str]] = None,
    on_position_added: Optional[Callable[[str], None]] = None,
) -> DisagreementMiningResult:
    """Self-play games (driven by the trainee net's own 0-ply move
    choice), collecting positions in ``config.target_class`` where the
    trainee and reference nets disagree.

    :param trainee_handle: The net being trained (a
        :func:`gnubg_nn.net_load` handle) -- also the policy that plays
        every self-play game.
    :param reference_handle: The fixed net disagreements are measured
        against -- never modified.
    :param already_have: Position keys to skip (e.g. from a previous
        call/session) -- updated in place with every newly-added key.
    :param on_position_added: Optional callback, called with each new
        position's key as it's added (e.g. for a progress log).
    :returns: A :class:`DisagreementMiningResult`.
    """
    seen = already_have if already_have is not None else set()
    result = DisagreementMiningResult()
    started_at = time.monotonic()

    while (
        len(result.new_lines) < config.target_positions and result.games_played < config.max_games
    ):
        gnubg_nn.net_use(trainee_handle)
        position = to_board(START_POSITION)
        while True:
            die1, die2 = gnubg_nn.roll()
            if die1 != die2:
                break
        result.games_played += 1

        for _ in range(config.max_game_plies):
            gnubg_nn.net_use(trainee_handle)
            if gnubg_nn.classify(position) == gnubg_nn.c_over:
                break

            die_high, die_low = sorted((die1, die2), reverse=True)

            if gnubg_nn.classify(position) == config.target_class:
                position_key = gnubg_nn.key_of_board(position)

                if position_key not in seen:
                    trainee_probs = gnubg_nn.probabilities(position, 0)

                    gnubg_nn.net_use(reference_handle)
                    reference_probs = gnubg_nn.probabilities(position, config.reference_ply)

                    if (
                        abs(equity(trainee_probs) - equity(reference_probs))
                        >= config.equity_threshold
                    ):
                        disagrees = _cube_decision_disagrees(
                            position_key, trainee_probs, reference_probs
                        )
                        if disagrees:
                            result.new_lines.append(
                                f"{position_key} " + " ".join(f"{p:.5f}" for p in reference_probs)
                            )
                            seen.add(position_key)
                            if on_position_added is not None:
                                on_position_added(position_key)
                            if len(result.new_lines) >= config.target_positions:
                                break

                    gnubg_nn.net_use(trainee_handle)
                    _check_move_disagreement(
                        position,
                        die_high,
                        die_low,
                        trainee_handle,
                        reference_handle,
                        config,
                        seen,
                        result,
                        on_position_added,
                    )
                    if len(result.new_lines) >= config.target_positions:
                        break

            gnubg_nn.net_use(trainee_handle)
            _moves, chosen_key, *_rest = gnubg_nn.best_move(position, die1, die2, 0, b=1)
            position = to_board(gnubg_nn.board_from_position_key(chosen_key))
            die1, die2 = gnubg_nn.roll()

    result.elapsed_seconds = time.monotonic() - started_at
    return result


def _check_move_disagreement(
    position,
    die_high: int,
    die_low: int,
    trainee_handle,
    reference_handle,
    config: DisagreementMiningConfig,
    seen: Set[str],
    result: DisagreementMiningResult,
    on_position_added: Optional[Callable[[str], None]],
) -> None:
    """Compare the trainee's 0-ply move choice against the reference
    net's ``config.reference_ply`` choice; if they differ by enough
    equity, add whichever of the two resulting positions still qualify
    for ``config.target_class`` (mirrors the original's own per-move
    comparison, without its further ``do1p`` expansion -- see module
    docstring)."""
    gnubg_nn.net_use(trainee_handle)
    _m, trainee_key, *_r = gnubg_nn.best_move(position, die_high, die_low, 0, b=1)

    gnubg_nn.net_use(reference_handle)
    _m, reference_key, *_r = gnubg_nn.best_move(
        position, die_high, die_low, config.reference_ply, b=1
    )

    if trainee_key == reference_key:
        return

    trainee_result = to_board(gnubg_nn.board_from_position_key(trainee_key))
    reference_result = to_board(gnubg_nn.board_from_position_key(reference_key))
    trainee_probs = gnubg_nn.probabilities(trainee_result, config.reference_ply)
    reference_probs = gnubg_nn.probabilities(reference_result, config.reference_ply)

    if abs(equity(trainee_probs) - equity(reference_probs)) < config.equity_threshold:
        return

    for key, board, probs in (
        (trainee_key, trainee_result, trainee_probs),
        (reference_key, reference_result, reference_probs),
    ):
        if key in seen or gnubg_nn.classify(board) != config.target_class:
            continue
        result.new_lines.append(f"{key} " + " ".join(f"{p:.5f}" for p in probs))
        seen.add(key)
        if on_position_added is not None:
            on_position_added(key)


__all__ = [
    "DisagreementMiningConfig",
    "DisagreementMiningResult",
    "self_play_and_mine",
]
