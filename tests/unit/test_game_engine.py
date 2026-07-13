from engine.game_engine import GAME_OVER, MOTION_IN_PROGRESS, GameEngine
from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.rook import Rook
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import ILLEGAL_PIECE_MOVE, OK, RuleEngine


class SpyRuleEngine:
    """Test double that records whether it was ever asked to validate -
    used to prove a guard short-circuits before RuleEngine runs."""

    def __init__(self) -> None:
        self.called = False

    def validate_move(self, board, source, destination):
        self.called = True
        raise AssertionError("RuleEngine.validate_move must not run past an application-level guard")


class SpyRealTimeArbiter:
    """Test double recording calls, and letting tests force
    has_active_motion() - used to prove GameEngine delegates to it
    correctly without touching Board itself."""

    def __init__(self, has_active_motion: bool = False) -> None:
        self._has_active_motion = has_active_motion
        self.start_motion_calls: list[tuple] = []
        self.advance_time_calls: list[int] = []

    def has_active_motion(self) -> bool:
        return self._has_active_motion

    def start_motion(self, piece, source, destination) -> None:
        self.start_motion_calls.append((piece, source, destination))

    def advance_time(self, ms: int) -> list:
        self.advance_time_calls.append(ms)
        return []


def _engine():
    board = Board(width=5, height=5)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(2, 2)))
    rule_engine = RuleEngine(piece_rules_by_kind={"R": Rook()})
    real_time_arbiter = RealTimeArbiter(board)
    return GameEngine(board, rule_engine, real_time_arbiter), board, real_time_arbiter


def test_accepts_a_legal_move_and_starts_a_motion_without_moving_the_piece_yet():
    engine, board, real_time_arbiter = _engine()

    result = engine.request_move(Position(2, 2), Position(2, 4))

    assert result.is_accepted is True
    assert result.reason == OK
    assert board.piece_at(Position(2, 2)) is not None
    assert board.is_empty(Position(2, 4))
    assert real_time_arbiter.has_active_motion() is True


def test_rejects_an_illegal_move_with_the_rule_engines_reason():
    engine, board, _ = _engine()

    result = engine.request_move(Position(2, 2), Position(3, 3))

    assert result.is_accepted is False
    assert result.reason == ILLEGAL_PIECE_MOVE
    assert board.piece_at(Position(2, 2)) is not None


def test_rejects_every_move_once_the_game_is_over():
    engine, _, _ = _engine()
    engine.mark_game_over()

    result = engine.request_move(Position(2, 2), Position(2, 4))

    assert result.is_accepted is False
    assert result.reason == GAME_OVER


def test_game_over_guard_runs_before_rule_engine_validation():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, SpyRuleEngine(), RealTimeArbiter(board))
    engine.mark_game_over()

    result = engine.request_move(Position(0, 0), Position(0, 1))

    assert result.reason == GAME_OVER


def test_rejects_a_move_while_another_motion_is_active():
    engine, board, _ = _engine()
    engine.request_move(Position(2, 2), Position(2, 4))

    result = engine.request_move(Position(2, 2), Position(3, 2))

    assert result.is_accepted is False
    assert result.reason == MOTION_IN_PROGRESS


def test_motion_in_progress_guard_runs_before_rule_engine_validation():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, SpyRuleEngine(), SpyRealTimeArbiter(has_active_motion=True))

    result = engine.request_move(Position(0, 0), Position(0, 1))

    assert result.reason == MOTION_IN_PROGRESS


def test_wait_delegates_to_real_time_arbiter_without_touching_board_directly():
    board = Board(width=3, height=3)
    real_time_arbiter = SpyRealTimeArbiter()
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)

    engine.wait(500)

    assert real_time_arbiter.advance_time_calls == [500]
