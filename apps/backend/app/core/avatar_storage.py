"""Shared local-disk storage helper for entity profile pictures / logos.

Files are written under ``settings.UPLOAD_DIR/avatars/<entity_type>/<uuid4>.<ext>``
with randomized filenames. The relative path (e.g. ``avatars/users/<uuid4>.jpg``) is
stored on the entity's ``avatar_path`` column and is never exposed to the frontend —
images are served via authenticated ``GET /{resource}/{id}/avatar`` endpoints that
call :func:`read_avatar`.
"""
import io
import mimetypes
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.core.exceptions import BadRequestException

# Content-types accepted for avatar uploads, mapped to a file extension.
ALLOWED_TYPES: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _upload_root() -> Path:
    return Path(get_settings().UPLOAD_DIR) / "avatars"


def validate_image(content: bytes, content_type: str | None) -> str:
    """Validate an uploaded avatar and return its file extension.

    Raises ``BadRequestException`` if the content-type isn't allowed, the file is
    too large, or the bytes aren't a valid image (corrupt/non-image upload).
    """
    if content_type not in ALLOWED_TYPES:
        raise BadRequestException(
            f"Unsupported image type '{content_type}'. Allowed: {', '.join(ALLOWED_TYPES)}"
        )

    max_bytes = get_settings().MAX_AVATAR_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise BadRequestException(
            f"Image too large. Maximum size is {get_settings().MAX_AVATAR_SIZE_MB} MB"
        )

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError):
        raise BadRequestException("Uploaded file is not a valid image")

    return ALLOWED_TYPES[content_type]


def save_avatar(entity_type: str, content: bytes, ext: str) -> str:
    """Write the image bytes to disk and return the relative path to store."""
    directory = _upload_root() / entity_type
    directory.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    (directory / filename).write_bytes(content)

    return f"avatars/{entity_type}/{filename}"


def delete_avatar(path: str | None) -> None:
    """Remove a previously-stored avatar file, if any. Never raises."""
    if not path:
        return

    file_path = Path(get_settings().UPLOAD_DIR) / path
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass


def read_avatar(path: str) -> tuple[bytes, str]:
    """Read a stored avatar's bytes and guess its MIME type."""
    file_path = Path(get_settings().UPLOAD_DIR) / path
    content = file_path.read_bytes()
    mime_type, _ = mimetypes.guess_type(file_path.name)
    return content, mime_type or "application/octet-stream"
