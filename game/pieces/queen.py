from pieces.bishop import Bishop
from pieces.piece import Piece, sliding_path_is_clear
from pieces.rook import Rook


class Queen(Piece):
    letter = "Q"

    def __init__(self):
        self._rook = Rook()
        self._bishop = Bishop()

    def can_move(self, d_row, d_col, color):
        return self._rook.can_move(d_row, d_col, color) or self._bishop.can_move(d_row, d_col, color)

    def is_path_clear(self, start, end, board):
        return sliding_path_is_clear(start, end, board)
