"""Shared domain constants and explicit errors."""

ENGINE_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.0"


class InvalidSimulationInputError(ValueError):
    """Raised when a state cannot be simulated safely."""


class InvalidScenarioError(ValueError):
    """Raised when a scenario or scenario branch is invalid."""


class BreakpointSearchError(ValueError):
    """Raised when breakpoint inputs cannot define a valid search."""


class InsufficientInformationError(ValueError):
    """Raised when simulation is requested but material decision inputs are missing."""

    def __init__(self, message: str, missing_fields: list[str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.missing_fields = missing_fields or []