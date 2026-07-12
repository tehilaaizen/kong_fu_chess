from pieces.piece import PieceRules, sliding_path_is_clear


class Bishop(PieceRules):
    letter = "B"

    def can_move(self, d_row, d_col, color):
        return abs(d_row) == abs(d_col)

    def is_path_clear(self, start, end, board, color):
        return sliding_path_is_clear(start, end, board)
