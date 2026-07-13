from engine.game_engine import GAME_OVER, GameEngine
from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.rook import Rook
from rules.rule_engine import ILLEGAL_PIECE_MOVE, OK, RuleEngine


class SpyRuleEngine:
    """Test double that records whether it was ever asked to validate -
    used to prove the game-over guard short-circuits before RuleEngine."""

    def __init__(self):
        self.called = False

    def validate_move(self, board, source, destination):
        self.called = True
        raise AssertionError("RuleEngine.validate_move must not run after game_over")


def _engine():
    board = Board(width=5, height=5)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(2, 2)))
    rule_engine = RuleEngine(piece_rules_by_kind={"R": Rook()})
    return GameEngine(board, rule_engine), board


def test_accepts_a_legal_move_without_mutating_the_board():
    engine, board = _engine()

    result = engine.request_move(Position(2, 2), Position(2, 4))

    assert result.is_accepted is True
    assert result.reason == OK
    assert board.piece_at(Position(2, 2)) is not None
    assert board.is_empty(Position(2, 4))


def test_rejects_an_illegal_move_with_the_rule_engines_reason():
    engine, board = _engine()

    result = engine.request_move(Position(2, 2), Position(3, 3))

    assert result.is_accepted is False
    assert result.reason == ILLEGAL_PIECE_MOVE
    assert board.piece_at(Position(2, 2)) is not None


def test_rejects_every_move_once_the_game_is_over():
    engine, _ = _engine()
    engine.mark_game_over()

    result = engine.request_move(Position(2, 2), Position(2, 4))

    assert result.is_accepted is False
    assert result.reason == GAME_OVER


def test_game_over_guard_runs_before_rule_engine_validation():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, SpyRuleEngine())
    engine.mark_game_over()

    result = engine.request_move(Position(0, 0), Position(0, 1))

    assert result.reason == GAME_OVER
