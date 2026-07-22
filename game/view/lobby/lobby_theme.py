from __future__ import annotations

# One place for the lobby's look and layout, so no colors/sizes are
# hard-coded inside the widgets or screens. Colors are BGR (OpenCV order).

# Window.
WINDOW_NAME = "KFChess"
WINDOW_WIDTH = 620
WINDOW_HEIGHT = 470
BACKGROUND_COLOR = (42, 42, 40)  # dark grey

# Buttons.
BUTTON_COLOR = (78, 120, 82)  # muted green
BUTTON_TEXT_COLOR = (235, 235, 225)
BUTTON_HEIGHT = 46
BUTTON_GAP = 12  # vertical space between stacked buttons

# Text fields.
FIELD_COLOR = (54, 46, 66)  # dark reddish
FIELD_TEXT_COLOR = (235, 235, 225)
FIELD_FOCUSED_BORDER_COLOR = (150, 150, 150)

# Text.
TITLE_COLOR = (245, 245, 245)
LABEL_COLOR = (210, 210, 210)
ERROR_COLOR = (90, 90, 220)  # red, for a failed login
TITLE_FONT_SIZE = 1.4
LABEL_FONT_SIZE = 0.6
BUTTON_FONT_SIZE = 0.7
