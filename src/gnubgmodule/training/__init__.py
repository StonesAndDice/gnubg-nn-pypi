"""Train :mod:`gnubg_nn` nets against GNU Backgammon's own published
rollout data, or against each other.

Python 3 ports of the original ``gnubg-nn`` project's ``scripts/train/*.py``
(Python 2, ``pygnubg``-only) -- see each submodule's own docstring for what
changed and what was deliberately left out. Typical usage is the
:func:`run_cycles` CLI driver (``gnubg-nn-buildnet`` after installing this
package), which ties the other pieces together into the same self-play ->
mine-disagreements -> train -> repeat loop the original scripts implement
as one large script. See the ``training`` page in this package's docs for
a full walkthrough.
"""

from .buildnet import DisagreementMiningConfig, DisagreementMiningResult, self_play_and_mine
from .cli import run_cycles
from .download import (
    CLASSES,
    download_all,
    download_benchmark,
    download_reference_net,
    download_training_data,
)
from .referr import BenchmarkError, benchmark_error
from .train import TrainingErrors, TrainResult, load_training_lines, train

__all__ = [
    "DisagreementMiningConfig",
    "DisagreementMiningResult",
    "self_play_and_mine",
    "BenchmarkError",
    "benchmark_error",
    "TrainingErrors",
    "TrainResult",
    "load_training_lines",
    "train",
    "CLASSES",
    "download_all",
    "download_benchmark",
    "download_reference_net",
    "download_training_data",
    "run_cycles",
]
