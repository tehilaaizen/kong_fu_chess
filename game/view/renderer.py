from __future__ import annotations

import pathlib

from view.image_view import Img

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BOARD_IMAGE_PATH = str(PROJECT_ROOT / "assets" / "bord.png")

# 8 cells x CELL_SIZE (see input/board_mapper.py) - keeps the on-screen
# board pixel-aligned with click-to-cell mapping, regardless of the
# source asset's own resolution.
BOARD_SIZE_PX = 800


class Renderer:
    """Draws visual state using Img. This first slice only shows the
    board background - drawing pieces from a GameSnapshot comes once
    that layer exists."""

    def __init__(self, board_image_path: str = BOARD_IMAGE_PATH, board_size_px: int = BOARD_SIZE_PX) -> None:
        """board_image_path is the file to load as the board background;
        board_size_px is the square pixel size to resize it to."""
        self._board_image_path = board_image_path
        self._board_size_px = board_size_px

    def load_board(self) -> Img:
        """Load and return the board background image resized to
        board_size_px, without opening any window - lets tests check the
        loaded image without a GUI."""
        return Img().read(self._board_image_path, size=(self._board_size_px, self._board_size_px))

    def show_board(self) -> None:
        """Load the board background and display it in a blocking window."""
        self.load_board().show()


if __name__ == "__main__":
    Renderer().show_board()
