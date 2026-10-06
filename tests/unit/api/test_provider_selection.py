from services.api.dependencies import Settings


def test_nebius_is_the_default_provider(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert Settings().llm_provider == "nebius"
    assert Settings().llm_model == Settings().nebius_model


def test_token_harbor_provider_selects_its_model() -> None:
    settings = Settings(llm_provider="token_harbor")
    assert settings.llm_model == "deepseek-v4.1-flash:free"


def test_unknown_provider_is_rejected() -> None:
    try:
        Settings(llm_provider="unknown")
    except ValueError as error:
        assert "unsupported LLM_PROVIDER" in str(error)
    else:
        raise AssertionError("unknown providers must be rejected")
