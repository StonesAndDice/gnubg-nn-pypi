# Examples

This directory contains example scripts demonstrating how to use `gnubg_nn`.

## `print_board.py` — Print a Board from a Position ID

Print the checker positions for a gnubg Position ID.

### Usage

```bash
python examples/print_board.py <position_id>
```

### Examples

Opening position:
```bash
python examples/print_board.py 4HPwATDgc/ABMA
```

Output:
```
Position ID: 4HPwATDgc/ABMA
Board layout: 2x25 array (X on row 0, O on row 1)

Player X:
  Point  1:  2 checkers
  Point  6:  5 checkers
  Point  8:  3 checkers
  Point 13:  5 checkers

Player O:
  Point  6:  5 checkers
  Point  8:  3 checkers
  Point 13:  5 checkers
  Point 24:  2 checkers
```

If you have both a position ID and match ID (separated by `:` or space), only the position part is used:
```bash
python examples/print_board.py "4HPwATDgc/ABMA:some-match-id"
# Output will note that the match ID is ignored
```

---

## `rest_api.py` — REST API Server

A FastAPI server exposing the gnubg_nn engine over HTTP.

### Installation

```bash
pip install fastapi uvicorn
```

### Running

```bash
uvicorn examples.rest_api:app --reload
```

Then visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Endpoints

#### `GET /health`
Health check — always returns `{"status": "ok"}`.

#### `POST /board`
Convert a position ID to a board array.

Request body:
```json
{
  "position_id": "4HPwATDgc/ABMA"
}
```

Response:
```json
{
  "position_id": "4HPwATDgc/ABMA",
  "board": [
    [2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2]
  ]
}
```

#### `POST /evaluate`
Evaluate win/gammon/backgammon probabilities.

Request body:
```json
{
  "position_id": "4HPwATDgc/ABMA",
  "plies": 0
}
```

Response:
```json
{
  "position_id": "4HPwATDgc/ABMA",
  "plies": 0,
  "win_prob": 0.48,
  "win_gammon": 0.12,
  "win_backgammon": 0.02,
  "lose_gammon": 0.15,
  "lose_backgammon": 0.03
}
```

#### `POST /best-move`
Find the best move for a given dice roll.

Request body:
```json
{
  "position_id": "4HPwATDgc/ABMA",
  "dice1": 6,
  "dice2": 5
}
```

Response:
```json
{
  "position_id": "4HPwATDgc/ABMA",
  "dice1": 6,
  "dice2": 5,
  "best_move": [[0, 6], [0, 11]]
}
```

### Example with `curl`

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"position_id": "4HPwATDgc/ABMA", "plies": 0}'
```
