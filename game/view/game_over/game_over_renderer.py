from __future__ import annotations

from view import consts
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
            consts.GAME_OVER_OVERLAY_COLOR, consts.GAME_OVER_OVERLAY_ALPHA,
        )

        text_width, text_height = canvas.text_size(
            consts.GAME_OVER_TEXT, consts.GAME_OVER_FONT_SIZE, consts.GAME_OVER_FONT_THICKNESS
        )
        x = (window_width - text_width) // 2
        y = (window_height + text_height) // 2
        canvas.put_text(
            consts.GAME_OVER_TEXT, x, y,
            consts.GAME_OVER_FONT_SIZE, consts.GAME_OVER_TEXT_COLOR, consts.GAME_OVER_FONT_THICKNESS,
        )
        self._draw_winner(canvas, game_over_data, window_width, y)
        return canvas

    def _draw_winner(self, canvas: Img, game_over_data: GameOverData, window_width: int, banner_y: int) -> None:
        """Draw a smaller "<name> wins!" line centered below the GAME OVER
        text, when a winner is known."""
        winner = game_over_data.winner_label()
        if winner is None:
            return
        line = f"{winner} wins!"
        text_width, _ = canvas.text_size(
            line, consts.GAME_OVER_WINNER_FONT_SIZE, consts.GAME_OVER_WINNER_FONT_THICKNESS
        )
        x = (window_width - text_width) // 2
        y = banner_y + consts.GAME_OVER_WINNER_Y_OFFSET_PX
        canvas.put_text(
            line, x, y,
            consts.GAME_OVER_WINNER_FONT_SIZE, consts.GAME_OVER_TEXT_COLOR, consts.GAME_OVER_WINNER_FONT_THICKNESS,
        )
