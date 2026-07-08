from abc import ABC, abstractmethod


class Piece(ABC):
    """Base class for a piece type. A subclass defines the letter used in
    board tokens (e.g. "K") and its movement shape. Adding a new piece type
    means adding a new subclass here - nothing else in the engine changes."""

    letter = None

    @abstractmethod
    def can_move(self, d_row, d_col):
        """Whether a move with these row/col deltas matches this piece's shape."""
