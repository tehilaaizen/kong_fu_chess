from __future__ import annotations

import json
from dataclasses import dataclass


class SchemaError(ValueError):
    """Raised when an inbound frame isn't a well-formed message envelope
    (not JSON, not an object, or missing a string type)."""


@dataclass(frozen=True)
class InboundMessage:
    """One parsed client->server frame: its type (e.g. "make_move"), its
    payload object, and the client's optional message_id (echoed back as
    a correlation_id on the response)."""

    type: str
    payload: dict
    message_id: str | None


def parse_inbound(raw: str) -> InboundMessage:
    """Parse a raw client frame into an InboundMessage. Raises SchemaError
    on anything malformed, so the gateway can reply with an error and keep
    the connection open instead of crashing."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise SchemaError("frame is not valid JSON")

    if not isinstance(data, dict):
        raise SchemaError("envelope must be a JSON object")

    message_type = data.get("type")
    if not isinstance(message_type, str) or not message_type:
        raise SchemaError("envelope is missing a non-empty 'type'")

    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        raise SchemaError("'payload' must be a JSON object")

    message_id = data.get("message_id")
    if not isinstance(message_id, str):
        message_id = None

    return InboundMessage(type=message_type, payload=payload, message_id=message_id)


def serialize(message: dict) -> str:
    """Render an outbound message dict to a JSON string for the wire."""
    return json.dumps(message)


def _envelope(message_type: str, payload: dict, correlation_id: str | None = None) -> dict:
    """The common server->client envelope; correlation_id echoes the
    request's message_id when this frame is a direct reply."""
    message: dict = {"type": message_type, "payload": payload}
    if correlation_id is not None:
        message["correlation_id"] = correlation_id
    return message


def state_snapshot(board: list[list[str]], sequence: int, game_over: bool) -> dict:
    """Full board state broadcast (also used on reconnect)."""
    return _envelope("state_snapshot", {"board": board, "sequence": sequence, "game_over": game_over})


def move_accepted(sequence: int, correlation_id: str | None) -> dict:
    """Reply to an accepted make_move, correlated to the request."""
    return _envelope("move_accepted", {"sequence": sequence}, correlation_id)


def move_rejected(reason: str, correlation_id: str | None) -> dict:
    """Reply to a rejected make_move, carrying the engine/application
    rejection reason."""
    return _envelope("move_rejected", {"reason": reason}, correlation_id)


def game_started(white_user: str, black_user: str) -> dict:
    """Broadcast when a game begins (drives start animation/sound)."""
    return _envelope("game_started", {"white": white_user, "black": black_user})


def game_over(winner: str) -> dict:
    """Broadcast when a king was captured."""
    return _envelope("game_over", {"winner": winner, "reason": "king_capture"})


def error(code: str, message: str, correlation_id: str | None = None) -> dict:
    """A non-fatal error reply; the connection stays open."""
    return _envelope("error", {"code": code, "message": message}, correlation_id)


def pong() -> dict:
    """Liveness reply to a ping."""
    return _envelope("pong", {})
