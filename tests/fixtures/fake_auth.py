"""Credential-to-principal adapter used only by tests."""

from packages.ports.auth import AuthPrincipal


class FakeAuthProvider:
    def __init__(self, principals: dict[str, AuthPrincipal]) -> None:
        self._principals = principals

    def authenticate(self, credential: str) -> AuthPrincipal | None:
        return self._principals.get(credential)