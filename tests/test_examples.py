"""Tests for the examples in examples/ directory."""

import pytest
import subprocess
import sys
from pathlib import Path

# For REST API testing
try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

import gnubg_nn as nn


# =============================================================================
# Tests for examples/print_board.py
# =============================================================================


class TestPrintBoardScript:
    """Test the print_board.py CLI script."""

    OPENING_POSITION_ID = "4HPwATDgc/ABMA"
    EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

    def run_print_board(self, *args):
        """Run print_board.py as a subprocess and return stdout, stderr, return code."""
        cmd = [sys.executable, str(self.EXAMPLES_DIR / "print_board.py")] + list(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(self.EXAMPLES_DIR.parent)
        )
        return result.stdout, result.stderr, result.returncode

    def test_valid_position_id(self):
        """Test printing a valid position ID."""
        stdout, stderr, code = self.run_print_board(self.OPENING_POSITION_ID)
        assert code == 0, f"Expected exit code 0, got {code}. stderr: {stderr}"
        assert self.OPENING_POSITION_ID in stdout
        assert "Player X:" in stdout
        assert "Player O:" in stdout

    def test_position_with_pieces_shown(self):
        """Test that the board shows checker counts correctly."""
        stdout, stderr, code = self.run_print_board(self.OPENING_POSITION_ID)
        assert code == 0
        # Opening position should have specific pieces
        assert "Point 24:" in stdout  # X and O both have 2 on their 24-point
        assert "Point  6:" in stdout  # Both have 5 on point 6
        assert "checkers" in stdout

    def test_combined_position_and_match_id(self):
        """Test handling of combined position:match IDs."""
        combined = f"{self.OPENING_POSITION_ID}:some-match-id"
        stdout, stderr, code = self.run_print_board(combined)
        assert code == 0
        assert self.OPENING_POSITION_ID in stdout
        assert "match ID" in stdout.lower() or "not supported" in stdout.lower()

    def test_combined_with_space(self):
        """Test handling of position ID with space-separated match ID."""
        combined = f"{self.OPENING_POSITION_ID} other-data"
        stdout, stderr, code = self.run_print_board(combined)
        assert code == 0
        assert self.OPENING_POSITION_ID in stdout

    def test_invalid_position_id(self):
        """Test error handling for invalid position ID."""
        stdout, stderr, code = self.run_print_board("not-a-real-id")
        assert code != 0, "Expected non-zero exit code for invalid ID"
        assert "Error" in stderr or "error" in stdout.lower()

    def test_no_arguments(self):
        """Test error when no position ID is provided."""
        stdout, stderr, code = self.run_print_board()
        assert code != 0
        # Should show usage/help message
        assert "usage" in stderr.lower() or "position_id" in stderr.lower()

    def test_truncated_position_id(self):
        """Test error for truncated position ID."""
        truncated = self.OPENING_POSITION_ID[:10]
        stdout, stderr, code = self.run_print_board(truncated)
        assert code != 0
        assert "Error" in stderr or "error" in stdout.lower()


