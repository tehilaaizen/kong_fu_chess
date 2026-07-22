from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from persistence.repositories import UserExists, UserRecord, UserRepository

# AuthResult reasons.
OK = "ok"
USERNAME_TAKEN = "username_taken"
NO_SUCH_USER = "no_such_user"
WRONG_PASSWORD = "wrong_password"


class Hasher(Protocol):
    """The slice of PasswordHasher AuthService needs - a Protocol so a test
    can inject a trivial fake instead of paying scrypt's cost per case."""

    def hash(self, password: str) -> str:
        ...

    def verify(self, password: str, stored: str) -> bool:
        ...


@dataclass(frozen=True)
class AuthResult:
    """The outcome of a register/login attempt: whether it authenticated, a
    stable machine-readable reason ("ok" on success), and the resulting user
    record (with its rating) when it succeeded."""

    is_authenticated: bool
    reason: str
    user: UserRecord | None = None


class AuthService:
    """Registers and authenticates users over a UserRepository, hashing
    passwords through an injected Hasher. It is the only place that turns a
    username+password into an authenticated account; it never touches the
    network or a database directly (the repository does), and it stores only
    hashed passwords, never plaintext."""

    def __init__(self, user_repository: UserRepository, hasher: Hasher) -> None:
        self._users = user_repository
        self._hasher = hasher

    def register(self, username: str, password: str) -> AuthResult:
        """Create a new account for username with a hashed password.
        Rejected with USERNAME_TAKEN if the name is already in use."""
        try:
            user = self._users.create_user(username, self._hasher.hash(password))
        except UserExists:
            return AuthResult(False, USERNAME_TAKEN)
        return AuthResult(True, OK, user)

    def login(self, username: str, password: str) -> AuthResult:
        """Authenticate an existing account. Rejected with NO_SUCH_USER if
        the name is unknown, or WRONG_PASSWORD if the password doesn't match
        - kept distinct so a client can auto-register an unknown user while
        still reporting a genuine bad password."""
        user = self._users.get_user(username)
        if user is None:
            return AuthResult(False, NO_SUCH_USER)
        if not self._hasher.verify(password, user.password_hash):
            return AuthResult(False, WRONG_PASSWORD)
        return AuthResult(True, OK, user)
