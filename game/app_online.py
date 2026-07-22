# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import sys
import time

from app_support import build_game_window
from client import client_messages
from client.network_commands import NetworkCommands
from client.network_game_adapter import NetworkGameAdapter, decode_snapshot, player_names_from_started
from client.server_event_dispatcher import ServerEventDispatcher
from client.websocket_connection import WebSocketConnection
from engine.game_snapshot import GameSnapshot
from input.board_mapper import BoardMapper
from input.controller import Controller
from model.board import Board
from rules.rule_engine import RuleEngine
from view.consts import DEFAULT_PLAYER_NAME_BY_COLOR
from view.lobby.lobby_flow import await_restore, run_lobby
from view.lobby.waiting_screen import STARTED

DEFAULT_SERVER_URI = "ws://localhost:8765"
# How long to nap between polls while waiting for the game to start. Real
# wall-clock sleep is fine here - this is an application entry point, not a
# test (the no-real-sleep rule applies to tests).
HANDSHAKE_POLL_SECONDS = 0.05


def main_gui(uri: str = DEFAULT_SERVER_URI) -> None:
    """Graphical entry point: open the window first, then run the lobby
    (login -> home menu -> matchmaking/room), and hand off to the game window
    once a game starts. The whole flow is driven by clicks and typing in the
    window, so no username/room is needed on the command line."""
    print(f"Connecting to {uri}...")
    connection = WebSocketConnection()
    connection.start(uri)
    if connection.is_closed():
        print(f"Could not reach the server at {uri}. Is it running?")
        return

    outcome = run_lobby(connection, lambda username, password: _login_or_register(connection, username, password))
    if outcome is None:
        return  # the player quit the lobby
    if outcome.reason != STARTED:
        print("Connection to the server was lost.")
        return
    _play(connection, outcome.snapshot, outcome.names)


def main(username: str, password: str, room: str, uri: str = DEFAULT_SERVER_URI, matchmake: bool = False) -> None:
    """Command-line entry point: authenticate as username, then either join
    the room named room or (when matchmake is True) search for an ELO-matched
    opponent, wait for the game to start, and drive the same interactive
    window as offline play - but from a NetworkGameAdapter, so the server owns
    state and time. A terminal alternative to the graphical main_gui."""
    where = "matchmaking" if matchmake else f"room '{room}'"
    print(f"Connecting to {uri} as '{username}', {where}...")
    connection = WebSocketConnection()
    connection.start(uri)
    if connection.is_closed():
        print(f"Could not reach the server at {uri}. Is it running?")
        return

    error = _login_or_register(connection, username, password)
    if error is not None:
        print(f"Login failed: {error}.")
        return
    print(f"Logged in as '{username}'.")

    restored = await_restore(connection)
    if restored is not None:
        print("Rejoining your game in progress...")
        _play(connection, restored.snapshot, restored.names)
        return

    if matchmake:
        connection.send(client_messages.find_match())
        print("Searching for an opponent of similar rating (leave this running)...")
    else:
        connection.send(client_messages.join_room(room))
        print("Waiting for the game to start (leave this running)...")

    initial_snapshot, player_names = _await_game_start(connection)
    if initial_snapshot is None:
        if connection.is_closed():
            print("Connection to the server was lost before the game started.")
        else:
            print("No opponent of similar rating was found - the search timed out. Try again.")
        return
    print("Game starting - opening the board...")
    _play(connection, initial_snapshot, player_names)


def _play(connection: WebSocketConnection, initial_snapshot: GameSnapshot, player_names: dict[str, str]) -> None:
    """Build the online game stack around initial_snapshot and run the window
    until the player quits - shared by the graphical and command-line paths."""
    board = Board(initial_snapshot.board_width, initial_snapshot.board_height)
    board_mapper = BoardMapper(board)
    rule_engine = RuleEngine()
    commands = NetworkCommands(connection, board)
    controller = Controller(board, board_mapper, commands)
    dispatcher = ServerEventDispatcher()
    client = NetworkGameAdapter(connection, controller, board, rule_engine, dispatcher, initial_snapshot)

    window = build_game_window(client, board_mapper, player_names)
    window.run()


def _login_or_register(connection: WebSocketConnection, username: str, password: str) -> str | None:
    """Log in, auto-registering the account if the username is new. Returns
    None once authenticated, or a short error message otherwise (a genuine
    bad password, a failed registration, or a dropped connection) - suitable
    both for printing on the CLI and for showing on the login screen. This is
    the smooth "just works" flow: a first-time username registers itself, a
    returning one logs in, and only a real bad password is refused."""
    connection.send(client_messages.login(username, password))
    reply = _await_auth(connection)
    if reply is None:
        return "connection lost"
    if reply["type"] == "auth_ok":
        return None
    if reply["payload"]["reason"] != "no_such_user":
        return "wrong password"

    # Brand-new username - create the account.
    connection.send(client_messages.register(username, password))
    reply = _await_auth(connection)
    if reply is None:
        return "connection lost"
    if reply["type"] == "auth_ok":
        return None
    return f"registration failed: {reply['payload']['reason']}"


def _await_auth(connection: WebSocketConnection) -> dict | None:
    """Wait for the server's auth_ok/auth_failed reply, or None if the
    connection drops first."""
    while not connection.is_closed():
        for message in connection.poll():
            if message["type"] in ("auth_ok", "auth_failed"):
                return message
        time.sleep(HANDSHAKE_POLL_SECONDS)
    return None


def _await_game_start(connection: WebSocketConnection) -> tuple[GameSnapshot | None, dict[str, str]]:
    """Block until the server starts the game, returning the opening
    snapshot and the two players' names for the HUD. game_started names the
    players; the state_snapshot that follows is the opening board. Returns
    (None, names) if the connection drops or a matchmaking search times out
    while waiting, so the caller can report it instead of waiting forever (it
    tells the two apart by whether the connection is still open)."""
    player_names = dict(DEFAULT_PLAYER_NAME_BY_COLOR)
    while not connection.is_closed():
        for message in connection.poll():
            if message["type"] == "game_started":
                player_names = player_names_from_started(message["payload"])
            elif message["type"] == "state_snapshot":
                return decode_snapshot(message["payload"]), player_names
            elif message["type"] == "match_timeout":
                return None, player_names
        time.sleep(HANDSHAKE_POLL_SECONDS)
    return None, player_names


if __name__ == "__main__":
    # No arguments -> graphical lobby (login and menu in the window).
    # app_online.py <username> <password> <room>       -> command-line room
    # app_online.py <username> <password> --matchmake  -> command-line matchmaking
    if len(sys.argv) <= 1:
        main_gui()
    else:
        cli_username = sys.argv[1]
        cli_password = sys.argv[2] if len(sys.argv) > 2 else "password"
        cli_third = sys.argv[3] if len(sys.argv) > 3 else "lobby"
        if cli_third == "--matchmake":
            main(cli_username, cli_password, room="", matchmake=True)
        else:
            main(cli_username, cli_password, room=cli_third)
