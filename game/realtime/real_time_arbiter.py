from __future__ import annotations

from model.board import Board
from model.piece import CAPTURED, Piece
from model.position import Position
from pieces import PIECE_TYPES
from pieces.piece import PieceRules
from realtime.jump import Jump
from realtime.motion import Motion
from realtime.rest import Rest

MOVE_REST_DURATION_MS = 5000
JUMP_REST_DURATION_MS = 3000
LONG_REST = "long_rest"
SHORT_REST = "short_rest"


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


class RestStartedEvent:
    """Reported by take_rest_starts for every cooldown that began during
    the most recent advance_time call - the real duration/label
    (long_rest after a move, short_rest after a jump) is otherwise
    private to RealTimeArbiter, so this is the only way a GameObserver
    (e.g. PieceAnimator) can learn how long to show the rest animation."""

    def __init__(self, piece: Piece, duration_ms: int, label: str) -> None:
        self.piece = piece
        self.duration_ms = duration_ms
        self.label = label


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
        self._resting: list[Rest] = []
        self._pending_rest_starts: list[RestStartedEvent] = []

    def has_active_motion(self) -> bool:
        """Whether any motion is still travelling."""
        return len(self._active_motions) > 0

    def is_moving(self, piece: Piece) -> bool:
        """Whether this specific piece currently has a motion in flight,
        so it can't be redirected until it arrives. Unlike
        has_active_motion(), this asks about one piece - other pieces are
        free to move at the same time (this is real-time chess)."""
        return any(motion.piece is piece for motion in self._active_motions)

    def is_resting(self, piece: Piece) -> bool:
        """Whether piece is currently in cooldown (after a move or a
        jump) and cannot move or jump again yet."""
        return any(rest.piece is piece and rest.until_clock_ms > self._clock_ms for rest in self._resting)

    def take_rest_starts(self) -> list[RestStartedEvent]:
        """Every rest that started during the most recent advance_time
        call, clearing the list so each is reported exactly once."""
        rest_starts = self._pending_rest_starts
        self._pending_rest_starts = []
        return rest_starts

    def _start_rest(self, piece: Piece, duration_ms: int, label: str) -> None:
        """Put piece into cooldown for duration_ms starting now, tagged
        with label ("long_rest"/"short_rest"), and record a
        RestStartedEvent for take_rest_starts to report."""
        self._resting.append(Rest(piece, self._clock_ms + duration_ms, label))
        self._pending_rest_starts.append(RestStartedEvent(piece, duration_ms, label))

    def start_motion(self, piece: Piece, source: Position, destination: Position) -> int:
        """Begin moving piece from source to destination. Board occupancy
        is unchanged until the motion arrives. Returns the travel
        duration in ms, as reported by piece's own PieceRules, so
        GameEngine can pass it along to on_motion_started observers."""
        duration = self._piece_rules_by_kind[piece.kind].get_arrival_duration(source, destination)
        self._active_motions.append(Motion(piece, source, destination, self._clock_ms + duration))
        return duration

    def is_airborne(self, position: Position) -> bool:
        """Whether some piece is currently airborne (mid-jump) at
        position. A jump expiring at exactly this clock reading still
        counts as airborne (>=, not >): ties favor the jumper, matching
        the dodge rule - an attacker arriving exactly as the jump ends is
        still destroyed. advance_time prunes truly-past jumps afterward."""
        return any(jump.cell == position and jump.until_clock_ms >= self._clock_ms for jump in self._airborne)

    def start_jump(self, piece: Piece, cell: Position) -> int:
        """Make piece (sitting at cell) briefly airborne: an attacker
        arriving at cell before the jump ends is destroyed instead of
        capturing it. Returns the jump duration in ms, as reported by
        piece's own PieceRules, so GameEngine can pass it along to
        on_jump_started observers."""
        duration = self._piece_rules_by_kind[piece.kind].get_jump_duration()
        self._airborne.append(Jump(piece, cell, self._clock_ms + duration))
        return duration

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
                events.append(self._resolve_airborne_defense(motion))
                continue

            captured_piece = self._board.piece_at(motion.destination)
            self._board.move_piece(motion.source, motion.destination)

            if captured_piece is not None:
                captured_piece.state = CAPTURED

            self._piece_rules_by_kind[motion.piece.kind].on_piece_arrival(self._board, motion.piece)

            self._start_rest(motion.piece, MOVE_REST_DURATION_MS, LONG_REST)
            events.append(ArrivalEvent(motion.piece, motion.source, motion.destination, captured_piece))

        still_airborne: list[Jump] = []
        for jump in self._airborne:
            if jump.until_clock_ms > self._clock_ms:
                still_airborne.append(jump)
            else:
                self._start_rest(jump.piece, JUMP_REST_DURATION_MS, SHORT_REST)
        self._airborne = still_airborne

        self._resting = [rest for rest in self._resting if rest.until_clock_ms > self._clock_ms]

        return events

    def _resolve_airborne_defense(self, motion: Motion) -> ArrivalEvent:
        """An attacker arrived at a cell whose piece is still airborne
        (mid-jump): the jumper destroys the attacker and stays put,
        surviving into its own (short) cooldown - it "used up" its jump
        just as if it had expired naturally. Reported as an ArrivalEvent
        crediting the jumper with capturing the attacker, so scoring (and
        the king-capture win condition) treat the defensive kill like any
        other capture - the jumper is both the arriving piece and the one
        left standing on the cell."""
        jumper = next(jump.piece for jump in self._airborne if jump.cell == motion.destination)
        self._clear_airborne(motion.destination)
        self._start_rest(jumper, JUMP_REST_DURATION_MS, SHORT_REST)
        self._board.remove_piece(motion.source)
        motion.piece.state = CAPTURED
        return ArrivalEvent(jumper, motion.destination, motion.destination, motion.piece)

    def _clear_airborne(self, cell: Position) -> None:
        """Remove the jump record for cell (it has just been resolved by
        an attacker arriving while it was still active)."""
        self._airborne = [jump for jump in self._airborne if jump.cell != cell]

