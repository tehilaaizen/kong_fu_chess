from __future__ import annotations

from model.board import Board
from model.position import Position


class PiecePlacement:
    """A read-only description of one piece's identity, kind, color and
    cell - everything a Renderer needs to draw a piece at its current
    position, without exposing the live model.Piece object it came from.
    Animation state (idle/move/rest) is owned entirely by the view layer
    (PieceAnimator, driven by GameEngine's push notifications) - not part
    of this pull-based snapshot at all."""

    def __init__(self, id: int, kind: str, color: str, cell: Position) -> None:
        self.id = id
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
        """Build a snapshot from board's current state - the single place
        that converts live Piece objects into read-only placements."""
        pieces = [PiecePlacement(piece.id, piece.kind, piece.color, piece.cell) for piece in board.pieces()]
        return GameSnapshot(board.width, board.height, pieces)
