from services.simulator.engine import simulate
from tests.fixtures.golden_cases import golden_cases


def test_golden_simulations_are_exact_and_reproducible() -> None:
    for case in golden_cases():
        first = simulate(
            case.state,
            case.scenario,
            seed=7,
            enable_uncertainty=False,
            monte_carlo_samples=1,
            scenario_catalog=case.scenario_catalog,
        )
        second = simulate(
            case.state,
            case.scenario,
            seed=7,
            enable_uncertainty=False,
            monte_carlo_samples=1,
            scenario_catalog=case.scenario_catalog,
        )
        assert first == second, case.name
        assert (
            tuple(item.ending_cash for item in first.monthly_states)
            == case.expected_monthly_cash
        )
        assert first.metrics.ending_cash == case.expected_final_cash
        assert first.metrics.minimum_cash == case.expected_minimum_cash
        assert first.metrics.total_spend == case.expected_total_spend
