from __future__ import annotations

from view.config import DEFAULT_PLAYER_NAME_BY_COLOR
from view.geometry import BoardGeometry
from view.image_view import Img

TEXT_MARGIN_PX = 10
NAME_LINE_Y_PX = 30
FONT_SIZE = 0.6
WHITE_TEXT_COLOR = (255, 255, 255, 255)


class PlayerPanelRenderer:
    """Draws each color's player name into its own HUD column - a fixed
    label, not a GameObserver, since names never change during a game.
    name_by_color is injectable so a future real name-entry flow (or
    just different defaults) doesn't require touching this class."""

    def __init__(self, geometry: BoardGeometry, name_by_color: dict[str, str] = DEFAULT_PLAYER_NAME_BY_COLOR) -> None:
        self._geometry = geometry
        self._name_by_color = name_by_color

    def render(self, canvas: Img) -> Img:
        """Draw both colors' player names onto canvas, in place, and
        return it for chaining."""
        canvas.put_text(self._name_by_color["w"], TEXT_MARGIN_PX, NAME_LINE_Y_PX, FONT_SIZE, WHITE_TEXT_COLOR)
        canvas.put_text(
            self._name_by_color["b"],
            self._geometry.right_column_x + TEXT_MARGIN_PX,
            NAME_LINE_Y_PX,
            FONT_SIZE,
            WHITE_TEXT_COLOR,
        )
        return canvas
