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
