from pieces.piece import Piece, sliding_path_is_clear


class Bishop(Piece):
    letter = "B"

    def can_move(self, d_row, d_col):
        return d_row == d_col

    def is_path_clear(self, start, end, board):
        return sliding_path_is_clear(start, end, board)
