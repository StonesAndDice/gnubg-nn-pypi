"""``gnubg-nn-buildnet`` -- the outer self-play/mine/train cycle loop.

Ties :mod:`gnubg_nn.training.buildnet` (self-play + disagreement mining)
and :mod:`gnubg_nn.training.train` (training) together into the same
repeating cycle the original ``gnubg-nn`` project's ``scripts/train/
buildnet.py`` ran as one script, plus :mod:`gnubg_nn.training.referr` for
progress reporting against a real rollout benchmark each cycle (not the
trainee's own error on its own training data, which can't tell you
whether it's actually getting closer to reality -- see the module
docstrings for why this project ran into exactly that trap using the
original Python 2 tooling before this port existed).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import gnubg_nn

from .buildnet import DisagreementMiningConfig, self_play_and_mine
from .referr import benchmark_error
from .train import load_training_lines, train


def run_cycles(
    trainee_path: str,
    reference_path: str,
    data_path: str,
    benchmark_path: str,
    *,
    target_class_name: str = "contact",
    cycles: int = 10,
    positions_per_cycle: int = 1000,
    equity_threshold: float = 0.02,
    save_path: Optional[str] = None,
    verbose: bool = True,
) -> None:
    """Run ``cycles`` rounds of self-play, disagreement mining, and
    training, saving the trainee net (to ``save_path``, defaulting to
    overwriting ``trainee_path``) whenever a cycle's real-benchmark
    ``move_error`` improves on the best seen so far.

    :param trainee_path: Starting weights file for the net being trained.
    :param reference_path: Fixed reference net -- never modified, never
        overwritten.
    :param data_path: Training-data file to append newly-mined positions
        to (created if missing, resumed/reused if it already has
        content from a previous run).
    :param benchmark_path: A real rollout benchmark file (see
        :mod:`gnubg_nn.training.download`) matching ``target_class_name``
        -- used only for progress reporting and deciding when to save,
        never as a training signal itself.
    :param target_class_name: One of ``"contact"``, ``"race"``,
        ``"crashed"``.
    """
    target_class = {
        "contact": gnubg_nn.c_contact,
        "race": gnubg_nn.c_race,
        "crashed": gnubg_nn.c_crashed,
    }[target_class_name]

    trainee_handle = gnubg_nn.net_load(trainee_path)
    reference_handle = gnubg_nn.net_load(reference_path)
    save_path = save_path or trainee_path

    data_file = Path(data_path)
    seen: set = set()
    if data_file.exists():
        for line in load_training_lines(str(data_file)):
            seen.add(line.split()[0])

    gnubg_nn.net_use(trainee_handle)
    best_move_error = benchmark_error(benchmark_path).move_error
    if verbose:
        print(f"baseline move_error={best_move_error:.6f} ({len(seen)} positions on file)")

    config = DisagreementMiningConfig(
        target_class=target_class,
        equity_threshold=equity_threshold,
        target_positions=positions_per_cycle,
    )

    for cycle in range(1, cycles + 1):
        mined = self_play_and_mine(trainee_handle, reference_handle, config, already_have=seen)
        with open(data_file, "a") as handle:
            handle.writelines(line + "\n" for line in mined.new_lines)
        if verbose:
            print(
                f"cycle {cycle}: {mined.games_played} games, "
                f"{len(mined.new_lines)} new positions "
                f"({mined.elapsed_seconds:.1f}s)"
            )

        all_lines = load_training_lines(str(data_file))
        result = train(all_lines, trainee_handle, on_checkpoint=None)
        if verbose:
            print(
                f"  trained {result.epochs_run} epochs, "
                f"internal error {result.best_errors.mean:.5f}/{result.best_errors.max:.5f}"
            )

        gnubg_nn.net_use(trainee_handle)
        move_error = benchmark_error(benchmark_path).move_error
        if verbose:
            print(f"  benchmark move_error={move_error:.6f}")

        if move_error <= best_move_error:
            best_move_error = move_error
            gnubg_nn.net_use(trainee_handle)  # net_save() saves whatever's active
            gnubg_nn.net_save(save_path)
            if verbose:
                print(f"  saved (new best) -> {save_path}")


def _main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Self-play, mine disagreements against a reference net, and train."
    )
    parser.add_argument("trainee", help="Starting weights file for the net being trained.")
    parser.add_argument("reference", help="Fixed reference net (never modified).")
    parser.add_argument("data", help="Training-data file to append to (created if missing).")
    parser.add_argument("benchmark", help="Real rollout benchmark file for progress reporting.")
    parser.add_argument(
        "--class",
        dest="target_class_name",
        choices=("contact", "race", "crashed"),
        default="contact",
    )
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--positions-per-cycle", type=int, default=1000)
    parser.add_argument("--equity-threshold", type=float, default=0.02)
    parser.add_argument(
        "--save", dest="save_path", default=None, help="Defaults to overwriting `trainee`."
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    run_cycles(
        args.trainee,
        args.reference,
        args.data,
        args.benchmark,
        target_class_name=args.target_class_name,
        cycles=args.cycles,
        positions_per_cycle=args.positions_per_cycle,
        equity_threshold=args.equity_threshold,
        save_path=args.save_path,
        verbose=not args.quiet,
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())


__all__ = ["run_cycles"]
