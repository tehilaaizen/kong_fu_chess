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

FIXED_TIME = "12:34:56"


def _data(max_lines: int = 10) -> MovesLogData:
    return MovesLogData(max_lines=max_lines, now=lambda: FIXED_TIME)


def _arrival(color: str, src: tuple[int, int], dst: tuple[int, int], captured: Piece | None = None) -> ArrivalEvent:
    piece = Piece(id=1, color=color, kind="R", cell=Position(*src))
    return ArrivalEvent(piece=piece, source=Position(*src), destination=Position(*dst), captured_piece=captured)


def test_starts_with_no_lines_for_either_color():
    data = _data()

    assert data.lines_for("w") == []
    assert data.lines_for("b") == []


def test_on_arrival_logs_a_timestamped_line_under_the_moving_color():
    data = _data()

    data.on_arrival(_arrival("w", (0, 0), (0, 1)))

    assert data.lines_for("w") == [f"{FIXED_TIME} R (0,0)->(0,1)"]
    assert data.lines_for("b") == []


def test_on_arrival_with_a_capture_notes_it_in_the_line():
    data = _data()
    pawn = Piece(id=2, color="b", kind="P", cell=Position(0, 1))

    data.on_arrival(_arrival("w", (0, 0), (0, 1), captured=pawn))

    assert data.lines_for("w") == [f"{FIXED_TIME} R (0,0)->(0,1) xP"]


def test_each_color_keeps_its_own_log():
    data = _data()

    data.on_arrival(_arrival("w", (0, 0), (0, 1)))
    data.on_arrival(_arrival("b", (7, 0), (7, 1)))

    assert data.lines_for("w") == [f"{FIXED_TIME} R (0,0)->(0,1)"]
    assert data.lines_for("b") == [f"{FIXED_TIME} R (7,0)->(7,1)"]


def test_most_recent_line_comes_first_within_a_color():
    data = _data()

    data.on_arrival(_arrival("w", (0, 0), (0, 1)))
    data.on_arrival(_arrival("w", (0, 1), (0, 2)))

    lines = data.lines_for("w")
    assert lines[0] == f"{FIXED_TIME} R (0,1)->(0,2)"
    assert lines[1] == f"{FIXED_TIME} R (0,0)->(0,1)"


def test_log_is_capped_at_max_lines_per_color():
    data = _data(max_lines=2)

    for col in range(3):
        data.on_arrival(_arrival("w", (0, col), (0, col + 1)))

    assert len(data.lines_for("w")) == 2


def test_the_log_declares_only_the_arrival_hook():
    data = _data()

    assert isinstance(data, ArrivalObserver)
    assert not isinstance(data, MotionStartedObserver)
    assert not isinstance(data, JumpStartedObserver)
    assert not isinstance(data, RestStartedObserver)
    assert not isinstance(data, GameOverObserver)
