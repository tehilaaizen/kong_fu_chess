from view.lobby.home_screen import MATCHMAKING, ROOM, HomeChoice
from view.lobby.lobby_flow import _request_game, await_restore
from view.lobby.waiting_screen import STARTED


class _RecordingConnection:
    """Records the messages a caller sends."""

    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


class _RestoreConnection:
    """Delivers a queued burst of messages once, then nothing - and is never
    closed. Enough for await_restore's first poll to see the restore."""

    def __init__(self, messages):
        self._messages = messages

    def poll(self):
        drained, self._messages = self._messages, []
        return drained

    def is_closed(self):
        return False


def test_await_restore_returns_started_when_the_server_puts_us_back_in_a_game():
    connection = _RestoreConnection([
        {"type": "game_started", "payload": {"white": "alice", "black": "bob", "white_rating": 1200, "black_rating": 1200}},
        {"type": "state_snapshot", "payload": {"width": 1, "height": 1, "pieces": [{"id": 1, "kind": "K", "color": "w", "row": 0, "col": 0}]}},
    ])

    outcome = await_restore(connection)

    assert outcome is not None
    assert outcome.reason == STARTED
    assert outcome.names == {"w": "alice (1200)", "b": "bob (1200)"}


def test_a_matchmaking_choice_sends_find_match():
    connection = _RecordingConnection()

    message = _request_game(connection, HomeChoice(MATCHMAKING))

    assert connection.sent == [{"type": "find_match", "payload": {}}]
    assert "opponent" in message.lower()


def test_a_room_choice_sends_join_room_with_the_name():
    connection = _RecordingConnection()

    message = _request_game(connection, HomeChoice(ROOM, "arena"))

    assert connection.sent == [{"type": "join_room", "payload": {"room": "arena"}}]
    assert "arena" in message
