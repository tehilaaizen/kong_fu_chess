from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.bishop import Bishop
from pieces.piece import PieceRules
from pieces.rook import Rook


class Queen(PieceRules):
    letter = "Q"

    def __init__(self) -> None:
        """Composes Rook + Bishop rather than duplicating their shape logic."""
        self._rook = Rook()
        self._bishop = Bishop()

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """A queen's legal destinations are a rook's plus a bishop's from
        the same cell - reuses the two composed instances directly rather
        than re-deriving the combined direction set."""
        return self._rook.legal_destinations(board, piece) | self._bishop.legal_destinations(board, piece)
