from __future__ import annotations

from model.board import Board
from model.piece import CAPTURED, Piece
from model.position import Position
from pieces import PIECE_TYPES
from pieces.piece import PieceRules
from realtime.jump import Jump
from realtime.motion import Motion

MS_PER_CELL = 1000
JUMP_DURATION_MS = 1000


class ArrivalEvent:
    """Reported by advance_time for each motion that logically arrived
    during that step, including whatever piece it captured (None for a
    move onto an empty cell) - GameEngine decides what, if anything, a
    capture means (e.g. ending the game on a king capture)."""

    def __init__(
        self, piece: Piece, source: Position, destination: Position, captured_piece: Piece | None
    ) -> None:
        self.piece = piece
        self.source = source
        self.destination = destination
        self.captured_piece = captured_piece


class RealTimeArbiter:
    """Owns active Motion objects and simulated time. Receives only
    already-validated move commands (GameEngine's job to validate first)
    and updates Board occupancy only on arrival - Board itself has no
    notion of time or motion in progress."""

    def __init__(self, board: Board, piece_rules_by_kind: dict[str, PieceRules] = PIECE_TYPES) -> None:
        """piece_rules_by_kind maps a piece kind letter to the PieceRules
        strategy consulted for post-arrival effects (e.g. pawn promotion) -
        defaults to the project-wide PIECE_TYPES registry, same as
        RuleEngine."""
        self._board = board
        self._piece_rules_by_kind = piece_rules_by_kind
        self._clock_ms = 0
        self._active_motions: list[Motion] = []
        self._airborne: list[Jump] = []

    def has_active_motion(self) -> bool:
        """Whether any motion is still travelling."""
        return len(self._active_motions) > 0

    def start_motion(self, piece: Piece, source: Position, destination: Position) -> None:
        """Begin moving piece from source to destination. Board occupancy
        is unchanged until the motion arrives."""
        duration = self._travel_time(source, destination)
        self._active_motions.append(Motion(piece, source, destination, self._clock_ms + duration))

    def is_airborne(self, position: Position) -> bool:
        """Whether some piece is currently airborne (mid-jump) at
        position. A jump expiring at exactly this clock reading still
        counts as airborne (>=, not >): ties favor the jumper, matching
        the dodge rule - an attacker arriving exactly as the jump ends is
        still destroyed. advance_time prunes truly-past jumps afterward."""
        return any(jump.cell == position and jump.until_clock_ms >= self._clock_ms for jump in self._airborne)

    def start_jump(self, piece: Piece, cell: Position) -> None:
        """Make piece (sitting at cell) briefly airborne: an attacker
        arriving at cell before the jump ends is destroyed instead of
        capturing it."""
        self._airborne.append(Jump(piece, cell, self._clock_ms + JUMP_DURATION_MS))

    def advance_time(self, ms: int) -> list[ArrivalEvent]:
        """Advance the simulated clock by ms, relocating on Board (and
        reporting) every motion whose arrival time has now passed. A piece
        already occupying the destination is captured: it is overwritten
        on Board and its own state becomes CAPTURED."""
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
            if self.is_airborne(motion.destination):
                # the airborne defender destroys the arriving attacker and stays put
                self._clear_airborne(motion.destination)
                self._board.remove_piece(motion.source)
                motion.piece.state = CAPTURED
                continue

            captured_piece = self._board.piece_at(motion.destination)
            self._board.move_piece(motion.source, motion.destination)

            if captured_piece is not None:
                captured_piece.state = CAPTURED

            self._piece_rules_by_kind[motion.piece.kind].on_piece_arrival(self._board, motion.piece)

            events.append(ArrivalEvent(motion.piece, motion.source, motion.destination, captured_piece))

        self._airborne = [jump for jump in self._airborne if jump.until_clock_ms > self._clock_ms]

        return events

    def _clear_airborne(self, cell: Position) -> None:
        """Remove the jump record for cell (it has just been resolved by
        an attacker arriving while it was still active)."""
        self._airborne = [jump for jump in self._airborne if jump.cell != cell]

    def _travel_time(self, source: Position, destination: Position) -> int:
        """Cell-step duration (not Euclidean distance): the number of king
        steps between source and destination, times MS_PER_CELL."""
        distance = max(abs(destination.row - source.row), abs(destination.col - source.col))
        return distance * MS_PER_CELL
