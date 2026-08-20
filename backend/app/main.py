import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ApiError
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.db.session import SessionLocal
from app.schemas.common import ErrorBody, ErrorEnvelope
from app.services.rbac_service import (
    ensure_permission_catalog,
    sync_system_role_permissions,
)

logger = logging.getLogger("app")

try:  # Sentry is optional; the app runs without it in local/offline setups.
    import sentry_sdk

    if settings.sentry_dsn and settings.app_env != "development":
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized")
except ImportError:  # pragma: no cover - optional dependency
    sentry_sdk = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        ensure_permission_catalog(db)
        sync_system_role_permissions(db)
        db.commit()
    yield


def _db_ready() -> bool:
    """True when a trivial query succeeds against Postgres."""
    from sqlalchemy import text

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - defensive probe
        return False


def _redis_ready() -> bool:
    """True when Redis is reachable. Skipped when Redis is disabled."""
    if not settings.redis_enabled or not settings.redis_url:
        return True
    try:
        from app.core.redis import redis_client

        return bool(redis_client.ping())
    except Exception:  # pragma: no cover - defensive probe
        return False


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    origins = [
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    # Security headers and request IDs run first (outermost).
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(set(origins)),
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope(error=ErrorBody(
                code=exc.code, message=exc.message, details=exc.details
            )).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorEnvelope(error=ErrorBody(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": jsonable_encoder(exc.errors())},
            )).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        if sentry_sdk is not None:
            sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope(error=ErrorBody(
                code="INTERNAL_ERROR", message="Internal server error"
            )).model_dump(),
        )

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/api/health/live", tags=["system"])
    def health_live() -> dict:
        return {"status": "ok"}

    @app.get("/api/health/ready", tags=["system"])
    def health_ready(request: Request) -> JSONResponse:
        db_ok = _db_ready()
        redis_ok = _redis_ready()
        ready = db_ok and redis_ok
        return JSONResponse(
            status_code=200 if ready else 503,
            content={
                "status": "ok" if ready else "degraded",
                "checks": {
                    "database": "ok" if db_ok else "error",
                    "redis": "ok" if redis_ok else "error",
                },
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    return app


app = create_app()
