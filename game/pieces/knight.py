from pieces.piece import PieceRules


class Knight(PieceRules):
    letter = "N"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A knight moves in an L-shape: (1,2) or (2,1) deltas in either
        direction. is_path_clear keeps PieceRules' default (no blockers),
        since knights jump over other pieces."""
        return (abs(d_row), abs(d_col)) in {(1, 2), (2, 1)}
