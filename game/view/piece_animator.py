from __future__ import annotations

from typing import Callable

from view.animation_clip import AnimationClip, load_animation_clip
from view.image_view import Img

IDLE = "idle"


class PieceAnimator:
    """Tracks one specific piece's current animation state and when it
    started, so it can pick the right frame as time passes. clip_loader
    is injectable (defaults to load_animation_clip) so tests can supply
    fake clips instead of reading real asset files."""

    def __init__(self, kind: str, color: str, clip_loader: Callable[[str, str, str], AnimationClip] = load_animation_clip) -> None:
        self._kind = kind
        self._color = color
        self._clip_loader = clip_loader
        self._state = IDLE
        self._state_started_at_ms = 0

    def set_kind(self, kind: str) -> None:
        """Update the piece's current kind (e.g. after pawn promotion) so
        future frames load the right clip - a no-op when unchanged."""
        self._kind = kind

    def set_state(self, state: str, now_ms: int) -> None:
        """Switch to state if it's different from the current one - the
        new state's animation starts immediately, from its first frame,
        at now_ms. Calling this with the same state again is a no-op:
        the animation keeps running from when it actually started."""
        if state != self._state:
            self._state = state
            self._state_started_at_ms = now_ms

    def current_frame(self, now_ms: int) -> Img:
        """The frame to show right now, from the current state's clip,
        based on how long that state has been active."""
        clip = self._clip_loader(self._kind, self._color, self._state)
        return clip.frame_at(now_ms - self._state_started_at_ms)
