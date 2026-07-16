from __future__ import annotations

from dataclasses import dataclass

from pieces import PIECE_TYPES, VALID_COLORS
from view.animation.animation_config_loader import AnimationConfigLoader
from view.animation.state_config import StateConfig
from view.config import ANIMATION_FRAME_COUNT, ANIMATION_STATES
from view.image_view import Img
from view.pieces.piece_loader import PieceLoader


@dataclass(frozen=True)
class AnimationClip:
    """One piece-state's playable animation: its sprite frames plus the
    state's parsed config. Frame selection is driven purely by elapsed
    time - it knows nothing about pieces, the board, or game state;
    something else (PieceAnimator) decides which state a piece is in and
    for how long."""

    frames: list[Img]
    state_config: StateConfig

    def frame_at(self, elapsed_ms: int) -> Img:
        """The frame to show elapsed_ms after this state began: cycles
        forever if the state loops, otherwise holds on the last frame
        once the sequence has played through once."""
        frames_per_sec = self.state_config.graphics.frames_per_sec
        index = int(elapsed_ms / 1000 * frames_per_sec)

        if self.state_config.graphics.is_loop:
            index %= len(self.frames)
        else:
            index = min(index, len(self.frames) - 1)

        return self.frames[index]


class AnimationLibrary:
    """Loads and caches every (kind, color, state) AnimationClip up
    front, so there is no disk I/O during normal frame-by-frame
    rendering - there are only 12 piece kind/color combinations x 5
    states regardless of how many piece instances are on the board."""

    def __init__(
        self,
        piece_loader: PieceLoader,
        config_loader: AnimationConfigLoader,
        kinds: tuple[str, ...] = tuple(PIECE_TYPES),
        colors: tuple[str, ...] = tuple(VALID_COLORS),
        states: tuple[str, ...] = ANIMATION_STATES,
        frame_count: int = ANIMATION_FRAME_COUNT,
    ) -> None:
        self._clips: dict[tuple[str, str, str], AnimationClip] = {}

        for kind in kinds:
            for color in colors:
                state_configs = config_loader.load(kind, color)
                for state in states:
                    frames = [piece_loader.load_sprite(kind, color, state, i) for i in range(1, frame_count + 1)]
                    self._clips[(kind, color, state)] = AnimationClip(frames=frames, state_config=state_configs[state])

    def get_clip(self, kind: str, color: str, state: str) -> AnimationClip:
        """The pre-loaded AnimationClip for kind/color/state."""
        return self._clips[(kind, color, state)]
