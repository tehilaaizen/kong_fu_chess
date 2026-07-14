from __future__ import annotations

from model.piece import Piece


class Rest:
    """A piece currently resting (in cooldown) after a move or a jump,
    unable to move or jump again until the arbiter's clock reaches
    until_clock_ms. label identifies which cooldown produced this rest
    ("long_rest" after a normal move, "short_rest" after a jump) so a
    future renderer can pick the matching animation without RealTimeArbiter
    exposing anything beyond this record."""

    def __init__(self, piece: Piece, until_clock_ms: int, label: str) -> None:
        self.piece = piece
        self.until_clock_ms = until_clock_ms
        self.label = label
