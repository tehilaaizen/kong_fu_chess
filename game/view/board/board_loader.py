from __future__ import annotations

import numpy as np

from view import consts
from view.geometry import BoardGeometry
from view.image_view import Img


class BoardLoader:
    """Loads the board background image once, resized to the board's own
    pixel dimensions, and composites a fresh full-window canvas for each
    frame: a blank (black) background sized to the whole window (board
    plus both HUD side columns), with the board image drawn onto it at
    geometry's origin offset. Reads from disk only once, not every frame."""

    def __init__(self, geometry: BoardGeometry, image_path: str = consts.BOARD_IMAGE_PATH) -> None:
        self._geometry = geometry
        self._image_path = image_path
        self._clean_board = self._read_from_disk()

    def _read_from_disk(self) -> Img:
        """Load and resize the board image fresh from disk, to the
        board's own size (not the full window)."""
        return Img().read(self._image_path, size=(self._geometry.width_px, self._geometry.height_px))

    def reload(self) -> None:
        """Re-read the board image from disk at geometry's current board
        size - called after a window resize changed cell_size_px, so the
        cached background matches the new board dimensions."""
        self._clean_board = self._read_from_disk()

    def fresh_canvas(self) -> Img:
        """A fresh full-window canvas: blank HUD columns either side of
        an in-memory copy of the loaded board background, positioned at
        geometry's origin offset - safe to draw on without mutating the
        cached original."""
        canvas = Img()
        canvas.img = np.zeros(
            (self._geometry.window_height_px, self._geometry.window_width_px, self._clean_board.img.shape[2]),
            dtype=self._clean_board.img.dtype,
        )

        board_copy = Img()
        board_copy.img = self._clean_board.img.copy()
        board_copy.draw_on(canvas, self._geometry.board_origin_x, self._geometry.board_origin_y)

        return canvas
