from pieces.piece import Piece


class Rook(Piece):
    letter = "R"

    def can_move(self, d_row, d_col):
        return d_row == 0 or d_col == 0
