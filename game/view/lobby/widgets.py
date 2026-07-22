from __future__ import annotations

from view.image_view import Img
from view.lobby import lobby_theme as theme

# Keycodes cv2.waitKey returns for editing a text field.
_BACKSPACE_KEYS = (8, 127)
_TEXT_PADDING_PX = 12


class Label:
    """A line of static text at a fixed position - a caption or heading with
    no interaction."""

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        font_size: float = theme.LABEL_FONT_SIZE,
        color: tuple[int, int, int] = theme.LABEL_COLOR,
    ) -> None:
        self.text = text
        self._x = x
        self._y = y
        self._font_size = font_size
        self._color = color

    def render(self, canvas: Img) -> None:
        """Draw the label's text onto canvas at its position."""
        canvas.put_text(self.text, self._x, self._y, self._font_size, self._color)


class Button:
    """A clickable rectangle with a centered label. Hit-testing (contains) is
    pure logic a screen uses to route a click; rendering just fills the
    rectangle and centers the label."""

    def __init__(self, label: str, x: int, y: int, width: int, height: int = theme.BUTTON_HEIGHT) -> None:
        self.label = label
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def contains(self, px: int, py: int) -> bool:
        """Whether the pixel (px, py) falls inside this button's rectangle."""
        return self._x <= px <= self._x + self._width and self._y <= py <= self._y + self._height

    def render(self, canvas: Img) -> None:
        """Fill the button and draw its label centered inside it."""
        canvas.overlay_rect(self._x, self._y, self._width, self._height, theme.BUTTON_COLOR, alpha=1.0)
        text_width, text_height = canvas.text_size(self.label, theme.BUTTON_FONT_SIZE)
        text_x = self._x + (self._width - text_width) // 2
        text_y = self._y + (self._height + text_height) // 2
        canvas.put_text(self.label, text_x, text_y, theme.BUTTON_FONT_SIZE, theme.BUTTON_TEXT_COLOR)


class TextField:
    """A single-line text input. Editing (type_key) and its displayed value
    (masked for a password) are pure logic; focus decides whether keystrokes
    reach it and whether a caret is shown. The owning screen sets focus on a
    click inside the field."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int = theme.BUTTON_HEIGHT,
        masked: bool = False,
        placeholder: str = "",
    ) -> None:
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._masked = masked
        self._placeholder = placeholder
        self._text = ""
        self.focused = False

    @property
    def text(self) -> str:
        """The raw typed text (never the masked form)."""
        return self._text

    def contains(self, px: int, py: int) -> bool:
        """Whether the pixel (px, py) falls inside this field's rectangle."""
        return self._x <= px <= self._x + self._width and self._y <= py <= self._y + self._height

    def type_key(self, key: int) -> None:
        """Apply one keystroke: backspace deletes the last character, a
        printable character is appended, anything else is ignored. A no-op
        unless the field is focused."""
        if not self.focused:
            return
        if key in _BACKSPACE_KEYS:
            self._text = self._text[:-1]
        elif 32 <= key < 127:
            self._text += chr(key)

    def display_text(self) -> str:
        """What to draw: the placeholder when empty and unfocused, otherwise
        the text (masked to bullets for a password) plus a caret when
        focused."""
        if not self._text and not self.focused:
            return self._placeholder
        shown = "*" * len(self._text) if self._masked else self._text
        return shown + "|" if self.focused else shown

    def render(self, canvas: Img) -> None:
        """Fill the field and draw its current text."""
        canvas.overlay_rect(self._x, self._y, self._width, self._height, theme.FIELD_COLOR, alpha=1.0)
        if self.focused:
            self._draw_border(canvas)
        _, text_height = canvas.text_size("Ag", theme.LABEL_FONT_SIZE)
        text_y = self._y + (self._height + text_height) // 2
        canvas.put_text(
            self.display_text(), self._x + _TEXT_PADDING_PX, text_y, theme.LABEL_FONT_SIZE, theme.FIELD_TEXT_COLOR
        )

    def _draw_border(self, canvas: Img) -> None:
        """Draw a thin frame around the field to show it has focus."""
        color = theme.FIELD_FOCUSED_BORDER_COLOR
        canvas.overlay_rect(self._x, self._y, self._width, 2, color, alpha=1.0)
        canvas.overlay_rect(self._x, self._y + self._height - 2, self._width, 2, color, alpha=1.0)
        canvas.overlay_rect(self._x, self._y, 2, self._height, color, alpha=1.0)
        canvas.overlay_rect(self._x + self._width - 2, self._y, 2, self._height, color, alpha=1.0)
