from __future__ import annotations

class Position:
    """A single board cell (row, col) - not pixels. Board owns bounds
    checking; Position is a plain value object."""

    def __init__(self, row: int, col: int) -> None:
        """Store the cell's row/column coordinates."""
        self.row = row
        self.col = col

    def __eq__(self, other: object) -> bool:
        """Two positions are equal when their row and col both match."""
        return isinstance(other, Position) and self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        """Hash by (row, col) so Position can key dicts/sets (e.g. Board's
        piece-by-cell map, PieceRules.legal_destinations)."""
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        """Readable representation for assertion failures and debugging."""
        return f"Position(row={self.row}, col={self.col})"
