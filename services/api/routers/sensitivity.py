"""Sensitivity analysis API routes."""

from fastapi import APIRouter

from packages.api_models.requests import SensitivityRequest
from packages.api_models.responses import SensitivityResultResponse
from services.simulator.sensitivity import sensitivity_analysis

router = APIRouter(prefix="/api/v1", tags=["sensitivity"])


@router.post("/sensitivity", response_model=list[SensitivityResultResponse])
def analyze_sensitivity(request: SensitivityRequest) -> list[SensitivityResultResponse]:
    results = sensitivity_analysis(
        request.life_state,
        request.scenario,
        request.variable_keys,
        perturbation_percent=request.perturbation_percent,
    )
    return [SensitivityResultResponse.from_domain(item) for item in results]
