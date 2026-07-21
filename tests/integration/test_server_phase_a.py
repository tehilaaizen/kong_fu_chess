"""End-to-end Phase A acceptance flow, exercised synchronously through the
real command path (dispatcher -> GameService -> GameEngine) and the real
broadcast path (bus -> Broadcaster), with no sockets or event loop - the
async GameServer is only the transport around exactly these pieces."""

from application.game_service import GameService
from application.game_session import NOT_YOUR_PIECE
from messaging.application_message_bus import ApplicationMessageBus
from server.broadcaster import Broadcaster
from server.connection_manager import ConnectionManager
from server.message_dispatcher import MessageDispatcher
from server.schemas import InboundMessage

# White rook a1, lone black king a8: white can win in one move (a1->a8).
QUICK_BOARD = "\n".join(
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


def _inbound(message_type, payload=None, message_id=None):
    return InboundMessage(type=message_type, payload=payload or {}, message_id=message_id)


def _wire():
    bus = ApplicationMessageBus()
    service = GameService(bus)
    connections = ConnectionManager()
    dispatcher = MessageDispatcher(service, connections, game_id_factory=lambda: "g1", start_board=QUICK_BOARD)
    broadcasts: list = []
    broadcaster = Broadcaster(service, connections, broadcasts.append)
    bus.subscribe(broadcaster.handle)
    return dispatcher, service, broadcasts


def _messages(outgoing):
    return [o.message for o in outgoing]


def test_two_players_connect_join_move_and_finish_with_a_king_capture():
    dispatcher, service, broadcasts = _wire()

    # (1) both identify by username, first to join is White, second is Black
    dispatcher.dispatch("c1", _inbound("connect", {"username": "alice"}))
    dispatcher.dispatch("c2", _inbound("connect", {"username": "bob"}))
    dispatcher.dispatch("c1", _inbound("join_game"))
    start = dispatcher.dispatch("c2", _inbound("join_game"))

    # (2) both receive game_started and an opening state_snapshot (sequence 0)
    start_types = [m["type"] for m in _messages(start)]
    assert start_types == ["game_started", "game_started", "state_snapshot", "state_snapshot"]
    assert _messages(start)[2]["payload"]["sequence"] == 0

    # (4) Black attempting to move a White piece is rejected, board untouched
    rejected = dispatcher.dispatch("c2", _inbound("make_move", {"move": "WRa1a8"}, message_id="b1"))
    assert _messages(rejected)[0]["type"] == "move_rejected"
    assert _messages(rejected)[0]["payload"]["reason"] == NOT_YOUR_PIECE

    # (5) a structurally illegal move (rook diagonally) is rejected
    illegal = dispatcher.dispatch("c1", _inbound("make_move", {"move": "WRa1b2"}, message_id="w0"))
    assert _messages(illegal)[0]["type"] == "move_rejected"

    # (3) White's legal move is accepted (correlated to the request)
    accepted = dispatcher.dispatch("c1", _inbound("make_move", {"move": "WRa1a8"}, message_id="w1"))
    assert _messages(accepted)[0]["type"] == "move_accepted"
    assert _messages(accepted)[0]["correlation_id"] == "w1"

    # (6) the accepted move broadcasts motion_started at once; once it
    # resolves on a tick both clients get the arrival, the corrective
    # snapshot, game_over naming White the winner, and the mover's cooldown
    service.tick_all(LONG_ENOUGH_MS)
    types_by_conn = {"c1": [], "c2": []}
    for outgoing in broadcasts:
        types_by_conn[outgoing.connection_id].append(outgoing.message["type"])
    expected = ["motion_started", "arrival", "state_snapshot", "game_over", "rest_started"]
    assert types_by_conn["c1"] == expected
    assert types_by_conn["c2"] == expected
    game_over = next(o for o in broadcasts if o.message["type"] == "game_over")
    assert game_over.message["payload"]["winner"] == "w"
