from __future__ import annotations

import json
import pathlib
from functools import lru_cache

from input.board_mapper import CELL_SIZE
from view.image_view import Img

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PIECES_ASSETS_DIR = PROJECT_ROOT / "assets" / "pieces"

FRAME_COUNT = 5


class AnimationClip:
    """One piece-state's playable animation: its sprite frames plus
    playback settings (fps, loop). Frame selection is driven purely by
    elapsed time - it knows nothing about pieces, the board, or game
    state; something else decides which state a piece is in and for how
    long."""

    def __init__(self, frames: list, frames_per_sec: int, is_loop: bool) -> None:
        """frames is an ordered list of images (frame 1 first);
        frames_per_sec/is_loop come straight from the state's config.json."""
        self._frames = frames
        self._frames_per_sec = frames_per_sec
        self._is_loop = is_loop

    def frame_at(self, elapsed_ms: int):
        """The frame to show elapsed_ms after this state began: cycles
        forever if is_loop, otherwise holds on the last frame once the
        sequence has played through once."""
        index = int(elapsed_ms / 1000 * self._frames_per_sec)
        if self._is_loop:
            index %= len(self._frames)
        else:
            index = min(index, len(self._frames) - 1)
        return self._frames[index]


@lru_cache(maxsize=None)
def load_animation_clip(kind: str, color: str, state: str) -> AnimationClip:
    """Load (and cache) the AnimationClip for one piece kind/color/state
    combination. There are only a handful of these regardless of how many
    piece instances are on the board - e.g. every white pawn shares the
    same loaded frames instead of re-reading the same files from disk."""
    folder = f"{kind}{'W' if color == 'w' else 'B'}"
    state_dir = PIECES_ASSETS_DIR / folder / "states" / state

    with open(state_dir / "config.json", encoding="utf-8") as config_file:
        config = json.load(config_file)

    frames = [
        Img().read(state_dir / "sprites" / f"{i}.png", size=(CELL_SIZE, CELL_SIZE)).to_rgba()
        for i in range(1, FRAME_COUNT + 1)
    ]

    return AnimationClip(
        frames=frames,
        frames_per_sec=config["graphics"]["frames_per_sec"],
        is_loop=config["graphics"]["is_loop"],
    )
