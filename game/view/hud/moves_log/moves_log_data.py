from __future__ import annotations

import datetime
from typing import Callable

from realtime.real_time_arbiter import ArrivalEvent

MAX_LOGGED_LINES = 10


def _now_hhmmss() -> str:
    """The current wall-clock time as HH:MM:SS - the default timestamp
    source. Injectable so tests can pin a fixed time, and so a later
    server build can swap in authoritative server time instead."""
    return datetime.datetime.now().strftime("%H:%M:%S")


class MovesLogData:
    """ArrivalObserver that keeps a running text log of every arrival (a
    move or a jump-defense), split into a separate list per color and
    most recent first - so MovesLogRenderer can draw white's moves under
    the white player and black's under the black player. This class only
    decides what each line says (including a timestamp of when the move
    landed) and how many are kept per color; the renderer decides where
    they go. The log reacts to arrivals only, so on_arrival is the single
    hook it declares."""

    def __init__(self, max_lines: int = MAX_LOGGED_LINES, now: Callable[[], str] = _now_hhmmss) -> None:
        """max_lines caps how many moves are kept per color; now supplies
        each line's timestamp (defaults to wall-clock HH:MM:SS)."""
        self._max_lines = max_lines
        self._now = now
        self._lines_by_color: dict[str, list[str]] = {"w": [], "b": []}

    def lines_for(self, color: str) -> list[str]:
        """That color's logged lines, most recent first."""
        return list(self._lines_by_color[color])

    def on_arrival(self, event: ArrivalEvent) -> None:
        """Log one timestamped line describing the arrival (including what,
        if anything, it captured) under the moving piece's color."""
        captured = f" x{event.captured_piece.kind}" if event.captured_piece is not None else ""
        source = f"({event.source.row},{event.source.col})"
        destination = f"({event.destination.row},{event.destination.col})"
        line = f"{self._now()} {event.piece.kind} {source}->{destination}{captured}"

        lines = self._lines_by_color[event.piece.color]
        lines.insert(0, line)
        del lines[self._max_lines :]
