from __future__ import annotations

from view.geometry import BoardGeometry
from view.hud.moves_log.moves_log_data import MovesLogData
from view.image_view import Img

TEXT_MARGIN_PX = 10
FIRST_LINE_Y_PX = 100
LINE_HEIGHT_PX = 20
FONT_SIZE = 0.4
# Black - the moves log sits over the light background image, where white
# text is unreadable.
TEXT_COLOR = (0, 0, 0, 255)


class MovesLogRenderer:
    """Draws the moves log into both HUD columns - white's moves under the
    white player (left column), black's under the black player (right
    column), one line per entry, most recent first - put_text only, never
    touches cv2 directly."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, moves_log_data: MovesLogData) -> Img:
        """Draw each color's logged lines into its own column on canvas,
        in place, and return it for chaining."""
        self._render_column(canvas, moves_log_data.lines_for("w"), self._geometry.left_column_x)
        self._render_column(canvas, moves_log_data.lines_for("b"), self._geometry.right_column_x)
        return canvas

    def _render_column(self, canvas: Img, lines: list[str], column_x: int) -> None:
        """Draw one color's lines stacked down the column starting at
        column_x, below that column's name/score header."""
        x = column_x + TEXT_MARGIN_PX
        for index, line in enumerate(lines):
            y = self._geometry.board_origin_y + FIRST_LINE_Y_PX + index * LINE_HEIGHT_PX
            canvas.put_text(line, x, y, FONT_SIZE, TEXT_COLOR)
