import pytest

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
from realtime.real_time_arbiter import ArrivalEvent, RealTimeArbiter, RestStartedEvent
from rules.rule_engine import ILLEGAL_PIECE_MOVE, OK, RuleEngine


def test_legal_destinations_delegates_to_the_rule_engine():
    board = Board(width=5, height=5)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(2, 2)))
    engine = GameEngine(board, RuleEngine(piece_rules_by_kind={"R": Rook()}), SpyRealTimeArbiter())

    destinations = engine.legal_destinations(Position(2, 2))

    assert Position(2, 4) in destinations
    assert Position(3, 3) not in destinations


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
        is_moving: bool = False,
        is_resting: bool = False,
        motion_duration_ms: int = 1000,
        jump_duration_ms: int = 1000,
        rest_starts_to_return: list | None = None,
    ) -> None:
        self._has_active_motion = has_active_motion
        self._events_to_return = events_to_return or []
        self._is_airborne = is_airborne
        self._is_moving = is_moving
        self._is_resting = is_resting
        self._motion_duration_ms = motion_duration_ms
        self._jump_duration_ms = jump_duration_ms
        self._rest_starts_to_return = rest_starts_to_return or []
        self.start_motion_calls: list[tuple] = []
        self.advance_time_calls: list[int] = []
        self.start_jump_calls: list[tuple] = []

    def has_active_motion(self) -> bool:
        return self._has_active_motion

    def start_motion(self, piece, source, destination) -> int:
        self.start_motion_calls.append((piece, source, destination))
        return self._motion_duration_ms

    def advance_time(self, ms: int) -> list:
        self.advance_time_calls.append(ms)
        return self._events_to_return

    def is_airborne(self, position) -> bool:
        return self._is_airborne

    def is_moving(self, piece) -> bool:
        return self._is_moving

    def start_jump(self, piece, cell) -> int:
        self.start_jump_calls.append((piece, cell))
        return self._jump_duration_ms

    def is_resting(self, piece) -> bool:
        return self._is_resting

    def take_rest_starts(self) -> list:
        return self._rest_starts_to_return


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


def test_two_different_pieces_can_move_at_the_same_time():
    board = Board(width=5, height=5)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    board.add_piece(Piece(id=2, color="w", kind="R", cell=Position(4, 4)))
    arbiter = RealTimeArbiter(board)
    engine = GameEngine(board, RuleEngine(piece_rules_by_kind={"R": Rook()}), arbiter)
    first_piece = board.piece_at(Position(0, 0))
    second_piece = board.piece_at(Position(4, 4))

    first = engine.request_move(Position(0, 0), Position(0, 3))
    second = engine.request_move(Position(4, 4), Position(4, 1))  # while the first is still travelling

    assert first.is_accepted is True
    assert second.is_accepted is True
    assert arbiter.is_moving(first_piece) is True
    assert arbiter.is_moving(second_piece) is True


def test_motion_in_progress_guard_runs_before_rule_engine_validation():
    board = Board(width=3, height=3)
    board.add_piece(Piece(id=1, color="w", kind="R", cell=Position(0, 0)))
    engine = GameEngine(board, SpyRuleEngine(), SpyRealTimeArbiter(is_moving=True))

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
    engine = GameEngine(board, RuleEngine(), SpyRealTimeArbiter(is_moving=True))

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
    """Records every notification it receives, split by event type."""

    def __init__(self) -> None:
        self.arrivals: list = []
        self.motions_started: list = []
        self.jumps_started: list = []
        self.rests_started: list = []
        self.game_overs: int = 0
        self.game_over_losers: list = []

    def on_arrival(self, event) -> None:
        self.arrivals.append(event)

    def on_motion_started(self, piece, source, destination, duration_ms) -> None:
        self.motions_started.append((piece, source, destination, duration_ms))

    def on_jump_started(self, piece, position, duration_ms) -> None:
        self.jumps_started.append((piece, position, duration_ms))

    def on_rest_started(self, piece, duration_ms, label) -> None:
        self.rests_started.append((piece, duration_ms, label))

    def on_game_over(self, loser_color) -> None:
        self.game_overs += 1
        self.game_over_losers.append(loser_color)


