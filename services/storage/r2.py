"""Cloudflare R2 adapter using its S3-compatible API."""

from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from packages.ports.object_store import ObjectMetadata


@dataclass(frozen=True, slots=True)
class R2Settings:
    account_id: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    endpoint_url: str
    presign_ttl_seconds: int = 300
    max_upload_bytes: int = 50 * 1024 * 1024

    def validate(self) -> None:
        if self.presign_ttl_seconds < 1:
            raise ValueError("R2_PRESIGN_TTL_SECONDS must be positive")
        if self.max_upload_bytes < 1:
            raise ValueError("R2_MAX_UPLOAD_BYTES must be positive")


class R2ObjectStore:
    def __init__(self, settings: R2Settings, client: BaseClient | None = None) -> None:
        settings.validate()
        self._bucket = settings.bucket
        self._client = client or boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
            region_name="auto",
        )

    def create_presigned_upload(
        self, object_key: str, *, content_type: str, expires_in: int
    ) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": object_key, "ContentType": content_type},
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

    def create_presigned_download(self, object_key: str, *, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": object_key},
            ExpiresIn=expires_in,
            HttpMethod="GET",
        )

    def head_object(self, object_key: str) -> ObjectMetadata | None:
        try:
            result = self._client.head_object(Bucket=self._bucket, Key=object_key)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            if error.get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        return ObjectMetadata(
            size_bytes=int(result["ContentLength"]),
            content_type=result.get("ContentType"),
        )

    def delete_object(self, object_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=object_key)
