"""Train a net against a fixed set of labeled positions.

A Python 3 port of the bounded training loop shared by the original
``gnubg-nn`` project's ``scripts/train/train.py`` and (embedded) ``scripts/
train/buildnet.py``, retargeted at :mod:`gnubg_nn`. ``train.py`` itself was
an infinite, interactive daemon (it polled stdin every cycle for commands
to ``exec``) -- not a shape that makes sense as a library function, so this
ports the bounded, checkpoint-on-improvement variant embedded in
``buildnet.py``'s own ``train()`` instead, which is what
:mod:`gnubg_nn.training.buildnet` also builds on.

Training data is the ``<20-char position key> <5 probabilities>`` line
format written by :mod:`gnubg_nn.training.buildnet` and published at
https://alpha.gnu.org/gnu/gnubg/nn-training/ (see
:mod:`gnubg_nn.training.download`) -- ``gnubg_nn.Trainer`` parses it
directly, so no separate loader is needed here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, List, NamedTuple, Optional, Sequence

import gnubg_nn

from ._util import random_order


class TrainingErrors(NamedTuple):
    """One :meth:`gnubg_nn.Trainer.errors` reading.

    :ivar mean: Mean absolute equity error over the training set.
    :ivar max: Worst single-position equity error.
    """

    mean: float
    max: float


@dataclass
class TrainResult:
    """What :func:`train` returns.

    :ivar epochs_run: Total training epochs (``Trainer.train()`` calls)
        performed.
    :ivar bottoms_hit: How many times the learning rate decayed all the
        way to ``alpha_low`` before being reset -- ``stop_after_bottoms``
        of these ends the run.
    :ivar best_errors: The best (lowest mean-error) :class:`TrainingErrors`
        reading seen, which is also the state the net handle is left in
        (see ``on_checkpoint`` below -- the net is never rolled back to an
        earlier checkpoint automatically; a caller wanting that should
        save on every improving ``on_checkpoint`` call and reload the best
        one afterwards).
    :ivar elapsed_seconds: Wall-clock time spent in this call.
    """

    epochs_run: int
    bottoms_hit: int
    best_errors: TrainingErrors
    elapsed_seconds: float


def train(
    data: Sequence[str],
    net_handle,
    *,
    ignore_backgammons: bool = False,
    alpha_start: float = 20.0,
    alpha_low: float = 0.1,
    improve_factor: float = 0.995,
    min_decrement: float = 0.5,
    min_bottoms: int = 3,
    stop_after_bottoms: int = 20,
    max_seconds: Optional[float] = None,
    on_checkpoint: Optional[Callable[[int, TrainingErrors], None]] = None,
) -> TrainResult:
    """Train ``net_handle`` (from :func:`gnubg_nn.net_load`) against
    ``data`` until the learning rate has bottomed out and failed to
    improve ``stop_after_bottoms`` times, or ``max_seconds`` elapses.

    The learning rate starts at ``alpha_start`` and decays by up to 10%
    (never by less than ``min_decrement``) whenever the error stops
    improving by at least ``improve_factor`` per epoch; once it reaches
    ``alpha_low`` it resets to ``alpha_start`` and the "bottom" counter
    increments -- the same annealing schedule the original
    ``buildnet.py``'s ``train()`` uses. Training position order is
    reshuffled whenever an epoch makes things *worse* than the previous
    one, not every epoch.

    :param data: Training lines, ``gnubg_nn.Trainer``'s own format (see
        module docstring).
    :param net_handle: A handle from :func:`gnubg_nn.net_load` -- this is
        the net that gets trained; it does not need to already be the
        active net (:func:`gnubg_nn.net_use` is called internally).
    :param ignore_backgammons: Passed through to ``gnubg_nn.Trainer`` --
        exclude backgammon outcome components from the error/training
        signal (sensible for race-class data, which usually has none).
    :param on_checkpoint: Called with ``(epoch, errors)`` every time an
        epoch improves on the best error seen so far -- e.g. to save
        ``net_handle`` to disk. Not called otherwise.
    :param max_seconds: Optional wall-clock budget. Checked only after
        ``min_bottoms`` bottoms have been hit (matching the original: a
        time limit shouldn't cut off a run that hasn't stabilized yet).
    :returns: A :class:`TrainResult`.
    """
    gnubg_nn.net_use(net_handle)
    trainer = gnubg_nn.Trainer(list(data), int(ignore_backgammons))

    order = random_order(len(data))
    alpha = alpha_start
    previous_mean = previous_max = float("inf")
    bottoms_hit = 0
    epoch = 0
    started_at = time.monotonic()

    def read_errors() -> TrainingErrors:
        # Trainer.errors() returns (absEquityError, maxAbsEquityError,
        # equityError, maxEquityError, noBGerror, maxNoBGerror) -- indices
        # 4/5 are the "no backgammon" mean/max variant, 0/1 the plain
        # mean/max, matching the original buildnet.py's own
        # terrors[4:6]-for-ignoreBGs / terrors[0:2]-otherwise indexing.
        raw = trainer.errors()
        return TrainingErrors(*raw[4:6]) if ignore_backgammons else TrainingErrors(*raw[0:2])

    best_errors = read_errors()

    while bottoms_hit < stop_after_bottoms:
        current = read_errors()

        if current.mean <= best_errors.mean:
            best_errors = current
            if on_checkpoint is not None:
                on_checkpoint(epoch, current)

        if max_seconds is not None and bottoms_hit >= min_bottoms:
            if time.monotonic() - started_at >= max_seconds:
                break

        improving = (
            current.mean < improve_factor * previous_mean
            or current.max < (1 - 2 * (1 - improve_factor)) * previous_max
        )
        if not improving:
            alpha = max(alpha - max(alpha * 0.1, min_decrement), alpha_low)
            if current.mean > previous_mean:
                order = random_order(len(data))

        previous_mean, previous_max = current.mean, current.max
        epoch += 1

        trainer.train(alpha, order)

        if alpha <= alpha_low:
            alpha = alpha_start
            bottoms_hit += 1

    return TrainResult(
        epochs_run=epoch,
        bottoms_hit=bottoms_hit,
        best_errors=best_errors,
        elapsed_seconds=time.monotonic() - started_at,
    )


def load_training_lines(path: str) -> List[str]:
    """Read a training-data file, skipping blank lines and ``#``
    comments -- matches the format :func:`gnubg_nn.training.buildnet`
    writes and the published ``*-train-data`` files use."""
    with open(path) as handle:
        return [line for line in handle if line.strip() and not line.startswith("#")]


__all__ = ["TrainingErrors", "TrainResult", "train", "load_training_lines"]
