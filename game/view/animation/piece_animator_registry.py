from __future__ import annotations

from engine.game_snapshot import GameSnapshot
from model.piece import Piece
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent
from view.animation.animation_library import AnimationLibrary
from view.animation.piece_animator import PieceAnimator
from view.image_view import Img


class PieceAnimatorRegistry:
    """Owns one PieceAnimator per piece (by id), driven by GameEngine's
    push notifications (a GameObserver itself) rather than a per-frame
    snapshot pull. seed() creates idle animators for pieces that exist
    before any notification ever fires (the starting position); every
    animator it creates shares the same AnimationLibrary as its clip
    source, so sprites are loaded once at startup, not per piece."""

    def __init__(self, animation_library: AnimationLibrary) -> None:
        self._animation_library = animation_library
        self._animators: dict[int, PieceAnimator] = {}

    def seed(self, snapshot: GameSnapshot) -> None:
        """Create an idle PieceAnimator for every piece in snapshot that
        doesn't have one yet - called once at startup, before any
        GameEngine notification has fired, so pieces that haven't moved
        yet still have something to draw."""
        for placement in snapshot.pieces:
            if placement.id not in self._animators:
                self._animators[placement.id] = PieceAnimator(
                    placement.kind, placement.color, self._animation_library.get_clip
                )

    def _animator_for(self, piece: Piece) -> PieceAnimator:
        """The animator tracking piece, creating one (in idle state) if
        this is the first notification ever seen for it."""
        animator = self._animators.get(piece.id)
        if animator is None:
            animator = PieceAnimator(piece.kind, piece.color, self._animation_library.get_clip)
            self._animators[piece.id] = animator
        return animator

    def on_arrival(self, event: ArrivalEvent) -> None:
        """GameObserver hook: sync the arrived piece's kind (pawn
        promotion mutates it in place, so the animator must pick that up
        to load the right clip going forward)."""
        self._animator_for(event.piece).set_kind(event.piece.kind)

    def on_motion_started(self, piece: Piece, source: Position, destination: Position, duration_ms: int) -> None:
        """GameObserver hook: show piece's move animation."""
        self._animator_for(piece).start_motion()

    def on_jump_started(self, piece: Piece, position: Position, duration_ms: int) -> None:
        """GameObserver hook: show piece's jump animation."""
        self._animator_for(piece).start_jump()

    def on_rest_started(self, piece: Piece, duration_ms: int, label: str) -> None:
        """GameObserver hook: show piece's cooldown animation for
        duration_ms."""
        self._animator_for(piece).start_rest(duration_ms, label)

    def on_game_over(self) -> None:
        """GameObserver hook: no animation reaction to game-over today."""
        return None

    def advance_time(self, dt_ms: int) -> None:
        """Advance every tracked piece's animation clock by dt_ms - the
        same dt_ms fed to GameEngine.wait() this frame. Not itself a
        GameObserver hook - called directly by the render loop, once per
        frame, alongside wait()."""
        for animator in self._animators.values():
            animator.advance_time(dt_ms)

    def current_frames(self, snapshot: GameSnapshot) -> dict[int, Img]:
        """The frame to draw right now for every piece in snapshot,
        keyed by piece id."""
        return {placement.id: self._animators[placement.id].current_frame() for placement in snapshot.pieces}
