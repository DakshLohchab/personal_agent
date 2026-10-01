from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from packages.schemas import LifeState, Scenario
from services.api.main import app
from services.simulator.engine import simulate

client = TestClient(app)


def _base_state() -> LifeState:
    return LifeState.model_validate(
        {
            "start_date": date(2026, 1, 1),
            "horizon_months": 12,
            "cash": Decimal(50000),
            "monthly_income": Decimal(20000),
            "monthly_essential_expenses": Decimal(12000),
            "monthly_time_available_hours": Decimal(40),
        }
    )


def test_simulation_endpoint_returns_200_for_valid_request() -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 12,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
            },
            "scenario": {"id": "laptop", "name": "Laptop", "deltas": {"cash": -35000}},
            "seed": 42,
            "enable_uncertainty": False,
            "monte_carlo_samples": 100,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    reference = simulate(
        _base_state(),
        Scenario(id="laptop", name="Laptop", deltas={"cash": Decimal(-35000)}),
        seed=42,
        enable_uncertainty=False,
        monte_carlo_samples=100,
    )
    assert payload["summary"]["ending_cash"] == str(reference.metrics.ending_cash)
    assert payload["summary"]["minimum_cash"] == str(reference.metrics.minimum_cash)
    assert payload["summary"]["total_spend"] == str(reference.metrics.total_spend)
    assert payload["summary"]["total_time_used"] == str(
        reference.metrics.total_time_used
    )
    assert payload["monthly_states"][0]["ending_cash"] == str(
        reference.monthly_states[0].ending_cash
    )
    assert payload["engine_version"] == "0.1.0"
    assert payload["schema_version"] == "0.1.0"


def test_invalid_life_state_returns_422() -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 0,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
            },
            "scenario": {"id": "base", "name": "Base"},
        },
    )

    assert response.status_code == 422


def test_invalid_scenario_returns_422() -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 12,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
            },
            "scenario": {"id": "bad", "name": "Bad", "deltas": {"unknown_key": -500}},
        },
    )

    assert response.status_code == 422


def test_invalid_monte_carlo_sample_count_returns_422() -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 12,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
            },
            "scenario": {"id": "base", "name": "Base"},
            "monte_carlo_samples": 0,
        },
    )

    assert response.status_code == 422


def test_simulation_results_are_deterministic_with_seed() -> None:
    body = {
        "life_state": {
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "cash": 50000,
            "monthly_income": 20000,
            "monthly_essential_expenses": 12000,
            "monthly_time_available_hours": 40,
        },
        "scenario": {"id": "laptop", "name": "Laptop", "deltas": {"cash": -35000}},
        "seed": 42,
        "enable_uncertainty": True,
        "monte_carlo_samples": 250,
    }

    first = client.post("/api/v1/simulations", json=body)
    second = client.post("/api/v1/simulations", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_simulation_endpoint_uses_phase_1_engine() -> None:
    state = _base_state()
    scenario = Scenario(id="laptop", name="Laptop", deltas={"cash": Decimal(-35000)})
    reference = simulate(state, scenario, enable_uncertainty=False)

    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 12,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
            },
            "scenario": {"id": "laptop", "name": "Laptop", "deltas": {"cash": -35000}},
            "enable_uncertainty": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["ending_cash"] == str(reference.metrics.ending_cash)
    assert payload["monthly_states"][0]["ending_cash"] == str(
        reference.monthly_states[0].ending_cash
    )


def test_simulation_money_values_are_json_strings() -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 12,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
            },
            "scenario": {"id": "laptop", "name": "Laptop", "deltas": {"cash": -35000}},
            "enable_uncertainty": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    for field in [
        "ending_cash",
        "minimum_cash",
        "total_spend",
        "total_time_used",
        "starting_cash",
        "income",
        "essential_expenses",
    ]:
        assert isinstance(payload["summary"].get(field, "0"), str)
        assert isinstance(payload["monthly_states"][0].get(field, "0"), str)


def test_constraint_violations_are_preserved() -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 2,
                "cash": 50000,
                "monthly_income": 20000,
                "monthly_essential_expenses": 12000,
                "monthly_time_available_hours": 40,
                "constraints": [
                    {
                        "id": "emergency_fund",
                        "name": "Emergency fund",
                        "metric": "minimum_cash",
                        "limit": 20000,
                    }
                ],
            },
            "scenario": {
                "id": "large-purchase",
                "name": "Large purchase",
                "deltas": {"cash": -60000},
            },
            "enable_uncertainty": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["constraint_violations"][0]["constraint_id"] == "emergency_fund"
    assert payload["constraint_violations"][0]["observed"] == "-2000"
