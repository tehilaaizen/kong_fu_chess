# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import sys
import time

from app_support import build_game_window
from client import client_messages
from client.network_commands import NetworkCommands
from client.network_game_adapter import NetworkGameAdapter, decode_snapshot
from client.server_connection import ServerConnection
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


def main(username: str, room: str, uri: str = DEFAULT_SERVER_URI) -> None:
    """Online entry point: connect to the server as username, join the room
    named room, wait for the game to start, then drive the same interactive
    window as offline play - but from a NetworkGameAdapter, so the server
    owns state and time. The first into a room plays White, the second Black,
    and anyone after that spectates. Blocks during the handshake until the
    game starts and the opening board arrives; the view half is built by the
    shared app_support.build_game_window."""
    print(f"Connecting to {uri} as '{username}', room '{room}'...")
    connection = WebSocketConnection()
    connection.start(uri)
    connection.send(client_messages.connect(username))
    connection.send(client_messages.join_room(room))
    print("Connected. Waiting for the game to start (leave this running)...")

    initial_snapshot, player_names = _await_game_start(connection)
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


def _await_game_start(connection: ServerConnection) -> tuple[GameSnapshot, dict[str, str]]:
    """Block until the server pairs us into a game, returning the opening
    snapshot and the two players' names for the HUD. game_started names the
    players; the state_snapshot that follows is the opening board."""
    player_names = dict(DEFAULT_PLAYER_NAME_BY_COLOR)
    while True:
        for message in connection.poll():
            if message["type"] == "game_started":
                payload = message["payload"]
                player_names = {"w": payload["white"], "b": payload["black"]}
            elif message["type"] == "state_snapshot":
                return decode_snapshot(message["payload"]), player_names
        time.sleep(HANDSHAKE_POLL_SECONDS)


if __name__ == "__main__":
    cli_username = sys.argv[1] if len(sys.argv) > 1 else "player"
    cli_room = sys.argv[2] if len(sys.argv) > 2 else "lobby"
    main(cli_username, cli_room)
