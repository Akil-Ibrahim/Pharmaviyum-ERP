"""Authentication security API backed by the canonical security package."""

from ...core.security import (create_access_token, create_password_reset_token,
                              create_refresh_token, decode_access_token,
                              decode_password_reset_token,
                              decode_refresh_token, get_password_hash,
                              verify_password)


def verify_token(token: str, expected_type: str = "access") -> dict | None:
    """Verify a token using the canonical decoder for its expected type."""
    if expected_type == "access":
        return decode_access_token(token)
    if expected_type == "refresh":
        return decode_refresh_token(token)
    if expected_type == "password_reset":
        return decode_password_reset_token(token)
    return None


def constant_time_compare(a: str, b: str) -> bool:
    """Compare strings without exposing timing information."""
    import hmac

    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


__all__ = [
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "create_password_reset_token",
    "decode_access_token",
    "decode_refresh_token",
    "decode_password_reset_token",
    "verify_token",
    "constant_time_compare",
]
