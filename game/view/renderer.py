from __future__ import annotations

import pathlib

from engine.game_snapshot import GameSnapshot
from input.board_mapper import CELL_SIZE
from text_io.board_parser import BoardParser
from view.image_view import Img

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BOARD_IMAGE_PATH = str(PROJECT_ROOT / "assets" / "bord.png")
PIECES_ASSETS_DIR = PROJECT_ROOT / "assets" / "pieces"

# A standard chess board is 8x8 cells - reuses CELL_SIZE (input/board_mapper.py)
# rather than hardcoding a second pixel size.
BOARD_SIZE_PX = 8 * CELL_SIZE

# Pixel offset from the window's top-left corner to the board's own
# top-left corner - reserved for future non-board UI (moves log, score,
# player names) drawn around the board. 0 for now, so nothing shifts yet.
# If this ever becomes non-zero, BoardMapper.pixel_to_cell needs the same
# offset to keep click mapping aligned with the drawn board.
BOARD_PADDING_PX = 0

# This state/frame is shown for every piece until real game-loop/animation
# wiring exists.
STATIC_PIECE_STATE = "idle"
STATIC_PIECE_FRAME = "1.png"


class Renderer:
    """Draws visual state from a read-only GameSnapshot using Img - never
    a live Board/Piece (see kung_fu_chess_design_guide.md §12)."""

    def __init__(self, board_image_path: str = BOARD_IMAGE_PATH, board_size_px: int = BOARD_SIZE_PX) -> None:
        """board_image_path is the file to load as the board background;
        board_size_px is the square pixel size to resize it to."""
        self._board_image_path = board_image_path
        self._board_size_px = board_size_px

    def load_board(self) -> Img:
        """Load and return the board background image resized to
        board_size_px, without opening any window - lets tests check the
        loaded image without a GUI."""
        return Img().read(self._board_image_path, size=(self._board_size_px, self._board_size_px))

    def show_board(self) -> None:
        """Load the board background and display it in a blocking window."""
        self.load_board().show()

    def render_snapshot(self, snapshot: GameSnapshot) -> Img:
        """Draw the board background plus every piece in snapshot at its
        cell, without opening any window - lets tests check the composed
        image without a GUI."""
        canvas = self.load_board()

        for placement in snapshot.pieces:
            sprite = self._load_piece_sprite(placement.kind, placement.color)
            x = BOARD_PADDING_PX + placement.cell.col * CELL_SIZE
            y = BOARD_PADDING_PX + placement.cell.row * CELL_SIZE
            sprite.draw_on(canvas, x, y)

        return canvas

    def show_snapshot(self, snapshot: GameSnapshot) -> None:
        """Render snapshot and display it in a blocking window."""
        self.render_snapshot(snapshot).show()

    def _load_piece_sprite(self, kind: str, color: str) -> Img:
        """Load the static idle sprite for a piece of kind/color, resized
        to one cell. Asset folders are named <kind><color-letter> (e.g.
        PW, RB) - the opposite order from this project's own wP/bR
        convention - so this mapping only lives here, not in the model."""
        folder = f"{kind}{'W' if color == 'w' else 'B'}"
        path = PIECES_ASSETS_DIR / folder / "states" / STATIC_PIECE_STATE / "sprites" / STATIC_PIECE_FRAME
        return Img().read(path, size=(CELL_SIZE, CELL_SIZE)).to_rgba()


# Standard chess starting position, in this project's own board notation
# (text_io/board_parser.py) - a placeholder for manual/visual demoing until
# a real GameEngine is wired into the renderer.
STARTING_POSITION_TEXT = """\
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR"""

if __name__ == "__main__":
    starting_board = BoardParser.parse(STARTING_POSITION_TEXT)
    Renderer().show_snapshot(GameSnapshot.from_board(starting_board))
