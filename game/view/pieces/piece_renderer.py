from __future__ import annotations

from engine.game_snapshot import GameSnapshot
from view.geometry import BoardGeometry
from view.image_view import Img


class PieceRenderer:
    """Draws every piece in a GameSnapshot onto a canvas at its cell,
    using the already-resolved frame_by_piece_id (from
    PieceAnimatorRegistry.current_frames) - never resolves a frame
    itself, and never reads a sprite off disk."""

    def __init__(self, geometry: BoardGeometry) -> None:
        self._geometry = geometry

    def render(
        self,
        canvas: Img,
        snapshot: GameSnapshot,
        frame_by_piece_id: dict[int, Img],
        offset_by_piece_id: dict[int, tuple[float, float]],
    ) -> Img:
        """Draw every piece in snapshot onto canvas, in place, and return
        it for chaining. offset_by_piece_id slides a piece by a
        fractional (row, col) cell amount while it is mid-move, so it
        travels smoothly across the board instead of snapping on
        arrival - (0.0, 0.0) for a piece that isn't moving."""
        for placement in snapshot.pieces:
            sprite = frame_by_piece_id[placement.id]
            x, y = self._geometry.cell_to_pixel(placement.cell)
            row_offset, col_offset = offset_by_piece_id[placement.id]
            x += round(col_offset * self._geometry.cell_size_px)
            y += round(row_offset * self._geometry.cell_size_px)
            sprite.draw_on(canvas, x, y)

        return canvas
