from decimal import Decimal
from unittest.mock import Mock

from services.application.analysis_service import AnalysisService
from services.application.simulation_service import SimulationService
from tests.fixtures.golden_cases import golden_cases


def test_simulation_service_runs_real_phase_one_engine() -> None:
    case = golden_cases()[0]

    result = SimulationService().run(
        case.state,
        case.scenario,
        seed=42,
        enable_uncertainty=False,
        monte_carlo_samples=1,
    )

    assert result.metrics.ending_cash == case.expected_final_cash


def test_analysis_service_delegates_to_existing_operations(monkeypatch) -> None:
    from services.application import analysis_service as analysis_module

    case = golden_cases()[0]
    sensitivity_result = []
    sensitivity_mock = Mock(return_value=sensitivity_result)
    breakpoint_mock = Mock(return_value=Decimal("125.5"))
    monkeypatch.setattr(analysis_module, "sensitivity_analysis", sensitivity_mock)
    monkeypatch.setattr(analysis_module, "find_breakpoint", breakpoint_mock)
    service = AnalysisService()

    sensitivity = service.sensitivity_analysis(
        case.state,
        case.scenario,
        ["monthly_income"],
        perturbation_percent=Decimal("5"),
    )
    breakpoint = service.find_breakpoint(
        case.state,
        case.scenario,
        "cash",
        Decimal("100"),
        Decimal("200"),
        "reserve",
        tolerance=Decimal("0.5"),
    )

    assert sensitivity == sensitivity_result
    assert breakpoint == Decimal("125.5")
    sensitivity_mock.assert_called_once_with(
        case.state,
        case.scenario,
        ["monthly_income"],
        perturbation_percent=Decimal("5"),
    )
    breakpoint_mock.assert_called_once_with(
        case.state,
        case.scenario,
        "cash",
        Decimal("100"),
        Decimal("200"),
        "reserve",
        tolerance=Decimal("0.5"),
    )