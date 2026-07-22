from view.image_view import Img
from view.lobby.waiting_screen import LOST, STARTED, TIMEOUT, WaitingScreen


class _FakeConnection:
    """A ServerConnection stand-in: poll() returns queued messages once,
    is_closed() reports a preset flag."""

    def __init__(self, closed=False):
        self._messages = []
        self._closed = closed

    def queue(self, *messages):
        self._messages.extend(messages)

    def poll(self):
        drained, self._messages = self._messages, []
        return drained

    def is_closed(self):
        return self._closed


def _game_started(white="alice", black="bob", wr=1200, br=1250):
    return {"type": "game_started", "payload": {"white": white, "black": black, "white_rating": wr, "black_rating": br}}


def _snapshot():
    return {
        "type": "state_snapshot",
        "payload": {"width": 1, "height": 1, "pieces": [{"id": 1, "kind": "K", "color": "w", "row": 0, "col": 0}]},
    }


def test_waiting_with_no_messages_has_no_outcome_yet():
    screen = WaitingScreen(_FakeConnection())

    assert screen.result() is None


def test_game_started_then_snapshot_resolves_to_started_with_names():
    connection = _FakeConnection()
    screen = WaitingScreen(connection)
    connection.queue(_game_started(), _snapshot())

    outcome = screen.result()

    assert outcome.reason == STARTED
    assert outcome.snapshot is not None
    assert outcome.names == {"w": "alice (1200)", "b": "bob (1250)"}


def test_a_match_timeout_resolves_to_timeout():
    connection = _FakeConnection()
    screen = WaitingScreen(connection)
    connection.queue({"type": "match_timeout", "payload": {}})

    assert screen.result().reason == TIMEOUT


def test_a_dropped_connection_resolves_to_lost():
    screen = WaitingScreen(_FakeConnection(closed=True))

    assert screen.result().reason == LOST


def test_once_resolved_it_stops_polling_and_renders():
    connection = _FakeConnection()
    screen = WaitingScreen(connection)
    connection.queue(_game_started(), _snapshot())
    first = screen.result()

    # a later poll (even with the connection now closed) keeps the first outcome
    connection._closed = True
    assert screen.result() is first
    screen.render(Img().blank(620, 470))  # draws the status message, no crash


def test_on_click_and_on_key_are_inert():
    screen = WaitingScreen(_FakeConnection())

    screen.on_click(1, 2)
    screen.on_key(65)

    assert screen.result() is None
