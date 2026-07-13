from pieces import PIECE_TYPES

OK = "ok"
OUTSIDE_BOARD = "outside_board"
EMPTY_SOURCE = "empty_source"
FRIENDLY_DESTINATION = "friendly_destination"
ILLEGAL_PIECE_MOVE = "illegal_piece_move"


class MoveValidation:
    def __init__(self, is_valid, reason):
        self.is_valid = is_valid
        self.reason = reason


class RuleEngine:
    """Read-only legality validation for a requested move. Never mutates
    Board, starts motions, or knows about game-over - GameEngine owns
    those application-level concerns."""

    def __init__(self, piece_rules_by_kind=PIECE_TYPES):
        self._piece_rules_by_kind = piece_rules_by_kind

    def validate_move(self, board, source, destination):
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
