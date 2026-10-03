"""Provider-neutral object storage contract."""

from typing import Protocol


class ObjectStore(Protocol):
    def create_presigned_upload(
        self, object_key: str, *, content_type: str, expires_in: int
    ) -> str: ...

    def create_presigned_download(self, object_key: str, *, expires_in: int) -> str: ...

    def head_object(self, object_key: str) -> "ObjectMetadata | None": ...

    def delete_object(self, object_key: str) -> None: ...


class ObjectMetadata:
    def __init__(self, *, size_bytes: int, content_type: str | None = None) -> None:
        self.size_bytes = size_bytes
        self.content_type = content_type
