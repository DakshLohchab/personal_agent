"""Simulation use-case coordination."""

from packages.schemas import LifeState, Scenario
from packages.schemas.simulation import SimulationResult
from services.simulator.engine import simulate


class SimulationService:
    def run(
        self,
        life_state: LifeState,
        scenario: Scenario,
        *,
        seed: int,
        enable_uncertainty: bool,
        monte_carlo_samples: int,
    ) -> SimulationResult:
        return simulate(
            life_state,
            scenario,
            seed=seed,
            enable_uncertainty=enable_uncertainty,
            monte_carlo_samples=monte_carlo_samples,
        )