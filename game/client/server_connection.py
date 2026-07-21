from __future__ import annotations

from typing import Protocol


class ServerConnection(Protocol):
    """The client's view of its link to the server, decoupled from the
    transport. send() queues one message for delivery; poll() returns every
    message that has arrived since the last call (never blocking). The real
    implementation runs a WebSocket on a background asyncio thread and
    bridges through thread-safe queues; tests inject a synchronous fake.
    Both NetworkCommands (which sends) and NetworkGameAdapter (which polls)
    depend only on this narrow surface."""

    def send(self, message: dict) -> None:
        """Queue message (a wire envelope) for delivery to the server."""
        ...

    def poll(self) -> list[dict]:
        """Every server message received since the last poll, in order;
        empty if none. Never blocks."""
        ...
