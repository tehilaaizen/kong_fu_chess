from model.position import Position

IDLE = "idle"
MOVING = "moving"
CAPTURED = "captured"


class Piece:
    """One specific chess piece placed on the board (not to be confused
    with pieces.piece.PieceRules, which is the shared movement-rule
    strategy for a whole kind). state is only a lifecycle flag - it holds
    no path, destination, elapsed time, or speed; those belong to
    Motion/RealTimeArbiter once real-time movement is introduced."""

    def __init__(self, id: int, color: str, kind: str, cell: Position, state: str = IDLE) -> None:
        """Create a piece with a stable id, its color ("w"/"b"), its kind
        letter ("K"/"Q"/"R"/"B"/"N"/"P"), its current cell, and its
        lifecycle state (defaults to idle)."""
        self.id = id
        self.color = color
        self.kind = kind
        self.cell = cell
        self.state = state
