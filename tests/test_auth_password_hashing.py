"""Regression tests for bcrypt's 72-byte input limit."""

from src.pharmaviyum.api.v1.auth import (
    _hash_password,
    _verify_password,
    pwd_context,
)


def test_hash_and_verify_password_longer_than_72_ascii_bytes() -> None:
    password = "pharmaviyum-" * 12

    hashed_password = _hash_password(password)

    assert hashed_password.startswith("$bcrypt-sha256$")
    assert _verify_password(password, hashed_password)
    assert not _verify_password(password + "wrong", hashed_password)


def test_hash_and_verify_multibyte_unicode_password() -> None:
    password = "药房安全🔐" * 20

    hashed_password = _hash_password(password)

    assert _verify_password(password, hashed_password)
    assert not _verify_password(password + "x", hashed_password)


def test_legacy_bcrypt_hash_remains_verifiable() -> None:
    # Previous versions truncated ASCII passwords to 72 characters.
    password = "a" * 72
    legacy_hash = pwd_context.hash(password, scheme="bcrypt")

    assert _verify_password(password, legacy_hash)
