from __future__ import annotations

import hashlib
import hmac
import os

# scrypt cost parameters (n must be a power of two). These give a ~0.1s
# hash on a typical machine - slow enough to resist brute force, fast
# enough for an interactive login.
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_SEPARATOR = "$"


class PasswordHasher:
    """Hashes and verifies passwords with the standard library's scrypt and
    a fresh random salt per password - no third-party dependency. The stored
    form is "salt_hex$hash_hex", so the salt travels with the hash and no
    separate salt column is needed. Injected into AuthService, so a test can
    swap in a trivial fake instead of paying scrypt's cost on every case."""

    def hash(self, password: str) -> str:
        """Return a self-contained "salt$hash" string for password, with a
        new random salt each call (so equal passwords hash differently)."""
        salt = os.urandom(_SALT_BYTES)
        digest = self._scrypt(password, salt)
        return f"{salt.hex()}{_SEPARATOR}{digest.hex()}"

    def verify(self, password: str, stored: str) -> bool:
        """Whether password matches a previously stored "salt$hash". Returns
        False (rather than raising) on a malformed stored value, and uses a
        constant-time comparison so a wrong password can't be timed out."""
        salt_hex, separator, hash_hex = stored.partition(_SEPARATOR)
        if not separator or not salt_hex or not hash_hex:
            return False
        try:
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False
        return hmac.compare_digest(self._scrypt(password, salt).hex(), hash_hex)

    def _scrypt(self, password: str, salt: bytes) -> bytes:
        """Derive the raw scrypt digest of password under salt."""
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
