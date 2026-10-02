"""Sensitivity analysis API routes."""

from fastapi import APIRouter

from packages.api_models.requests import SensitivityRequest
from packages.api_models.responses import SensitivityResultResponse
from services.api.decimal_json import DecimalJSONRoute
from services.application.analysis_service import AnalysisService

router = APIRouter(prefix="/api/v1", tags=["sensitivity"], route_class=DecimalJSONRoute)
analysis_service = AnalysisService()


@router.post("/sensitivity", response_model=list[SensitivityResultResponse])
def analyze_sensitivity(request: SensitivityRequest) -> list[SensitivityResultResponse]:
    results = analysis_service.sensitivity_analysis(
        request.life_state,
        request.scenario,
        request.variable_keys,
        perturbation_percent=request.perturbation_percent,
    )
    return [SensitivityResultResponse.from_domain(item) for item in results]
