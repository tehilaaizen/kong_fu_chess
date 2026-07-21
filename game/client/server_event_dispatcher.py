from __future__ import annotations

from engine.game_observers import GameObserver, ObserverHub
from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent

# Wire message types this dispatcher understands - the client half of the
# contract server/schemas.py builds. Kept as named constants so the routing
# below reads as intent, not magic strings.
MOTION_STARTED = "motion_started"
JUMP_STARTED = "jump_started"
REST_STARTED = "rest_started"
ARRIVAL = "arrival"
GAME_OVER = "game_over"

WHITE = "w"
BLACK = "b"

# A placeholder cell for events whose observer hook never reads the piece's
# cell (rest_started carries none, since on_rest_started keys off the piece
# id, not its position).
_NO_CELL = Position(-1, -1)


class ServerEventDispatcher:
    """Reconstructs the engine's domain notifications from server wire
    messages and fans them out - through the shared ObserverHub - to the
    same view observers a local GameEngine drives. This is what makes a
    networked client animate identically to a local one: the server sends
    the same motion/jump/rest/arrival/game-over events, and here they
    become the exact on_motion_started / on_arrival / ... calls the local
    engine would have made. Owns no game state; snapshot/board handling
    lives in NetworkGameAdapter."""

    def __init__(self, observers: ObserverHub | None = None) -> None:
        """observers is the hub the view observers register on; a fresh one
        is created if not supplied (lets NetworkGameAdapter share a single
        hub with this dispatcher)."""
        self._observers = observers if observers is not None else ObserverHub()

    def add_observer(self, observer: GameObserver) -> None:
        """Subscribe a view observer to the reconstructed events it
        declares a hook for (delegated to the shared ObserverHub)."""
        self._observers.add_observer(observer)

    def dispatch(self, message_type: str, payload: dict) -> None:
        """Reconstruct one server event and notify the observers, or do
        nothing for a message type this dispatcher doesn't translate (e.g.
        state_snapshot, handled by NetworkGameAdapter instead)."""
        if message_type == MOTION_STARTED:
            self._motion_started(payload)
        elif message_type == JUMP_STARTED:
            self._jump_started(payload)
        elif message_type == REST_STARTED:
            self._rest_started(payload)
        elif message_type == ARRIVAL:
            self._arrival(payload)
        elif message_type == GAME_OVER:
            self._game_over(payload)

    def _motion_started(self, payload: dict) -> None:
        """A move began travelling: replay it as on_motion_started."""
        source = _position(payload["source"])
        destination = _position(payload["destination"])
        piece = _piece(payload["piece"], source)
        self._observers.notify_motion_started(piece, source, destination, payload["duration_ms"])

    def _jump_started(self, payload: dict) -> None:
        """A piece went airborne: replay it as on_jump_started."""
        cell = _position(payload["cell"])
        piece = _piece(payload["piece"], cell)
        self._observers.notify_jump_started(piece, cell, payload["duration_ms"])

    def _rest_started(self, payload: dict) -> None:
        """A piece entered a cooldown: replay it as on_rest_started."""
        piece = _piece(payload["piece"], _NO_CELL)
        self._observers.notify_rest_started(piece, payload["duration_ms"], payload["label"])

    def _arrival(self, payload: dict) -> None:
        """A motion landed: replay it as on_arrival, reconstructing the
        captured piece (if any) from just its kind - the color is the
        mover's opponent, and its exact id doesn't matter to the observers
        that read an arrival (they only look at the captured kind)."""
        source = _position(payload["source"])
        destination = _position(payload["destination"])
        piece = _piece(payload["piece"], destination)
        captured = _captured_piece(payload["captured_kind"], piece.color, destination)
        self._observers.notify_arrival(ArrivalEvent(piece, source, destination, captured))

    def _game_over(self, payload: dict) -> None:
        """The game ended: the wire names the winner, but on_game_over's
        contract is the loser's color, so translate before notifying."""
        winner = payload["winner"]
        loser_color = BLACK if winner == WHITE else WHITE
        self._observers.notify_game_over(loser_color)


def _position(cell: dict) -> Position:
    """Rebuild a Position from a {row, col} wire record."""
    return Position(cell["row"], cell["col"])


def _piece(ref: dict, cell: Position) -> Piece:
    """Rebuild a Piece from an {id, color, kind} wire record placed at
    cell. The id is the server's stable id, so it keys the same animator
    across every event about this piece."""
    return Piece(id=ref["id"], color=ref["color"], kind=ref["kind"], cell=cell)


def _captured_piece(captured_kind: str | None, mover_color: str, cell: Position) -> Piece | None:
    """Rebuild the captured piece from its kind alone, or None if nothing
    was captured. A capture is always cross-color, so the captured piece's
    color is the mover's opponent; its id is a sentinel (-1) because no
    observer tracks a captured piece by id."""
    if captured_kind is None:
        return None
    captured_color = BLACK if mover_color == WHITE else WHITE
    return Piece(id=-1, color=captured_color, kind=captured_kind, cell=cell)
