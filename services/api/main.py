"""FastAPI application entrypoint for the Life Sandbox API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api.dependencies import get_settings
from services.api.errors import register_exception_handlers
from services.api.logging import configure_logging
from services.api.routers import breakpoints, health, sensitivity, simulations

settings = get_settings()
logger = configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup", extra={"app_env": settings.app_env})
    yield


app = FastAPI(
    title="Life Sandbox API",
    description="Backend API for Life Sandbox decision simulation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(simulations.router)
app.include_router(sensitivity.router)
app.include_router(breakpoints.router)


@app.middleware("http")
async def log_requests(request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled API exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                }
            },
        )
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
