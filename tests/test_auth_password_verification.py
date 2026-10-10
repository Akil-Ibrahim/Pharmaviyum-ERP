from src.pharmaviyum.api.v1.auth import _verify_password, pwd_context


def test_verify_password_returns_false_for_multibyte_password_over_bcrypt_limit():
    hashed_password = pwd_context.hash("a-valid-password")
    password = "пароль" * 12

    assert len(password) <= 72
    assert len(password.encode("utf-8")) > 72
    assert _verify_password(password, hashed_password) is False


def test_verify_password_accepts_correct_password():
    password = "a-valid-password"
    hashed_password = pwd_context.hash(password)

    assert _verify_password(password, hashed_password) is True
