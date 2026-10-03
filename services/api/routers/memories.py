"""Authenticated structured memory endpoints."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from packages.ports.auth import AuthPrincipal
from services.api.dependencies import get_current_principal
from services.memory.service import MemoryService
from services.persistence.database import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


class MemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    memory_type: str = Field(min_length=1)
    content: str = Field(min_length=1)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    provenance_type: str | None = None
    provenance_ref: str | None = None
    confidence: float | None = None
    status: str = "active"
    retention_policy: str = "persistent"
    expires_at: Any | None = None


class MemoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str | None = None
    structured_data: dict[str, Any] | None = None
    confidence: float | None = None
    status: str | None = None
    retention_policy: str | None = None
    expires_at: Any | None = None


def _service(principal: AuthPrincipal) -> MemoryService:
    uow = SqlAlchemyUnitOfWork(principal)
    return MemoryService(uow.memories, uow.embeddings)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_memory(
    request: MemoryRequest,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> dict:
    with SqlAlchemyUnitOfWork(principal) as uow:
        return MemoryService(uow.memories, uow.embeddings).create_memory(
            principal.user_id, request.model_dump()
        )


@router.get("")
def list_memories(
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> list[dict]:
    with SqlAlchemyUnitOfWork(principal) as uow:
        return MemoryService(uow.memories, uow.embeddings).list_memories(principal.user_id)


class MemorySearchRequest(BaseModel):
    query_embedding: list[float] = Field(min_length=1)
    model_name: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


@router.post("/search")
def search_memories(
    request: MemorySearchRequest,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> list[dict]:
    with SqlAlchemyUnitOfWork(principal) as uow:
        results = MemoryService(uow.memories, uow.embeddings).search_memories(
            principal.user_id, request.query_embedding, request.model_name, request.limit
        )
    return [{key: value for key, value in item.items() if key != "embedding"} for item in results]


@router.patch("/{memory_id}")
def update_memory(
    memory_id: UUID,
    request: MemoryPatch,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> dict:
    with SqlAlchemyUnitOfWork(principal) as uow:
        result = MemoryService(uow.memories, uow.embeddings).update_memory(
            principal.user_id, memory_id, request.model_dump(exclude_unset=True)
        )
        if result is None:
            raise HTTPException(status_code=404, detail="memory not found")
        return result


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> None:
    with SqlAlchemyUnitOfWork(principal) as uow:
        if not MemoryService(uow.memories).delete_memory(principal.user_id, memory_id):
            raise HTTPException(status_code=404, detail="memory not found")
