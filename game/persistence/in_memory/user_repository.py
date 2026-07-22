from __future__ import annotations

from persistence.repositories import DEFAULT_RATING, UserExists, UserRecord


class InMemoryUserRepository:
    """A UserRepository backed by a plain dict - the offline/test backing,
    with no persistence across process restarts. Satisfies the same contract
    as the SQLite repository."""

    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}

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
