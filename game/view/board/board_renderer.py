from __future__ import annotations

from view.board.board_loader import BoardLoader
from view.image_view import Img


class BoardRenderer:
    """Draws just the board background onto a fresh canvas each frame -
    no piece-drawing here, that's PieceRenderer's job
    (view/pieces/piece_renderer.py)."""

    def __init__(self, board_loader: BoardLoader) -> None:
        self._board_loader = board_loader

    def render(self) -> Img:
        """A fresh canvas with the board background drawn on it."""
        return self._board_loader.fresh_canvas()
