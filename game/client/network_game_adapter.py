from __future__ import annotations

from client.server_connection import ServerConnection
from client.server_event_dispatcher import ServerEventDispatcher
from engine.game_snapshot import GameSnapshot, PiecePlacement
from input.commands import Command, LocalCommandSender
from input.controller import Controller
from model.board import Board
from model.piece import Piece
from model.position import Position
from rules.rule_engine import RuleEngine

STATE_SNAPSHOT = "state_snapshot"


def decode_snapshot(payload: dict) -> GameSnapshot:
    """Rebuild a GameSnapshot from a state_snapshot payload - the inverse
    of application.dto.board_placements. Ids are preserved, so the rebuilt
    snapshot's ids match the ones the motion/arrival events carry (that is
    what keys each piece's animator)."""
    pieces = [
        PiecePlacement(id=p["id"], kind=p["kind"], color=p["color"], cell=Position(p["row"], p["col"]))
        for p in payload["pieces"]
    ]
    return GameSnapshot(board_width=payload["width"], board_height=payload["height"], pieces=pieces)


class NetworkGameAdapter:
    """A GameClient backed by a remote server - the online mode, mirroring
    LocalGameAdapter. The server owns time and rules, so this adapter never
    runs an engine: it forwards player commands to the server (through the
    Controller, whose command sink is a NetworkCommands) and, each frame,
    applies whatever the server has sent - updating the drawn snapshot from
    state_snapshots and re-driving the view observers from the fine-grained
    motion/jump/rest/arrival/game-over events (via ServerEventDispatcher).
    Because those are the same observers and calls a local GameEngine makes,
    the whole view/ layer animates identically online and offline.

    It also keeps a mirror Board in sync with each snapshot, so the same
    Controller (selection logic) and a local RuleEngine (destination
    highlighting) work exactly as in local play - the server stays
    authoritative; those are only client-side reads."""

    def __init__(
        self,
        connection: ServerConnection,
        controller: Controller,
        board: Board,
        rule_engine: RuleEngine,
        dispatcher: ServerEventDispatcher,
        initial_snapshot: GameSnapshot,
    ) -> None:
        """connection is the link to the server; controller resolves clicks
        (its command sink already points at the server); board is the mirror
        this adapter keeps in sync (shared with controller/NetworkCommands);
        rule_engine answers destination-highlight queries over that mirror;
        dispatcher turns server events into view-observer calls;
        initial_snapshot is the opening board already received from the
        server, seeded into both the drawn snapshot and the mirror."""
        self._connection = connection
        self._controller = controller
        self._board = board
        self._rule_engine = rule_engine
        self._dispatcher = dispatcher
        self._command_sender = LocalCommandSender(controller)
        self._snapshot = initial_snapshot
        self._repopulate_board(initial_snapshot)

    def snapshot(self) -> GameSnapshot:
        """The latest board state the server has sent."""
        return self._snapshot

    def advance(self, dt_ms: int) -> None:
        """Apply everything the server has sent since the last frame:
        snapshots refresh the drawn board and the mirror, other events drive
        the view observers. dt_ms is ignored - the server owns time, so this
        client never simulates it. Draining here (on the render thread, the
        only caller) keeps all snapshot/observer state single-threaded; the
        connection's background thread only queues raw messages."""
        for message in self._connection.poll():
            self._handle(message)

    def _handle(self, message: dict) -> None:
        """Route one server message: a state_snapshot updates the board, any
        other type is reconstructed into a view-observer notification."""
        message_type = message["type"]
        payload = message.get("payload", {})
        if message_type == STATE_SNAPSHOT:
            self._apply_state(payload)
        else:
            self._dispatcher.dispatch(message_type, payload)

    def _apply_state(self, payload: dict) -> None:
        """Adopt a fresh authoritative snapshot as both the drawn state and
        the mirror board."""
        snapshot = decode_snapshot(payload)
        self._snapshot = snapshot
        self._repopulate_board(snapshot)

    def _repopulate_board(self, snapshot: GameSnapshot) -> None:
        """Rebuild the mirror board to match snapshot exactly: clear it,
        then place a piece per placement (ids preserved). O(pieces) per
        snapshot, which is trivial for a chess board."""
        for piece in self._board.pieces():
            self._board.remove_piece(piece.cell)
        for placement in snapshot.pieces:
            self._board.add_piece(
                Piece(id=placement.id, color=placement.color, kind=placement.kind, cell=placement.cell)
            )

    def legal_destinations(self, source: Position) -> set[Position]:
        """The legal destinations of the piece at source, computed locally
        over the mirror board for highlighting - the same query
        GameEngine.legal_destinations answers, so highlights match local
        play. The server still validates the actual move."""
        return self._rule_engine.legal_destinations(self._board, source)

    def send(self, command: Command) -> None:
        """Forward a click/jump to the Controller, whose command sink
        serializes it to the server."""
        self._command_sender.send(command)

    def add_observer(self, observer: object) -> None:
        """Subscribe a view observer to the reconstructed server events."""
        self._dispatcher.add_observer(observer)

    @property
    def selected_cell(self) -> Position | None:
        """The Controller's currently selected cell."""
        return self._controller.selected_cell

    def connection_lost(self) -> bool:
        """Whether the link to the server has dropped - the window shows a
        banner and stops trusting the (now frozen) board."""
        return self._connection.is_closed()
