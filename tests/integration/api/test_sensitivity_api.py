from unittest.mock import Mock

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_sensitivity_endpoint_returns_valid_results() -> None:
    response = client.post(
        "/api/v1/sensitivity",
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
            "variable_keys": ["monthly_income", "monthly_essential_expenses"],
            "perturbation_percent": "10",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 2
    assert payload[0]["variable_key"] in {"monthly_income", "monthly_essential_expenses"}
    assert isinstance(payload[0]["baseline_ending_cash"], str)
    assert isinstance(payload[0]["absolute_impact"], str)


def test_sensitivity_endpoint_calls_application_service(monkeypatch) -> None:
    from services.api.routers import sensitivity as sensitivity_router

    service = Mock()
    service.sensitivity_analysis.return_value = []
    monkeypatch.setattr(sensitivity_router, "analysis_service", service)

    response = client.post(
        "/api/v1/sensitivity",
        json={
            "life_state": {
                "start_date": "2026-01-01",
                "horizon_months": 1,
                "cash": 100,
                "monthly_income": 10,
                "monthly_essential_expenses": 5,
                "monthly_time_available_hours": 4,
            },
            "scenario": {"id": "base", "name": "Base"},
            "variable_keys": ["monthly_income"],
        },
    )

    assert response.status_code == 200
    assert response.json() == []
    service.sensitivity_analysis.assert_called_once()
