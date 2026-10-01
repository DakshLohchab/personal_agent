"""Central API exception handling."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from packages.api_models.errors import ErrorDetail, ErrorEnvelope
from packages.schemas.common import (
    BreakpointSearchError,
    InvalidScenarioError,
    InvalidSimulationInputError,
)
from services.api.logging import get_logger

logger = get_logger()


def _error_payload(code: str, message: str) -> dict[str, Any]:
    return ErrorEnvelope(error=ErrorDetail(code=code, message=message)).model_dump(mode="json")


def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    message = exc.errors()[0]["msg"] if exc.errors() else "Request validation failed."
    return JSONResponse(status_code=422, content=_error_payload("INVALID_REQUEST", message))


def _handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    code = f"HTTP_{exc.status_code}"
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(status_code=exc.status_code, content=_error_payload(code, message))


def _handle_domain_error(_: Request, exc: Exception, status_code: int, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_error_payload(code, str(exc)))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _handle_validation_error(_, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return _handle_http_exception(_, exc)

    @app.exception_handler(InvalidSimulationInputError)
    async def invalid_simulation_input_handler(
        _: Request, exc: InvalidSimulationInputError
    ) -> JSONResponse:
        return _handle_domain_error(_, exc, 422, "INVALID_SIMULATION_INPUT")

    @app.exception_handler(InvalidScenarioError)
    async def invalid_scenario_handler(_: Request, exc: InvalidScenarioError) -> JSONResponse:
        return _handle_domain_error(_, exc, 422, "INVALID_SCENARIO")

    @app.exception_handler(BreakpointSearchError)
    async def breakpoint_error_handler(_: Request, exc: BreakpointSearchError) -> JSONResponse:
        return _handle_domain_error(_, exc, 422, "BREAKPOINT_SEARCH_ERROR")

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API exception")
        return JSONResponse(
            status_code=500,
            content=_error_payload("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )
