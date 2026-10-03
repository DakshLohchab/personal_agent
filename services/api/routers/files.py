"""Private user file upload, download, and lifecycle endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from packages.ports.auth import AuthPrincipal
from packages.ports.object_store import ObjectStore
from services.api.dependencies import get_current_principal, get_object_store, get_settings
from services.persistence.database import SqlAlchemyUnitOfWork
from services.storage.keys import object_key, safe_filename

router = APIRouter(prefix="/api/v1/files", tags=["files"])
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "image/png",
    "image/jpeg",
    "text/plain",
    "application/json",
}


class UploadURLRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str
    size_bytes: int = Field(ge=0)

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, value: str) -> str:
        if value not in ALLOWED_MIME_TYPES:
            raise ValueError("unsupported MIME type")
        return value


class UploadURLResponse(BaseModel):
    file_id: UUID
    object_key: str
    upload_url: str
    expires_in: int


class DownloadURLResponse(BaseModel):
    download_url: str
    expires_in: int


def _uow(principal: AuthPrincipal) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(principal)


@router.post("/upload-url", response_model=UploadURLResponse, status_code=status.HTTP_201_CREATED)
def create_upload_url(
    request: UploadURLRequest,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
    object_store: Annotated[ObjectStore, Depends(get_object_store)],
) -> UploadURLResponse:
    settings = get_settings()
    if request.size_bytes > settings.r2_max_upload_bytes:
        raise HTTPException(status_code=413, detail="file exceeds maximum upload size")
    filename = safe_filename(request.filename)
    file_id = uuid4()
    with _uow(principal) as unit_of_work:
        record = unit_of_work.files.create(
            principal.user_id,
            {
                "original_filename": filename,
                "id": file_id,
                "mime_type": request.mime_type,
                "size_bytes": request.size_bytes,
                "object_key": object_key(principal.user_id, file_id, filename),
                "created_by": principal.user_id,
                "status": "pending",
                "extraction_status": "not_started",
            },
        )
        upload_url = object_store.create_presigned_upload(
            record["object_key"],
            content_type=request.mime_type,
            expires_in=settings.r2_presign_ttl_seconds,
        )
    return UploadURLResponse(
        file_id=record["id"],
        object_key=record["object_key"],
        upload_url=upload_url,
        expires_in=settings.r2_presign_ttl_seconds,
    )


@router.post("/{file_id}/complete")
def complete_upload(
    file_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
    object_store: Annotated[ObjectStore, Depends(get_object_store)],
) -> dict[str, str]:
    with _uow(principal) as unit_of_work:
        record = unit_of_work.files.get(principal.user_id, file_id)
        if record is None:
            raise HTTPException(status_code=404, detail="file not found")
        metadata = object_store.head_object(record["object_key"])
        if metadata is None:
            raise HTTPException(status_code=409, detail="uploaded object was not found")
        if metadata.size_bytes != record["size_bytes"]:
            raise HTTPException(status_code=409, detail="uploaded object size mismatch")
        if metadata.content_type and metadata.content_type != record["mime_type"]:
            raise HTTPException(status_code=409, detail="uploaded object content type mismatch")
        unit_of_work.files.update(
            principal.user_id, file_id, {"status": "uploaded", "uploaded_at": datetime.now(UTC)}
        )
    return {"status": "uploaded"}


@router.post("/{file_id}/download-url", response_model=DownloadURLResponse)
def create_download_url(
    file_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
    object_store: Annotated[ObjectStore, Depends(get_object_store)],
) -> DownloadURLResponse:
    settings = get_settings()
    with _uow(principal) as unit_of_work:
        record = unit_of_work.files.get(principal.user_id, file_id)
        if record is None or record["status"] == "deleted":
            raise HTTPException(status_code=404, detail="file not found")
        url = object_store.create_presigned_download(
            record["object_key"], expires_in=settings.r2_presign_ttl_seconds
        )
    return DownloadURLResponse(download_url=url, expires_in=settings.r2_presign_ttl_seconds)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
    object_store: Annotated[ObjectStore, Depends(get_object_store)],
) -> None:
    with _uow(principal) as unit_of_work:
        record = unit_of_work.files.get(principal.user_id, file_id)
        if record is None:
            raise HTTPException(status_code=404, detail="file not found")
        object_store.delete_object(record["object_key"])
        unit_of_work.files.update(principal.user_id, file_id, {"status": "deleted"})
