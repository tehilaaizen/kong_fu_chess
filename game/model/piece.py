IDLE = "idle"
MOVING = "moving"
CAPTURED = "captured"


class Piece:
    """One specific chess piece placed on the board (not to be confused
    with pieces.piece.PieceRules, which is the shared movement-rule
    strategy for a whole kind). state is only a lifecycle flag - it holds
    no path, destination, elapsed time, or speed; those belong to
    Motion/RealTimeArbiter once real-time movement is introduced."""

    def __init__(self, id, color, kind, cell, state=IDLE):
        self.id = id
        self.color = color
        self.kind = kind
        self.cell = cell
        self.state = state
