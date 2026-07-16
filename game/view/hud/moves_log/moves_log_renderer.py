from __future__ import annotations

from view.geometry import BoardGeometry
from view.hud.moves_log.moves_log_data import MovesLogData
from view.image_view import Img

TEXT_MARGIN_PX = 10
FIRST_LINE_Y_PX = 100
LINE_HEIGHT_PX = 20
FONT_SIZE = 0.4
WHITE_TEXT_COLOR = (255, 255, 255, 255)


class MovesLogRenderer:
    """Draws the moves log into the left HUD column, one line per entry,
    most recent first - put_text only, never touches cv2 directly."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, moves_log_data: MovesLogData) -> Img:
        """Draw every logged line onto canvas, in place, and return it
        for chaining."""
        for index, line in enumerate(moves_log_data.lines()):
            y = FIRST_LINE_Y_PX + index * LINE_HEIGHT_PX
            canvas.put_text(line, TEXT_MARGIN_PX, y, FONT_SIZE, WHITE_TEXT_COLOR)

        return canvas
