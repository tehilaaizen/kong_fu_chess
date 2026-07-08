from pieces.piece import Piece


class Knight(Piece):
    letter = "N"

    def can_move(self, d_row, d_col):
        return (d_row, d_col) in {(1, 2), (2, 1)}
