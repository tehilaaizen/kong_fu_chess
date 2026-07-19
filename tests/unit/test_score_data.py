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
from view.hud.score.score_data import ScoreData


def test_score_starts_at_zero_for_both_colors():
    data = ScoreData()

    assert data.score_for("w") == 0
    assert data.score_for("b") == 0


def test_on_arrival_with_no_capture_does_not_change_score():
    data = ScoreData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=None)

    data.on_arrival(event)

    assert data.score_for("w") == 0


def test_on_arrival_credits_the_capturing_colors_score():
    data = ScoreData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    pawn = Piece(id=2, color="b", kind="P", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=pawn)

    data.on_arrival(event)

    assert data.score_for("w") == 1
    assert data.score_for("b") == 0


def test_score_uses_standard_point_values():
    data = ScoreData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    queen = Piece(id=2, color="b", kind="Q", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=queen)

    data.on_arrival(event)

    assert data.score_for("w") == 9


def test_score_accumulates_across_multiple_captures():
    data = ScoreData()
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    pawn = Piece(id=2, color="b", kind="P", cell=Position(0, 1))
    knight = Piece(id=3, color="b", kind="N", cell=Position(0, 2))

    data.on_arrival(ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=pawn))
    data.on_arrival(ArrivalEvent(piece=rook, source=Position(0, 1), destination=Position(0, 2), captured_piece=knight))

    assert data.score_for("w") == 4


def test_a_custom_point_value_table_can_be_injected():
    data = ScoreData(point_value_by_kind={"P": 100})
    rook = Piece(id=1, color="w", kind="R", cell=Position(0, 0))
    pawn = Piece(id=2, color="b", kind="P", cell=Position(0, 1))
    event = ArrivalEvent(piece=rook, source=Position(0, 0), destination=Position(0, 1), captured_piece=pawn)

    data.on_arrival(event)

    assert data.score_for("w") == 100


def test_scoring_declares_only_the_arrival_hook():
    data = ScoreData()

    assert isinstance(data, ArrivalObserver)
    assert not isinstance(data, MotionStartedObserver)
    assert not isinstance(data, JumpStartedObserver)
    assert not isinstance(data, RestStartedObserver)
    assert not isinstance(data, GameOverObserver)
