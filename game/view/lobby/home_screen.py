from __future__ import annotations

from dataclasses import dataclass

from view.image_view import Img
from view.lobby import lobby_theme as theme
from view.lobby.widgets import Button, Label, TextField

# What the home screen resolves to.
MATCHMAKING = "matchmaking"
ROOM = "room"
BACK = "back"

_ENTER_KEYS = (10, 13)

# Layout (pixels).
_LEFT = 120
_BUTTON_WIDTH = 380
_FIELD_HEIGHT = 34


@dataclass(frozen=True)
class HomeChoice:
    """What the player picked on the home screen: matchmaking, a named room
    to join (room holds the typed name), or back to the login screen."""

    kind: str
    room: str = ""


class HomeScreen:
    """The lobby menu (as in the mockup): Matchmaking, Create Room and Join
    Room over a room-name field, plus Back. Create and Join behave the same -
    both hand back the typed room name, since the server's model is that the
    first connection to name a room creates it and the second joins. Pure UI:
    it only resolves to a HomeChoice; the caller sends the matching server
    message."""

    def __init__(self, username: str) -> None:
        self._username = username
        self._matchmaking = Button("Matchmaking", _LEFT, 150, _BUTTON_WIDTH)
        self._create = Button("Create Room", _LEFT, 208, _BUTTON_WIDTH)
        self._join = Button("Join Room", _LEFT, 266, _BUTTON_WIDTH)
        self._room = TextField(_LEFT, 316, _BUTTON_WIDTH, _FIELD_HEIGHT, placeholder="room name")
        self._back = Button("Back", _LEFT, 372, 120)
        self._result: HomeChoice | None = None

    def on_click(self, x: int, y: int) -> None:
        """Route a click: start matchmaking, enter a room (if one is typed),
        focus the room field, or go back."""
        if self._matchmaking.contains(x, y):
            self._result = HomeChoice(MATCHMAKING)
        elif self._create.contains(x, y) or self._join.contains(x, y):
            self._enter_room()
        elif self._room.contains(x, y):
            self._room.focused = True
        elif self._back.contains(x, y):
            self._result = HomeChoice(BACK)

    def on_key(self, key: int) -> None:
        """Enter joins the typed room; other keys edit the room field."""
        if key in _ENTER_KEYS:
            self._enter_room()
        else:
            self._room.type_key(key)

    def result(self) -> HomeChoice | None:
        """The chosen HomeChoice once the player picked, else None."""
        return self._result

    def render(self, canvas: Img) -> None:
        """Draw the title, the logged-in line, the three action buttons, the
        room field and Back."""
        Label("KFChess", 30, 60, theme.TITLE_FONT_SIZE, theme.TITLE_COLOR).render(canvas)
        Label(f"Logged in as {self._username}", _LEFT, 120).render(canvas)
        self._matchmaking.render(canvas)
        self._create.render(canvas)
        self._join.render(canvas)
        self._room.render(canvas)
        self._back.render(canvas)

    def _enter_room(self) -> None:
        """Resolve to joining the typed room, ignoring an empty field."""
        room = self._room.text.strip()
        if room:
            self._result = HomeChoice(ROOM, room)
