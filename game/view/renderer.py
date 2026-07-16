from __future__ import annotations

import pathlib

from engine.game_snapshot import GameSnapshot
from input.board_mapper import CELL_SIZE
from view.image_view import Img

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BOARD_IMAGE_PATH = str(PROJECT_ROOT / "assets" / "bord.png")

BOARD_HEIGHT = 8
BOARD_WIDTH = 8
BOARD_HEIGHT_PX = BOARD_HEIGHT * CELL_SIZE
BOARD_WIDTH_PX = BOARD_WIDTH * CELL_SIZE

# Pixel offset from the window's top-left corner to the board's own
# top-left corner - reserved for future non-board UI (moves log, score,
# player names) drawn around the board. 0 for now, so nothing shifts yet.
# If this ever becomes non-zero, BoardMapper.pixel_to_cell needs the same
# offset to keep click mapping aligned with the drawn board.
BOARD_PADDING_WIDTH_PX = 0
BOARD_PADDING_HEIGHT_PX = 0


class Renderer:
    """Draws visual state from a read-only GameSnapshot using Img - never
    a live Board/Piece (see kung_fu_chess_design_guide.md §12). Knows
    nothing about animation timing - it draws whatever frame it's handed
    for each piece; PieceAnimatorRegistry decides what that frame is."""

    def __init__(self, board_image_path: str = BOARD_IMAGE_PATH, board_height_px: int = BOARD_HEIGHT_PX, board_width_px: int = BOARD_WIDTH_PX) -> None:
        """board_image_path is the file to load as the board background;
        board_height_px and board_width_px are the pixel dimensions to resize it to."""
        self._board_image_path = board_image_path
        self._board_height_px = board_height_px
        self._board_width_px = board_width_px

    def load_board(self) -> Img:
        """Load and return the board background image resized to
        board_height_px/board_width_px, without opening any window - lets
        tests check the loaded image without a GUI."""
        return Img().read(self._board_image_path, size=(self._board_width_px, self._board_height_px))

    def show_board(self) -> None:
        """Load the board background and display it in a blocking window."""
        self.load_board().show()

    def render_snapshot(self, snapshot: GameSnapshot, frame_by_piece_id: dict[int, Img]) -> Img:
        """Draw the board background plus every piece in snapshot at its
        cell, using the already-resolved frame_by_piece_id (from
        PieceAnimatorRegistry.current_frames), without opening any window
        - lets tests check the composed image without a GUI."""
        canvas = self.load_board()

        for placement in snapshot.pieces:
            sprite = frame_by_piece_id[placement.id]
            x = BOARD_PADDING_WIDTH_PX + placement.cell.col * CELL_SIZE
            y = BOARD_PADDING_HEIGHT_PX + placement.cell.row * CELL_SIZE
            sprite.draw_on(canvas, x, y)

        return canvas

    def show_snapshot(self, snapshot: GameSnapshot, frame_by_piece_id: dict[int, Img]) -> None:
        """Render snapshot and display it in a blocking window."""
        self.render_snapshot(snapshot, frame_by_piece_id).show()
