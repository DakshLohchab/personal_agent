"""Simulation API endpoints."""

from fastapi import APIRouter

from packages.api_models.requests import SimulationRequest
from packages.api_models.responses import SimulationResponse
from services.simulator.engine import simulate

router = APIRouter(prefix="/api/v1", tags=["simulations"])


@router.post("/simulations", response_model=SimulationResponse)
def create_simulation(request: SimulationRequest) -> SimulationResponse:
    result = simulate(
        request.life_state,
        request.scenario,
        seed=request.seed,
        enable_uncertainty=request.enable_uncertainty,
        monte_carlo_samples=request.monte_carlo_samples,
    )
    return SimulationResponse.from_domain(result)
