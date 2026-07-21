from application.game_service import GameService
from messaging.application_events import GameEndedEvent, GameMoveAppliedEvent, GameStartedEvent
from messaging.application_message_bus import ApplicationMessageBus
from model.position import Position
from server.broadcaster import Broadcaster
from server.connection_manager import ConnectionManager

# White rook a1, lone black king a8 - a1->a8 captures the king in one move.
BOARD_TEXT = "\n".join(
    [
        "bK . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        "wR . . . . . . .",
    ]
)
LONG_ENOUGH_MS = 100_000


def _wired():
    """A bus/service/broadcaster wired together with two seated players in
    game g1, and the list the broadcaster's sink appends to."""
    bus = ApplicationMessageBus()
    service = GameService(bus)
    connections = ConnectionManager()
    sink: list = []
    broadcaster = Broadcaster(service, connections, sink.append)
    bus.subscribe(broadcaster.handle)

    service.create_session("g1", "alice", "bob", BOARD_TEXT)
    connections.register("c1", "alice")
    connections.register("c2", "bob")
    connections.assign_to_game("c1", "g1", "w")
    connections.assign_to_game("c2", "g1", "b")
    return service, connections, sink


def test_an_arrival_broadcasts_a_state_snapshot_to_everyone_in_the_game():
    service, _, sink = _wired()

    service.handle_move("g1", "w", "WRa1a7")
    service.tick("g1", LONG_ENOUGH_MS)

    snapshots = [o for o in sink if o.message["type"] == "state_snapshot"]
    assert {o.connection_id for o in snapshots} == {"c1", "c2"}
    # the rook has moved off a1 to a7 in the broadcast board
    board = snapshots[0].message["payload"]["board"]
    assert board[7][0] == "."
    assert board[1][0] == "wR"


def test_capturing_the_king_broadcasts_game_over_with_the_winner():
    service, _, sink = _wired()

    service.handle_move("g1", "w", "WRa1a8")
    service.tick("g1", LONG_ENOUGH_MS)

    game_overs = [o for o in sink if o.message["type"] == "game_over"]
    assert {o.connection_id for o in game_overs} == {"c1", "c2"}
    assert game_overs[0].message["payload"]["winner"] == "w"


def test_an_event_for_an_unknown_game_broadcasts_nothing():
    service, _, sink = _wired()
    broadcaster = Broadcaster(service, ConnectionManager(), sink.append)

    broadcaster.handle(
        GameMoveAppliedEvent(
            game_id="ghost",
            sequence=1,
            piece_id=1,
            source=Position(0, 0),
            destination=Position(0, 1),
            color="w",
            kind="R",
            captured_kind=None,
        )
    )

    assert sink == []


def test_an_untranslated_event_type_is_ignored():
    service, connections, sink = _wired()
    broadcaster = Broadcaster(service, connections, sink.append)

    broadcaster.handle(GameStartedEvent("g1", "alice", "bob"))

    assert sink == []
