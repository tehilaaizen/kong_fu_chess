from application.game_service import GameService
from application.game_session import NOT_YOUR_PIECE
from messaging.application_message_bus import ApplicationMessageBus
from server.connection_manager import ConnectionManager
from server.message_dispatcher import MessageDispatcher, Outgoing
from server.schemas import InboundMessage


def _inbound(message_type, payload=None, message_id=None):
    return InboundMessage(type=message_type, payload=payload or {}, message_id=message_id)


def _dispatcher():
    connections = ConnectionManager()
    service = GameService(ApplicationMessageBus())
    dispatcher = MessageDispatcher(service, connections, game_id_factory=lambda: "g1")
    return dispatcher, service, connections


def _started():
    """A dispatcher with two connected players (alice=White, bob=Black) in
    a live game in room "lobby", plus the outgoing messages the game start
    produced."""
    dispatcher, service, connections = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))
    dispatcher.dispatch("c2", _inbound("connect", {"username": "bob"}))
    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))
    start_outgoing = dispatcher.dispatch("c2", _inbound("join_room", {"room": "lobby"}))
    return dispatcher, service, connections, start_outgoing


def _types(outgoing: list[Outgoing]) -> list[str]:
    return [o.message["type"] for o in outgoing]


def test_connect_registers_the_username():
    dispatcher, _, connections = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))

    assert result == []
    assert connections.get("c1").username == "alice"


def test_connect_without_a_username_is_an_error():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("connect", {}))

    assert _types(result) == ["error"]
    assert result[0].message["payload"]["code"] == "MISSING_FIELD"


def test_join_before_connect_is_an_error():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))

    assert result[0].message["payload"]["code"] == "NOT_CONNECTED"


def test_join_room_without_a_room_name_is_an_error():
    dispatcher, _, _ = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))

    result = dispatcher.dispatch("c1", _inbound("join_room", {}))

    assert result[0].message["payload"]["code"] == "MISSING_FIELD"


def test_the_room_creator_plays_white_and_the_second_joiner_starts_the_game():
    dispatcher, service, connections, start_outgoing = _started()

    # first into the room is White, second is Black
    assert connections.get("c1").color == "w"
    assert connections.get("c2").color == "b"
    assert service.session("g1") is not None
    # both players get game_started then the opening snapshot
    assert _types(start_outgoing) == ["game_started", "game_started", "state_snapshot", "state_snapshot"]
    assert {o.connection_id for o in start_outgoing} == {"c1", "c2"}


def test_players_in_different_rooms_do_not_pair_together():
    dispatcher, service, connections = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))
    dispatcher.dispatch("c2", _inbound("connect", {"username": "bob"}))

    first = dispatcher.dispatch("c1", _inbound("join_room", {"room": "alpha"}))
    second = dispatcher.dispatch("c2", _inbound("join_room", {"room": "beta"}))

    # each created their own room and is waiting - no game started, so neither
    # has been seated yet (color is assigned only when a game begins)
    assert first == []
    assert second == []
    assert connections.get("c1").game_id is None
    assert connections.get("c2").game_id is None
    assert service.session("g1") is None


def test_a_third_joiner_is_seated_as_a_spectator_and_shown_the_game():
    dispatcher, service, connections, _ = _started()
    dispatcher.dispatch("c3", _inbound("connect", {"username": "carol"}))

    result = dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    # the spectator is seated in the game (color None) and shown it in progress
    assert connections.get("c3").game_id == "g1"
    assert connections.get("c3").color is None
    assert _types(result) == ["game_started", "state_snapshot"]
    assert {o.connection_id for o in result} == {"c3"}


def test_a_spectators_move_is_rejected():
    dispatcher, _, _, _ = _started()
    dispatcher.dispatch("c3", _inbound("connect", {"username": "carol"}))
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.dispatch("c3", _inbound("make_move", {"move": "WPa2a4"}, message_id="s1"))

    assert _types(result) == ["move_rejected"]
    assert result[0].message["payload"]["reason"] == "spectator"
    assert result[0].message["correlation_id"] == "s1"


def test_a_spectators_jump_is_rejected():
    dispatcher, _, _, _ = _started()
    dispatcher.dispatch("c3", _inbound("connect", {"username": "carol"}))
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.dispatch("c3", _inbound("jump_request", {"cell": "a2"}))

    assert _types(result) == ["move_rejected"]
    assert result[0].message["payload"]["reason"] == "spectator"


