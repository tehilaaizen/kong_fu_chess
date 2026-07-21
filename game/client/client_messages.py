from __future__ import annotations


def _envelope(message_type: str, payload: dict) -> dict:
    """The client->server frame shape server/schemas.parse_inbound reads:
    a type and its payload. message_id is left off - the interactive GUI
    fires commands and relies on the broadcast state_snapshot for truth,
    so it needs no per-command correlation."""
    return {"type": message_type, "payload": payload}


def connect(username: str) -> dict:
    """Identify to the server by username (Phase A's only identity)."""
    return _envelope("connect", {"username": username})


def join_game() -> dict:
    """Ask to be seated in a game; the server pairs the first two joiners."""
    return _envelope("join_game", {})


def make_move(move: str) -> dict:
    """Request a move in "WRa1a7" wire notation."""
    return _envelope("make_move", {"move": move})


def jump_request(cell: str) -> dict:
    """Request the piece at algebraic cell (e.g. "a2") to jump."""
    return _envelope("jump_request", {"cell": cell})


def ping() -> dict:
    """Liveness probe; the server answers with a pong."""
    return _envelope("ping", {})
