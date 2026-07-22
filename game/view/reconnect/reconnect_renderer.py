from __future__ import annotations

from view import consts
from view.geometry import BoardGeometry
from view.image_view import Img


class ReconnectRenderer:
    """Draws the "opponent left - waiting for them to reconnect" overlay on
    the remaining player's window: a dark wash with a message and a big
    countdown of the seconds left, so the frozen board reads as "on hold, they
    might come back" rather than broken. Purely visual - it is handed the
    reconnect status each frame (opponent name + seconds, or None). A no-op
    while the game is running (and so always in offline play)."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, status: tuple[str, int] | None) -> Img:
        """Draw the overlay onto canvas, in place, and return it - or leave
        canvas untouched when status is None (nobody is mid-reconnect)."""
        if status is None:
            return canvas

        name, seconds = status
        window_width = self._geometry.window_width_px
        window_height = self._geometry.window_height_px
        canvas.overlay_rect(
            0, 0, window_width, window_height,
            consts.RECONNECT_OVERLAY_COLOR, consts.RECONNECT_OVERLAY_ALPHA,
        )

        message = f"{name} left - waiting to reconnect"
        message_y = window_height // 2
        self._centered(canvas, message, window_width, message_y,
                       consts.RECONNECT_MESSAGE_FONT_SIZE, consts.RECONNECT_MESSAGE_FONT_THICKNESS)
        self._centered(canvas, str(seconds), window_width, message_y + consts.RECONNECT_COUNTDOWN_Y_OFFSET_PX,
                       consts.RECONNECT_COUNTDOWN_FONT_SIZE, consts.RECONNECT_COUNTDOWN_FONT_THICKNESS)
        return canvas

    def _centered(self, canvas: Img, text: str, window_width: int, y: int, font_size: float, thickness: int) -> None:
        """Draw text horizontally centered at vertical position y."""
        text_width, _ = canvas.text_size(text, font_size, thickness)
        x = (window_width - text_width) // 2
        canvas.put_text(text, x, y, font_size, consts.RECONNECT_TEXT_COLOR, thickness)
