from application.auth_service import AuthService
from application.game_service import GameService
from application.game_session import NOT_YOUR_PIECE
from messaging.application_message_bus import ApplicationMessageBus
from persistence.in_memory.user_repository import InMemoryUserRepository
from server.connection_manager import ConnectionManager
from server.grace_registry import GraceRegistry
from server.matchmaking import MatchmakingService
from server.message_dispatcher import MessageDispatcher, Outgoing
from server.schemas import InboundMessage


class _FakeHasher:
    """A trivial reversible "hash" so these tests skip scrypt's cost."""

    def hash(self, password: str) -> str:
        return f"H:{password}"

    def verify(self, password: str, stored: str) -> bool:
        return stored == f"H:{password}"


def _inbound(message_type, payload=None, message_id=None):
    return InboundMessage(type=message_type, payload=payload or {}, message_id=message_id)


def _dispatcher():
    connections = ConnectionManager()
    service = GameService(ApplicationMessageBus())
    auth = AuthService(InMemoryUserRepository(), _FakeHasher())
    dispatcher = MessageDispatcher(service, connections, auth, game_id_factory=lambda: "g1")
    return dispatcher, service, connections


def _identify(dispatcher, connection_id, username, password="pw"):
    """Register (and so identify) a connection - the usual precondition for
    joining a room."""
    return dispatcher.dispatch(
        connection_id, _inbound("register", {"username": username, "password": password})
    )


def _started():
    """A dispatcher with two authenticated players (alice=White, bob=Black)
    in a live game in room "lobby", plus the outgoing messages the game start
    produced."""
    dispatcher, service, connections = _dispatcher()
    _identify(dispatcher, "c1", "alice")
    _identify(dispatcher, "c2", "bob")
    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))
    start_outgoing = dispatcher.dispatch("c2", _inbound("join_room", {"room": "lobby"}))
    return dispatcher, service, connections, start_outgoing


def _types(outgoing: list[Outgoing]) -> list[str]:
    return [o.message["type"] for o in outgoing]


def test_register_creates_and_identifies_the_user():
    dispatcher, _, connections = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("register", {"username": "alice", "password": "pw"}, message_id="a1"))

    assert _types(result) == ["auth_ok"]
    assert result[0].message["payload"] == {"username": "alice", "rating": 1200}
    assert result[0].message["correlation_id"] == "a1"
    assert connections.get("c1").username == "alice"


def test_register_without_credentials_is_an_error():
    dispatcher, _, _ = _dispatcher()

    no_password = dispatcher.dispatch("c1", _inbound("register", {"username": "alice"}))
    no_username = dispatcher.dispatch("c2", _inbound("register", {"password": "pw"}))

    assert no_password[0].message["payload"]["code"] == "MISSING_FIELD"
    assert no_username[0].message["payload"]["code"] == "MISSING_FIELD"


def test_registering_a_taken_username_fails():
    dispatcher, _, _ = _dispatcher()
    _identify(dispatcher, "c1", "alice", "secret")

    result = dispatcher.dispatch("c2", _inbound("register", {"username": "alice", "password": "other"}))

    assert _types(result) == ["auth_failed"]
    assert result[0].message["payload"]["reason"] == "username_taken"


def test_login_after_register_succeeds_and_identifies_the_connection():
    dispatcher, _, connections = _dispatcher()
    _identify(dispatcher, "c1", "alice", "secret")

    result = dispatcher.dispatch("c2", _inbound("login", {"username": "alice", "password": "secret"}))

    assert _types(result) == ["auth_ok"]
    assert result[0].message["payload"]["username"] == "alice"
    assert connections.get("c2").username == "alice"


def test_logging_in_an_unknown_user_fails_with_no_such_user():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("login", {"username": "ghost", "password": "x"}))

    assert _types(result) == ["auth_failed"]
    assert result[0].message["payload"]["reason"] == "no_such_user"


def test_logging_in_with_a_wrong_password_fails():
    dispatcher, _, _ = _dispatcher()
    _identify(dispatcher, "c1", "alice", "secret")

    result = dispatcher.dispatch("c2", _inbound("login", {"username": "alice", "password": "wrong"}))

    assert _types(result) == ["auth_failed"]
    assert result[0].message["payload"]["reason"] == "wrong_password"


def test_join_before_authenticating_is_an_error():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))

    assert result[0].message["payload"]["code"] == "NOT_CONNECTED"


def test_join_room_without_a_room_name_is_an_error():
    dispatcher, _, _ = _dispatcher()
    _identify(dispatcher, "c1", "alice")

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


def test_game_started_carries_both_players_names_and_ratings():
    _, _, _, start_outgoing = _started()

    started = next(o for o in start_outgoing if o.message["type"] == "game_started")
    assert started.message["payload"] == {
        "white": "alice",
        "black": "bob",
        "white_rating": 1200,
        "black_rating": 1200,
    }


