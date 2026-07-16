from __future__ import annotations

from engine.game_snapshot import GameSnapshot
from view.image_view import Img
from view.piece_animator import PieceAnimator


class PieceAnimatorRegistry:
    """Owns one PieceAnimator per piece (by id) across frames, creating
    them as new pieces appear in a snapshot and keeping each one's
    animation state in sync with the snapshot's reported state."""

    def __init__(self) -> None:
        self._animators: dict[int, PieceAnimator] = {}

    def update(self, snapshot: GameSnapshot, now_ms: int) -> None:
        """Sync every piece in snapshot to its animator, creating one for
        any piece id seen for the first time."""
        for placement in snapshot.pieces:
            animator = self._animators.get(placement.id)
            if animator is None:
                animator = PieceAnimator(placement.kind, placement.color)
                self._animators[placement.id] = animator
            animator.set_kind(placement.kind)
            animator.set_state(placement.state, now_ms)

    def current_frames(self, snapshot: GameSnapshot, now_ms: int) -> dict[int, Img]:
        """The frame to draw right now for every piece in snapshot,
        keyed by piece id."""
        return {placement.id: self._animators[placement.id].current_frame(now_ms) for placement in snapshot.pieces}
