from __future__ import annotations

from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent

MAX_LOGGED_LINES = 10


class MovesLogData:
    """GameObserver that keeps a running text log of every arrival (a
    move or a jump-defense), most recent first - MovesLogRenderer
    decides how to draw the lines it hands out, this class only decides
    what they say and how many are kept."""

    def __init__(self, max_lines: int = MAX_LOGGED_LINES) -> None:
        self._max_lines = max_lines
        self._lines: list[str] = []

    def lines(self) -> list[str]:
        """The logged lines, most recent first."""
        return list(self._lines)

    def on_arrival(self, event: ArrivalEvent) -> None:
        """GameObserver hook: log one line describing the arrival,
        including what (if anything) it captured."""
        captured = f" x{event.captured_piece.kind}" if event.captured_piece is not None else ""
        source = f"({event.source.row},{event.source.col})"
        destination = f"({event.destination.row},{event.destination.col})"
        line = f"{event.piece.color}{event.piece.kind} {source}->{destination}{captured}"

        self._lines.insert(0, line)
        self._lines = self._lines[: self._max_lines]
