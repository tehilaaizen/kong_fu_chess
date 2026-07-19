from engine.game_engine import (
    ArrivalObserver,
    GameOverObserver,
    JumpStartedObserver,
    MotionStartedObserver,
    RestStartedObserver,
)
from view.game_over.game_over_data import GameOverData


def test_a_new_game_is_not_over():
    assert GameOverData().is_over() is False


def test_on_game_over_marks_the_game_over():
    data = GameOverData()

    data.on_game_over()

    assert data.is_over() is True


def test_game_over_declares_only_the_game_over_hook():
    data = GameOverData()

    assert isinstance(data, GameOverObserver)
    assert not isinstance(data, ArrivalObserver)
    assert not isinstance(data, MotionStartedObserver)
    assert not isinstance(data, JumpStartedObserver)
    assert not isinstance(data, RestStartedObserver)
