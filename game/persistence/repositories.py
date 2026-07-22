from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# Every new account starts here; games later move a player's rating up or
# down from this baseline (the ELO work).
DEFAULT_RATING = 1200


class UserExists(Exception):
    """Raised by UserRepository.create_user when the username is taken."""


@dataclass(frozen=True)
class UserRecord:
    """A stored user account: the unique username, the hashed password
    (never the plaintext), and the current rating."""

    username: str
    password_hash: str
    rating: int


class UserRepository(Protocol):
    """Persistence for user accounts, so the auth/application layers never
    talk to a database directly. Backed in-memory for tests and offline
    use, and by SQLite in production - both implementations satisfy the same
    shared contract tests."""

    def create_user(self, username: str, password_hash: str) -> UserRecord:
        """Create a user at the default rating and return it; raise
        UserExists if the username is already taken."""
        ...

    def get_user(self, username: str) -> UserRecord | None:
        """The stored user with this username, or None if there is none."""
        ...
