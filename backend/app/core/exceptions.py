from typing import Any


class ApiError(Exception):
    """Domain error rendered as a consistent JSON envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def bad_request(code: str, message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(400, code, message, details)


def unauthorized(code: str = "UNAUTHORIZED", message: str = "Authentication required") -> ApiError:
    return ApiError(401, code, message)


def forbidden(code: str = "PERMISSION_DENIED", message: str = "Insufficient permissions", details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(403, code, message, details)


def not_found(entity: str = "Resource") -> ApiError:
    return ApiError(404, f"{entity.upper()}_NOT_FOUND", f"{entity} not found")


def conflict(code: str, message: str) -> ApiError:
    return ApiError(409, code, message)


def payment_required(code: str, message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(402, code, message, details)
