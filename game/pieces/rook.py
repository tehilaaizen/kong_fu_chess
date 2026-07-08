from pieces.piece import Piece, sliding_path_is_clear


class Rook(Piece):
    letter = "R"

    def can_move(self, d_row, d_col):
        return d_row == 0 or d_col == 0

    def is_path_clear(self, start, end, board):
        return sliding_path_is_clear(start, end, board)
