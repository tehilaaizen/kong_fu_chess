from application.auth_service import (
    NO_SUCH_USER,
    OK,
    USERNAME_TAKEN,
    WRONG_PASSWORD,
    AuthService,
)
from persistence.in_memory.user_repository import InMemoryUserRepository
from persistence.repositories import DEFAULT_RATING


class FakeHasher:
    """A trivial reversible "hash" so tests avoid scrypt's cost while still
    exercising the hash/verify pairing."""

    def hash(self, password: str) -> str:
        return f"H:{password}"

    def verify(self, password: str, stored: str) -> bool:
        return stored == f"H:{password}"


def _service():
    return AuthService(InMemoryUserRepository(), FakeHasher())


def test_registering_a_new_user_succeeds_at_the_default_rating():
    service = _service()

    result = service.register("alice", "secret")

    assert result.is_authenticated is True
    assert result.reason == OK
    assert result.user.username == "alice"
    assert result.user.rating == DEFAULT_RATING


def test_registering_a_taken_username_is_rejected():
    service = _service()
    service.register("alice", "secret")

    result = service.register("alice", "other")

    assert result.is_authenticated is False
    assert result.reason == USERNAME_TAKEN
    assert result.user is None


def test_a_registered_user_can_log_in_with_the_right_password():
    service = _service()
    service.register("alice", "secret")

    result = service.login("alice", "secret")

    assert result.is_authenticated is True
    assert result.reason == OK
    assert result.user.username == "alice"


def test_logging_in_an_unknown_user_reports_no_such_user():
    service = _service()

    result = service.login("ghost", "secret")

    assert result.is_authenticated is False
    assert result.reason == NO_SUCH_USER


def test_logging_in_with_a_wrong_password_is_rejected():
    service = _service()
    service.register("alice", "secret")

    result = service.login("alice", "wrong")

    assert result.is_authenticated is False
    assert result.reason == WRONG_PASSWORD


def test_the_stored_password_is_hashed_not_plaintext():
    repo = InMemoryUserRepository()
    AuthService(repo, FakeHasher()).register("alice", "secret")

    assert repo.get_user("alice").password_hash == "H:secret"  # never the raw password
