# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import asyncio
import json
import sys

import websockets

DEFAULT_URI = "ws://localhost:8765"


def render_board(board: list[list[str]]) -> str:
    """A board grid (rows of tokens) as printable text, blanks for empty
    cells."""
    return "\n".join(" ".join(cell if cell != "." else " ." for cell in row) for row in board)


async def receive_loop(websocket) -> None:
    """Print every server message until the connection closes."""
    async for raw in websocket:
        message = json.loads(raw)
        message_type = message["type"]
        payload = message.get("payload", {})
        if message_type == "state_snapshot":
            print("\n" + render_board(payload["board"]) + f"\n(seq {payload['sequence']})")
        elif message_type == "game_started":
            print(f"\nGame started - White: {payload['white']}  Black: {payload['black']}")
        elif message_type == "move_rejected":
            print(f"move rejected: {payload['reason']}")
        elif message_type == "game_over":
            print(f"\n*** GAME OVER - winner: {payload['winner']} ***")
        elif message_type == "error":
            print(f"error: {payload.get('code')} - {payload.get('message')}")
        elif message_type != "move_accepted":
            print(f"<- {message_type} {payload}")


async def input_loop(websocket) -> None:
    """Read commands from the terminal and send them: a full move string
    like "WPa2a4", "jump e2", or "quit"."""
    while True:
        line = (await asyncio.to_thread(input, "")).strip()
        if not line:
            continue
        if line in ("quit", "exit"):
            await websocket.close()
            return
        if line.startswith("jump "):
            await websocket.send(json.dumps({"type": "jump_request", "payload": {"cell": line[5:].strip()}}))
        else:
            await websocket.send(json.dumps({"type": "make_move", "payload": {"move": line}}))


async def main(username: str, uri: str = DEFAULT_URI) -> None:
    """Connect, identify as username, join the quick-match queue, then run
    the receive and input loops together until the user quits."""
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"type": "connect", "payload": {"username": username}}))
        await websocket.send(json.dumps({"type": "join_game", "payload": {}}))
        print(f"Connected as {username}. Waiting for an opponent to join...")
        print('Type a move like "WPa2a4" (Color+Kind+from+to), "jump e2", or "quit".')
        await asyncio.gather(receive_loop(websocket), input_loop(websocket))


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else input("username: ").strip()
    server_uri = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_URI
    try:
        asyncio.run(main(name, server_uri))
    except (KeyboardInterrupt, websockets.WebSocketException):
        pass
