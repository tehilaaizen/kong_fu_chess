from pieces.piece import PieceRules


class King(PieceRules):
    letter = "K"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A king moves exactly one cell in any direction."""
        return abs(d_row) <= 1 and abs(d_col) <= 1
