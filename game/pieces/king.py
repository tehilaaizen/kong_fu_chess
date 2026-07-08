from pieces.piece import Piece


class King(Piece):
    letter = "K"

    def can_move(self, d_row, d_col, color):
        return abs(d_row) <= 1 and abs(d_col) <= 1
