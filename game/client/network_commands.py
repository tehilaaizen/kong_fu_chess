from __future__ import annotations

from client import client_messages
from client.server_connection import ServerConnection
from model.board import Board
from model.position import Position
from text_io.move_notation import MoveNotation


class NetworkCommands:
    """Controller's game-command sink for online play. Where the local
    GameEngine would apply a move itself, this serializes the move (or
    jump) to wire notation and sends it to the server, which is
    authoritative - the board only changes here when the server's next
    state_snapshot arrives. It implements the same request_move /
    request_jump surface (Controller's GameCommands Protocol) as
    GameEngine, so the very same Controller drives local and online play;
    only this sink differs."""

    def __init__(self, connection: ServerConnection, board: Board) -> None:
        """connection carries frames to the server; board is the client's
        mirror of the current position, read only to name the moving piece
        (its color/kind) and to know the board height for rank flipping."""
        self._connection = connection
        self._board = board

    def request_move(self, source: Position, destination: Position) -> None:
        """Serialize a move from source to destination and send it. A no-op
        if source is now empty (the piece was captured between selecting it
        and clicking its destination), since there is nothing to name."""
        piece = self._board.piece_at(source)
        if piece is None:
            return
        move = MoveNotation.format(piece.color, piece.kind, source, destination, self._board.height)
        self._connection.send(client_messages.make_move(move))

    def request_jump(self, position: Position) -> None:
        """Serialize a jump at position and send it."""
        cell = MoveNotation.format_cell(position, self._board.height)
        self._connection.send(client_messages.jump_request(cell))
