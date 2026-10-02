"""Breakpoint search API routes."""

from fastapi import APIRouter

from packages.api_models.requests import BreakpointRequest
from packages.api_models.responses import BreakpointResponse
from services.api.decimal_json import DecimalJSONRoute
from services.application.analysis_service import AnalysisService

router = APIRouter(prefix="/api/v1", tags=["breakpoints"], route_class=DecimalJSONRoute)
analysis_service = AnalysisService()


@router.post("/breakpoints", response_model=BreakpointResponse)
def find_breakpoint_for_constraint(request: BreakpointRequest) -> BreakpointResponse:
    breakpoint = analysis_service.find_breakpoint(
        request.life_state,
        request.scenario,
        request.variable_key,
        request.lower_bound,
        request.upper_bound,
        request.target_constraint_id,
        tolerance=request.tolerance,
    )
    return BreakpointResponse(
        variable_key=request.variable_key,
        breakpoint=breakpoint,
        target_constraint_id=request.target_constraint_id,
    )
