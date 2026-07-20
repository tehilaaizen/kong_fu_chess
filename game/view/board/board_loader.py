from __future__ import annotations

from view import consts
from view.geometry import BoardGeometry
from view.image_view import Img


class BoardLoader:
    """Loads the board background image and a full-window backdrop once,
    and composites a fresh canvas for each frame: the backdrop (sized to
    the whole window, so it also fills the HUD side columns and any
    letterbox margins), with the board image drawn onto it at geometry's
    origin offset. Reads from disk only once, not every frame."""

    def __init__(
        self,
        geometry: BoardGeometry,
        image_path: str = consts.BOARD_IMAGE_PATH,
        background_image_path: str = consts.BACKGROUND_IMAGE_PATH,
    ) -> None:
        self._geometry = geometry
        self._image_path = image_path
        self._background_image_path = background_image_path
        self._clean_board = self._read_board_from_disk()
        self._background = self._read_background_from_disk()

    def _read_board_from_disk(self) -> Img:
        """Load and resize the board image fresh from disk, to the
        board's own size (not the full window)."""
        return Img().read(self._image_path, size=(self._geometry.width_px, self._geometry.height_px))

    def _read_background_from_disk(self) -> Img:
        """Load and resize the backdrop fresh from disk, to the full
        window size, so it covers the board area, both HUD columns and
        the letterbox margins."""
        return Img().read(
            self._background_image_path,
            size=(self._geometry.window_width_px, self._geometry.window_height_px),
        )

    def reload(self) -> None:
        """Re-read both images from disk at geometry's current sizes -
        called after a window resize changed cell_size_px / the window
        size, so the cached backdrop and board match the new dimensions."""
        self._clean_board = self._read_board_from_disk()
        self._background = self._read_background_from_disk()

    def fresh_canvas(self) -> Img:
        """A fresh full-window canvas: an in-memory copy of the backdrop
        with an in-memory copy of the board background drawn onto it at
        geometry's origin offset - safe to draw on without mutating
        either cached original."""
        canvas = Img()
        canvas.img = self._background.img.copy()

        board_copy = Img()
        board_copy.img = self._clean_board.img.copy()
        board_copy.draw_on(canvas, self._geometry.board_origin_x, self._geometry.board_origin_y)

        return canvas
