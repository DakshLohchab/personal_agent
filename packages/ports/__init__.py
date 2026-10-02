"""Application-facing identity and persistence interfaces."""

from .auth import AuthPrincipal, AuthProvider

__all__ = ["AuthPrincipal", "AuthProvider"]