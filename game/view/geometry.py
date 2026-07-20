from __future__ import annotations

from dataclasses import dataclass

from input.board_mapper import CELL_SIZE
from model.position import Position
from view import consts


@dataclass
class BoardGeometry:
    """Single source of truth for window/board pixel geometry, injected
    into whichever view/ components need it - replaces the ad hoc x/y
    arithmetic that used to be duplicated inline in Renderer.
    cell_size_px reuses input.board_mapper.CELL_SIZE (the only other
    place pixel size matters) rather than redefining it.

    The window is laid out as three columns: a left HUD column (player
    1), the board itself, and a right HUD column (player 2) - no
    top/bottom HUD elements.

    Window resize is supported by scaling the whole layout uniformly
    (see fit_to_window): cell_size_px and the HUD column widths grow or
    shrink together so the board stays square, and any leftover space is
    added as centering margins (letterbox_x_px horizontally,
    board_origin_y vertically). Every pixel-position accessor already
    folds those margins in, so renderers and the mouse extractor follow a
    resize without any change of their own. At construction the margins
    are zero and window_width_px/height_px equal the board-plus-HUD
    content size, so the default geometry is unchanged."""

    width_cells: int = consts.BOARD_WIDTH
    height_cells: int = consts.BOARD_HEIGHT
    cell_size_px: int = CELL_SIZE
    left_column_width_px: int = consts.HUD_COLUMN_WIDTH_PX
    right_column_width_px: int = consts.HUD_COLUMN_WIDTH_PX
    board_origin_y: int = consts.BOARD_PADDING_HEIGHT_PX
    letterbox_x_px: int = 0
    _outer_width_px: int | None = None
    _outer_height_px: int | None = None

    @property
    def left_column_x(self) -> int:
        """The x pixel where the left HUD column begins - the horizontal
        letterbox margin, so the whole content block stays centered."""
        return self.letterbox_x_px

    @property
    def board_origin_x(self) -> int:
        """The board's left edge: the left HUD column starts after the
        letterbox margin, and the board starts after that column."""
        return self.letterbox_x_px + self.left_column_width_px

    @property
    def width_px(self) -> int:
        """The board's own width in pixels, excluding either HUD column."""
        return self.width_cells * self.cell_size_px

    @property
    def height_px(self) -> int:
        """The board's own height in pixels."""
        return self.height_cells * self.cell_size_px

    @property
    def content_width_px(self) -> int:
        """Both HUD columns plus the board - the drawn content's width,
        excluding any horizontal letterbox margin."""
        return self.left_column_width_px + self.width_px + self.right_column_width_px

    @property
    def window_width_px(self) -> int:
        """Total canvas/window width: the outer size a resize fitted us
        to, or (before any resize) exactly the content width."""
        return self._outer_width_px if self._outer_width_px is not None else self.content_width_px

    @property
    def window_height_px(self) -> int:
        """Total canvas/window height: the outer size a resize fitted us
        to, or (before any resize) exactly the board height, since there
        is no top/bottom HUD element."""
        return self._outer_height_px if self._outer_height_px is not None else self.height_px

    @property
    def right_column_x(self) -> int:
        """The x pixel where the right HUD column begins."""
        return self.board_origin_x + self.width_px

    def cell_to_pixel(self, position: Position) -> tuple[int, int]:
        """The (x, y) pixel offset of position's top-left corner,
        including the board's origin offset within the window."""
        return (
            self.board_origin_x + position.col * self.cell_size_px,
            self.board_origin_y + position.row * self.cell_size_px,
        )

    def fit_to_window(self, outer_width_px: int, outer_height_px: int) -> None:
        """Rescale the whole layout to fill a window of outer_width_px x
        outer_height_px while preserving the board's square aspect: pick
        the largest uniform scale that fits both dimensions, apply it to
        the cell size and both HUD column widths, then center the
        resulting content with letterbox margins. All pixel-position
        accessors read these fields, so callers that hold this same
        instance need no further update."""
        base_width = 2 * consts.HUD_COLUMN_WIDTH_PX + self.width_cells * CELL_SIZE
        base_height = self.height_cells * CELL_SIZE
        scale = min(outer_width_px / base_width, outer_height_px / base_height)

        self.cell_size_px = max(1, round(CELL_SIZE * scale))
        column_width = max(0, round(consts.HUD_COLUMN_WIDTH_PX * scale))
        self.left_column_width_px = column_width
        self.right_column_width_px = column_width

        self.letterbox_x_px = max(0, (outer_width_px - self.content_width_px) // 2)
        self.board_origin_y = max(0, (outer_height_px - self.height_px) // 2)
        self._outer_width_px = outer_width_px
        self._outer_height_px = outer_height_px
