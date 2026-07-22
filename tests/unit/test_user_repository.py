import sqlite3

import pytest

from persistence.in_memory.user_repository import InMemoryUserRepository
from persistence.repositories import DEFAULT_RATING, UserExists
from persistence.sqlite.user_repository import SqliteUserRepository, connect


@pytest.fixture(params=["in_memory", "sqlite"])
def repo(request):
    """A UserRepository under test, run once per backing so both satisfy the
    identical contract. SQLite uses a throwaway in-memory database."""
    if request.param == "in_memory":
        return InMemoryUserRepository()
    if request.param == "sqlite":
        return SqliteUserRepository(sqlite3.connect(":memory:"))
    raise AssertionError(f"unknown repo backing {request.param!r}")


def test_create_user_returns_a_record_at_the_default_rating(repo):
    record = repo.create_user("alice", "hash-of-alice")

    assert record.username == "alice"
    assert record.password_hash == "hash-of-alice"
    assert record.rating == DEFAULT_RATING


def test_get_user_returns_the_created_user(repo):
    repo.create_user("alice", "hash-of-alice")

    fetched = repo.get_user("alice")

    assert fetched is not None
    assert fetched.username == "alice"
    assert fetched.password_hash == "hash-of-alice"


def test_get_unknown_user_returns_none(repo):
    assert repo.get_user("nobody") is None


def test_creating_a_duplicate_username_raises(repo):
    repo.create_user("alice", "hash-of-alice")

    with pytest.raises(UserExists):
        repo.create_user("alice", "another-hash")


def test_sqlite_persists_across_connections_to_the_same_file(tmp_path):
    db_path = str(tmp_path / "users.db")
    SqliteUserRepository(connect(db_path)).create_user("alice", "hash-of-alice")

    # a fresh connection to the same file still sees the account
    reopened = SqliteUserRepository(connect(db_path))
    assert reopened.get_user("alice").username == "alice"
