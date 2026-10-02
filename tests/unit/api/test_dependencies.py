from services.api.dependencies import Settings


def test_cloud_platform_port_takes_precedence(monkeypatch) -> None:
    monkeypatch.setenv("API_PORT", "8123")
    monkeypatch.setenv("PORT", "9123")

    assert Settings.from_env().api_port == 9123


def test_api_port_is_used_when_port_is_absent(monkeypatch) -> None:
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setenv("API_PORT", "8123")

    assert Settings.from_env().api_port == 8123


def test_default_port_is_8000(monkeypatch) -> None:
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)

    assert Settings.from_env().api_port == 8000