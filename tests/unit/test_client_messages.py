from client import client_messages


def test_connect_carries_the_username():
    assert client_messages.connect("alice") == {"type": "connect", "payload": {"username": "alice"}}


def test_join_game_has_an_empty_payload():
    assert client_messages.join_game() == {"type": "join_game", "payload": {}}


def test_make_move_carries_the_move_string():
    assert client_messages.make_move("WRa1a7") == {"type": "make_move", "payload": {"move": "WRa1a7"}}


def test_jump_request_carries_the_cell():
    assert client_messages.jump_request("a2") == {"type": "jump_request", "payload": {"cell": "a2"}}


def test_ping_has_an_empty_payload():
    assert client_messages.ping() == {"type": "ping", "payload": {}}
