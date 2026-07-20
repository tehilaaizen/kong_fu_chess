from __future__ import annotations

import pathlib

from input.board_mapper import CELL_SIZE
from view import consts
from view.image_view import Img


class PieceLoader:
    """Builds sprite paths and loads individual sprite images - the only
    place that knows the asset folder's Kind+Color naming convention
    (e.g. "PW"), the opposite order from the model's own Color+Kind
    convention (piece.color, piece.kind)."""

    def __init__(self, assets_root: pathlib.Path = consts.PIECES_ASSETS_DIR, cell_size: int = CELL_SIZE) -> None:
        self._assets_root = assets_root
        self._cell_size = cell_size

    def state_dir(self, kind: str, color: str, state: str) -> pathlib.Path:
        """The states/<state> directory for one piece kind/color
        combination (e.g. kind="P", color="w", state="idle")."""
        folder = f"{kind}{'W' if color == 'w' else 'B'}"
        return self._assets_root / folder / "states" / state

    def load_sprite(self, kind: str, color: str, state: str, frame_index: int) -> Img:
        """Load one sprite frame (1-indexed), resized to cell_size with a
        real alpha channel."""
        path = self.state_dir(kind, color, state) / "sprites" / f"{frame_index}.png"
        return Img().read(path, size=(self._cell_size, self._cell_size)).to_rgba()
