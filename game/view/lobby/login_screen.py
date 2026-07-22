from __future__ import annotations

from typing import Callable

from view.image_view import Img
from view.lobby import lobby_theme as theme
from view.lobby.widgets import Button, Label, TextField

# Keys.
_ENTER_KEYS = (10, 13)
_TAB_KEY = 9

# Layout (pixels within the lobby window).
_MARGIN = 60
_FIELD_WIDTH = theme.WINDOW_WIDTH - 2 * _MARGIN

# The injected login attempt: given username+password, returns None on
# success or a short error message to show (e.g. "wrong password").
Authenticate = Callable[[str, str], str | None]


class LoginScreen:
    """The first lobby screen: a username field, a masked password field, and
    a Login button. Submitting (the button or Enter) calls the injected
    authenticate; on success the screen finishes and yields the username, and
    on failure it shows the returned message and stays. Kept free of any
    network itself - authenticate is where the real handshake lives - so its
    behaviour is unit-tested with a fake."""

    def __init__(self, authenticate: Authenticate) -> None:
        self._authenticate = authenticate
        self._username = TextField(_MARGIN, 165, _FIELD_WIDTH, placeholder="username")
        self._password = TextField(_MARGIN, 260, _FIELD_WIDTH, masked=True, placeholder="password")
        self._login_button = Button("Login", _MARGIN, 340, _FIELD_WIDTH)
        self._username.focused = True
        self._error = ""
        self._result: str | None = None

    def on_click(self, x: int, y: int) -> None:
        """Focus a clicked field, or submit if the Login button was clicked."""
        if self._username.contains(x, y):
            self._focus(self._username)
        elif self._password.contains(x, y):
            self._focus(self._password)
        elif self._login_button.contains(x, y):
            self._submit()

    def on_key(self, key: int) -> None:
        """Enter submits; Tab moves between the fields; anything else is a
        keystroke for whichever field is focused."""
        if key in _ENTER_KEYS:
            self._submit()
        elif key == _TAB_KEY:
            self._focus(self._password if self._username.focused else self._username)
        else:
            self._username.type_key(key)
            self._password.type_key(key)

    def result(self) -> str | None:
        """The authenticated username once login succeeded, else None."""
        return self._result

    def render(self, canvas: Img) -> None:
        """Draw the title, both fields with captions, the button, and any
        error message."""
        Label("KFChess", 30, 60, theme.TITLE_FONT_SIZE, theme.TITLE_COLOR).render(canvas)
        Label("Username", _MARGIN, 150).render(canvas)
        Label("Password", _MARGIN, 245).render(canvas)
        self._username.render(canvas)
        self._password.render(canvas)
        self._login_button.render(canvas)
        if self._error:
            Label(self._error, _MARGIN, 410, theme.LABEL_FONT_SIZE, theme.ERROR_COLOR).render(canvas)

    def _submit(self) -> None:
        """Try to authenticate; finish with the username on success, or show
        the error and stay on the screen."""
        username = self._username.text
        if not username or not self._password.text:
            self._error = "enter a username and password"
            return
        error = self._authenticate(username, self._password.text)
        if error is None:
            self._result = username
        else:
            self._error = error

    def _focus(self, field: TextField) -> None:
        """Give keyboard focus to field, taking it from the other."""
        self._username.focused = field is self._username
        self._password.focused = field is self._password
