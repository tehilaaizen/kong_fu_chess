from __future__ import annotations

from input.commands import ClickCommand, JumpCommand
from view.geometry import BoardGeometry


class MouseCommandExtractor:
    """Classifies a raw window mouse event into a Command, or None if it
    fell outside the board's drawn rectangle (e.g. on a future HUD
    sidebar). Translates window-pixel coordinates to board-local pixel
    coordinates by subtracting geometry's origin offset -
    input/board_mapper.py itself stays origin-unaware, exactly as it is
    today; this is the only place that knows about the offset."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def extract_left_click(self, x: int, y: int) -> ClickCommand | None:
        """A left-button-down event at window pixel (x, y)."""
        board_local = self._board_local_pixel(x, y)
        return ClickCommand(*board_local) if board_local is not None else None

    def extract_right_click(self, x: int, y: int) -> JumpCommand | None:
        """A right-button-down event at window pixel (x, y)."""
        board_local = self._board_local_pixel(x, y)
        return JumpCommand(*board_local) if board_local is not None else None

    def _board_local_pixel(self, x: int, y: int) -> tuple[int, int] | None:
        """(x, y) translated to board-local pixels, or None if it falls
        outside the board's drawn rectangle."""
        local_x = x - self._geometry.board_origin_x
        local_y = y - self._geometry.board_origin_y

        if not (0 <= local_x < self._geometry.width_px and 0 <= local_y < self._geometry.height_px):
            return None

        return local_x, local_y
