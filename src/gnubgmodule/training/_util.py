"""Small, dependency-free helpers shared by the training tools.

A Python 3 port of the reusable parts of the original ``gnubg-nn`` project's
``py/bgutil.py`` (Python 2, ``pygnubg``-only). Only the functions actually
used by :mod:`gnubg_nn.training.referr`, :mod:`gnubg_nn.training.train`, and
:mod:`gnubg_nn.training.buildnet` are ported -- interactive-shell helpers
(``anyInput``, stdin polling for mid-run tweaks) and one-shot analysis
helpers not used by the training loop (``bestMoveOSR``, ``pipcount``) are
left out rather than carried forward unused. Nothing here depends on
:mod:`gnubg_nn` itself except the ``START_POSITION`` constant (which needs
it once, at import time, purely to decode a Position ID -- everything else
in this module is plain arithmetic), so the rest stays trivially
unit-testable without a loaded net.
"""

from __future__ import annotations

import random
from typing import Iterable, List, Sequence, Tuple

import gnubg_nn

#: Standard backgammon starting position, as the 2x25 ``Board`` shape
#: gnubg_nn.classify()/probabilities()/best_move()/etc. all expect.
#: Derived from the well-known starting Position ID rather than
#: hand-encoding the point counts -- the original ``bgutil.py``'s own
#: ``startPos`` constant used a different, flat 26-int layout that these
#: bindings' ``Board`` functions do NOT accept (confirmed empirically:
#: passing it to ``classify()`` raises "Expected 2x25 board list").
START_POSITION: Tuple[Tuple[int, ...], Tuple[int, ...]] = gnubg_nn.board_from_position_id(
    "4HPwATDgc/ABMA"
)


def to_board(rows) -> List[List[int]]:
    """Convert a 2-row board-like value (e.g. the tuple-of-tuples
    :func:`gnubg_nn.board_from_position_key`/``board_from_position_id``
    return, or :data:`START_POSITION`) into the plain ``[[int; 25]; 2]``
    shape some -- not all -- :mod:`gnubg_nn` functions require.

    Not universal: ``best_move()`` accepts a tuple-of-tuples directly
    (confirmed empirically), but ``classify()`` does not (raises "Expected
    2x25 board list" -- its C binding checks ``PyList_Check`` per row,
    which rejects a tuple even though it's otherwise the right shape).
    Call this before any :mod:`gnubg_nn` call that needs it; the cheaper
    tuple form is fine everywhere else.
    """
    return [list(row) for row in rows]


def equity(probabilities: Sequence[float]) -> float:
    """Cubeless equity from a 5-tuple of outcome probabilities.

    :param probabilities: ``(win, win_gammon, win_backgammon, lose_gammon,
        lose_backgammon)``, the same order every :mod:`gnubg_nn` evaluation
        function returns.
    :returns: Equity on the standard -1..+1 cubeless scale.
    """
    win, win_gammon, win_backgammon, lose_gammon, lose_backgammon = probabilities
    return 2 * win - 1 + win_gammon + win_backgammon - lose_gammon - lose_backgammon


def equity_error(px: Sequence[float], py: Sequence[float]) -> float:
    """Sum of absolute per-outcome differences between two probability
    vectors, weighted double on the plain win/loss term.

    Used to measure how far a net's own evaluation of a position has
    drifted from a labeled target -- the same weighting the original
    ``bgutil.py``'s ``eqError`` uses (double weight on ``p0`` since it's
    also folded into gammon/backgammon terms via :func:`equity`).
    """
    return sum((2 if i == 0 else 1) * abs(x - y) for i, (x, y) in enumerate(zip(px, py)))


def format_probabilities(probabilities: Iterable[float], as_percent: bool = True) -> str:
    """Render a probability vector as space-separated fixed-width numbers,
    for log/printout use. ``as_percent=True`` (the default) scales by 100,
    matching the original ``formatedp``'s own default."""
    factor = 100 if as_percent else 1
    return " ".join(f"{factor * x:5.2f}" for x in probabilities)


def format_equity(probabilities: Sequence[float]) -> str:
    """``"<equity> (<formatted probabilities>)"`` -- log-line convenience,
    port of ``bgutil.py``'s ``formatedeq``."""
    return f"{equity(probabilities):.4f} ({format_probabilities(probabilities)})"


def random_order(n: int) -> List[int]:
    """A random permutation of ``range(n)`` -- used to shuffle training
    position order between epochs."""
    order = list(range(n))
    random.shuffle(order)
    return order


def format_seconds(seconds: float) -> str:
    """``H:MM:SS`` (or ``M:SS`` under an hour) -- log-line convenience,
    port of ``bgutil.py``'s ``ftime``."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
