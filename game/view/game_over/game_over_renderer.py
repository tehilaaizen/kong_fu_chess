from __future__ import annotations

from view import config
from view.game_over.game_over_data import GameOverData
from view.geometry import BoardGeometry
from view.image_view import Img


class GameOverRenderer:
    """Draws the full-window game-over banner once the game has ended: a
    semi-transparent dark wash over the whole window with big centered
    text on top. Purely visual - it reads game state only through the
    GameOverData observer it is handed, never touching cv2 or the engine
    directly. A no-op while the game is still going."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, game_over_data: GameOverData) -> Img:
        """Draw the banner onto canvas, in place, and return it for
        chaining - or leave canvas untouched while the game is not over."""
        if not game_over_data.is_over():
            return canvas

        window_width = self._geometry.window_width_px
        window_height = self._geometry.window_height_px
        canvas.overlay_rect(
            0, 0, window_width, window_height,
            config.GAME_OVER_OVERLAY_COLOR, config.GAME_OVER_OVERLAY_ALPHA,
        )

        text_width, text_height = canvas.text_size(
            config.GAME_OVER_TEXT, config.GAME_OVER_FONT_SIZE, config.GAME_OVER_FONT_THICKNESS
        )
        x = (window_width - text_width) // 2
        y = (window_height + text_height) // 2
        canvas.put_text(
            config.GAME_OVER_TEXT, x, y,
            config.GAME_OVER_FONT_SIZE, config.GAME_OVER_TEXT_COLOR, config.GAME_OVER_FONT_THICKNESS,
        )
        return canvas
