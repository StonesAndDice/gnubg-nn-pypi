"""
REST API example for gnubg_nn.

To run:
    pip install fastapi uvicorn
    uvicorn examples.rest_api:app --reload

Then access:
    http://localhost:8000/health
    http://localhost:8000/docs (interactive API docs)

Example requests:
    curl -X POST http://localhost:8000/board \
      -H "Content-Type: application/json" \
      -d '{"position_id": "4HPwATDgc/ABMA"}'

    curl -X POST http://localhost:8000/evaluate \
      -H "Content-Type: application/json" \
      -d '{"position_id": "4HPwATDgc/ABMA", "plies": 0}'

    curl -X POST http://localhost:8000/best-move \
      -H "Content-Type: application/json" \
      -d '{"position_id": "4HPwATDgc/ABMA", "dice1": 6, "dice2": 5}'
"""

from fastapi import FastAPI
from pydantic import BaseModel
import gnubg_nn

app = FastAPI(
    title="GNUBG Neural Networks REST API",
    description="Simple REST interface to the GNU Backgammon position-evaluation engine",
    version="0.1.0",
)


# Request/response models
class BoardRequest(BaseModel):
    position_id: str


class BoardResponse(BaseModel):
    position_id: str
    board: list[list[int]]


class EvaluateRequest(BaseModel):
    position_id: str
    plies: int = 0


class EvaluateResponse(BaseModel):
    position_id: str
    plies: int
    win_prob: float
    win_gammon: float
    win_backgammon: float
    lose_gammon: float
    lose_backgammon: float


class BestMoveRequest(BaseModel):
    position_id: str
    dice1: int
    dice2: int


class BestMoveResponse(BaseModel):
    position_id: str
    dice1: int
    dice2: int
    best_move: list[list[int]]


# Endpoints
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/board", response_model=BoardResponse)
def get_board(request: BoardRequest):
    """Convert a position ID to a 2x25 board array."""
    board = gnubg_nn.board_from_position_id(request.position_id)
    return BoardResponse(position_id=request.position_id, board=board)


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate_position(request: EvaluateRequest):
    """Evaluate win/gammon/backgammon probabilities at the given ply depth."""
    board = gnubg_nn.board_from_position_id(request.position_id)
    probs = gnubg_nn.probabilities(board, request.plies)
    win, win_gammon, win_bg, lose_gammon, lose_bg = probs
    return EvaluateResponse(
        position_id=request.position_id,
        plies=request.plies,
        win_prob=win,
        win_gammon=win_gammon,
        win_backgammon=win_bg,
        lose_gammon=lose_gammon,
        lose_backgammon=lose_bg,
    )


@app.post("/best-move", response_model=BestMoveResponse)
def get_best_move(request: BestMoveRequest):
    """Find the best move for a given position and dice roll."""
    board = gnubg_nn.board_from_position_id(request.position_id)
    move = gnubg_nn.best_move(board, request.dice1, request.dice2)
    return BestMoveResponse(
        position_id=request.position_id,
        dice1=request.dice1,
        dice2=request.dice2,
        best_move=move,
    )
