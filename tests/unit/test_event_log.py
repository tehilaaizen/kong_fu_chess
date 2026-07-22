from messaging.application_events import (
    GameEndedEvent,
    GameMoveAppliedEvent,
    GameStartedEvent,
    JumpStartedEvent,
    MotionStartedEvent,
    RestStartedEvent,
)
from model.position import Position
from server.event_log import EventLog


def _log():
    lines: list[str] = []
    return EventLog(lines.append), lines


def test_a_game_start_is_logged_with_both_players():
    log, lines = _log()

    log.handle(GameStartedEvent(game_id="g1", white_user="alice", black_user="bob"))

    assert lines == ["game g1 started - white=alice black=bob"]


def test_a_motion_start_is_logged_with_the_piece_and_travel():
    log, lines = _log()

    log.handle(
        MotionStartedEvent(
            game_id="g1", piece_id=7, color="w", kind="P", source=Position(6, 4), destination=Position(4, 4),
            duration_ms=500,
        )
    )

    assert lines == ["game g1: wP#7 move (6,4)->(4,4) (500ms)"]


def test_a_jump_start_is_logged_with_its_cell():
    log, lines = _log()

    log.handle(JumpStartedEvent(game_id="g1", piece_id=3, color="b", kind="N", position=Position(0, 1), duration_ms=300))

    assert lines == ["game g1: bN#3 jump @(0,1) (300ms)"]


def test_an_arrival_without_a_capture_is_logged():
    log, lines = _log()

    log.handle(
        GameMoveAppliedEvent(
            game_id="g1", sequence=1, piece_id=7, source=Position(6, 4), destination=Position(4, 4),
            color="w", kind="P", captured_kind=None,
        )
    )

    assert lines == ["game g1 #1: wP arrived (6,4)->(4,4)"]


def test_an_arrival_with_a_capture_names_the_captured_kind():
    log, lines = _log()

    log.handle(
        GameMoveAppliedEvent(
            game_id="g1", sequence=2, piece_id=7, source=Position(7, 0), destination=Position(0, 0),
            color="w", kind="R", captured_kind="K",
        )
    )

    assert lines == ["game g1 #2: wR arrived (7,0)->(0,0) captured K"]


def test_a_game_end_is_logged_with_the_winner():
    log, lines = _log()

    log.handle(GameEndedEvent(game_id="g1", winner="w"))

    assert lines == ["game g1 ended - winner=w"]


def test_rest_and_unknown_events_are_not_logged():
    log, lines = _log()

    log.handle(RestStartedEvent(game_id="g1", piece_id=7, color="w", kind="P", duration_ms=5000, label="long_rest"))
    log.handle(object())

    assert lines == []
