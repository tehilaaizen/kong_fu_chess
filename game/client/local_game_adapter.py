from __future__ import annotations

from typing import Protocol

from engine.game_snapshot import GameSnapshot
from input.commands import Command, LocalCommandSender
from input.controller import Controller
from model.position import Position


class LocalEngine(Protocol):
    """The slice of GameEngine the local adapter drives - a Protocol so
    tests can inject a lightweight fake instead of the full engine stack."""

    def wait(self, ms: int) -> None:
        ...

    def snapshot(self) -> GameSnapshot:
        ...

    def legal_destinations(self, source: Position) -> set[Position]:
        ...

    def add_observer(self, observer: object) -> None:
        ...


class LocalGameAdapter:
    """A GameClient backed by an in-process GameEngine - the offline /
    test mode. Wraps the same GameEngine + Controller stack the app used
    to hold directly, so local play (GUI and CLI) stays fully offline and
    the view sees identical behavior. advance() is a real simulated-time
    step; add_observer() forwards to the engine's own push notifications,
    so the animation/HUD observers work exactly as before."""

    def __init__(self, game_engine: LocalEngine, controller: Controller) -> None:
        self._game_engine = game_engine
        self._controller = controller
        self._command_sender = LocalCommandSender(controller)

    def snapshot(self) -> GameSnapshot:
        """The engine's current board snapshot."""
        return self._game_engine.snapshot()

    def advance(self, dt_ms: int) -> None:
        """Step the engine's simulated time by dt_ms."""
        self._game_engine.wait(dt_ms)

    def legal_destinations(self, source: Position) -> set[Position]:
        """The legal destinations of the piece at source."""
        return self._game_engine.legal_destinations(source)

    def send(self, command: Command) -> None:
        """Deliver a command straight to the local Controller."""
        self._command_sender.send(command)

    def add_observer(self, observer: object) -> None:
        """Subscribe a view observer to the engine's push notifications."""
        self._game_engine.add_observer(observer)

    @property
    def selected_cell(self) -> Position | None:
        """The Controller's currently selected cell."""
        return self._controller.selected_cell

    def connection_lost(self) -> bool:
        """Never lost: local play has no network to drop."""
        return False
