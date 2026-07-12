from pieces.piece import PieceRules, sliding_path_is_clear


class Rook(PieceRules):
    letter = "R"

    def can_move(self, d_row, d_col, color):
        return d_row == 0 or d_col == 0

    def is_path_clear(self, start, end, board, color):
        return sliding_path_is_clear(start, end, board)
