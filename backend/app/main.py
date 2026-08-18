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
from app.db.session import SessionLocal
from app.schemas.common import ErrorBody, ErrorEnvelope
from app.services.rbac_service import (
    ensure_permission_catalog,
    sync_system_role_permissions,
)

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        ensure_permission_catalog(db)
        sync_system_role_permissions(db)
        db.commit()
    yield


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
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope(error=ErrorBody(
                code="INTERNAL_ERROR", message="Internal server error"
            )).model_dump(),
        )

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
