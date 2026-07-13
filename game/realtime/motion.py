from model.piece import Piece
from model.position import Position


class Motion:
    """A piece currently travelling from source to destination, due to
    logically arrive once the arbiter's clock reaches arrival_clock_ms.
    Board occupancy does not change until then - see RealTimeArbiter."""

    def __init__(self, piece: Piece, source: Position, destination: Position, arrival_clock_ms: int) -> None:
        self.piece = piece
        self.source = source
        self.destination = destination
        self.arrival_clock_ms = arrival_clock_ms
