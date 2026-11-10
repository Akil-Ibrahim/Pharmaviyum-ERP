"""Tests for profile avatar image validation."""

from io import BytesIO

import pytest
from PIL import Image

from src.pharmaviyum.services.profile_avatar import get_profile_avatar_content_type


def _image_bytes(image_format: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color="white").save(buffer, format=image_format)
    return buffer.getvalue()


def test_accepts_png_and_returns_verified_content_type() -> None:
    assert get_profile_avatar_content_type(_image_bytes("PNG")) == "image/png"


def test_accepts_jpeg_and_webp() -> None:
    assert get_profile_avatar_content_type(_image_bytes("JPEG")) == "image/jpeg"
    assert get_profile_avatar_content_type(_image_bytes("WEBP")) == "image/webp"


def test_rejects_unsupported_image_format() -> None:
    with pytest.raises(ValueError, match="Only JPEG, PNG, and WebP"):
        get_profile_avatar_content_type(_image_bytes("GIF"))


def test_rejects_non_image_payload() -> None:
    with pytest.raises(ValueError, match="valid supported image"):
        get_profile_avatar_content_type(b"not an image")
