from decimal import Decimal
from unittest.mock import Mock

from fastapi.testclient import TestClient

from packages.schemas import LifeState, Scenario
from services.api.main import app
from services.simulator.breakpoint import find_breakpoint

client = TestClient(app)


def _state() -> dict:
    return {
        "start_date": "2026-01-01",
        "horizon_months": 12,
        "cash": 50000,
        "monthly_income": 20000,
        "monthly_essential_expenses": 12000,
        "monthly_time_available_hours": 40,
    }


def test_breakpoint_endpoint_returns_correct_result() -> None:
    request = {
        "life_state": {
            **_state(),
            "constraints": [
                {"id": "reserve", "name": "Reserve", "metric": "minimum_cash", "limit": 60000}
            ],
        },
        "scenario": {"id": "base", "name": "Base"},
        "variable_key": "cash",
        "lower_bound": "50000",
        "upper_bound": "60000",
        "target_constraint_id": "reserve",
        "tolerance": "1",
    }
    state = LifeState.model_validate(request["life_state"])
    scenario = Scenario.model_validate(request["scenario"])
    expected = find_breakpoint(
        state,
        scenario,
        request["variable_key"],
        Decimal(request["lower_bound"]),
        Decimal(request["upper_bound"]),
        request["target_constraint_id"],
        tolerance=Decimal(request["tolerance"]),
    )

    response = client.post("/api/v1/breakpoints", json=request)

    assert response.status_code == 200
    payload = response.json()
    assert payload["variable_key"] == "cash"
    assert payload["target_constraint_id"] == "reserve"
    assert Decimal(payload["breakpoint"]) == expected


def test_breakpoint_endpoint_returns_none_when_no_breakpoint_exists() -> None:
    request = {
        "life_state": {
            **_state(),
            "constraints": [
                {"id": "reserve", "name": "Reserve", "metric": "minimum_cash", "limit": 1}
            ],
            "variables": [{"key": "laptop_cost", "value": 100, "unit": "currency"}],
        },
        "scenario": {"id": "base", "name": "Base"},
        "variable_key": "laptop_cost",
        "lower_bound": "0",
        "upper_bound": "200",
        "target_constraint_id": "reserve",
        "tolerance": "1",
    }

    response = client.post("/api/v1/breakpoints", json=request)

    assert response.status_code == 200
    assert response.json()["breakpoint"] is None


def test_breakpoint_endpoint_calls_application_service(monkeypatch) -> None:
    from services.api.routers import breakpoints as breakpoints_router

    service = Mock()
    service.find_breakpoint.return_value = Decimal("125.50")
    monkeypatch.setattr(breakpoints_router, "analysis_service", service)

    response = client.post(
        "/api/v1/breakpoints",
        json={
            "life_state": _state(),
            "scenario": {"id": "base", "name": "Base"},
            "variable_key": "cash",
            "lower_bound": "100",
            "upper_bound": "200",
            "target_constraint_id": "reserve",
        },
    )

    assert response.status_code == 200
    assert response.json()["breakpoint"] == "125.50"
    service.find_breakpoint.assert_called_once()
