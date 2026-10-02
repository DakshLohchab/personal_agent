from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_unexpected_errors_return_500_without_stack_trace(caplog) -> None:
    from services.api.routers import simulations as simulations_router

    original = simulations_router.simulation_service.run
    simulations_router.simulation_service.run = lambda *args, **kwargs: (
        _ for _ in ()
    ).throw(RuntimeError("boom"))
    try:
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
                "enable_uncertainty": False,
            },
        )
    finally:
        simulations_router.simulation_service.run = original

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "boom" not in payload["error"]["message"]
    assert "Traceback" not in response.text
    assert "request failed" in caplog.text
    assert "boom" not in caplog.text
    assert "Traceback" not in caplog.text
