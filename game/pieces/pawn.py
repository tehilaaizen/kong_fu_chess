from __future__ import annotations

from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules
from pieces.queen import Queen

FORWARD_DIRECTION: dict[str, int] = {"w": -1, "b": 1}


def _promotion_row(color: str, height: int) -> int:
    """The row a pawn of this color promotes on, given the board's height."""
    return height - 1 if FORWARD_DIRECTION[color] == 1 else 0


def _start_row(color: str, height: int) -> int:
    """The row this color's pawns begin on, given the board's height."""
    return 1 if FORWARD_DIRECTION[color] == 1 else height - 2


class Pawn(PieceRules):
    letter = "P"

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Pawn rules: one step forward onto an empty cell (plus a
        two-step start move from the pawn's home row, requiring both
        cells empty), or one step diagonally forward only as a capture.
        No en passant, no promotion here - promotion is a post-arrival
        effect, see on_piece_arrival."""
        direction = FORWARD_DIRECTION[piece.color]
        destinations: set[Position] = set()

        forward = Position(piece.cell.row + direction, piece.cell.col)
        if board.in_bounds(forward) and board.is_empty(forward):
            destinations.add(forward)

            if piece.cell.row == _start_row(piece.color, board.height):
                double_forward = Position(piece.cell.row + 2 * direction, piece.cell.col)
                if board.in_bounds(double_forward) and board.is_empty(double_forward):
                    destinations.add(double_forward)

        for d_col in (-1, 1):
            diagonal = Position(piece.cell.row + direction, piece.cell.col + d_col)
            if board.in_bounds(diagonal):
                occupant = board.piece_at(diagonal)
                if occupant is not None and occupant.color != piece.color:
                    destinations.add(diagonal)

        return destinations

    def on_piece_arrival(self, board: Board, piece: Piece) -> None:
        """A pawn reaching the last row promotes to a queen - mutates
        piece.kind in place (Board keys pieces by Position, not by kind,
        so this needs no cooperation from Board)."""
        if piece.cell.row == _promotion_row(piece.color, board.height):
            piece.kind = Queen.letter
