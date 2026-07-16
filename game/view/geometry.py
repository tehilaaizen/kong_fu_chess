from __future__ import annotations

from dataclasses import dataclass

from input.board_mapper import CELL_SIZE
from model.position import Position
from view import config


@dataclass
class BoardGeometry:
    """Single source of truth for window/board pixel geometry, injected
    into whichever view/ components need it - replaces the ad hoc x/y
    arithmetic that used to be duplicated inline in Renderer.
    cell_size_px reuses input.board_mapper.CELL_SIZE (the only other
    place pixel size matters) rather than redefining it.

    The window is laid out as three columns: a left HUD column (player
    1), the board itself, and a right HUD column (player 2) - no
    top/bottom HUD elements, so there is only one y-axis offset."""

    width_cells: int = config.BOARD_WIDTH
    height_cells: int = config.BOARD_HEIGHT
    cell_size_px: int = CELL_SIZE
    left_column_width_px: int = config.HUD_COLUMN_WIDTH_PX
    right_column_width_px: int = config.HUD_COLUMN_WIDTH_PX
    board_origin_y: int = config.BOARD_PADDING_HEIGHT_PX

    @property
    def board_origin_x(self) -> int:
        """The board's left edge sits right after the left HUD column."""
        return self.left_column_width_px

    @property
    def width_px(self) -> int:
        """The board's own width in pixels, excluding either HUD column."""
        return self.width_cells * self.cell_size_px

    @property
    def height_px(self) -> int:
        """The board's own height in pixels."""
        return self.height_cells * self.cell_size_px

    @property
    def window_width_px(self) -> int:
        """Total window width: both HUD columns plus the board."""
        return self.left_column_width_px + self.width_px + self.right_column_width_px

    @property
    def window_height_px(self) -> int:
        """Total window height - same as the board's, since there is no
        top/bottom HUD element."""
        return self.height_px

    @property
    def right_column_x(self) -> int:
        """The x pixel where the right HUD column begins."""
        return self.left_column_width_px + self.width_px

    def cell_to_pixel(self, position: Position) -> tuple[int, int]:
        """The (x, y) pixel offset of position's top-left corner,
        including the board's origin offset within the window."""
        return (
            self.board_origin_x + position.col * self.cell_size_px,
            self.board_origin_y + position.row * self.cell_size_px,
        )
