from application.game_service import GameService
from messaging.application_events import (
    GameEndedEvent,
    GameMoveAppliedEvent,
    GameStartedEvent,
    JumpStartedEvent,
    RestStartedEvent,
)
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


def _of_type(sink, message_type):
    return [o for o in sink if o.message["type"] == message_type]


def test_accepting_a_move_broadcasts_motion_started_to_everyone_in_the_game():
    service, _, sink = _wired()

    service.handle_move("g1", "w", "WRa1a7")

    motions = _of_type(sink, "motion_started")
    assert {o.connection_id for o in motions} == {"c1", "c2"}
    payload = motions[0].message["payload"]
    assert payload["piece"]["color"] == "w"
    assert payload["piece"]["kind"] == "R"
    assert payload["source"] == {"row": 7, "col": 0}
    assert payload["destination"] == {"row": 1, "col": 0}
    assert payload["duration_ms"] > 0


def test_an_arrival_broadcasts_arrival_then_the_authoritative_state_snapshot():
    service, _, sink = _wired()

    service.handle_move("g1", "w", "WRa1a7")
    service.tick("g1", LONG_ENOUGH_MS)

    # each client sees: motion_started (on accept), then on the tick the
    # arrival, the corrective snapshot, and the mover's cooldown.
    types_c1 = [o.message["type"] for o in sink if o.connection_id == "c1"]
    assert types_c1 == ["motion_started", "arrival", "state_snapshot", "rest_started"]

    state = next(o for o in sink if o.connection_id == "c1" and o.message["type"] == "state_snapshot")
    cells = {(p["row"], p["col"]): p["color"] + p["kind"] for p in state.message["payload"]["pieces"]}
    assert cells[(1, 0)] == "wR"  # rook has moved to a7
    assert (7, 0) not in cells  # a1 is now empty


def test_the_arrival_message_carries_the_captured_kind():
    service, _, sink = _wired()

    service.handle_move("g1", "w", "WRa1a8")  # captures the king
    service.tick("g1", LONG_ENOUGH_MS)

    arrival = _of_type(sink, "arrival")[0]
    assert arrival.message["payload"]["captured_kind"] == "K"


def test_a_jump_started_event_is_broadcast_to_everyone_in_the_game():
    service, connections, sink = _wired()
    broadcaster = Broadcaster(service, connections, sink.append)

    broadcaster.handle(
        JumpStartedEvent(game_id="g1", piece_id=5, color="w", kind="R", position=Position(7, 0), duration_ms=3000)
    )

    jumps = _of_type(sink, "jump_started")
    assert {o.connection_id for o in jumps} == {"c1", "c2"}
    assert jumps[0].message["payload"] == {
        "piece": {"id": 5, "color": "w", "kind": "R"},
        "cell": {"row": 7, "col": 0},
        "duration_ms": 3000,
    }


def test_a_rest_started_event_is_broadcast_to_everyone_in_the_game():
    service, connections, sink = _wired()
    broadcaster = Broadcaster(service, connections, sink.append)

    broadcaster.handle(
        RestStartedEvent(game_id="g1", piece_id=5, color="w", kind="R", duration_ms=5000, label="long_rest")
    )

    rests = _of_type(sink, "rest_started")
    assert {o.connection_id for o in rests} == {"c1", "c2"}
    assert rests[0].message["payload"] == {
        "piece": {"id": 5, "color": "w", "kind": "R"},
        "duration_ms": 5000,
        "label": "long_rest",
    }


def test_capturing_the_king_broadcasts_game_over_with_the_winner():
    service, _, sink = _wired()

    service.handle_move("g1", "w", "WRa1a8")
    service.tick("g1", LONG_ENOUGH_MS)

    game_overs = _of_type(sink, "game_over")
    assert {o.connection_id for o in game_overs} == {"c1", "c2"}
    assert game_overs[0].message["payload"]["winner"] == "w"


def test_an_arrival_for_an_unknown_game_broadcasts_nothing():
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
