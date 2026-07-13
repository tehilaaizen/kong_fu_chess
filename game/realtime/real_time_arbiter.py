from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.motion import Motion

MS_PER_CELL = 1000


class ArrivalEvent:
    """Reported by advance_time for each motion that logically arrived
    during that step. A future iteration (captures/king-capture) extends
    this with what, if anything, was captured - request_move/wait don't
    need to change when that happens."""

    def __init__(self, piece: Piece, source: Position, destination: Position) -> None:
        self.piece = piece
        self.source = source
        self.destination = destination


class RealTimeArbiter:
    """Owns active Motion objects and simulated time. Receives only
    already-validated move commands (GameEngine's job to validate first)
    and updates Board occupancy only on arrival - Board itself has no
    notion of time or motion in progress."""

    def __init__(self, board: Board) -> None:
        self._board = board
        self._clock_ms = 0
        self._active_motions: list[Motion] = []

    def has_active_motion(self) -> bool:
        """Whether any motion is still travelling."""
        return len(self._active_motions) > 0

    def start_motion(self, piece: Piece, source: Position, destination: Position) -> None:
        """Begin moving piece from source to destination. Board occupancy
        is unchanged until the motion arrives."""
        duration = self._travel_time(source, destination)
        self._active_motions.append(Motion(piece, source, destination, self._clock_ms + duration))

    def advance_time(self, ms: int) -> list[ArrivalEvent]:
        """Advance the simulated clock by ms, relocating on Board (and
        reporting) every motion whose arrival time has now passed."""
        self._clock_ms += ms

        arrived: list[Motion] = []
        still_active: list[Motion] = []
        for motion in self._active_motions:
            if motion.arrival_clock_ms <= self._clock_ms:
                arrived.append(motion)
            else:
                still_active.append(motion)
        self._active_motions = still_active

        events: list[ArrivalEvent] = []
        for motion in arrived:
            self._board.move_piece(motion.source, motion.destination)
            events.append(ArrivalEvent(motion.piece, motion.source, motion.destination))

        return events

    def _travel_time(self, source: Position, destination: Position) -> int:
        """Cell-step duration (not Euclidean distance): the number of king
        steps between source and destination, times MS_PER_CELL."""
        distance = max(abs(destination.row - source.row), abs(destination.col - source.col))
        return distance * MS_PER_CELL
