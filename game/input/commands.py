from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Union

from input.controller import Controller


@dataclass(frozen=True)
class ClickCommand:
    """A left-click at window-local pixel (x, y) - Controller resolves
    it to a board cell (and decides selection vs move) itself."""

    x: int
    y: int


@dataclass(frozen=True)
class JumpCommand:
    """A right-click at window-local pixel (x, y) - Controller resolves
    it to a board cell and requests a jump."""

    x: int
    y: int


Command = Union[ClickCommand, JumpCommand]


class CommandSender(Protocol):
    """The only capability input extraction needs from wherever a
    Command ends up - lets a future NetworkCommandSender (serializing to
    JSON and sending it to a real server) replace LocalCommandSender
    without touching any input/ extraction code."""

    def send(self, command: Command) -> None:
        ...


class LocalCommandSender:
    """Sends a Command straight to the local Controller - no network
    involved. Controller.click/jump already take raw pixel coordinates,
    so no further translation happens here."""

    def __init__(self, controller: Controller) -> None:
        self._controller = controller

    def send(self, command: Command) -> None:
        match command:
            case ClickCommand(x=x, y=y):
                self._controller.click(x, y)
            case JumpCommand(x=x, y=y):
                self._controller.jump(x, y)
