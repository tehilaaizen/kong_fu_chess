from pieces.piece import PieceRules, TokenBoard, sliding_path_is_clear


class Bishop(PieceRules):
    letter = "B"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A bishop moves along a diagonal (equal row/col deltas)."""
        return abs(d_row) == abs(d_col)

    def is_path_clear(self, start: tuple[int, int], end: tuple[int, int], board: TokenBoard, color: str) -> bool:
        """Reuses the shared straight-line walk - it steps by the sign of
        each delta independently, so it works for diagonals too."""
        return sliding_path_is_clear(start, end, board)
