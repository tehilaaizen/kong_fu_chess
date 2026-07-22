from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

# How long a player who left has to reconnect before they auto-resign.
DEFAULT_GRACE_MS = 30_000


def _monotonic_ms() -> int:
    """Wall-clock milliseconds from a monotonic source - the default grace
    clock (injectable so a test can drive time by hand)."""
    return int(time.monotonic() * 1000)


@dataclass(frozen=True)
class GraceEntry:
    """A player who dropped mid-game and may still reconnect: their username
    (the identity they log back in as), the game and color they left, and the
    deadline after which they auto-resign."""

    username: str
    game_id: str
    color: str
    deadline_ms: int


class GraceRegistry:
    """Tracks players who left a game and are within their reconnect window.
    Keyed by username, since that is the stable identity a player logs back in
    as (their connection id changes on reconnect). Pure and synchronous like
    the other server registries; its clock is injected so timeout tests drive
    time by hand rather than sleeping. A game holds at most one player in
    grace at a time (the game is paused while it does)."""

    def __init__(self, now_ms: Callable[[], int] = _monotonic_ms, grace_ms: int = DEFAULT_GRACE_MS) -> None:
        self._now_ms = now_ms
        self._grace_ms = grace_ms
        self._by_user: dict[str, GraceEntry] = {}
        self._user_by_game: dict[str, str] = {}

    @property
    def grace_seconds(self) -> int:
        """The reconnect window in whole seconds, for the countdown shown to
        the waiting opponent."""
        return self._grace_ms // 1000

    def begin(self, username: str, game_id: str, color: str) -> GraceEntry:
        """Start the reconnect window for username, who just left game_id as
        color. Returns the recorded entry."""
        entry = GraceEntry(username, game_id, color, self._now_ms() + self._grace_ms)
        self._by_user[username] = entry
        self._user_by_game[game_id] = username
        return entry

    def take(self, username: str) -> GraceEntry | None:
        """Remove and return username's grace entry if they are within their
        window (i.e. they reconnected in time), else None."""
        entry = self._by_user.pop(username, None)
        if entry is not None:
            self._user_by_game.pop(entry.game_id, None)
        return entry

    def game_is_waiting(self, game_id: str) -> bool:
        """Whether game_id currently has a player in grace (so it is paused)."""
        return game_id in self._user_by_game

    def discard_game(self, game_id: str) -> None:
        """Forget any grace for game_id - used when the game ends for another
        reason so a stale entry can't later auto-resign a finished game."""
        username = self._user_by_game.pop(game_id, None)
        if username is not None:
            self._by_user.pop(username, None)

    def expired(self) -> list[GraceEntry]:
        """Remove and return every entry whose reconnect window has closed -
        the players who should now auto-resign. Called on the server's tick."""
        now = self._now_ms()
        due = [entry for entry in self._by_user.values() if now >= entry.deadline_ms]
        for entry in due:
            self._by_user.pop(entry.username, None)
            self._user_by_game.pop(entry.game_id, None)
        return due
