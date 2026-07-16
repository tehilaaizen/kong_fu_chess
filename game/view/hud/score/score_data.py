from __future__ import annotations

from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent
from view.config import POINT_VALUE_BY_KIND


class ScoreData:
    """GameObserver that accumulates each color's score by the point
    value of every piece it captures - registered directly with
    GameEngine, exactly like PieceAnimatorRegistry. Captures are read
    straight off ArrivalEvent.captured_piece, the same field GameEngine
    itself already keys off for the king-capture win condition; there is
    no separate "on_capture" notification."""

    def __init__(self, point_value_by_kind: dict[str, int] = POINT_VALUE_BY_KIND) -> None:
        self._point_value_by_kind = point_value_by_kind
        self._score_by_color: dict[str, int] = {"w": 0, "b": 0}

    def score_for(self, color: str) -> int:
        """color's accumulated score so far."""
        return self._score_by_color[color]

    def on_arrival(self, event: ArrivalEvent) -> None:
        """GameObserver hook: credit the arriving piece's color with the
        captured piece's point value, if any."""
        if event.captured_piece is None:
            return

        points = self._point_value_by_kind.get(event.captured_piece.kind, 0)
        self._score_by_color[event.piece.color] += points

    def on_motion_started(self, piece: Piece, source: Position, destination: Position, duration_ms: int) -> None:
        """GameObserver hook: scoring only reacts to arrivals."""
        return None

    def on_jump_started(self, piece: Piece, position: Position, duration_ms: int) -> None:
        """GameObserver hook: scoring only reacts to arrivals."""
        return None

    def on_rest_started(self, piece: Piece, duration_ms: int, label: str) -> None:
        """GameObserver hook: scoring only reacts to arrivals."""
        return None

    def on_game_over(self) -> None:
        """GameObserver hook: scoring only reacts to arrivals."""
        return None
