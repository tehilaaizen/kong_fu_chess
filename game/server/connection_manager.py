from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConnectionInfo:
    """What the server tracks about one live connection: its id, the
    username it identified as, and (once it joins a game) which game and
    color it plays. color is None for a spectator or a not-yet-seated
    connection."""

    connection_id: str
    username: str
    game_id: str | None = None
    color: str | None = None


class ConnectionManager:
    """Tracks live connections and their identities, and answers "who is
    in this game?" for broadcasting. Holds no socket objects itself (the
    gateway owns those) and no game rules - purely a registry keyed by a
    connection id."""

    def __init__(self) -> None:
        self._by_id: dict[str, ConnectionInfo] = {}

    def register(self, connection_id: str, username: str) -> ConnectionInfo:
        """Record a newly connected, identified client. Returns its
        ConnectionInfo."""
        info = ConnectionInfo(connection_id=connection_id, username=username)
        self._by_id[connection_id] = info
        return info

    def assign_to_game(self, connection_id: str, game_id: str, color: str | None) -> None:
        """Seat a connection in a game as color ("w"/"b"), or as a
        spectator when color is None."""
        info = self._by_id[connection_id]
        info.game_id = game_id
        info.color = color

    def get(self, connection_id: str) -> ConnectionInfo | None:
        """The ConnectionInfo for connection_id, or None if unknown."""
        return self._by_id.get(connection_id)

    def connections_in_game(self, game_id: str) -> list[str]:
        """Every connection id currently seated in game_id (players and
        spectators) - the broadcast set for that game."""
        return [cid for cid, info in self._by_id.items() if info.game_id == game_id]

    def remove(self, connection_id: str) -> ConnectionInfo | None:
        """Drop a disconnected connection, returning what it was (or None
        if it wasn't tracked)."""
        return self._by_id.pop(connection_id, None)
