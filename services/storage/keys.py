"""Server-generated object-key helpers."""

import re
from uuid import UUID


def safe_filename(filename: str) -> str:
    basename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", basename).strip("._")
    return (safe or "file")[:255]


def object_key(
    user_id: UUID, object_id: UUID, filename: str, *, kind: str = "files"
) -> str:
    if kind not in {"files", "artifacts"}:
        raise ValueError("object key kind must be files or artifacts")
    return f"users/{user_id}/{kind}/{object_id}/{safe_filename(filename)}"
