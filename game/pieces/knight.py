from pieces.piece import Piece


class Knight(Piece):
    letter = "N"

    def can_move(self, d_row, d_col, color):
        return (abs(d_row), abs(d_col)) in {(1, 2), (2, 1)}
