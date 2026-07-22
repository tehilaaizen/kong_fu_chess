from __future__ import annotations

from dataclasses import replace

from persistence.repositories import DEFAULT_RATING, RatingUpdate, UserExists, UserRecord


class InMemoryUserRepository:
    """A UserRepository backed by a plain dict - the offline/test backing,
    with no persistence across process restarts. Satisfies the same contract
    as the SQLite repository."""

    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}
        self._recorded_games: set[str] = set()

    def create_user(self, username: str, password_hash: str) -> UserRecord:
        """Create a user at the default rating and return it; raise
        UserExists if the username is already taken."""
        if username in self._users:
            raise UserExists(username)
        record = UserRecord(username=username, password_hash=password_hash, rating=DEFAULT_RATING)
        self._users[username] = record
        return record

    def get_user(self, username: str) -> UserRecord | None:
        """The stored user with this username, or None if there is none."""
        return self._users.get(username)

    def record_game_result(self, game_id: str, updates: list[RatingUpdate]) -> bool:
        """Apply each player's new rating, remembering the game_id so a
        repeat is a no-op. Returns False if this game was already recorded,
        mirroring the SQLite primary-key idempotency guard."""
        if game_id in self._recorded_games:
            return False
        self._recorded_games.add(game_id)
        for update in updates:
            existing = self._users.get(update.username)
            if existing is not None:
                self._users[update.username] = replace(existing, rating=update.new_rating)
        return True
