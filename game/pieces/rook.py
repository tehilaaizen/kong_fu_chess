from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules, sliding_destinations

ORTHOGONAL_DIRECTIONS: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Rook(PieceRules):
    letter = "R"

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every cell reachable by sliding horizontally/vertically from
        piece's cell until blocked (capture-eligible on the first enemy
        piece encountered)."""
        return sliding_destinations(board, piece.cell, piece.color, ORTHOGONAL_DIRECTIONS)
