from client.network_commands import NetworkCommands
from client.network_game_adapter import NetworkGameAdapter, decode_snapshot
from client.server_event_dispatcher import ServerEventDispatcher
from engine.game_snapshot import GameSnapshot, PiecePlacement
from input.board_mapper import BoardMapper
from input.commands import ClickCommand, JumpCommand
from input.controller import Controller
from model.board import Board
from model.position import Position
from rules.rule_engine import RuleEngine


class FakeConnection:
    """Records outbound frames; returns a preset list of inbound frames
    once when polled, then nothing."""

    def __init__(self, inbound=None) -> None:
        self.sent: list = []
        self._inbound = list(inbound or [])
        self.closed = False

    def send(self, message) -> None:
        self.sent.append(message)

    def poll(self) -> list:
        drained, self._inbound = self._inbound, []
        return drained

    def is_closed(self) -> bool:
        return self.closed


class SpyObserver:
    def __init__(self) -> None:
        self.motions: list = []
        self.game_overs: list = []

    def on_motion_started(self, piece, source, destination, duration_ms) -> None:
        self.motions.append((piece, source, destination, duration_ms))

    def on_game_over(self, loser_color) -> None:
        self.game_overs.append(loser_color)


def _initial_snapshot() -> GameSnapshot:
    # White rook a1 (row 7), black king a8 (row 0).
    return GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[
            PiecePlacement(id=1, kind="R", color="w", cell=Position(7, 0)),
            PiecePlacement(id=2, kind="K", color="b", cell=Position(0, 0)),
        ],
    )


def _state_snapshot_message(pieces, sequence=1):
    return {
        "type": "state_snapshot",
        "payload": {"pieces": pieces, "width": 8, "height": 8, "sequence": sequence, "game_over": False},
    }


def _adapter(inbound=None):
    connection = FakeConnection(inbound)
    board = Board(width=8, height=8)
    board_mapper = BoardMapper(board)
    rule_engine = RuleEngine()
    commands = NetworkCommands(connection, board)
    controller = Controller(board, board_mapper, commands)
    dispatcher = ServerEventDispatcher()
    adapter = NetworkGameAdapter(connection, controller, board, rule_engine, dispatcher, _initial_snapshot())
    return adapter, connection, board, controller


def test_decode_snapshot_rebuilds_placements_with_their_ids():
    snapshot = decode_snapshot(
        {"pieces": [{"id": 9, "color": "b", "kind": "N", "row": 0, "col": 1}], "width": 8, "height": 8,
         "sequence": 0, "game_over": False}
    )

    assert snapshot.board_width == 8
    assert snapshot.board_height == 8
    assert snapshot.pieces[0].id == 9
    assert snapshot.pieces[0].cell == Position(0, 1)


def test_the_initial_snapshot_is_drawn_and_mirrored_onto_the_board():
    adapter, _, board, _ = _adapter()

    assert {(p.color, p.kind) for p in adapter.snapshot().pieces} == {("w", "R"), ("b", "K")}
    assert board.piece_at(Position(7, 0)).kind == "R"
    assert board.piece_at(Position(0, 0)).kind == "K"


def test_advance_applies_a_state_snapshot_to_the_drawn_state_and_the_mirror():
    moved = [
        {"id": 1, "color": "w", "kind": "R", "row": 3, "col": 0},  # rook slid a1 -> a5
        {"id": 2, "color": "b", "kind": "K", "row": 0, "col": 0},
    ]
    adapter, _, board, _ = _adapter(inbound=[_state_snapshot_message(moved)])

    adapter.advance(16)

    assert board.piece_at(Position(7, 0)) is None  # a1 vacated
    assert board.piece_at(Position(3, 0)).kind == "R"  # rook now at a5
    assert {(p.cell.row, p.cell.col) for p in adapter.snapshot().pieces} == {(3, 0), (0, 0)}


def test_advance_reconstructs_a_motion_started_event_for_observers():
    motion = {
        "type": "motion_started",
        "payload": {
            "piece": {"id": 1, "color": "w", "kind": "R"},
            "source": {"row": 7, "col": 0},
            "destination": {"row": 3, "col": 0},
            "duration_ms": 500,
        },
    }
    adapter, _, _, _ = _adapter(inbound=[motion])
    observer = SpyObserver()
    adapter.add_observer(observer)

    adapter.advance(16)

    piece, source, destination, duration = observer.motions[0]
    assert piece.id == 1
    assert source == Position(7, 0)
    assert destination == Position(3, 0)
    assert duration == 500


def test_advance_reconstructs_game_over_as_the_losers_color():
    over = {"type": "game_over", "payload": {"winner": "w", "reason": "king_capture"}}
    adapter, _, _, _ = _adapter(inbound=[over])
    observer = SpyObserver()
    adapter.add_observer(observer)

    adapter.advance(16)

    assert observer.game_overs == ["b"]


def test_legal_destinations_is_computed_over_the_mirror_board():
    adapter, _, _, _ = _adapter()

    destinations = adapter.legal_destinations(Position(7, 0))  # the white rook

    # a rook on an otherwise-open file/rank can slide up its column
    assert Position(3, 0) in destinations


def test_two_clicks_send_the_resolved_move_to_the_server():
    adapter, connection, _, _ = _adapter()

    adapter.send(ClickCommand(10, 710))  # select the rook at a1 (row 7)
    adapter.send(ClickCommand(10, 510))  # click a3 (row 5) -> issue the move

    assert connection.sent == [{"type": "make_move", "payload": {"move": "WRa1a3"}}]


def test_a_right_click_sends_a_jump_request():
    adapter, connection, _, _ = _adapter()

    adapter.send(JumpCommand(10, 710))  # right-click the rook at a1

    assert connection.sent == [{"type": "jump_request", "payload": {"cell": "a1"}}]


def test_selected_cell_reflects_the_controller_selection():
    adapter, _, _, controller = _adapter()

    adapter.send(ClickCommand(10, 710))  # select a1

    assert adapter.selected_cell == Position(7, 0)
    assert controller.selected_cell == Position(7, 0)


def test_connection_lost_reflects_the_underlying_connection_state():
    adapter, connection, _, _ = _adapter()

    assert adapter.connection_lost() is False

    connection.closed = True

    assert adapter.connection_lost() is True