class ArrivalOnlyObserver:
    """Declares the arrival hook and nothing else - the shape ScoreData
    and MovesLogData have, proving a partial observer is never called for
    events it didn't subscribe to."""

    def __init__(self) -> None:
        self.arrivals: list = []

    def on_arrival(self, event) -> None:
        self.arrivals.append(event)


def test_an_observer_is_only_notified_of_events_it_declares_a_hook_for():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    board.add_piece(rook)
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)
    engine = GameEngine(board, RuleEngine(), SpyRealTimeArbiter(events_to_return=[event]))
    observer = ArrivalOnlyObserver()
    engine.add_observer(observer)

    # None of these may reach an observer without the matching hook.
    engine.request_move(Position(0, 0), Position(0, 1))
    engine.request_jump(Position(0, 0))
    engine.wait(1000)

    assert observer.arrivals == [event]


def test_adding_an_observer_with_no_hooks_at_all_is_rejected():
    board = Board(width=3, height=3)
    engine = GameEngine(board, RuleEngine(), SpyRealTimeArbiter())

    class NotAnObserver:
        pass

    with pytest.raises(ValueError):
        engine.add_observer(NotAnObserver())


def test_wait_notifies_a_registered_observer_on_arrival():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.wait(1000)

    assert observer.arrivals == [event]


def test_wait_notifies_every_registered_observer_on_arrival():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)
    first, second = SpyObserver(), SpyObserver()
    engine.add_observer(first)
    engine.add_observer(second)

    engine.wait(1000)

    assert len(first.arrivals) == 1
    assert len(second.arrivals) == 1


def test_wait_notifies_on_game_over_when_an_arrival_captures_the_king():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    king = Piece(id=2, color="b", kind="K", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=king)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.wait(1000)

    assert observer.game_overs == 1
    assert observer.game_over_losers == ["b"]  # the captured king was black


def test_wait_does_not_notify_on_game_over_when_no_king_is_captured():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)
    real_time_arbiter = SpyRealTimeArbiter(events_to_return=[event])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.wait(1000)

    assert observer.game_overs == 0


def test_request_move_notifies_on_motion_started_with_the_real_arbiters_duration():
    engine, _, _ = _engine()
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.request_move(Position(2, 2), Position(2, 4))

    assert len(observer.motions_started) == 1
    piece, source, destination, duration_ms = observer.motions_started[0]
    assert (source, destination) == (Position(2, 2), Position(2, 4))
    assert duration_ms == 2000  # 2 cells, 1000ms each


def test_request_move_does_not_notify_on_an_illegal_move():
    engine, _, _ = _engine()
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.request_move(Position(2, 2), Position(3, 3))

    assert observer.motions_started == []


def test_request_jump_notifies_on_jump_started():
    engine, _, _ = _engine()
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.request_jump(Position(2, 2))

    assert len(observer.jumps_started) == 1
    piece, position, duration_ms = observer.jumps_started[0]
    assert position == Position(2, 2)
    assert duration_ms == 1000


def test_request_jump_does_not_notify_on_an_empty_cell():
    engine, _, _ = _engine()
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.request_jump(Position(0, 0))

    assert observer.jumps_started == []


def test_snapshot_reports_every_pieces_identity_kind_color_and_cell():
    engine, board, _ = _engine()

    snapshot = engine.snapshot()

    assert snapshot.pieces[0].kind == "R"
    assert snapshot.pieces[0].color == "w"
    assert snapshot.pieces[0].cell == Position(2, 2)


def test_wait_notifies_on_rest_started_for_each_rest_the_arbiter_reports():
    board = Board(width=3, height=3)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    rest_start = RestStartedEvent(piece=rook, duration_ms=5000, label="long_rest")
    real_time_arbiter = SpyRealTimeArbiter(rest_starts_to_return=[rest_start])
    engine = GameEngine(board, RuleEngine(), real_time_arbiter)
    observer = SpyObserver()
    engine.add_observer(observer)

    engine.wait(1000)

    assert observer.rests_started == [(rook, 5000, "long_rest")]
