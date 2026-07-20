"""Tests for the Trainer class."""

import pytest
import gnubg_nn as nn


@pytest.fixture
def sample_position_key():
    """Get a valid position key from the opening position."""
    board = nn.board_from_position_id("4HPwATDgc/ABMA")
    return nn.key_of_board(board)


@pytest.fixture
def sample_training_data(sample_position_key):
    """Create sample training data: position key + 5 probabilities."""
    # Format: 20-char key followed by 5 space-separated floats
    return [
        f"{sample_position_key} 0.5 0.1 0.05 0.1 0.05",
        f"{sample_position_key} 0.6 0.15 0.08 0.08 0.04",
    ]


class TestTrainerBasics:
    """Test basic Trainer construction and usage."""

    def test_trainer_construction(self, sample_training_data):
        """Test that Trainer can be constructed from valid data."""
        trainer = nn.Trainer(sample_training_data)
        assert trainer is not None

    def test_trainer_errors_returns_tuple(self, sample_training_data):
        """Test that errors() method returns a 6-tuple of floats."""
        trainer = nn.Trainer(sample_training_data)
        errors = trainer.errors()
        assert isinstance(errors, tuple)
        assert len(errors) == 6
        assert all(isinstance(e, float) for e in errors)

    def test_trainer_errors_all_positive(self, sample_training_data):
        """Test that error values are all non-negative."""
        trainer = nn.Trainer(sample_training_data)
        errors = trainer.errors()
        assert all(e >= 0 for e in errors)

    def test_trainer_train_doesnt_crash(self, sample_training_data):
        """Test that train() method executes without crashing."""
        trainer = nn.Trainer(sample_training_data)
        # Just ensure it doesn't raise
        trainer.train(0.01)

    def test_trainer_train_with_order(self, sample_training_data):
        """Test train() with custom order."""
        trainer = nn.Trainer(sample_training_data)
        # Train in reverse order
        order = list(range(len(sample_training_data) - 1, -1, -1))
        trainer.train(0.01, order)


class TestTrainerOptions:
    """Test constructor options."""

    def test_trainer_with_ignore_bgs(self, sample_training_data):
        """Test Trainer with ignoreBGs=1."""
        trainer = nn.Trainer(sample_training_data, ignoreBGs=1)
        errors = trainer.errors()
        assert isinstance(errors, tuple)
        assert len(errors) == 6

    def test_trainer_with_prune_net(self, sample_training_data):
        """Test Trainer with pruneNet=1."""
        trainer = nn.Trainer(sample_training_data, pruneNet=1)
        errors = trainer.errors()
        assert isinstance(errors, tuple)
        assert len(errors) == 6

    def test_trainer_with_tlist(self, sample_training_data):
        """Test Trainer with tList option."""
        trainer = nn.Trainer(sample_training_data, tList=[0, 1, 2])
        errors = trainer.errors()
        assert isinstance(errors, tuple)
        assert len(errors) == 6

    def test_trainer_all_options(self, sample_training_data):
        """Test Trainer with all options specified."""
        trainer = nn.Trainer(sample_training_data, ignoreBGs=1, pruneNet=0, tList=[0])
        errors = trainer.errors()
        assert isinstance(errors, tuple)


class TestTrainerErrorHandling:
    """Test error handling."""

    def test_trainer_invalid_data_type(self):
        """Test that non-sequence data raises TypeError."""
        with pytest.raises(TypeError):
            nn.Trainer("not a sequence")

    def test_trainer_invalid_string_format(self):
        """Test that invalid position key format raises ValueError."""
        with pytest.raises(ValueError):
            nn.Trainer(["tooshort 0.5 0.1 0.05 0.1 0.05"])

    def test_trainer_missing_probabilities(self, sample_position_key):
        """Test that missing probability values raise ValueError."""
        with pytest.raises(ValueError):
            nn.Trainer([f"{sample_position_key} 0.5 0.1"])

    def test_trainer_invalid_order_length(self, sample_training_data):
        """Test that order list of wrong length raises ValueError."""
        trainer = nn.Trainer(sample_training_data)
        with pytest.raises(ValueError):
            trainer.train(0.01, [0])  # Should have 2 elements

    def test_trainer_train_empty_data(self):
        """Test Trainer with empty data."""
        trainer = nn.Trainer([])
        errors = trainer.errors()
        # Should return 6 zeros or NaNs, not crash
        assert len(errors) == 6


class TestTrainerResponsiveness:
    """Test that training actually affects the network."""

    def test_errors_respond_to_training(self, sample_training_data):
        """Test that errors() changes after calling train()."""
        trainer = nn.Trainer(sample_training_data)
        errors_before = trainer.errors()
        trainer.train(0.01)
        errors_after = trainer.errors()
        # At least one error metric should change (no assertion on direction,
        # just that they're not identical)
        assert errors_before != errors_after


class TestTrainerWithDifferentPositions:
    """Test Trainer with various positions."""

    def test_trainer_many_positions(self):
        """Test Trainer with multiple different positions."""
        positions = [
            ("4HPwATDgc/ABMA", 0.5, 0.1, 0.05, 0.1, 0.05),
            ("4HPwATDgc/ABMA", 0.6, 0.15, 0.08, 0.08, 0.04),
        ]

        data = []
        for pos_id, *probs in positions:
            board = nn.board_from_position_id(pos_id)
            key = nn.key_of_board(board)
            prob_str = " ".join(str(p) for p in probs)
            data.append(f"{key} {prob_str}")

        trainer = nn.Trainer(data)
        errors = trainer.errors()
        assert len(errors) == 6
        assert all(isinstance(e, float) for e in errors)
