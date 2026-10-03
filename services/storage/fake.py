"""In-memory object store for deterministic API tests."""

from __future__ import annotations

from packages.ports.object_store import ObjectMetadata


class FakeObjectStore:
    def __init__(self) -> None:
        self.objects: dict[str, ObjectMetadata] = {}
        self.deleted: list[str] = []

    def create_presigned_upload(
        self, object_key: str, *, content_type: str, expires_in: int
    ) -> str:
        return f"https://fake-r2.invalid/upload/{object_key}?expires_in={expires_in}"

    def create_presigned_download(self, object_key: str, *, expires_in: int) -> str:
        return f"https://fake-r2.invalid/download/{object_key}?expires_in={expires_in}"

    def head_object(self, object_key: str) -> ObjectMetadata | None:
        return self.objects.get(object_key)

    def delete_object(self, object_key: str) -> None:
        self.objects.pop(object_key, None)
        self.deleted.append(object_key)

    def put_object(self, object_key: str, *, size_bytes: int, content_type: str) -> None:
        self.objects[object_key] = ObjectMetadata(
            size_bytes=size_bytes, content_type=content_type
        )
