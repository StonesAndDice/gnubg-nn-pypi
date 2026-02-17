from typing import List, Tuple, Union

# --- Core Types ---
Board = List[List[int]]  # 2x25
AnalyzeBoard = List[int]  # 26 elements
Move = Tuple[int, int]
MoveList = List[Move]

# --- Main API ---
def classify(board: Board) -> int: ...
def pub_best_move(board: Board, dice1: int, dice2: int) -> List[int]: ...
def board_from_position_id(pos_id: str) -> Board: ...
def board_from_position_key(key: str) -> Tuple[Tuple[int, ...], Tuple[int, ...]]: ...
def key_of_board(board: Board) -> str: ...
def position_id(board: Board) -> str: ...
def pub_eval_score(board: Board) -> float: ...
def roll() -> Tuple[int, int]: ...
def best_move(
    pos: Board,
    dice1: int,
    dice2: int,
    n: int = 0,
    s: str = "",
    b: int = 0,
    r: int = 0,
    list: int = 0,
    reduced: int = 0,
) -> Union[
    MoveList,
    Tuple[
        MoveList,
        str,
        int,
        List[Tuple[str, List[int], Tuple[float, float, float, float, float], float]],
    ],
]: ...
def bearoff_id_2_pos(id: int) -> Tuple[int, int, int, int, int, int]: ...
def bearoff_probabilities(
    id_or_pips: Union[int, Tuple[int, int, int, int, int, int]],
) -> Tuple[float, ...]: ...
def moves(
    board: Board, die1: int, die2: int, verbose: int = 0
) -> Union[List[str], List[Tuple[str, MoveList]]]: ...
def probabilities(
    board: Board, nPlies: int, nr: int = 1296
) -> Tuple[float, float, float, float, float]: ...
def rollout(
    pos: Union[AnalyzeBoard, str],
    ngames: int = 1296,
    n: int = 0,
    level: int = 3,
    nt: int = 500,
    std: int = 0,
) -> Union[
    Tuple[float, float, float, float, float],
    Tuple[Tuple[float, ...], Tuple[float, ...]],
]: ...
def cubeful_rollout(
    pos: Union[AnalyzeBoard, str], ngames: int = 576, side: str = "X", ply: int = 0
) -> Tuple[float, ...]: ...
def one_checker_race(n: int) -> Tuple[float, float]: ...
def evaluate_cube_decision(
    pos: Union[AnalyzeBoard, str],
    n: int = 0,
    v: int = -1,
    s: str = "X",
    i: int = 0,
    p: Union[None, Tuple[float, float, float, float, float]] = None,
) -> Union[int, Tuple[int, int, int, float, float, float]]: ...

# --- Submodules ---
class set:
    @staticmethod
    def seed(seed: int) -> None: ...
    @staticmethod
    def shortcuts(use: int) -> None: ...
    @staticmethod
    def osdb(use: int) -> None: ...
    @staticmethod
    def ps(nPlies: int, nMoves: int, nAdditional: int, threshold: float) -> None: ...
    @staticmethod
    def equities(which_or_weights: Union[str, Tuple[float, float]]) -> None: ...
    @staticmethod
    def score(usAway: int, opAway: int, crawford: int = 0) -> None: ...
    @staticmethod
    def cube(cube: int, owner: str = "") -> None: ...

class equities:
    @staticmethod
    def value(xAway: int, oAway: int) -> float: ...

# --- Constants ---
c_over: int
c_bearoff: int
c_race: int
c_crashed: int
c_contact: int
p_osr: int
p_bearoff: int
p_prune: int
p_1sbear: int
p_race: int
p_1srace: int
p_0plus1: int
ro_race: int
ro_bearoff: int
ro_over: int
ro_auto: int
