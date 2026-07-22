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


def _piece_ref(piece_id: int, color: str, kind: str) -> dict:
    """The {id, color, kind} identity a client needs to key a piece's
    animator and know what sprite to draw - shared by every event that
    names a piece."""
    return {"id": piece_id, "color": color, "kind": kind}


def state_snapshot(pieces: list[dict], width: int, height: int, sequence: int, game_over: bool) -> dict:
    """Full board state broadcast (also used on reconnect): every piece as
    an {id, color, kind, row, col} record (see application.dto.board_placements),
    the board dimensions, and the game's monotonic sequence. Carrying ids -
    not just a token grid - lets a client rebuild an id-keyed snapshot whose
    ids match the motion/arrival events."""
    return _envelope(
        "state_snapshot",
        {"pieces": pieces, "width": width, "height": height, "sequence": sequence, "game_over": game_over},
    )


def motion_started(
    piece_id: int, color: str, kind: str, source: dict, destination: dict, duration_ms: int
) -> dict:
    """Broadcast when a move was accepted and the piece began travelling:
    lets a client play the same slide animation from source to destination
    over duration_ms. source/destination are {row, col} records."""
    return _envelope(
        "motion_started",
        {
            "piece": _piece_ref(piece_id, color, kind),
            "source": source,
            "destination": destination,
            "duration_ms": duration_ms,
        },
    )


def jump_started(piece_id: int, color: str, kind: str, cell: dict, duration_ms: int) -> dict:
    """Broadcast when a piece went airborne in place at cell for
    duration_ms. cell is a {row, col} record."""
    return _envelope(
        "jump_started",
        {"piece": _piece_ref(piece_id, color, kind), "cell": cell, "duration_ms": duration_ms},
    )


def rest_started(piece_id: int, color: str, kind: str, duration_ms: int, label: str) -> dict:
    """Broadcast when a piece entered a cooldown for duration_ms; label is
    "long_rest" after a move or "short_rest" after a jump, so a client can
    drive the draining rest overlay."""
    return _envelope(
        "rest_started",
        {"piece": _piece_ref(piece_id, color, kind), "duration_ms": duration_ms, "label": label},
    )


def arrival(piece_id: int, color: str, kind: str, source: dict, destination: dict, captured_kind: str | None) -> dict:
    """Broadcast when a motion logically arrived: lets a client re-drive the
    same on_arrival observers (score, moves log, promotion kind-sync).
    captured_kind is the captured piece's kind, or None if nothing was
    captured. source/destination are {row, col} records."""
    return _envelope(
        "arrival",
        {
            "piece": _piece_ref(piece_id, color, kind),
            "source": source,
            "destination": destination,
            "captured_kind": captured_kind,
        },
    )


def move_accepted(correlation_id: str | None) -> dict:
    """Ack for an accepted make_move, correlated to the request. The
    resulting board change is broadcast separately as a state_snapshot
    once the motion resolves, carrying its own sequence."""
    return _envelope("move_accepted", {}, correlation_id)


def move_rejected(reason: str, correlation_id: str | None) -> dict:
    """Reply to a rejected make_move, carrying the engine/application
    rejection reason."""
    return _envelope("move_rejected", {"reason": reason}, correlation_id)


def auth_ok(username: str, rating: int, correlation_id: str | None = None) -> dict:
    """Reply to a successful register/login: the authenticated username and
    their current rating, correlated to the request."""
    return _envelope("auth_ok", {"username": username, "rating": rating}, correlation_id)


def auth_failed(reason: str, correlation_id: str | None = None) -> dict:
    """Reply to a failed register/login, carrying a stable reason
    (username_taken / no_such_user / wrong_password) so the client can react
    - e.g. auto-register an unknown user."""
    return _envelope("auth_failed", {"reason": reason}, correlation_id)


def game_started(white_user: str, black_user: str) -> dict:
    """Broadcast when a game begins (drives start animation/sound)."""
    return _envelope("game_started", {"white": white_user, "black": black_user})


def game_over(winner: str, reason: str = "king_capture") -> dict:
    """Broadcast when a game ends. reason is why - "king_capture" for a
    normal win, "abandoned" when the loser disconnected."""
    return _envelope("game_over", {"winner": winner, "reason": reason})


def error(code: str, message: str, correlation_id: str | None = None) -> dict:
    """A non-fatal error reply; the connection stays open."""
    return _envelope("error", {"code": code, "message": message}, correlation_id)


def pong() -> dict:
    """Liveness reply to a ping."""
    return _envelope("pong", {})
