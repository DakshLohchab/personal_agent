"""Authenticated structured memory endpoints."""

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from packages.ports.auth import AuthPrincipal
from services.api.dependencies import get_current_principal
from services.memory.service import MemoryPolicyError, MemoryService
from services.persistence.database import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


class MemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    memory_type: Literal[
        "preference",
        "stable_constraint",
        "goal",
        "commitment",
        "past_decision",
        "correction",
        "workflow_pattern",
    ]
    content: str = Field(min_length=1)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    provenance_type: (
        Literal[
            "user_confirmed", "user_input", "prior_decision", "system_derived", "imported_source"
        ]
        | None
    ) = None
    provenance_ref: str | None = None
    confidence: float | None = None
    status: Literal["candidate"] = "candidate"
    retention_policy: str = "persistent"
    expires_at: Any | None = None


class MemoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str | None = None
    structured_data: dict[str, Any] | None = None
    confidence: float | None = None
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
        try:
            return MemoryService(uow.memories, uow.embeddings).create_memory(
                principal.user_id, request.model_dump()
            )
        except MemoryPolicyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


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


@router.post("/relevant")
def relevant_memories(
    request: dict[str, Any],
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> list[dict[str, Any]]:
    context = request.get("decision_context")
    if not isinstance(context, (str, dict)):
        raise HTTPException(status_code=422, detail="decision_context must be text or an object")
    with SqlAlchemyUnitOfWork(principal) as uow:
        memories = MemoryService(uow.memories, uow.embeddings).retrieve_relevant_memories(
            principal.user_id,
            context,
            filters=set(request.get("memory_types", [])),
            limit=int(request.get("limit", 10)),
        )
    return [memory.model_dump(mode="json") for memory in memories]


@router.post("/{memory_id}/approve")
def approve_memory(
    memory_id: UUID,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> dict:
    with SqlAlchemyUnitOfWork(principal) as uow:
        result = MemoryService(uow.memories).approve_memory(principal.user_id, memory_id)
        if result is None:
            raise HTTPException(status_code=404, detail="memory not found")
        return result


@router.patch("/{memory_id}")
def update_memory(
    memory_id: UUID,
    request: MemoryPatch,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> dict:
    with SqlAlchemyUnitOfWork(principal) as uow:
        try:
            result = MemoryService(uow.memories, uow.embeddings).update_memory(
                principal.user_id, memory_id, request.model_dump(exclude_unset=True)
            )
        except MemoryPolicyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
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
