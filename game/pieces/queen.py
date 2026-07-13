from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.bishop import Bishop
from pieces.piece import PieceRules, TokenBoard, sliding_path_is_clear
from pieces.rook import Rook


class Queen(PieceRules):
    letter = "Q"

    def __init__(self) -> None:
        """Composes Rook + Bishop rather than duplicating their shape logic."""
        self._rook = Rook()
        self._bishop = Bishop()

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A queen moves like a rook or like a bishop."""
        return self._rook.can_move(d_row, d_col, color) or self._bishop.can_move(d_row, d_col, color)

    def is_path_clear(self, start: tuple[int, int], end: tuple[int, int], board: TokenBoard, color: str) -> bool:
        return sliding_path_is_clear(start, end, board)

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """A queen's legal destinations are a rook's plus a bishop's from
        the same cell - reuses the two composed instances directly rather
        than re-deriving the combined direction set."""
        return self._rook.legal_destinations(board, piece) | self._bishop.legal_destinations(board, piece)
