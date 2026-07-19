from engine.game_engine import (
    ArrivalObserver,
    GameOverObserver,
    JumpStartedObserver,
    MotionStartedObserver,
    RestStartedObserver,
)
from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent
from view.hud.moves_log.moves_log_data import MovesLogData


def test_starts_with_no_lines():
    data = MovesLogData()

    assert data.lines() == []


def test_on_arrival_logs_a_line():
    data = MovesLogData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)

    data.on_arrival(event)

    assert data.lines() == ["wR (0,0)->(0,1)"]


def test_on_arrival_with_a_capture_notes_it_in_the_line():
    data = MovesLogData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    pawn = Piece(id=2, color="b", kind="P", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=pawn)

    data.on_arrival(event)

    assert data.lines() == ["wR (0,0)->(0,1) xP"]


def test_most_recent_line_comes_first():
    data = MovesLogData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    data.on_arrival(ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None))
    data.on_arrival(ArrivalEvent(piece=rook, source=Position(0, 1), destination=Position(0, 2), captured_piece=None))

    lines = data.lines()

    assert lines[0] == "wR (0,1)->(0,2)"
    assert lines[1] == "wR (0,0)->(0,1)"


def test_log_is_capped_at_max_lines():
    data = MovesLogData(max_lines=2)
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    for col in range(3):
        event = ArrivalEvent(piece=rook, source=Position(0, col), destination=Position(0, col + 1), captured_piece=None)
        data.on_arrival(event)

    assert len(data.lines()) == 2


def test_the_log_declares_only_the_arrival_hook():
    data = MovesLogData()

    assert isinstance(data, ArrivalObserver)
    assert not isinstance(data, MotionStartedObserver)
    assert not isinstance(data, JumpStartedObserver)
    assert not isinstance(data, RestStartedObserver)
    assert not isinstance(data, GameOverObserver)
