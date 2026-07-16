from __future__ import annotations

from typing import Callable

from model.position import Position
from view.animation.animation_library import AnimationClip
from view.image_view import Img

IDLE = "idle"
MOVE = "move"
JUMP = "jump"


class PieceAnimator:
    """Tracks one specific piece's current animation state, driven by
    GameEngine's push notifications (start_motion/start_jump/start_rest)
    rather than a per-frame snapshot pull. clip_loader is injectable
    (typically AnimationLibrary.get_clip) so tests can supply fake clips
    instead of reading real asset files.

    move/jump have no local timer: they hold until the next push
    notification supersedes them (GameEngine is authoritative about
    exactly when a motion actually arrives). Only a rest state
    (long_rest/short_rest) needs its own timer, since nothing else
    notifies this class when a cooldown naturally ends - it self-expires
    after duration_ms using that state's own next_state_when_finished."""

    def __init__(self, kind: str, color: str, clip_loader: Callable[[str, str, str], AnimationClip]) -> None:
        self._kind = kind
        self._color = color
        self._clip_loader = clip_loader
        self._state = IDLE
        self._elapsed_in_state_ms = 0
        self._rest_remaining_ms: int | None = None
        self._rest_total_ms: int | None = None
        self._motion_source: Position | None = None
        self._motion_destination: Position | None = None
        self._motion_duration_ms: int = 0

    def set_kind(self, kind: str) -> None:
        """Update the piece's current kind (e.g. after pawn promotion) so
        future frames load the right clip - a no-op when unchanged."""
        self._kind = kind

    def start_motion(self, source: Position, destination: Position, duration_ms: int) -> None:
        """Push: a move just started from source to destination, taking
        duration_ms - show the move animation until superseded by the
        next push (start_rest, once it actually arrives). GameEngine is
        authoritative about exactly when the motion arrives; the local
        source/destination/duration are used only to slide the sprite
        smoothly across the board in the meantime (render_offset_cells)."""
        self._switch_to(MOVE)
        self._motion_source = source
        self._motion_destination = destination
        self._motion_duration_ms = duration_ms

    def start_jump(self) -> None:
        """Push: a jump just started - show the jump animation until
        superseded by the next push (start_rest, once it resolves)."""
        self._switch_to(JUMP)

    def start_rest(self, duration_ms: int, label: str) -> None:
        """Push: a cooldown just started (label is "long_rest" or
        "short_rest") - shows that state's clip for exactly duration_ms,
        then self-transitions to its next_state_when_finished (idle),
        since nothing else notifies this class when a cooldown ends."""
        self._switch_to(label)
        self._rest_remaining_ms = duration_ms
        self._rest_total_ms = duration_ms

    def advance_time(self, dt_ms: int) -> None:
        """Advance this piece's animation clock by dt_ms - the same
        dt_ms fed to GameEngine.wait() this frame. Only has an effect
        while in a timed rest state; move/jump/idle are untimed here."""
        self._elapsed_in_state_ms += dt_ms

        if self._rest_remaining_ms is None:
            return

        self._rest_remaining_ms -= dt_ms
        if self._rest_remaining_ms <= 0:
            next_state = self._clip_loader(self._kind, self._color, self._state).state_config.physics.next_state_when_finished
            self._switch_to(next_state)

    def current_frame(self) -> Img:
        """The frame to show right now, from the current state's clip,
        based on how long that state has been active."""
        clip = self._clip_loader(self._kind, self._color, self._state)
        return clip.frame_at(self._elapsed_in_state_ms)

    def render_offset_cells(self) -> tuple[float, float]:
        """How far (in cells, as an (row, col) fraction) this piece has
        advanced from its source toward its destination while moving -
        (0.0, 0.0) whenever it isn't in a move. Lets the renderer slide
        the sprite smoothly across the board instead of snapping it to
        the destination only on arrival. Progress is clamped to 1.0, so
        the sprite never overshoots past its destination cell if the
        view's clock momentarily leads the engine's arrival."""
        if self._state != MOVE or self._motion_source is None or self._motion_duration_ms <= 0:
            return (0.0, 0.0)

        progress = min(self._elapsed_in_state_ms / self._motion_duration_ms, 1.0)
        return (
            progress * (self._motion_destination.row - self._motion_source.row),
            progress * (self._motion_destination.col - self._motion_source.col),
        )

    def rest_fraction_remaining(self) -> float | None:
        """Fraction (1.0 -> 0.0) of this piece's cooldown still left
        while it is resting, or None when it isn't - lets the view draw a
        draining hourglass-style overlay that empties as the rest
        elapses."""
        if self._rest_remaining_ms is None or self._rest_total_ms is None:
            return None
        return max(self._rest_remaining_ms, 0) / self._rest_total_ms

    def _switch_to(self, state: str) -> None:
        """Switch to state immediately, resetting the elapsed-time clock,
        any pending rest timer, and any in-progress motion tracking."""
        self._state = state
        self._elapsed_in_state_ms = 0
        self._rest_remaining_ms = None
        self._rest_total_ms = None
        self._motion_source = None
        self._motion_destination = None
        self._motion_duration_ms = 0
