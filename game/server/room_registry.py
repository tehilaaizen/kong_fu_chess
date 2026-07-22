from __future__ import annotations

from dataclasses import dataclass

ROLE_WHITE = "white"
ROLE_BLACK = "black"
ROLE_SPECTATOR = "spectator"


@dataclass(frozen=True)
class RoomJoin:
    """The outcome of one connection asking to join a room by name.

    role is who the connection is in that room (white/black/spectator).
    start_game is True only for the second distinct player - the moment the
    room fills and the game should begin - and then white_id/black_id name
    the two players so the caller can seat them. game_id is set once the
    room's game exists (so a spectator can be shown the game already in
    progress); it is None while the room is still waiting for its second
    player."""

    room: str
    role: str
    start_game: bool
    white_id: str | None
    black_id: str | None
    game_id: str | None


@dataclass
class _Room:
    """One room's mutable membership: the two players' connection ids (each
    None until taken) and the id of the game once it has started."""

    white_id: str | None = None
    black_id: str | None = None
    game_id: str | None = None


class RoomRegistry:
    """Maps room names to their membership and decides each joiner's role:
    the first connection to name a room creates it and plays White, the
    second (a different connection) plays Black and starts the game, and
    every later joiner is a spectator. Re-joining under the same connection
    is idempotent - a player who re-sends the room name keeps their seat
    rather than being demoted to spectator. Pure and synchronous, like
    ConnectionManager; it holds no sockets and no game rules, only the
    room->roles bookkeeping."""

    def __init__(self) -> None:
        self._rooms: dict[str, _Room] = {}

    def join(self, connection_id: str, room_name: str) -> RoomJoin:
        """Admit connection_id to room_name and report its role. Creates the
        room on the first join. The second distinct connection returns
        start_game=True (with both player ids); anyone after that is a
        spectator carrying the room's game_id."""
        room = self._rooms.setdefault(room_name, _Room())

        if connection_id == room.white_id:
            return self._seat(room_name, ROLE_WHITE, False, room)
        if connection_id == room.black_id:
            return self._seat(room_name, ROLE_BLACK, False, room)

        if room.white_id is None:
            room.white_id = connection_id
            return self._seat(room_name, ROLE_WHITE, False, room)

        if room.black_id is None:
            room.black_id = connection_id
            return self._seat(room_name, ROLE_BLACK, True, room)

        return self._seat(room_name, ROLE_SPECTATOR, False, room)

    def set_game_id(self, room_name: str, game_id: str) -> None:
        """Record the game a started room now owns, so later spectators can
        be pointed at it."""
        self._rooms[room_name].game_id = game_id

    def _seat(self, room_name: str, role: str, start_game: bool, room: _Room) -> RoomJoin:
        """Build the RoomJoin describing this admission from the room's
        current membership."""
        return RoomJoin(
            room=room_name,
            role=role,
            start_game=start_game,
            white_id=room.white_id,
            black_id=room.black_id,
            game_id=room.game_id,
        )
