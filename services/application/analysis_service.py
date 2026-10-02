"""Sensitivity and breakpoint use-case coordination."""

from decimal import Decimal

from packages.schemas import LifeState, Scenario
from packages.schemas.simulation import SensitivityResult
from services.simulator.breakpoint import find_breakpoint
from services.simulator.sensitivity import sensitivity_analysis


class AnalysisService:
    def sensitivity_analysis(
        self,
        life_state: LifeState,
        scenario: Scenario,
        variable_keys: list[str],
        *,
        perturbation_percent: Decimal,
    ) -> list[SensitivityResult]:
        return sensitivity_analysis(
            life_state,
            scenario,
            variable_keys,
            perturbation_percent=perturbation_percent,
        )

    def find_breakpoint(
        self,
        life_state: LifeState,
        scenario: Scenario,
        variable_key: str,
        lower_bound: Decimal,
        upper_bound: Decimal,
        target_constraint_id: str,
        *,
        tolerance: Decimal,
    ) -> Decimal | None:
        return find_breakpoint(
            life_state,
            scenario,
            variable_key,
            lower_bound,
            upper_bound,
            target_constraint_id,
            tolerance=tolerance,
        )