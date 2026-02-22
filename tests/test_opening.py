"""
Tests for opening rolls and opening replies.

Verifies that from the initial backgammon position we get valid legal moves
for every opening roll, and that after an opening move the opponent's replies
work correctly.
"""
import pytest
import gnubg_nn as nn

# Opening position ID used by the engine (standard start, X to move).
OPENING_POSITION_ID = "4HPwATDgc/ABMA"


# All 21 opening rolls: 15 non-doubles (order doesn't matter for count) + 6 doubles.
OPENING_ROLLS = [
    (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 3), (2, 4), (2, 5), (2, 6),
    (3, 4), (3, 5), (3, 6),
    (4, 5), (4, 6),
    (5, 6),
] + [(i, i) for i in range(1, 7)]


@pytest.fixture(scope="module")
def engine():
    """Module under test (engine is initialized at import)."""
    return nn


@pytest.fixture
def opening_board(engine):
    """Opening position as a 2x25 board (X to move)."""
    board = engine.board_from_position_id(OPENING_POSITION_ID)
    return [list(row) for row in board]


class TestOpeningRolls:
    """Test that every opening roll produces at least one legal move."""

    def test_moves_for_every_opening_roll(self, opening_board, engine):
        """For each of the 21 opening rolls, moves() returns at least one legal move."""
        for d1, d2 in OPENING_ROLLS:
            move_keys = engine.moves(opening_board, d1, d2)
            assert isinstance(move_keys, (list, tuple)), f"moves({d1},{d2}) should return sequence"
            assert len(move_keys) >= 1, (
                f"Opening roll {d1}-{d2} should have at least one legal move, got {len(move_keys)}"
            )
            for key in move_keys:
                assert isinstance(key, str), f"Move key should be string, got {type(key)}"
                assert len(key) >= 14, f"Position key should be at least 14 chars, got {len(key)}"

    def test_best_move_for_every_opening_roll(self, opening_board, engine):
        """For each opening roll, best_move() returns a valid result."""
        for d1, d2 in OPENING_ROLLS:
            result = engine.best_move(opening_board, d1, d2)
            assert isinstance(result, tuple), f"best_move({d1},{d2}) should return tuple"
            assert len(result) >= 1, f"best_move({d1},{d2}) should return at least one move"
            # First element is the move (list of (from, to) or similar)
            move = result[0]
            assert isinstance(move, (list, tuple)), f"First element of best_move should be move list/tuple"

    def test_pub_best_move_for_opening_rolls(self, opening_board, engine):
        """pub_best_move returns a valid move for a sample of opening rolls."""
        for d1, d2 in [(3, 1), (6, 1), (5, 3), (4, 2)]:
            move = engine.pub_best_move(opening_board, d1, d2)
            assert isinstance(move, (list, tuple)), f"pub_best_move({d1},{d2}) should return list/tuple"
            assert len(move) >= 2, "pub_best_move should return at least one (from, to) pair"


class TestOpeningReplies:
    """Test that after an opening move, the opponent's reply rolls work."""

    def test_reply_board_after_opening_move(self, opening_board, engine):
        """After applying an opening move, we get a valid board and can get reply moves."""
        # Use opening roll 3-1; get first legal move's position key
        move_keys = engine.moves(opening_board, 3, 1)
        assert len(move_keys) >= 1
        first_key = move_keys[0]
        # Decode to board (position after X moved; now O to move)
        reply_board = engine.board_from_position_key(first_key)
        # board_from_position_key can return (tuple, tuple) in some APIs
        if isinstance(reply_board, tuple) and len(reply_board) == 2:
            reply_board = [list(row) for row in reply_board]
        assert len(reply_board) == 2
        assert len(reply_board[0]) == 25 and len(reply_board[1]) == 25
        # O's reply: get moves for a reply roll (e.g. 2-1)
        reply_moves = engine.moves(reply_board, 2, 1)
        assert isinstance(reply_moves, (list, tuple))
        assert len(reply_moves) >= 1, "Reply roll 2-1 should have at least one legal move"

    def test_best_move_after_opening(self, opening_board, engine):
        """best_move works from the position after an opening move."""
        move_keys = engine.moves(opening_board, 6, 1)
        assert len(move_keys) >= 1
        key = move_keys[0]
        reply_board = engine.board_from_position_key(key)
        if isinstance(reply_board, tuple) and len(reply_board) == 2:
            reply_board = [list(row) for row in reply_board]
        result = engine.best_move(reply_board, 4, 3)
        assert isinstance(result, tuple)
        assert len(result) >= 1

    def test_multiple_opening_replies(self, opening_board, engine):
        """Several opening moves lead to positions where reply rolls have legal moves."""
        # Opening rolls to try
        for d1, d2 in [(1, 2), (5, 4), (6, 5)]:
            move_keys = engine.moves(opening_board, d1, d2)
            assert len(move_keys) >= 1, f"Opening {d1}-{d2} should have moves"
            key = move_keys[0]
            reply_board = engine.board_from_position_key(key)
            if isinstance(reply_board, tuple) and len(reply_board) == 2:
                reply_board = [list(row) for row in reply_board]
            # Reply roll
            reply_moves = engine.moves(reply_board, 1, 1)
            assert len(reply_moves) >= 1, f"Reply 1-1 after {d1}-{d2} should have moves"
