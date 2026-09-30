"""Exact deterministic scenarios used as regression fixtures."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from packages.schemas import Commitment, Constraint, LifeState, Scenario


@dataclass(frozen=True)
class GoldenCase:
    name: str
    state: LifeState
    scenario: Scenario
    expected_monthly_cash: tuple[Decimal, ...]
    expected_final_cash: Decimal
    expected_minimum_cash: Decimal
    expected_total_spend: Decimal
    expected_violations: tuple[tuple[int, str, Decimal, Decimal], ...] = ()
    scenario_catalog: dict[str, Scenario] | None = None


def base_state(**overrides: object) -> LifeState:
    values: dict[str, object] = {
        "start_date": date(2026, 1, 1),
        "horizon_months": 2,
        "cash": Decimal(50000),
        "monthly_income": Decimal(20000),
        "monthly_essential_expenses": Decimal(12000),
        "monthly_time_available_hours": Decimal(40),
    }
    values.update(overrides)
    return LifeState.model_validate(values)


def golden_cases() -> list[GoldenCase]:
    no_decision = Scenario(id="base", name="No decision")
    return [
        GoldenCase(
            "no decision",
            base_state(),
            no_decision,
            (Decimal(58000), Decimal(66000)),
            Decimal(66000),
            Decimal(58000),
            Decimal(24000),
        ),
        GoldenCase(
            "laptop purchase",
            base_state(),
            Scenario(id="laptop", name="Laptop", deltas={"cash": Decimal(-35000)}),
            (Decimal(23000), Decimal(31000)),
            Decimal(31000),
            Decimal(23000),
            Decimal(59000),
        ),
        GoldenCase(
            "travel purchase",
            base_state(),
            Scenario(
                id="travel",
                name="Travel",
                deltas={
                    "cash": Decimal(-15000),
                    "monthly_time_available_hours": Decimal(-20),
                },
            ),
            (Decimal(43000), Decimal(51000)),
            Decimal(51000),
            Decimal(43000),
            Decimal(39000),
        ),
        GoldenCase(
            "save money",
            base_state(),
            Scenario(id="save", name="Save", deltas={"cash": Decimal(5000)}),
            (Decimal(63000), Decimal(71000)),
            Decimal(71000),
            Decimal(63000),
            Decimal(24000),
        ),
        GoldenCase(
            "higher income",
            base_state(),
            Scenario(id="raise", name="Raise", deltas={"monthly_income": Decimal(5000)}),
            (Decimal(63000), Decimal(76000)),
            Decimal(76000),
            Decimal(63000),
            Decimal(24000),
        ),
        GoldenCase(
            "higher expenses",
            base_state(),
            Scenario(
                id="expenses", name="Expenses", deltas={"monthly_essential_expenses": Decimal(3000)}
            ),
            (Decimal(55000), Decimal(60000)),
            Decimal(60000),
            Decimal(55000),
            Decimal(30000),
        ),
        GoldenCase(
            "minimum cash violations",
            base_state(
                constraints=[
                    Constraint(
                        id="emergency_fund",
                        name="Emergency fund",
                        metric="minimum_cash",
                        limit=Decimal(20000),
                    )
                ]
            ),
            Scenario(id="large-purchase", name="Large purchase", deltas={"cash": Decimal(-60000)}),
            (Decimal(-2000), Decimal(6000)),
            Decimal(6000),
            Decimal(-2000),
            Decimal(84000),
            (
                (1, "emergency_fund", Decimal(-2000), Decimal(20000)),
                (2, "emergency_fund", Decimal(6000), Decimal(20000)),
            ),
        ),
        GoldenCase(
            "time constraint violation",
            base_state(
                monthly_time_available_hours=Decimal(20),
                commitments=[
                    Commitment(
                        id="care",
                        name="Care commitment",
                        monthly_cost=Decimal(500),
                        monthly_hours=Decimal(18),
                    )
                ],
                constraints=[
                    Constraint(
                        id="free-time",
                        name="Free time",
                        metric="minimum_time_available",
                        limit=Decimal(5),
                    )
                ],
            ),
            no_decision,
            (Decimal(57500), Decimal(65000)),
            Decimal(65000),
            Decimal(57500),
            Decimal(25000),
            (
                (1, "free-time", Decimal(2), Decimal(5)),
                (2, "free-time", Decimal(2), Decimal(5)),
            ),
        ),
        GoldenCase(
            "multiple commitments",
            base_state(
                commitments=[
                    Commitment(
                        id="rent",
                        name="Rent",
                        monthly_cost=Decimal(500),
                        monthly_hours=Decimal(8),
                    ),
                    Commitment(
                        id="course",
                        name="Course",
                        monthly_cost=Decimal(1200),
                        monthly_hours=Decimal(6),
                    ),
                ]
            ),
            no_decision,
            (Decimal(56300), Decimal(62600)),
            Decimal(62600),
            Decimal(56300),
            Decimal(27400),
        ),
        GoldenCase(
            "child composes parent",
            base_state(),
            Scenario(
                id="furnished",
                name="Furnished move",
                parent_id="move",
                deltas={"cash": Decimal(-5000)},
            ),
            (Decimal(43000), Decimal(51000)),
            Decimal(51000),
            Decimal(43000),
            Decimal(39000),
            scenario_catalog={
                "move": Scenario(
                    id="move", name="Move", deltas={"cash": Decimal(-10000)}
                )
            },
        ),
    ]