from view.lobby.home_screen import MATCHMAKING, ROOM, HomeChoice
from view.lobby.lobby_flow import _request_game


class _RecordingConnection:
    """Records the messages a caller sends."""

    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


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
