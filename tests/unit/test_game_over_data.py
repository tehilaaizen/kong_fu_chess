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

    data.on_game_over("b")

    assert data.is_over() is True


def test_winner_label_is_none_before_the_game_ends():
    assert GameOverData({"w": "alice", "b": "bob"}).winner_label() is None


def test_winner_label_names_the_winning_color():
    data = GameOverData({"w": "alice", "b": "bob"})

    data.on_game_over("b")  # Black's king fell, so White won

    assert data.winner_label() == "alice"


def test_winner_label_falls_back_to_the_generic_color_name():
    data = GameOverData()

    data.on_game_over("w")  # White lost, so Black won

    assert data.winner_label() == "Black"


def test_game_over_declares_only_the_game_over_hook():
    data = GameOverData()

    assert isinstance(data, GameOverObserver)
    assert not isinstance(data, ArrivalObserver)
    assert not isinstance(data, MotionStartedObserver)
    assert not isinstance(data, JumpStartedObserver)
    assert not isinstance(data, RestStartedObserver)
