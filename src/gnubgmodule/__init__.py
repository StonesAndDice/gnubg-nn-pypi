import os
from pathlib import Path

if os.name == "nt" and hasattr(os, "add_dll_directory"):
    pkgdir = Path(__file__).parent
    if pkgdir.is_dir():
        os.add_dll_directory(str(pkgdir))

# Import your compiled extension module
from ._gnubg_nn import *

# Optional: Expose a namespace
__all__ = [
    "bearoff_id_2_pos",
    "bearoff_probabilities",
    "best_move",
    "board_from_position_id",
    "board_from_position_key",
    "c_bearoff",
    "c_contact",
    "c_crashed",
    "c_over",
    "c_race",
    "classify",
    "cubeful_rollout",
    "equities",
    "evaluate_cube_decision",
    "gnubg",
    "key_of_board",
    "moves",
    "one_checker_race",
    "os",
    "p_0plus1",
    "p_1sbear",
    "p_1srace",
    "p_bearoff",
    "p_osr",
    "p_prune",
    "p_race",
    "position_id",
    "probabilities",
    "pub_best_move",
    "pub_eval_score",
    "ro_auto",
    "ro_bearoff",
    "ro_over",
    "ro_race",
    "roll",
    "rollout",
    "set",
]
