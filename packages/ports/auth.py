"""Authentication identity abstraction, independent of any provider SDK."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    user_id: UUID
    auth_subject: str
    provider: str


class AuthProvider(Protocol):
    def authenticate(self, credential: str) -> AuthPrincipal | None: ...