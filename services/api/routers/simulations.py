"""Simulation API endpoints."""

from fastapi import APIRouter

from packages.api_models.requests import SimulationRequest
from packages.api_models.responses import SimulationResponse
from services.api.decimal_json import DecimalJSONRoute
from services.application.simulation_service import SimulationService

router = APIRouter(prefix="/api/v1", tags=["simulations"], route_class=DecimalJSONRoute)
simulation_service = SimulationService()


@router.post("/simulations", response_model=SimulationResponse)
def create_simulation(request: SimulationRequest) -> SimulationResponse:
    result = simulation_service.run(
        request.life_state,
        request.scenario,
        seed=request.seed,
        enable_uncertainty=request.enable_uncertainty,
        monte_carlo_samples=request.monte_carlo_samples,
    )
    return SimulationResponse.from_domain(result)
