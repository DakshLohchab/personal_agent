"""Run a small offline simulation from the command line."""

from datetime import date
from decimal import Decimal

from packages.schemas.life_state import LifeState
from packages.schemas.scenario import Scenario

from .engine import simulate


def main() -> None:
    state = LifeState(
        start_date=date(2026, 1, 1),
        horizon_months=6,
        cash=Decimal(50000),
        monthly_income=Decimal(20000),
        monthly_essential_expenses=Decimal(12000),
        monthly_time_available_hours=Decimal(40),
    )
    scenario = Scenario(
        id="save-5000",
        name="Save 5000",
        deltas={"cash": Decimal(5000)},
    )
    result = simulate(state, scenario, enable_uncertainty=False)
    print(f"scenario={scenario.id}")
    print(f"ending_cash={result.metrics.ending_cash}")
    print(f"minimum_cash={result.metrics.minimum_cash}")
    print(f"total_spend={result.metrics.total_spend}")


if __name__ == "__main__":
    main()