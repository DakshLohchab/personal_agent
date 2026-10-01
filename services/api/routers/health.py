"""Health router."""

from fastapi import APIRouter

from packages.api_models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="life-sandbox-api", version="0.1.0")
