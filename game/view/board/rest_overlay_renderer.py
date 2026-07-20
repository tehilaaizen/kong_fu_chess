from __future__ import annotations

from model.position import Position
from view import consts
from view.geometry import BoardGeometry
from view.image_view import Img


class RestOverlayRenderer:
    """Draws a draining hourglass-style overlay on each resting piece's
    cell: a semi-transparent square whose height shrinks from full to
    empty as the cooldown elapses (fraction 1.0 -> 0.0), anchored at the
    cell's bottom so it appears to 'drain' downward like sand in an
    hourglass. Purely visual: it reads no game state itself - GameWindow
    passes it the already-computed (cell, fraction_remaining) pairs (from
    PieceAnimatorRegistry.resting_overlays)."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(self, canvas: Img, overlays: list[tuple[Position, float]]) -> Img:
        """Draw each (cell, fraction_remaining) overlay onto canvas, in
        place, and return it for chaining. A fraction of 0.0 draws
        nothing (Img.overlay_rect no-ops on a zero-height rect)."""
        cell_size = self._geometry.cell_size_px
        for cell, fraction in overlays:
            x, y = self._geometry.cell_to_pixel(cell)
            covered = round(cell_size * fraction)
            canvas.overlay_rect(
                x, y + (cell_size - covered),
                cell_size, covered,
                consts.REST_OVERLAY_COLOR, consts.REST_OVERLAY_ALPHA,
            )
        return canvas
