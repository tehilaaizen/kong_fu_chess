import sqlite3

import pytest

from persistence.in_memory.user_repository import InMemoryUserRepository
from persistence.repositories import DEFAULT_RATING, RatingUpdate, UserExists
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


def test_record_game_result_applies_both_players_new_ratings(repo):
    repo.create_user("alice", "h")
    repo.create_user("bob", "h")

    applied = repo.record_game_result(
        "g1", [RatingUpdate("alice", 1200, 1216), RatingUpdate("bob", 1200, 1184)]
    )

    assert applied is True
    assert repo.get_user("alice").rating == 1216
    assert repo.get_user("bob").rating == 1184


def test_recording_the_same_game_twice_is_a_no_op(repo):
    repo.create_user("alice", "h")
    repo.create_user("bob", "h")
    repo.record_game_result("g1", [RatingUpdate("alice", 1200, 1216), RatingUpdate("bob", 1200, 1184)])

    # a second attempt for the same game is rejected and changes nothing
    applied_again = repo.record_game_result(
        "g1", [RatingUpdate("alice", 1216, 1232), RatingUpdate("bob", 1184, 1168)]
    )

    assert applied_again is False
    assert repo.get_user("alice").rating == 1216
    assert repo.get_user("bob").rating == 1184


def test_a_different_game_id_is_recorded_independently(repo):
    repo.create_user("alice", "h")
    repo.create_user("bob", "h")
    repo.record_game_result("g1", [RatingUpdate("alice", 1200, 1216), RatingUpdate("bob", 1200, 1184)])

    applied = repo.record_game_result(
        "g2", [RatingUpdate("alice", 1216, 1232), RatingUpdate("bob", 1184, 1168)]
    )

    assert applied is True
    assert repo.get_user("alice").rating == 1232
    assert repo.get_user("bob").rating == 1168


def test_sqlite_persists_across_connections_to_the_same_file(tmp_path):
    db_path = str(tmp_path / "users.db")
    SqliteUserRepository(connect(db_path)).create_user("alice", "hash-of-alice")

    # a fresh connection to the same file still sees the account
    reopened = SqliteUserRepository(connect(db_path))
    assert reopened.get_user("alice").username == "alice"
