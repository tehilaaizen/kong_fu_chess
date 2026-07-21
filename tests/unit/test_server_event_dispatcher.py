from client.server_event_dispatcher import ServerEventDispatcher
from model.position import Position


class SpyObserver:
    """Implements all five hooks, so it is subscribed to everything the
    dispatcher reconstructs."""

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


def _dispatcher():
    dispatcher = ServerEventDispatcher()
    observer = SpyObserver()
    dispatcher.add_observer(observer)
    return dispatcher, observer


def test_motion_started_is_replayed_with_the_piece_id_source_and_destination():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch(
        "motion_started",
        {
            "piece": {"id": 7, "color": "w", "kind": "R"},
            "source": {"row": 7, "col": 0},
            "destination": {"row": 1, "col": 0},
            "duration_ms": 500,
        },
    )

    piece, source, destination, duration = observer.motions[0]
    assert piece.id == 7 and piece.color == "w" and piece.kind == "R"
    assert source == Position(7, 0)
    assert destination == Position(1, 0)
    assert duration == 500


def test_jump_started_is_replayed_at_its_cell():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch(
        "jump_started",
        {"piece": {"id": 3, "color": "b", "kind": "N"}, "cell": {"row": 0, "col": 1}, "duration_ms": 300},
    )

    piece, position, duration = observer.jumps[0]
    assert piece.id == 3
    assert position == Position(0, 1)
    assert duration == 300


def test_rest_started_is_replayed_with_duration_and_label():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch(
        "rest_started",
        {"piece": {"id": 3, "color": "w", "kind": "P"}, "duration_ms": 5000, "label": "long_rest"},
    )

    piece, duration, label = observer.rests[0]
    assert piece.id == 3
    assert duration == 5000
    assert label == "long_rest"


def test_arrival_without_a_capture_reconstructs_an_arrival_event():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch(
        "arrival",
        {
            "piece": {"id": 7, "color": "w", "kind": "R"},
            "source": {"row": 7, "col": 0},
            "destination": {"row": 1, "col": 0},
            "captured_kind": None,
        },
    )

    event = observer.arrivals[0]
    assert event.piece.id == 7
    assert event.source == Position(7, 0)
    assert event.destination == Position(1, 0)
    assert event.captured_piece is None


def test_arrival_with_a_capture_reconstructs_the_captured_piece_as_the_opponent():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch(
        "arrival",
        {
            "piece": {"id": 7, "color": "w", "kind": "R"},
            "source": {"row": 7, "col": 0},
            "destination": {"row": 0, "col": 0},
            "captured_kind": "K",
        },
    )

    captured = observer.arrivals[0].captured_piece
    assert captured is not None
    assert captured.kind == "K"
    assert captured.color == "b"  # the mover is white, so the captured piece is black


def test_game_over_translates_the_winner_into_the_losers_color():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch("game_over", {"winner": "w", "reason": "king_capture"})

    assert observer.game_overs == ["b"]


def test_an_untranslated_message_type_is_ignored():
    dispatcher, observer = _dispatcher()

    dispatcher.dispatch("state_snapshot", {"pieces": [], "width": 8, "height": 8, "sequence": 0, "game_over": False})

    assert observer.arrivals == []
    assert observer.motions == []
    assert observer.game_overs == []
