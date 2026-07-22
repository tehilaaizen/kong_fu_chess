from __future__ import annotations

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

BOARD_WIDTH = 8
BOARD_HEIGHT = 8

ANIMATION_STATES = ("idle", "move", "jump", "short_rest", "long_rest")
ANIMATION_FRAME_COUNT = 5

BOARD_IMAGE_PATH = str(PROJECT_ROOT / "assets" / "bord.png")
# Full-window backdrop drawn behind the board and both HUD columns
# (including the letterbox margins) - replaces a plain black fill.
BACKGROUND_IMAGE_PATH = str(PROJECT_ROOT / "assets" / "background.png")
PIECES_ASSETS_DIR = PROJECT_ROOT / "assets" / "pieces"

# Pixel offset from the window's top-left corner to the board's own
# top-left corner along the y-axis - no top/bottom HUD elements exist,
# so this stays 0. The x-axis offset comes from BoardGeometry's own
# left_column_width_px instead, since that one genuinely varies (HUD
# side columns).
BOARD_PADDING_HEIGHT_PX = 0

# HUD layout: one fixed-width column on each side of the board (left =
# player 1/white, right = player 2/black), each holding that player's
# name, score, and (left column) the moves log.
HUD_COLUMN_WIDTH_PX = 200

DEFAULT_PLAYER_NAME_BY_COLOR = {"w": "White", "b": "Black"}

# Standard chess point values, used only for scoring captures - the king
# is omitted (capturing it already ends the game via a separate win
# condition, not scored).
POINT_VALUE_BY_KIND = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9}

# Cell overlays drawn in code (no image asset - just an alpha-blended
# fill via Img.overlay_rect). Colors are BGR, alpha is 0..1.
# Highlight: the legal destinations of a selected piece
# (view/board/highlight_renderer.py).
HIGHLIGHT_COLOR = (0, 200, 0)  # green
HIGHLIGHT_ALPHA = 0.4
# Rest: a draining hourglass-style overlay on a piece in cooldown
# (view/board/rest_overlay_renderer.py) - shrinks from full to empty as
# the cooldown elapses.
REST_OVERLAY_COLOR = (0, 165, 255)  # amber
REST_OVERLAY_ALPHA = 0.5

# Game-over banner: a full-window dark wash with big centered text, drawn
# on top of everything once a king is captured
# (view/game_over/game_over_renderer.py).
GAME_OVER_TEXT = "GAME OVER"
GAME_OVER_OVERLAY_COLOR = (0, 0, 0)  # black wash
GAME_OVER_OVERLAY_ALPHA = 0.6
GAME_OVER_TEXT_COLOR = (255, 255, 255, 255)  # white
GAME_OVER_FONT_SIZE = 3.0
GAME_OVER_FONT_THICKNESS = 6

# The "connection lost" banner shown online when the link to the server
# drops mid-game (view/connection_lost_renderer.py). Reuses the game-over
# banner's dimmed-wash + centered-text look, tinted red to read as an error.
CONNECTION_LOST_TEXT = "CONNECTION LOST"
CONNECTION_LOST_OVERLAY_COLOR = (0, 0, 0)  # black wash
CONNECTION_LOST_OVERLAY_ALPHA = 0.7
CONNECTION_LOST_TEXT_COLOR = (60, 60, 255, 255)  # red (BGRA)
CONNECTION_LOST_FONT_SIZE = 2.2
CONNECTION_LOST_FONT_THICKNESS = 5