def test_a_spectator_is_shown_both_players_ratings():
    dispatcher, _, _, _ = _started()
    _identify(dispatcher, "c3", "carol")

    result = dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    started = next(o for o in result if o.message["type"] == "game_started")
    assert started.message["payload"] == {
        "white": "alice",
        "black": "bob",
        "white_rating": 1200,
        "black_rating": 1200,
    }


def test_players_in_different_rooms_do_not_pair_together():
    dispatcher, service, connections = _dispatcher()
    _identify(dispatcher, "c1", "alice")
    _identify(dispatcher, "c2", "bob")

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
    _identify(dispatcher, "c3", "carol")

    result = dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    # the spectator is seated in the game (color None) and shown it in progress
    assert connections.get("c3").game_id == "g1"
    assert connections.get("c3").color is None
    assert _types(result) == ["game_started", "state_snapshot"]
    assert {o.connection_id for o in result} == {"c3"}


def test_a_spectators_move_is_rejected():
    dispatcher, _, _, _ = _started()
    _identify(dispatcher, "c3", "carol")
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.dispatch("c3", _inbound("make_move", {"move": "WPa2a4"}, message_id="s1"))

    assert _types(result) == ["move_rejected"]
    assert result[0].message["payload"]["reason"] == "spectator"
    assert result[0].message["correlation_id"] == "s1"


def test_a_spectators_jump_is_rejected():
    dispatcher, _, _, _ = _started()
    _identify(dispatcher, "c3", "carol")
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
    _identify(dispatcher, "c1", "solo")

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
    _identify(dispatcher, "c1", "solo")

    result = dispatcher.dispatch("c1", _inbound("jump_request", {"cell": "a2"}))

    assert result[0].message["payload"]["code"] == "NOT_IN_GAME"


def test_disconnecting_a_player_freezes_the_game_and_warns_the_opponent():
    dispatcher, service, connections, _ = _started()
    _identify(dispatcher, "c3", "carol")
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.disconnect("c1")  # White leaves - but may come back

    # the opponent and spectator are warned with the countdown; the game is
    # frozen (not over), so White still has a window to reconnect
    assert {o.connection_id for o in result} == {"c2", "c3"}
    assert all(o.message["type"] == "player_disconnected" for o in result)
    assert result[0].message["payload"] == {"color": "w", "name": "alice", "seconds": 30}
    assert service.session("g1").is_over() is False
    assert service.is_paused("g1") is True
    assert connections.get("c1") is None


def test_a_move_is_rejected_while_the_game_is_paused_for_a_reconnect():
    dispatcher, service, _, _ = _started()
    dispatcher.disconnect("c1")  # White left -> frozen

    result = dispatcher.dispatch("c2", _inbound("make_move", {"move": "BPe7e5"}))

    assert result[0].message["type"] == "move_rejected"
    assert result[0].message["payload"]["reason"] == "paused"


def test_a_reconnecting_player_is_restored_and_the_opponent_is_told():
    dispatcher, service, connections, _ = _started()
    dispatcher.disconnect("c1")  # alice (White) leaves
    assert service.is_paused("g1") is True

    # alice logs back in on a fresh connection within the window
    result = dispatcher.dispatch("c9", _inbound("login", {"username": "alice", "password": "pw"}))

    to_alice = [o.message["type"] for o in result if o.connection_id == "c9"]
    to_bob = [o.message["type"] for o in result if o.connection_id == "c2"]
    assert to_alice == ["auth_ok", "game_started", "state_snapshot"]
    assert to_bob == ["player_reconnected"]
    assert service.is_paused("g1") is False  # the game resumes
    assert connections.get("c9").game_id == "g1"
    assert connections.get("c9").color == "w"


def test_reconnecting_to_a_game_that_already_ended_is_not_restored():
    dispatcher, service, _, _ = _started()
    dispatcher.disconnect("c1")  # alice -> grace
    service.session("g1").terminate()  # the game ends while she is away

    result = dispatcher.dispatch("c9", _inbound("login", {"username": "alice", "password": "pw"}))

    assert [o.message["type"] for o in result] == ["auth_ok"]  # just a plain login, no restore


def test_if_both_players_leave_the_game_ends_quietly():
    dispatcher, service, _, _ = _started()
    dispatcher.disconnect("c1")  # alice leaves -> frozen, waiting

    result = dispatcher.disconnect("c2")  # bob leaves too

    assert result == []  # nobody left to tell
    assert service.session("g1").is_over() is True
    assert service.is_paused("g1") is False


