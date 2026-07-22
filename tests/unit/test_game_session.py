from application.game_session import (
    EMPTY_SOURCE,
    NOT_YOUR_PIECE,
    PIECE_MISMATCH,
    GameSession,
)
from engine.game_engine import GameEngine
from engine.game_snapshot import GameSnapshot
from messaging.application_events import (
    GameEndedEvent,
    GameMoveAppliedEvent,
    JumpStartedEvent,
    MotionStartedEvent,
    RestStartedEvent,
)
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser
from text_io.move_notation import MoveNotation

# White rook on a1 (row 7), lone black king on a8 (row 0).
BOARD_TEXT = "\n".join(
    [
        "bK . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        "wR . . . . . . .",
    ]
)
LONG_ENOUGH_MS = 100_000  # more than any single motion here takes to arrive


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event) -> None:
        self.events.append(event)


def _session(publisher):
    board = BoardParser.parse(BOARD_TEXT)
    engine = GameEngine(board, RuleEngine(), RealTimeArbiter(board))
    return GameSession("g1", board, engine, "alice", "bob", publisher)


def _move(text, session):
    return MoveNotation.parse(text, session.board_height)


def test_a_move_for_the_other_color_is_rejected():
    publisher = RecordingPublisher()
    session = _session(publisher)

    result = session.request_move(_move("WRa1a7", session), "b")

    assert result.is_accepted is False
    assert result.reason == NOT_YOUR_PIECE
    assert publisher.events == []


def test_a_move_whose_stated_kind_does_not_match_the_piece_is_rejected():
    session = _session(RecordingPublisher())

    result = session.request_move(_move("WQa1a7", session), "w")  # a1 holds R, not Q

    assert result.is_accepted is False
    assert result.reason == PIECE_MISMATCH


def test_a_move_from_an_empty_source_is_rejected():
    session = _session(RecordingPublisher())

    result = session.request_move(_move("WRb1b4", session), "w")  # b1 is empty

    assert result.is_accepted is False
    assert result.reason == EMPTY_SOURCE


def test_accepting_a_move_immediately_publishes_a_motion_started():
    publisher = RecordingPublisher()
    session = _session(publisher)

    accepted = session.request_move(_move("WRa1a7", session), "w")
    assert accepted.is_accepted is True

    started = [e for e in publisher.events if isinstance(e, MotionStartedEvent)]
    assert len(started) == 1
    assert started[0].game_id == "g1"
    assert started[0].color == "w"
    assert started[0].kind == "R"
    assert started[0].source == Position(7, 0)
    assert started[0].destination == Position(1, 0)
    assert started[0].duration_ms > 0
    # No arrival yet - only the motion-started, nothing has landed.
    assert [e for e in publisher.events if isinstance(e, GameMoveAppliedEvent)] == []


def test_a_legal_move_publishes_on_arrival_after_it_lands():
    publisher = RecordingPublisher()
    session = _session(publisher)

    session.request_move(_move("WRa1a7", session), "w")
    session.tick(LONG_ENOUGH_MS)

    applied = [e for e in publisher.events if isinstance(e, GameMoveAppliedEvent)]
    assert len(applied) == 1
    assert applied[0].sequence == 1
    assert applied[0].source == Position(7, 0)
    assert applied[0].destination == Position(1, 0)
    assert applied[0].color == "w"
    assert applied[0].kind == "R"
    assert applied[0].captured_kind is None


def test_the_motion_started_and_arrival_carry_the_same_piece_id():
    publisher = RecordingPublisher()
    session = _session(publisher)

    session.request_move(_move("WRa1a7", session), "w")
    session.tick(LONG_ENOUGH_MS)

    started = next(e for e in publisher.events if isinstance(e, MotionStartedEvent))
    applied = next(e for e in publisher.events if isinstance(e, GameMoveAppliedEvent))
    assert started.piece_id == applied.piece_id  # one stable id keys the client's animator


def test_an_arrival_publishes_a_rest_started_for_the_moved_piece():
    publisher = RecordingPublisher()
    session = _session(publisher)

    session.request_move(_move("WRa1a7", session), "w")
    session.tick(LONG_ENOUGH_MS)

    rests = [e for e in publisher.events if isinstance(e, RestStartedEvent)]
    assert len(rests) == 1
    assert rests[0].game_id == "g1"
    assert rests[0].color == "w"
    assert rests[0].kind == "R"
    assert rests[0].label == "long_rest"
    assert rests[0].duration_ms > 0


def test_accepting_a_jump_immediately_publishes_a_jump_started():
    publisher = RecordingPublisher()
    session = _session(publisher)

    session.request_jump(Position(7, 0), "w")

    started = [e for e in publisher.events if isinstance(e, JumpStartedEvent)]
    assert len(started) == 1
    assert started[0].game_id == "g1"
    assert started[0].color == "w"
    assert started[0].kind == "R"
    assert started[0].position == Position(7, 0)
    assert started[0].duration_ms > 0


def test_capturing_the_king_publishes_a_capture_and_game_ended():
    publisher = RecordingPublisher()
    session = _session(publisher)

    session.request_move(_move("WRa1a8", session), "w")  # rook slides up and takes a8 king
    session.tick(LONG_ENOUGH_MS)

    applied = [e for e in publisher.events if isinstance(e, GameMoveAppliedEvent)]
    ended = [e for e in publisher.events if isinstance(e, GameEndedEvent)]
    assert applied[0].captured_kind == "K"
    assert ended == [
        GameEndedEvent(game_id="g1", winner="w", white_user="alice", black_user="bob", reason="king_capture")
    ]


def test_jumping_your_own_piece_is_accepted():
    session = _session(RecordingPublisher())

    result = session.request_jump(Position(7, 0), "w")

    assert result.is_accepted is True


def test_jumping_an_empty_cell_is_rejected():
    session = _session(RecordingPublisher())

    result = session.request_jump(Position(4, 4), "w")

    assert result.is_accepted is False
    assert result.reason == EMPTY_SOURCE


def test_jumping_an_opponents_piece_is_rejected():
    session = _session(RecordingPublisher())

    result = session.request_jump(Position(7, 0), "b")  # a1 is a white rook

    assert result.is_accepted is False
    assert result.reason == NOT_YOUR_PIECE


def test_a_new_game_is_not_over():
    session = _session(RecordingPublisher())

    assert session.is_over() is False


def test_abandon_marks_the_game_over():
    session = _session(RecordingPublisher())

    session.abandon("b")

    assert session.is_over() is True


def test_abandon_publishes_a_game_ended_for_the_winner():
    publisher = RecordingPublisher()
    session = _session(publisher)

    session.abandon("b")  # White left, so Black wins by abandonment

    ended = [e for e in publisher.events if isinstance(e, GameEndedEvent)]
    assert ended == [
        GameEndedEvent(game_id="g1", winner="b", white_user="alice", black_user="bob", reason="abandoned")
    ]


def test_snapshot_reports_the_current_board():
    session = _session(RecordingPublisher())

    snapshot = session.snapshot()

    assert isinstance(snapshot, GameSnapshot)
    assert {(p.color, p.kind) for p in snapshot.pieces} == {("w", "R"), ("b", "K")}
