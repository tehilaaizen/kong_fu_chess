from __future__ import annotations

from model.board import Board
from model.position import Position
from pieces import PIECE_TYPES
from pieces.piece import PieceRules

OK = "ok"
OUTSIDE_BOARD = "outside_board"
EMPTY_SOURCE = "empty_source"
FRIENDLY_DESTINATION = "friendly_destination"
ILLEGAL_PIECE_MOVE = "illegal_piece_move"


class MoveValidation:
    """Result of RuleEngine.validate_move: whether the move is legal, and
    a stable, machine-readable reason ("ok" when valid)."""

    def __init__(self, is_valid: bool, reason: str) -> None:
        self.is_valid = is_valid
        self.reason = reason


class RuleEngine:
    """Read-only legality validation for a requested move. Never mutates
    Board, starts motions, or knows about game-over - GameEngine owns
    those application-level concerns."""

    def __init__(self, piece_rules_by_kind: dict[str, PieceRules] = PIECE_TYPES) -> None:
        """piece_rules_by_kind maps a piece kind letter (e.g. "R") to the
        PieceRules strategy that knows its legal destinations. Defaults to
        the project-wide PIECE_TYPES registry; tests may inject a smaller
        mapping."""
        self._piece_rules_by_kind = piece_rules_by_kind

    def validate_move(self, board: Board, source: Position, destination: Position) -> MoveValidation:
        """Check whether moving the piece at source to destination is
        legal on board right now: both cells must be in bounds, source
        must hold a piece, destination must not hold a friendly piece, and
        destination must be one of that piece's legal destinations."""
        if not board.in_bounds(source) or not board.in_bounds(destination):
            return MoveValidation(False, OUTSIDE_BOARD)

        piece = board.piece_at(source)
        if piece is None:
            return MoveValidation(False, EMPTY_SOURCE)

        target = board.piece_at(destination)
        if target is not None and target.color == piece.color:
            return MoveValidation(False, FRIENDLY_DESTINATION)

        piece_rules = self._piece_rules_by_kind[piece.kind]
        if destination not in piece_rules.legal_destinations(board, piece):
            return MoveValidation(False, ILLEGAL_PIECE_MOVE)

        return MoveValidation(True, OK)
