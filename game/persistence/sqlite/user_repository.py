from __future__ import annotations

import sqlite3
from pathlib import Path

from persistence.repositories import DEFAULT_RATING, RatingUpdate, UserExists, UserRecord

_SCHEMA = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")


def connect(db_path: str) -> sqlite3.Connection:
    """Open (creating if needed) the SQLite database at db_path. The server
    runs on a single asyncio thread, so the default single-thread connection
    is fine."""
    return sqlite3.connect(db_path)


class SqliteUserRepository:
    """A UserRepository backed by SQLite - the production backing, so
    accounts survive a server restart. Given an open connection (injected,
    so tests can pass an in-memory database) and satisfies the same contract
    tests as the in-memory repository. Ensures its schema on construction."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    def create_user(self, username: str, password_hash: str) -> UserRecord:
        """Insert a user at the default rating and return it; raise
        UserExists if the username (the primary key) is already taken."""
        try:
            self._connection.execute(
                "INSERT INTO users (username, password_hash, rating) VALUES (?, ?, ?)",
                (username, password_hash, DEFAULT_RATING),
            )
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            raise UserExists(username) from error
        return UserRecord(username=username, password_hash=password_hash, rating=DEFAULT_RATING)

    def get_user(self, username: str) -> UserRecord | None:
        """The stored user with this username, or None if there is none."""
        row = self._connection.execute(
            "SELECT username, password_hash, rating FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return None
        return UserRecord(username=row[0], password_hash=row[1], rating=row[2])

    def record_game_result(self, game_id: str, updates: list[RatingUpdate]) -> bool:
        """Insert one rating_changes row per player and update their rating,
        all in one transaction. A duplicate (game_id, username) violates the
        primary key, rolling the whole transaction back and returning False -
        so recording the same game twice is a no-op."""
        try:
            with self._connection:  # commits on success, rolls back on IntegrityError
                for update in updates:
                    self._connection.execute(
                        "INSERT INTO rating_changes (game_id, username, old_rating, new_rating) "
                        "VALUES (?, ?, ?, ?)",
                        (game_id, update.username, update.old_rating, update.new_rating),
                    )
                    self._connection.execute(
                        "UPDATE users SET rating = ? WHERE username = ?",
                        (update.new_rating, update.username),
                    )
        except sqlite3.IntegrityError:
            return False
        return True
