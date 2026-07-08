from pieces.piece import Piece


class King(Piece):
    letter = "K"

    def can_move(self, d_row, d_col):
        return d_row <= 1 and d_col <= 1
