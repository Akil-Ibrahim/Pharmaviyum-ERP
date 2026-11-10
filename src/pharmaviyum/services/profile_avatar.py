"""Validation helpers for user-uploaded profile photos."""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

_AVATAR_CONTENT_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
_MAX_AVATAR_DIMENSION = 4096


def get_profile_avatar_content_type(contents: bytes) -> str:
    """Validate image bytes and return a trusted media type."""
    try:
        with Image.open(BytesIO(contents)) as image:
            image_format = image.format
            if image_format is None or image_format not in _AVATAR_CONTENT_TYPES:
                raise ValueError("Only JPEG, PNG, and WebP images are supported.")
            if (
                image.width > _MAX_AVATAR_DIMENSION
                or image.height > _MAX_AVATAR_DIMENSION
            ):
                raise ValueError(
                    "Image dimensions must not exceed 4096 × 4096 pixels."
                )
            image.verify()
    except (
        Image.DecompressionBombError,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
    ) as exc:
        raise ValueError("The uploaded file is not a valid supported image.") from exc

    return _AVATAR_CONTENT_TYPES[image_format]
