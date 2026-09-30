"""Branchable scenario definitions."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    parent_id: str | None = None
    deltas: dict[str, Decimal] = Field(default_factory=dict)
    assumption_ids: list[str] = Field(default_factory=list)

    @field_validator("deltas", mode="before")
    @classmethod
    def reject_float_deltas(cls, values: object) -> object:
        if isinstance(values, dict) and any(isinstance(value, float) for value in values.values()):
            raise ValueError("scenario deltas must use Decimal, not float")
        return values

    @field_validator("deltas")
    @classmethod
    def require_delta_keys(cls, values: dict[str, Decimal]) -> dict[str, Decimal]:
        if any(not key.strip() for key in values):
            raise ValueError("scenario delta keys must not be empty")
        return values