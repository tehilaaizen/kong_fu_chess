from application.password_hasher import PasswordHasher


def test_a_password_verifies_against_its_own_hash():
    hasher = PasswordHasher()

    stored = hasher.hash("correct horse")

    assert hasher.verify("correct horse", stored) is True


def test_a_wrong_password_does_not_verify():
    hasher = PasswordHasher()

    stored = hasher.hash("correct horse")

    assert hasher.verify("wrong horse", stored) is False


def test_the_same_password_hashes_differently_each_time():
    hasher = PasswordHasher()

    first = hasher.hash("secret")
    second = hasher.hash("secret")

    assert first != second  # different random salt
    assert hasher.verify("secret", first) is True
    assert hasher.verify("secret", second) is True


def test_a_malformed_stored_value_does_not_verify_and_does_not_raise():
    hasher = PasswordHasher()

    assert hasher.verify("secret", "not-a-valid-hash") is False
    assert hasher.verify("secret", "") is False
    assert hasher.verify("secret", "nothex$deadbeef") is False
