from pieces.piece import PieceRules


class King(PieceRules):
    letter = "K"

    def can_move(self, d_row, d_col, color):
        return abs(d_row) <= 1 and abs(d_col) <= 1
