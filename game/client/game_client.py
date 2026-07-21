from __future__ import annotations

from typing import Protocol

from engine.game_snapshot import GameSnapshot
from input.commands import Command
from model.position import Position


class GameClient(Protocol):
    """Everything GameWindow needs from the game, regardless of who owns
    the authoritative state: pull the current board (snapshot), advance
    time, query a piece's legal destinations, send a player command, and
    read the current selection. LocalGameAdapter satisfies this against an
    in-process GameEngine (offline / tests); a NetworkGameAdapter will
    satisfy it against a remote server - so the whole view/ layer is
    reused unchanged in both modes."""

    def snapshot(self) -> GameSnapshot:
        """The current board state to draw this frame."""
        ...

    def advance(self, dt_ms: int) -> None:
        """Move the game forward by dt_ms. Local: steps the engine's
        simulated time; network: the server owns time, so this applies
        whatever state has arrived rather than simulating locally."""
        ...

    def legal_destinations(self, source: Position) -> set[Position]:
        """The cells the piece at source may move to, for highlighting."""
        ...

    def send(self, command: Command) -> None:
        """Forward a player command (a click or jump) to wherever the
        game logic lives."""
        ...

    @property
    def selected_cell(self) -> Position | None:
        """The currently selected cell, or None."""
        ...
