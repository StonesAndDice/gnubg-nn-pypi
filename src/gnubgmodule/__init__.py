import os
from pathlib import Path

if os.name == "nt" and hasattr(os, "add_dll_directory"):
    pkgdir = Path(__file__).parent
    if pkgdir.is_dir():
        os.add_dll_directory(str(pkgdir))

# Import your compiled extension module
from ._gnubg_nn import *

# Make __version__ available as a module with all version attributes
# (don't overwrite the submodule reference with a string)
try:
    from . import __version__ as _version_module
except (ImportError, AttributeError):
    pass

# Deprecated aliases for backwards compatibility with pygnubg
boardfromkey = board_from_position_key
boardfromid = board_from_position_id
bestmove = best_move

__all__ = [
    # Board conversion
    "board_from_position_id",
    "board_from_position_key",
    "key_of_board",
    "position_id",
    # Move & evaluation
    "best_move",
    "moves",
    "pub_best_move",
    "pub_eval_score",
    # Classification
    "classify",
    # Probabilities & rollout
    "probabilities",
    "rollout",
    "cubeful_rollout",
    "one_checker_race",
    # Cube
    "evaluate_cube_decision",
    # Bearoff
    "bearoff_id_2_pos",
    "bearoff_probabilities",
    # Equity / match
    "equities",
    # Utility / version
    "roll",
    "eq2mwc",
    "mwc2eq",
    "eq2mwc_stderr",
    "mwc2eq_stderr",
    "luckrating",
    "errorrating",
    "parsemove",
    "movetupletostring",
    "full_version",
    "short_version",
    "git_revision",
    # Training
    "Trainer",
    # Multi-net handles
    "net_load",
    "net_use",
    "net_save",
    # Submodules
    "set",
    # Position type constants
    "c_bearoff",
    "c_contact",
    "c_crashed",
    "c_over",
    "c_race",
    # Ply constants
    "p_0plus1",
    "p_1sbear",
    "p_1srace",
    "p_bearoff",
    "p_osr",
    "p_prune",
    "p_race",
    # Rollout constants
    "ro_auto",
    "ro_bearoff",
    "ro_over",
    "ro_race",
    # Deprecated aliases (backwards compat with pygnubg)
    "boardfromkey",
    "boardfromid",
    "bestmove",
]
