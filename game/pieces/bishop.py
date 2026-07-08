from pieces.piece import Piece


class Bishop(Piece):
    letter = "B"

    def can_move(self, d_row, d_col):
        return d_row == d_col
