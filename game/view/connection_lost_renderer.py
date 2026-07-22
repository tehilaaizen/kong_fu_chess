from __future__ import annotations

from view import consts
from view.geometry import BoardGeometry
from view.image_view import Img


class ConnectionLostRenderer:
    """Draws a full-window "connection lost" banner when the online link to
    the server has dropped mid-game: a dark wash over the whole window with
    big centered red text, so the player sees why the board stopped updating
    instead of staring at a frozen game. Purely visual - it decides nothing,
    it is simply told each frame whether the connection is lost. A no-op
    while still connected (and so always a no-op in offline play)."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, connection_lost: bool) -> Img:
        """Draw the banner onto canvas, in place, and return it for
        chaining - or leave canvas untouched while still connected."""
        if not connection_lost:
            return canvas

        window_width = self._geometry.window_width_px
        window_height = self._geometry.window_height_px
        canvas.overlay_rect(
            0, 0, window_width, window_height,
            consts.CONNECTION_LOST_OVERLAY_COLOR, consts.CONNECTION_LOST_OVERLAY_ALPHA,
        )

        text_width, text_height = canvas.text_size(
            consts.CONNECTION_LOST_TEXT, consts.CONNECTION_LOST_FONT_SIZE, consts.CONNECTION_LOST_FONT_THICKNESS
        )
        x = (window_width - text_width) // 2
        y = (window_height + text_height) // 2
        canvas.put_text(
            consts.CONNECTION_LOST_TEXT, x, y,
            consts.CONNECTION_LOST_FONT_SIZE, consts.CONNECTION_LOST_TEXT_COLOR, consts.CONNECTION_LOST_FONT_THICKNESS,
        )
        return canvas
