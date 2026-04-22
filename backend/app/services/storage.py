import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

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


def save_upload_file(file: UploadFile, subdir: str = "uploads") -> Path:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Only JPEG, PNG, and WebP images are supported")
    suffix = ALLOWED_IMAGE_TYPES[file.content_type]
    filename = f"{uuid4().hex}{suffix}"
    destination = get_settings().storage_dir / subdir / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return destination


def save_bytes_file(content: bytes, content_type: str, subdir: str = "uploads") -> Path:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Only JPEG, PNG, and WebP images are supported")
    suffix = ALLOWED_IMAGE_TYPES[content_type]
    filename = f"{uuid4().hex}{suffix}"
    destination = get_settings().storage_dir / subdir / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination
