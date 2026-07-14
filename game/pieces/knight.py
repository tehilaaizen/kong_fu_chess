from __future__ import annotations

from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules, fixed_offset_destinations

L_SHAPE_OFFSETS: list[tuple[int, int]] = [
    (-2, -1), (-2, 1), (2, -1), (2, 1),
    (-1, -2), (-1, 2), (1, -2), (1, 2),
]


class Knight(PieceRules):
    letter = "N"

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every L-shaped cell reachable from piece's cell, ignoring
        blockers (a knight jumps over anything in between)."""
        return fixed_offset_destinations(board, piece.cell, piece.color, L_SHAPE_OFFSETS)