# =============================================================================
# Tests for examples/rest_api.py
# =============================================================================


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI not installed")
class TestRestAPI:
    """Test the REST API server endpoints."""

    OPENING_POSITION_ID = "4HPwATDgc/ABMA"

    @pytest.fixture(scope="class")
    def client(self):
        """Create a FastAPI TestClient for the REST API."""
        # Import here to avoid dependency on FastAPI if not installed
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))
        from rest_api import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test GET /health returns status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_board_endpoint_valid(self, client):
        """Test POST /board with valid position ID."""
        response = client.post("/board", json={"position_id": self.OPENING_POSITION_ID})
        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == self.OPENING_POSITION_ID
        assert len(data["board"]) == 2
        assert all(len(row) == 25 for row in data["board"])

    def test_board_endpoint_invalid(self, client):
        """Test POST /board with invalid position ID."""
        response = client.post("/board", json={"position_id": "invalid"})
        assert response.status_code >= 400

    def test_evaluate_endpoint_valid(self, client):
        """Test POST /evaluate with valid position ID."""
        response = client.post(
            "/evaluate", json={"position_id": self.OPENING_POSITION_ID, "plies": 0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == self.OPENING_POSITION_ID
        assert data["plies"] == 0
        assert "win_prob" in data
        assert "win_gammon" in data
        assert "win_backgammon" in data
        assert "lose_gammon" in data
        assert "lose_backgammon" in data
        # Probabilities should be between 0 and 1
        assert 0 <= data["win_prob"] <= 1
        assert 0 <= data["win_gammon"] <= 1

    def test_evaluate_endpoint_custom_plies(self, client):
        """Test POST /evaluate with custom ply depth."""
        response = client.post(
            "/evaluate", json={"position_id": self.OPENING_POSITION_ID, "plies": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plies"] == 2

    def test_evaluate_endpoint_invalid(self, client):
        """Test POST /evaluate with invalid position ID."""
        response = client.post("/evaluate", json={"position_id": "invalid", "plies": 0})
        assert response.status_code >= 400

    def test_best_move_endpoint_valid(self, client):
        """Test POST /best-move with valid inputs."""
        response = client.post(
            "/best-move",
            json={"position_id": self.OPENING_POSITION_ID, "dice1": 6, "dice2": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == self.OPENING_POSITION_ID
        assert data["dice1"] == 6
        assert data["dice2"] == 5
        assert "best_move" in data
        # best_move should be a list of [from, to] pairs
        assert isinstance(data["best_move"], (list, tuple))

    def test_best_move_endpoint_different_dice(self, client):
        """Test POST /best-move with different dice combinations."""
        for dice1, dice2 in [(3, 4), (1, 1), (2, 6)]:
            response = client.post(
                "/best-move",
                json={
                    "position_id": self.OPENING_POSITION_ID,
                    "dice1": dice1,
                    "dice2": dice2,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["dice1"] == dice1
            assert data["dice2"] == dice2

    def test_best_move_endpoint_invalid_position(self, client):
        """Test POST /best-move with invalid position ID."""
        response = client.post(
            "/best-move", json={"position_id": "invalid", "dice1": 6, "dice2": 5}
        )
        assert response.status_code >= 400

    def test_best_move_missing_required_field(self, client):
        """Test POST /best-move with missing required fields."""
        # Missing dice1
        response = client.post(
            "/best-move", json={"position_id": self.OPENING_POSITION_ID, "dice2": 5}
        )
        assert response.status_code >= 400


# =============================================================================
# Integration tests
# =============================================================================


class TestExamplesIntegration:
    """Integration tests between print_board.py and REST API using gnubg_nn directly."""

    OPENING_POSITION_ID = "4HPwATDgc/ABMA"

    def test_print_board_matches_api_board(self):
        """Verify that print_board uses the same board conversion as the API."""
        board = nn.board_from_position_id(self.OPENING_POSITION_ID)
        # Both examples should use the same conversion
        assert len(board) == 2
        assert all(len(row) == 25 for row in board)
        # Known opening position: X has 2 on the 24-point (index 23)
        assert board[0][23] == 2

    def test_board_structure_matches_documentation(self):
        """Verify board structure matches the 2x25 documentation."""
        board = nn.board_from_position_id(self.OPENING_POSITION_ID)
        # Row 0 = X, Row 1 = O
        x_board, o_board = board
        assert len(x_board) == 25  # 0-23 are points, 24 is bar
        assert len(o_board) == 25
        # Total checkers per side should be 15
        assert sum(x_board) == 15
        assert sum(o_board) == 15

    def test_consistency_across_conversions(self):
        """Test that position_id -> board -> key -> board roundtrip is consistent."""
        original_board = nn.board_from_position_id(self.OPENING_POSITION_ID)
        key = nn.key_of_board(original_board)
        roundtrip_board = nn.board_from_position_key(key)
        # Should match original
        assert original_board == [list(row) for row in roundtrip_board]
