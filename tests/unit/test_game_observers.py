import pytest

from engine.game_observers import ObserverHub
from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent


class SpyObserver:
    """Records every hook it is called on - implements all five, so the
    hub subscribes it to everything."""

    def __init__(self) -> None:
        self.arrivals: list = []
        self.motions: list = []
        self.jumps: list = []
        self.rests: list = []
        self.game_overs: list = []

    def on_arrival(self, event) -> None:
        self.arrivals.append(event)

    def on_motion_started(self, piece, source, destination, duration_ms) -> None:
        self.motions.append((piece, source, destination, duration_ms))

    def on_jump_started(self, piece, position, duration_ms) -> None:
        self.jumps.append((piece, position, duration_ms))

    def on_rest_started(self, piece, duration_ms, label) -> None:
        self.rests.append((piece, duration_ms, label))

    def on_game_over(self, loser_color) -> None:
        self.game_overs.append(loser_color)


class ArrivalOnlyObserver:
    def __init__(self) -> None:
        self.arrivals: list = []

    def on_arrival(self, event) -> None:
        self.arrivals.append(event)


def _piece() -> Piece:
    return Piece(id=1, color="w", kind="R", cell=Position(7, 0))


def test_an_observer_with_no_recognized_hook_is_rejected():
    class NotAnObserver:
        pass

    with pytest.raises(ValueError):
        ObserverHub().add_observer(NotAnObserver())


def test_an_observer_is_only_notified_of_events_it_declares_a_hook_for():
    hub = ObserverHub()
    observer = ArrivalOnlyObserver()
    hub.add_observer(observer)
    event = ArrivalEvent(_piece(), Position(7, 0), Position(1, 0), captured_piece=None)

    hub.notify_motion_started(_piece(), Position(7, 0), Position(1, 0), 500)
    hub.notify_game_over("b")
    hub.notify_arrival(event)

    assert observer.arrivals == [event]


def test_every_notification_reaches_every_subscribed_observer():
    hub = ObserverHub()
    first, second = SpyObserver(), SpyObserver()
    hub.add_observer(first)
    hub.add_observer(second)
    piece = _piece()

    hub.notify_motion_started(piece, Position(7, 0), Position(1, 0), 500)
    hub.notify_jump_started(piece, Position(7, 0), 300)
    hub.notify_rest_started(piece, 5000, "long_rest")
    hub.notify_arrival(ArrivalEvent(piece, Position(7, 0), Position(1, 0), None))
    hub.notify_game_over("b")

    for observer in (first, second):
        assert observer.motions == [(piece, Position(7, 0), Position(1, 0), 500)]
        assert observer.jumps == [(piece, Position(7, 0), 300)]
        assert observer.rests == [(piece, 5000, "long_rest")]
        assert len(observer.arrivals) == 1
        assert observer.game_overs == ["b"]
