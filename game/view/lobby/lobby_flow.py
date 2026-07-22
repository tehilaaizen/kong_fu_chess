from __future__ import annotations

import time

from client import client_messages
from client.server_connection import ServerConnection
from view.lobby.home_screen import BACK, MATCHMAKING, HomeScreen
from view.lobby.login_screen import Authenticate, LoginScreen
from view.lobby.screen import run_screen
from view.lobby.waiting_screen import LOST, STARTED, WaitOutcome, WaitingScreen

# After login, how long (and how often) to watch for an auto-restore before
# giving up and showing the menu. Short - a restore's messages arrive right
# after auth_ok.
_RESTORE_WINDOW_SECONDS = 0.8
_RESTORE_POLL_SECONDS = 0.02


def run_lobby(connection: ServerConnection, authenticate: Authenticate) -> WaitOutcome | None:
    """Drive the whole graphical lobby over an open connection: log in, pick
    matchmaking or a room on the home menu, then wait for the game to start.
    Returns the STARTED WaitOutcome (opening snapshot + HUD names) for the
    caller to hand to the game window, a LOST outcome if the connection
    dropped, or None if the player quit. Back on the home menu returns to
    login; a matchmaking timeout returns to the menu to try again. The lobby
    only sends the same find_match / join_room messages the CLI does - it
    starts no game itself."""
    while True:  # login screen, re-shown after Back
        username = run_screen(LoginScreen(authenticate))
        if username is None:
            return None

        restored = await_restore(connection)
        if restored is not None:
            return restored  # the server put us straight back into a game we left

        while True:  # home menu, re-shown after a matchmaking timeout
            choice = run_screen(HomeScreen(username))
            if choice is None:
                return None
            if choice.kind == BACK:
                break

            message = _request_game(connection, choice)
            outcome = run_screen(WaitingScreen(connection, message))
            if outcome is None:
                return None
            if outcome.reason in (STARTED, LOST):
                return outcome
            # a matchmaking timeout: fall through to re-show the home menu


def await_restore(connection: ServerConnection) -> WaitOutcome | None:
    """Right after login, briefly watch for the server dropping a
    reconnecting player straight back into the game they left (it sends a
    game_started + opening snapshot, just like starting a game). Returns the
    STARTED WaitOutcome if that arrives within the short window, or None for a
    normal login (then the caller shows the menu). Reuses WaitingScreen's
    message-consuming; only the timeout loop is here."""
    screen = WaitingScreen(connection)
    deadline = time.monotonic() + _RESTORE_WINDOW_SECONDS
    while time.monotonic() < deadline:
        outcome = screen.result()
        if outcome is not None:
            return outcome if outcome.reason == STARTED else None
        time.sleep(_RESTORE_POLL_SECONDS)
    return None


def _request_game(connection: ServerConnection, choice) -> str:
    """Send the server the message for this choice (find_match or join_room)
    and return the status line to show while waiting."""
    if choice.kind == MATCHMAKING:
        connection.send(client_messages.find_match())
        return "Searching for an opponent of similar rating..."
    connection.send(client_messages.join_room(choice.room))
    return f"Waiting in room '{choice.room}'..."
