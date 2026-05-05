from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings


ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def public_url_for_path(path: str | Path | None) -> str | None:
    if not path:
        return None
    settings = get_settings()
    path_obj = Path(path)
    try:
        relative = path_obj.relative_to(settings.storage_dir)
    except ValueError:
        relative = path_obj
    return f"{settings.public_base_url}/media/{relative.as_posix()}"


def _validate_image_content(content: bytes, content_type: str, max_bytes: int) -> str:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Only JPEG, PNG, and WebP images are supported")
    if not content:
        raise ValueError("Image file is empty")
    if len(content) > max_bytes:
        raise ValueError(f"Image exceeds the {max_bytes // (1024 * 1024)} MB size limit")

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Uploaded file is not a valid image") from exc

    return ALLOWED_IMAGE_TYPES[content_type]


def _save_content(content: bytes, suffix: str, subdir: str) -> Path:
    filename = f"{uuid4().hex}{suffix}"
    destination = get_settings().storage_dir / subdir / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination


def save_upload_file(file: UploadFile, subdir: str = "uploads") -> Path:
    content = file.file.read()
    suffix = _validate_image_content(content, file.content_type or "application/octet-stream", get_settings().max_upload_bytes)
    return _save_content(content, suffix, subdir)


def save_bytes_file(content: bytes, content_type: str, subdir: str = "uploads", *, max_bytes: int | None = None) -> Path:
    suffix = _validate_image_content(content, content_type, max_bytes or get_settings().max_upload_bytes)
    return _save_content(content, suffix, subdir)
