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

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A knight moves in an L-shape: (1,2) or (2,1) deltas in either
        direction. is_path_clear keeps PieceRules' default (no blockers),
        since knights jump over other pieces."""
        return (abs(d_row), abs(d_col)) in {(1, 2), (2, 1)}

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every L-shaped cell reachable from piece's cell, ignoring
        blockers (a knight jumps over anything in between)."""
        return fixed_offset_destinations(board, piece.cell, piece.color, L_SHAPE_OFFSETS)
