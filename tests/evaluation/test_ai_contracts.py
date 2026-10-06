from packages.schemas.ai import DecisionInterpretation


def test_decision_interpretation_contract_rejects_missing_required_fields() -> None:
    required = DecisionInterpretation.model_json_schema()["required"]
    assert required == ["objective"]
