from __future__ import annotations

from model.position import Position
from view import config
from view.geometry import BoardGeometry
from view.image_view import Img


class HighlightRenderer:
    """Draws a semi-transparent colored square over every cell a selected
    piece can currently move to. Purely visual: it reads no game state
    itself - GameWindow passes it the already-computed set of cells (from
    GameEngine.legal_destinations)."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, cells: set[Position]) -> Img:
        """Tint each cell in cells onto canvas, in place, and return it
        for chaining."""
        for cell in cells:
            x, y = self._geometry.cell_to_pixel(cell)
            canvas.overlay_rect(
                x, y,
                self._geometry.cell_size_px, self._geometry.cell_size_px,
                config.HIGHLIGHT_COLOR, config.HIGHLIGHT_ALPHA,
            )
        return canvas
