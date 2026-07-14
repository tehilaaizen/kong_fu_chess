from __future__ import annotations

from model.piece import Piece
from model.position import Position


class Jump:
    """A piece temporarily "airborne" after a jump command, until
    until_clock_ms. While airborne, an attacker arriving at this cell is
    destroyed instead of capturing the jumping piece - see
    RealTimeArbiter.advance_time."""

    def __init__(self, piece: Piece, cell: Position, until_clock_ms: int) -> None:
        self.piece = piece
        self.cell = cell
        self.until_clock_ms = until_clock_ms