def test_white_can_make_a_legal_move():
    dispatcher, _, _, _ = _started()

    result = dispatcher.dispatch("c1", _inbound("make_move", {"move": "WPa2a4"}, message_id="m1"))

    assert _types(result) == ["move_accepted"]
    assert result[0].message["correlation_id"] == "m1"


def test_black_moving_a_white_piece_is_rejected():
    dispatcher, _, _, _ = _started()

    result = dispatcher.dispatch("c2", _inbound("make_move", {"move": "WPa2a4"}, message_id="m2"))

    assert _types(result) == ["move_rejected"]
    assert result[0].message["payload"]["reason"] == NOT_YOUR_PIECE
    assert result[0].message["correlation_id"] == "m2"


def test_make_move_before_joining_a_game_is_an_error():
    dispatcher, _, _ = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "solo"}))

    result = dispatcher.dispatch("c1", _inbound("make_move", {"move": "WPa2a4"}))

    assert result[0].message["payload"]["code"] == "NOT_IN_GAME"


def test_make_move_without_a_move_string_is_an_error():
    dispatcher, _, _, _ = _started()

    result = dispatcher.dispatch("c1", _inbound("make_move", {}))

    assert result[0].message["payload"]["code"] == "MISSING_FIELD"


def test_jump_request_is_accepted_for_your_own_piece():
    dispatcher, _, _, _ = _started()

    result = dispatcher.dispatch("c1", _inbound("jump_request", {"cell": "a2"}, message_id="j1"))

    assert _types(result) == ["move_accepted"]


def test_jump_request_on_an_empty_cell_is_rejected():
    dispatcher, _, _, _ = _started()

    result = dispatcher.dispatch("c1", _inbound("jump_request", {"cell": "a5"}, message_id="j2"))

    assert _types(result) == ["move_rejected"]


def test_jump_request_without_a_cell_is_an_error():
    dispatcher, _, _, _ = _started()

    result = dispatcher.dispatch("c1", _inbound("jump_request", {}))

    assert result[0].message["payload"]["code"] == "MISSING_FIELD"


def test_jump_request_before_joining_a_game_is_an_error():
    dispatcher, _, _ = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "solo"}))

    result = dispatcher.dispatch("c1", _inbound("jump_request", {"cell": "a2"}))

    assert result[0].message["payload"]["code"] == "NOT_IN_GAME"


def test_disconnecting_a_player_ends_the_game_for_the_opponent_and_spectators():
    dispatcher, service, connections, _ = _started()
    dispatcher.dispatch("c3", _inbound("connect", {"username": "carol"}))
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.disconnect("c1")  # White abandons

    # everyone else in the game is told, and Black is named the winner
    assert {o.connection_id for o in result} == {"c2", "c3"}
    assert all(o.message["type"] == "game_over" for o in result)
    assert result[0].message["payload"] == {"winner": "b", "reason": "abandoned"}
    # the game is marked over and the connection is gone
    assert service.session("g1").is_over() is True
    assert connections.get("c1") is None


def test_a_spectator_disconnecting_broadcasts_nothing_and_leaves_the_game_running():
    dispatcher, service, connections, _ = _started()
    dispatcher.dispatch("c3", _inbound("connect", {"username": "carol"}))
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.disconnect("c3")

    assert result == []
    assert connections.get("c3") is None
    assert service.session("g1").is_over() is False


def test_a_waiting_player_disconnecting_broadcasts_nothing():
    dispatcher, _, connections = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))
    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))  # White, still waiting

    result = dispatcher.disconnect("c1")

    assert result == []
    assert connections.get("c1") is None


def test_disconnecting_a_player_after_the_game_already_ended_broadcasts_nothing():
    dispatcher, service, connections, _ = _started()
    service.session("g1").abandon()  # already over

    result = dispatcher.disconnect("c1")

    assert result == []
    assert connections.get("c1") is None


def test_disconnecting_an_unknown_connection_is_a_noop():
    dispatcher, _, _ = _dispatcher()

    assert dispatcher.disconnect("ghost") == []


def test_ping_is_answered_with_pong():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("ping"))

    assert _types(result) == ["pong"]


def test_an_unknown_message_type_is_an_error():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("frobnicate"))

    assert result[0].message["payload"]["code"] == "UNKNOWN_TYPE"


def test_the_same_connection_joining_a_room_twice_still_only_waits():
    dispatcher, service, _ = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))

    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))
    second = dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))

    assert second == []
    assert service.session("g1") is None
