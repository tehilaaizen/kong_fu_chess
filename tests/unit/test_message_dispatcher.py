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
    a live game, plus the outgoing messages the game start produced."""
    dispatcher, service, connections = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))
    dispatcher.dispatch("c2", _inbound("connect", {"username": "bob"}))
    dispatcher.dispatch("c1", _inbound("join_game"))
    start_outgoing = dispatcher.dispatch("c2", _inbound("join_game"))
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

    result = dispatcher.dispatch("c1", _inbound("join_game"))

    assert result[0].message["payload"]["code"] == "NOT_CONNECTED"


def test_the_first_joiner_waits_and_the_second_starts_the_game():
    dispatcher, service, connections, start_outgoing = _started()

    # first connector is White, second is Black
    assert connections.get("c1").color == "w"
    assert connections.get("c2").color == "b"
    assert service.session("g1") is not None
    # both players get game_started then the opening snapshot
    assert _types(start_outgoing) == ["game_started", "game_started", "state_snapshot", "state_snapshot"]
    assert {o.connection_id for o in start_outgoing} == {"c1", "c2"}


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


def test_ping_is_answered_with_pong():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("ping"))

    assert _types(result) == ["pong"]


def test_an_unknown_message_type_is_an_error():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("frobnicate"))

    assert result[0].message["payload"]["code"] == "UNKNOWN_TYPE"


def test_the_same_connection_joining_twice_still_only_waits():
    dispatcher, service, _ = _dispatcher()
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))

    dispatcher.dispatch("c1", _inbound("join_game"))
    second = dispatcher.dispatch("c1", _inbound("join_game"))

    assert second == []
    assert service.session("g1") is None
