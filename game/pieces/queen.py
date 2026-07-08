from pieces.bishop import Bishop
from pieces.piece import Piece
from pieces.rook import Rook


class Queen(Piece):
    letter = "Q"

    def __init__(self):
        self._rook = Rook()
        self._bishop = Bishop()

    def can_move(self, d_row, d_col):
        return self._rook.can_move(d_row, d_col) or self._bishop.can_move(d_row, d_col)
