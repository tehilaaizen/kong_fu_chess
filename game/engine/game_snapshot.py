from __future__ import annotations

from model.board import Board
from model.position import Position


class PiecePlacement:
    """A read-only description of one piece's kind, color and cell -
    everything a Renderer needs to draw a piece, without exposing the
    live model.Piece object it came from."""

    def __init__(self, kind: str, color: str, cell: Position) -> None:
        self.kind = kind
        self.color = color
        self.cell = cell


class GameSnapshot:
    """Read-only view model for the view layer: board dimensions plus
    where every piece currently sits. Renderer must only ever see this,
    never a live Board/Piece, so the view layer can't accidentally
    mutate game state."""

    def __init__(self, board_width: int, board_height: int, pieces: list[PiecePlacement]) -> None:
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces

    @staticmethod
    def from_board(board: Board) -> "GameSnapshot":
        """Build a snapshot from board's current state. The single place
        that converts live Piece objects into read-only placements - a
        future GameEngine.snapshot() calls this same method rather than
        duplicating the conversion."""
        pieces = [PiecePlacement(piece.kind, piece.color, piece.cell) for piece in board.pieces()]
        return GameSnapshot(board.width, board.height, pieces)
