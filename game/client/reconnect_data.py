from __future__ import annotations


class ReconnectData:
    """Tracks the "opponent left, waiting for them to reconnect" state on the
    remaining player's client, driven by the server's player_disconnected /
    player_reconnected messages. The countdown is ticked down locally each
    frame (advance) from the seconds the server gave, so the window can show a
    live stopwatch and lock input while it runs. Purely a small state holder;
    NetworkGameAdapter feeds it and GameWindow reads status() each frame."""

    def __init__(self) -> None:
        self._waiting = False
        self._name = ""
        self._remaining_ms = 0

    def opponent_left(self, name: str, seconds: int) -> None:
        """The named opponent dropped; start counting down their reconnect
        window (seconds)."""
        self._waiting = True
        self._name = name
        self._remaining_ms = seconds * 1000

    def opponent_returned(self) -> None:
        """The opponent reconnected in time; stop waiting."""
        self._waiting = False

    def advance(self, dt_ms: int) -> None:
        """Tick the countdown down by dt_ms (a no-op unless waiting); it never
        goes below zero - the server's game_over is what actually ends it."""
        if self._waiting:
            self._remaining_ms = max(0, self._remaining_ms - dt_ms)

    def status(self) -> tuple[str, int] | None:
        """(opponent name, whole seconds left) while waiting for a reconnect,
        or None when the game is running normally."""
        if not self._waiting:
            return None
        seconds = (self._remaining_ms + 999) // 1000  # round up so it hits 0 only at the end
        return self._name, seconds
