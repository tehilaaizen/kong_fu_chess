from __future__ import annotations

from dataclasses import dataclass

from client.network_game_adapter import decode_snapshot, player_names_from_started
from client.server_connection import ServerConnection
from engine.game_snapshot import GameSnapshot
from view.consts import DEFAULT_PLAYER_NAME_BY_COLOR
from view.image_view import Img
from view.lobby import lobby_theme as theme
from view.lobby.widgets import Label

# Why the wait ended.
STARTED = "started"
TIMEOUT = "timeout"
LOST = "lost"


@dataclass(frozen=True)
class WaitOutcome:
    """How the wait for a game resolved: STARTED (with the opening snapshot
    and the two players' HUD names), TIMEOUT (matchmaking found nobody), or
    LOST (the connection dropped)."""

    reason: str
    snapshot: GameSnapshot | None = None
    names: dict[str, str] | None = None


class WaitingScreen:
    """Shown after the player chose matchmaking or a room, until the server
    starts the game. Each frame it drains the connection: game_started names
    the players, the state_snapshot that follows is the opening board (STARTED),
    a match_timeout ends the search (TIMEOUT), and a dropped connection ends
    it too (LOST). The message-consuming logic is unit-tested with a fake
    connection; only the drawing needs the window."""

    def __init__(self, connection: ServerConnection, message: str = "Waiting for an opponent...") -> None:
        self._connection = connection
        self._message = message
        self._names = dict(DEFAULT_PLAYER_NAME_BY_COLOR)
        self._result: WaitOutcome | None = None

    def on_click(self, x: int, y: int) -> None:
        """No controls on this screen."""

    def on_key(self, key: int) -> None:
        """No controls on this screen."""

    def result(self) -> WaitOutcome | None:
        """Drain any server messages and report the outcome once the wait has
        resolved, else None. Polling here means it advances every frame the
        runner asks whether the screen is done."""
        self._poll()
        return self._result

    def render(self, canvas: Img) -> None:
        """Draw the title and a centered status message."""
        Label("KFChess", 30, 60, theme.TITLE_FONT_SIZE, theme.TITLE_COLOR).render(canvas)
        text_width, _ = canvas.text_size(self._message, theme.LABEL_FONT_SIZE)
        x = (theme.WINDOW_WIDTH - text_width) // 2
        Label(self._message, x, theme.WINDOW_HEIGHT // 2).render(canvas)

    def _poll(self) -> None:
        """Consume server messages until the wait resolves; a closed
        connection resolves it as LOST."""
        if self._result is not None:
            return
        if self._connection.is_closed():
            self._result = WaitOutcome(LOST, names=self._names)
            return
        for message in self._connection.poll():
            self._consume(message)

    def _consume(self, message: dict) -> None:
        """Apply one server message: remember the players, finish on the
        opening snapshot, or finish on a matchmaking timeout."""
        message_type = message["type"]
        if message_type == "game_started":
            self._names = player_names_from_started(message["payload"])
        elif message_type == "state_snapshot":
            self._result = WaitOutcome(STARTED, snapshot=decode_snapshot(message["payload"]), names=self._names)
        elif message_type == "match_timeout":
            self._result = WaitOutcome(TIMEOUT, names=self._names)