def test_when_the_reconnect_window_closes_the_opponent_wins():
    clock = _Clock()
    connections = ConnectionManager()
    service = GameService(ApplicationMessageBus())
    auth = AuthService(InMemoryUserRepository(), _FakeHasher())
    dispatcher = MessageDispatcher(
        service, connections, auth, game_id_factory=lambda: "g1", grace_registry=GraceRegistry(now_ms=clock)
    )
    _identify(dispatcher, "c1", "alice")
    _identify(dispatcher, "c2", "bob")
    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))
    dispatcher.dispatch("c2", _inbound("join_room", {"room": "lobby"}))
    dispatcher.disconnect("c1")  # alice leaves -> grace

    clock.now = 30_000
    dispatcher.expire_grace()

    assert service.session("g1").is_over() is True  # bob won by abandonment
    assert service.is_paused("g1") is False


def test_a_spectator_disconnecting_broadcasts_nothing_and_leaves_the_game_running():
    dispatcher, service, connections, _ = _started()
    _identify(dispatcher, "c3", "carol")
    dispatcher.dispatch("c3", _inbound("join_room", {"room": "lobby"}))

    result = dispatcher.disconnect("c3")

    assert result == []
    assert connections.get("c3") is None
    assert service.session("g1").is_over() is False


def test_a_waiting_player_disconnecting_broadcasts_nothing():
    dispatcher, _, connections = _dispatcher()
    _identify(dispatcher, "c1", "alice")
    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))  # White, still waiting

    result = dispatcher.disconnect("c1")

    assert result == []
    assert connections.get("c1") is None


def test_disconnecting_a_player_after_the_game_already_ended_broadcasts_nothing():
    dispatcher, service, connections, _ = _started()
    service.session("g1").abandon("b")  # already over

    result = dispatcher.disconnect("c1")

    assert result == []
    assert connections.get("c1") is None


def test_disconnecting_an_unknown_connection_is_a_noop():
    dispatcher, _, _ = _dispatcher()

    assert dispatcher.disconnect("ghost") == []


class _Clock:
    """A hand-driven clock for matchmaking timeout tests."""

    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


def _matchmaking_dispatcher(clock=None):
    """A dispatcher whose matchmaking uses an injected clock, with two
    authenticated players (alice, bob) not yet in any game."""
    connections = ConnectionManager()
    service = GameService(ApplicationMessageBus())
    auth = AuthService(InMemoryUserRepository(), _FakeHasher())
    matchmaking = MatchmakingService(now_ms=clock or _Clock())
    dispatcher = MessageDispatcher(
        service, connections, auth, game_id_factory=lambda: "g1", matchmaking=matchmaking
    )
    _identify(dispatcher, "c1", "alice")
    _identify(dispatcher, "c2", "bob")
    return dispatcher, service, connections


def test_find_match_queues_the_first_player_and_pairs_the_second():
    dispatcher, service, connections = _matchmaking_dispatcher()

    first = dispatcher.dispatch("c1", _inbound("find_match"))
    second = dispatcher.dispatch("c2", _inbound("find_match"))

    assert first == []  # nobody to match yet - waiting
    assert _types(second) == ["game_started", "game_started", "state_snapshot", "state_snapshot"]
    assert connections.get("c1").color == "w"  # first waiter is White
    assert connections.get("c2").color == "b"
    assert service.session("g1") is not None


def test_find_match_before_authenticating_is_an_error():
    dispatcher, _, _ = _dispatcher()

    result = dispatcher.dispatch("ghost", _inbound("find_match"))

    assert result[0].message["payload"]["code"] == "NOT_CONNECTED"


def test_cancelling_a_search_takes_the_player_out_of_the_queue():
    dispatcher, _, _ = _matchmaking_dispatcher()
    dispatcher.dispatch("c1", _inbound("find_match"))

    assert dispatcher.dispatch("c1", _inbound("cancel_match")) == []
    # with c1 gone from the queue, c2's search finds nobody and waits
    assert dispatcher.dispatch("c2", _inbound("find_match")) == []


def test_expire_matchmaking_times_out_a_long_waiting_player():
    clock = _Clock()
    dispatcher, _, _ = _matchmaking_dispatcher(clock)
    dispatcher.dispatch("c1", _inbound("find_match"))

    clock.now = 60_000  # past the timeout window
    timed_out = dispatcher.expire_matchmaking()

    assert [o.connection_id for o in timed_out] == ["c1"]
    assert timed_out[0].message["type"] == "match_timeout"


def test_disconnecting_a_waiting_matchmaker_drops_them_from_the_queue():
    dispatcher, _, _ = _matchmaking_dispatcher()
    dispatcher.dispatch("c1", _inbound("find_match"))

    dispatcher.disconnect("c1")

    # c1 was only in the queue (no game), so nothing is broadcast and c2 now
    # finds an empty queue
    assert dispatcher.dispatch("c2", _inbound("find_match")) == []


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
    _identify(dispatcher, "c1", "alice")

    dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))
    second = dispatcher.dispatch("c1", _inbound("join_room", {"room": "lobby"}))

    assert second == []
    assert service.session("g1") is None
