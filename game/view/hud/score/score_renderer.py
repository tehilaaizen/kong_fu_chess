from __future__ import annotations

from view.geometry import BoardGeometry
from view.hud.score.score_data import ScoreData
from view.image_view import Img

TEXT_MARGIN_PX = 10
SCORE_LINE_Y_PX = 60
FONT_SIZE = 0.6
WHITE_TEXT_COLOR = (255, 255, 255, 255)


class ScoreRenderer:
    """Draws each color's current score into its own HUD column - put_text
    only, never touches cv2 directly."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, score_data: ScoreData) -> Img:
        """Draw both colors' scores onto canvas, in place, and return it
        for chaining."""
        y = self._geometry.board_origin_y + SCORE_LINE_Y_PX
        canvas.put_text(
            f"Score: {score_data.score_for('w')}",
            self._geometry.left_column_x + TEXT_MARGIN_PX,
            y,
            FONT_SIZE,
            WHITE_TEXT_COLOR,
        )
        canvas.put_text(
            f"Score: {score_data.score_for('b')}",
            self._geometry.right_column_x + TEXT_MARGIN_PX,
            y,
            FONT_SIZE,
            WHITE_TEXT_COLOR,
        )
        return canvas
