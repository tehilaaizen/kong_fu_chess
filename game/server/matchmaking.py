from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

# How close two players' ELO ratings must be to be paired.
DEFAULT_ELO_RANGE = 100
# How long a player waits in the queue before timing out (60 seconds).
DEFAULT_TIMEOUT_MS = 60_000


def _monotonic_ms() -> int:
    """Wall-clock milliseconds from a monotonic source - the default queue
    clock (injectable so a test can drive time by hand)."""
    return int(time.monotonic() * 1000)


@dataclass(frozen=True)
class Pairing:
    """Two connections matched into a game. white_id waited in the queue and
    plays White; black_id is the arriving player and plays Black - mirroring
    the room model, where the first in is White."""

    white_id: str
    black_id: str


@dataclass
class _Waiting:
    """One player queued for a match: their connection id, ELO rating, and
    when they joined the queue (for the timeout)."""

    connection_id: str
    rating: int
    since_ms: int


class MatchmakingService:
    """Pairs waiting players by ELO. A player requests a match and is either
    paired at once with the closest-rated player already waiting within the
    ELO range, or held in a FIFO queue until such a player arrives or the
    wait times out. Pure and synchronous like the other server services: it
    holds no sockets and produces pairings and timeout lists for the
    dispatcher to act on. Its clock is injected, so timeout tests drive time
    by hand rather than sleeping."""

    def __init__(
        self,
        now_ms: Callable[[], int] = _monotonic_ms,
        elo_range: int = DEFAULT_ELO_RANGE,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ) -> None:
        self._now_ms = now_ms
        self._elo_range = elo_range
        self._timeout_ms = timeout_ms
        self._queue: list[_Waiting] = []

    def request_match(self, connection_id: str, rating: int) -> Pairing | None:
        """Try to match connection_id (rated rating) against the queue.
        Returns a Pairing with the closest-rated waiting player within the
        ELO range (removing them from the queue), or None if nobody qualifies
        - then connection_id is enqueued to wait. Re-requesting while already
        queued just keeps waiting (no duplicate entry)."""
        opponent = self._closest_within_range(rating, exclude=connection_id)
        if opponent is not None:
            self._queue.remove(opponent)
            return Pairing(white_id=opponent.connection_id, black_id=connection_id)

        if not self._is_queued(connection_id):
            self._queue.append(_Waiting(connection_id, rating, self._now_ms()))
        return None

    def cancel(self, connection_id: str) -> bool:
        """Remove connection_id from the queue (a player who gave up or
        disconnected). Returns whether it was queued."""
        waiting = self._find(connection_id)
        if waiting is None:
            return False
        self._queue.remove(waiting)
        return True

    def expire(self) -> list[str]:
        """Remove and return every queued connection whose wait has exceeded
        the timeout - the players the dispatcher should tell their search
        timed out. Called on the server's periodic tick."""
        now = self._now_ms()
        timed_out = [w for w in self._queue if now - w.since_ms >= self._timeout_ms]
        for waiting in timed_out:
            self._queue.remove(waiting)
        return [w.connection_id for w in timed_out]

    def _closest_within_range(self, rating: int, exclude: str) -> _Waiting | None:
        """The queued player (other than exclude) nearest in rating to rating
        and within the ELO range, or None if nobody qualifies. Excluding the
        requester stops a re-request from matching a player with themselves.
        Ties break to the longest-waiting (queue order)."""
        candidates = [
            w for w in self._queue if w.connection_id != exclude and abs(w.rating - rating) <= self._elo_range
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda w: abs(w.rating - rating))

    def _is_queued(self, connection_id: str) -> bool:
        """Whether connection_id is already waiting."""
        return self._find(connection_id) is not None

    def _find(self, connection_id: str) -> _Waiting | None:
        """The queue entry for connection_id, or None."""
        return next((w for w in self._queue if w.connection_id == connection_id), None)
