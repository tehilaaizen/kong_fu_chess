from engine.game_engine import (
    ALREADY_AIRBORNE,
    EMPTY_CELL,
    GAME_OVER,
    MOTION_IN_PROGRESS,
    PIECE_RESTING,
    GameEngine,
)
from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.rook import Rook
from realtime.real_time_arbiter import ArrivalEvent, RealTimeArbiter
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
    has_active_motion() and advance_time()'s return value - used to prove
    GameEngine delegates to it correctly without touching Board itself."""

    def __init__(
        self,
        has_active_motion: bool = False,
        events_to_return: list | None = None,
        is_airborne: bool = False,
        is_resting: bool = False,
    ) -> None:
        self._has_active_motion = has_active_motion
        self._events_to_return = events_to_return or []
        self._is_airborne = is_airborne
        self._is_resting = is_resting
        self.start_motion_calls: list[tuple] = []
        self.advance_time_calls: list[int] = []
        self.start_jump_calls: list[tuple] = []

    def has_active_motion(self) -> bool:
        return self._has_active_motion

    def start_motion(self, piece, source, destination) -> None:
        self.start_motion_calls.append((piece, source, destination))

    def advance_time(self, ms: int) -> list:
        self.advance_time_calls.append(ms)
        return self._events_to_return

    def is_airborne(self, position) -> bool:
        return self._is_airborne

    def start_jump(self, piece, cell) -> None:
        self.start_jump_calls.append((piece, cell))

    def is_resting(self, piece) -> bool:
        return self._is_resting


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
    engine, board, real_time_arbiter = _engine()

    result = engine.request_move(Position(2, 2), Position(3, 3))

    assert result.is_accepted is False
    assert result.reason == ILLEGAL_PIECE_MOVE
    assert board.piece_at(Position(2, 2)) is not None
    assert real_time_arbiter.has_active_motion() is False


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


def test_rejects_a_move_from_a_resting_piece():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, RuleEngine(), SpyRealTimeArbiter(is_resting=True))

    result = engine.request_move(Position(0, 0), Position(0, 1))

    assert result.is_accepted is False
    assert result.reason == PIECE_RESTING


def test_piece_resting_guard_runs_before_rule_engine_validation():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, SpyRuleEngine(), SpyRealTimeArbiter(is_resting=True))

    result = engine.request_move(Position(0, 0), Position(0, 1))

    assert result.reason == PIECE_RESTING


def test_wait_delegates_to_real_time_arbiter_without_touching_board_directly():
    board = Board(width=3, height=3)
    real_time_arbiter = SpyRealTimeArbiter()
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)

    engine.wait(500)

    assert real_time_arbiter.advance_time_calls == [500]


def test_capturing_the_king_ends_the_game():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    king = Piece(id=2, color="b", kind="K", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=king)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)

    engine.wait(1000)

    assert engine.is_game_over() is True


def test_capturing_a_non_king_does_not_end_the_game():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    pawn = Piece(id=2, color="b", kind="P", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=pawn)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)

    engine.wait(1000)

    assert engine.is_game_over() is False


def test_a_move_onto_an_empty_cell_does_not_end_the_game():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)

    engine.wait(1000)

    assert engine.is_game_over() is False


def test_request_jump_accepts_and_starts_a_jump_on_an_occupied_cell():
    engine, _, real_time_arbiter = _engine()

    result = engine.request_jump(Position(2, 2))

    assert result.is_accepted is True
    assert result.reason == OK
    assert real_time_arbiter.is_airborne(Position(2, 2)) is True


def test_request_jump_rejects_an_empty_cell():
    engine, _, _ = _engine()

    result = engine.request_jump(Position(0, 0))

    assert result.is_accepted is False
    assert result.reason == EMPTY_CELL


def test_request_jump_rejects_an_already_airborne_cell():
    engine, _, _ = _engine()
    engine.request_jump(Position(2, 2))

    result = engine.request_jump(Position(2, 2))

    assert result.is_accepted is False
    assert result.reason == ALREADY_AIRBORNE


def test_request_jump_rejects_when_the_game_is_over():
    engine, _, _ = _engine()
    engine.mark_game_over()

    result = engine.request_jump(Position(2, 2))

    assert result.is_accepted is False
    assert result.reason == GAME_OVER


def test_request_jump_rejects_while_a_motion_is_active():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, RuleEngine(), SpyRealTimeArbiter(has_active_motion=True))

    result = engine.request_jump(Position(0, 0))

    assert result.is_accepted is False
    assert result.reason == MOTION_IN_PROGRESS


def test_request_jump_never_consults_rule_engine():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, SpyRuleEngine(), SpyRealTimeArbiter())

    result = engine.request_jump(Position(0, 0))

    assert result.is_accepted is True


def test_request_jump_rejects_a_resting_piece():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, RuleEngine(), SpyRealTimeArbiter(is_resting=True))

    result = engine.request_jump(Position(0, 0))

    assert result.is_accepted is False
    assert result.reason == PIECE_RESTING


class SpyObserver:
    """Records every snapshot it's notified with."""

    def __init__(self) -> None:
        self.snapshots: list = []

    def on_snapshot(self, snapshot) -> None:
        self.snapshots.append(snapshot)


def test_wait_notifies_a_registered_observer_with_a_snapshot():
    engine, board, _ = _engine()
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.wait(0)

    assert len(observer.snapshots) == 1
    assert observer.snapshots[0].pieces[0].kind == "R"


def test_wait_notifies_every_registered_observer():
    engine, _, _ = _engine()
    first, second = SpyObserver(), SpyObserver()
    engine.add_observer(first)
    engine.add_observer(second)

    engine.wait(0)

    assert len(first.snapshots) == 1
    assert len(second.snapshots) == 1


def test_snapshot_reports_move_state_while_a_motion_is_active():
    engine, board, _ = _engine()

    engine.request_move(Position(2, 2), Position(2, 4))
    snapshot = engine.snapshot()

    assert snapshot.pieces[0].state == "move"


def test_snapshot_reports_long_rest_after_a_move_arrives():
    engine, board, _ = _engine()

    engine.request_move(Position(2, 2), Position(2, 4))
    engine.wait(2000)
    snapshot = engine.snapshot()

    assert snapshot.pieces[0].state == "long_rest"
