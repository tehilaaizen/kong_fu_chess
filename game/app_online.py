# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import sys
import time

from app_support import build_game_window
from client import client_messages
from client.network_commands import NetworkCommands
from client.network_game_adapter import NetworkGameAdapter, decode_snapshot
from client.server_event_dispatcher import ServerEventDispatcher
from client.websocket_connection import WebSocketConnection
from engine.game_snapshot import GameSnapshot
from input.board_mapper import BoardMapper
from input.controller import Controller
from model.board import Board
from rules.rule_engine import RuleEngine
from view.consts import DEFAULT_PLAYER_NAME_BY_COLOR

DEFAULT_SERVER_URI = "ws://localhost:8765"
# How long to nap between polls while waiting for the game to start. Real
# wall-clock sleep is fine here - this is an application entry point, not a
# test (the no-real-sleep rule applies to tests).
HANDSHAKE_POLL_SECONDS = 0.05


def main(username: str, password: str, room: str, uri: str = DEFAULT_SERVER_URI) -> None:
    """Online entry point: authenticate as username, join the room named
    room, wait for the game to start, then drive the same interactive window
    as offline play - but from a NetworkGameAdapter, so the server owns state
    and time. The first into a room plays White, the second Black, and anyone
    after that spectates. Blocks during the handshake until the game starts
    and the opening board arrives; the view half is built by the shared
    app_support.build_game_window."""
    print(f"Connecting to {uri} as '{username}', room '{room}'...")
    connection = WebSocketConnection()
    connection.start(uri)
    if connection.is_closed():
        print(f"Could not reach the server at {uri}. Is it running?")
        return

    if not _authenticate(connection, username, password):
        return  # _authenticate already explained why

    connection.send(client_messages.join_room(room))
    print("Waiting for the game to start (leave this running)...")

    initial_snapshot, player_names = _await_game_start(connection)
    if initial_snapshot is None:
        print("Connection to the server was lost before the game started.")
        return
    print("Game starting - opening the board...")

    board = Board(initial_snapshot.board_width, initial_snapshot.board_height)
    board_mapper = BoardMapper(board)
    rule_engine = RuleEngine()
    commands = NetworkCommands(connection, board)
    controller = Controller(board, board_mapper, commands)
    dispatcher = ServerEventDispatcher()
    client = NetworkGameAdapter(connection, controller, board, rule_engine, dispatcher, initial_snapshot)

    window = build_game_window(client, board_mapper, player_names)
    window.run()


def _authenticate(connection: WebSocketConnection, username: str, password: str) -> bool:
    """Log in, auto-registering the account if the username is new. Returns
    True once authenticated; otherwise prints why (wrong password, or the
    connection dropped) and returns False. This is the smooth "just works"
    flow: a first-time username registers itself, a returning one logs in,
    and only a genuine bad password is refused."""
    connection.send(client_messages.login(username, password))
    reply = _await_auth(connection)
    if reply is None:
        print("Connection lost during login.")
        return False
    if reply["type"] == "auth_ok":
        print(f"Logged in as '{username}' (rating {reply['payload']['rating']}).")
        return True

    if reply["payload"]["reason"] != "no_such_user":
        print("Login failed: wrong password.")
        return False

    # Brand-new username - create the account.
    connection.send(client_messages.register(username, password))
    reply = _await_auth(connection)
    if reply is None:
        print("Connection lost during registration.")
        return False
    if reply["type"] == "auth_ok":
        print(f"Registered new account '{username}' (rating {reply['payload']['rating']}).")
        return True
    print(f"Registration failed: {reply['payload']['reason']}.")
    return False


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
    (None, names) if the connection drops while waiting, so the caller can
    report the loss instead of waiting forever."""
    player_names = dict(DEFAULT_PLAYER_NAME_BY_COLOR)
    while not connection.is_closed():
        for message in connection.poll():
            if message["type"] == "game_started":
                payload = message["payload"]
                player_names = {"w": payload["white"], "b": payload["black"]}
            elif message["type"] == "state_snapshot":
                return decode_snapshot(message["payload"]), player_names
        time.sleep(HANDSHAKE_POLL_SECONDS)
    return None, player_names


if __name__ == "__main__":
    cli_username = sys.argv[1] if len(sys.argv) > 1 else "player"
    cli_password = sys.argv[2] if len(sys.argv) > 2 else "password"
    cli_room = sys.argv[3] if len(sys.argv) > 3 else "lobby"
    main(cli_username, cli_password, cli_room)
