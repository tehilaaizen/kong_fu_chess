from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules, sliding_destinations

DIAGONAL_DIRECTIONS: list[tuple[int, int]] = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


class Bishop(PieceRules):
    letter = "B"

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every cell reachable by sliding diagonally from piece's cell
        until blocked (capture-eligible on the first enemy piece
        encountered)."""
        return sliding_destinations(board, piece.cell, piece.color, DIAGONAL_DIRECTIONS)
