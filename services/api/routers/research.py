"""Research and evidence endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from packages.ports.auth import AuthPrincipal
from packages.ports.research import ResearchProvider
from services.api.dependencies import get_current_principal, get_research_provider
from services.persistence.database import SqlAlchemyUnitOfWork
from services.research.service import ResearchService

router = APIRouter(prefix="/api/v1", tags=["research"])


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    max_results: int = Field(default=10, ge=1, le=50)


class SourceResponse(BaseModel):
    id: UUID
    url: str
    title: str | None
    publisher: str | None
    source_type: str | None
    retrieved_at: datetime
    snippet: str | None
    content_hash: str | None


class ResearchResponse(BaseModel):
    research_query_id: UUID
    sources: list[SourceResponse]


class EvidenceRequest(BaseModel):
    research_source_id: UUID
    claim_text: str = Field(min_length=1, max_length=4000)
    evidence_text: str = Field(min_length=1, max_length=4000)


@router.post("/research", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
def search_research(
    request: ResearchRequest,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
    provider: Annotated[ResearchProvider, Depends(get_research_provider)],
) -> ResearchResponse:
    try:
        with SqlAlchemyUnitOfWork(principal) as uow:
            result = ResearchService(provider, uow.research).search(
                principal.user_id, request.query, request.max_results
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="research provider unavailable") from exc
    return ResearchResponse.model_validate(result)


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
def create_evidence(
    request: EvidenceRequest,
    principal: Annotated[AuthPrincipal, Depends(get_current_principal)],
) -> dict:
    with SqlAlchemyUnitOfWork(principal) as uow:
        try:
            return uow.evidence.create(principal.user_id, request.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
