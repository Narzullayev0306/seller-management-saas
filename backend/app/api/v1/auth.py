from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.ratelimit import check_rate_limit
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=201,
    summary="Register a new organization",
    description=(
        "Creates an organization with the five system roles and an owner user, "
        "then returns an access token and a rotating refresh token."
    ),
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
def register(
    payload: RegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TokenPair:
    check_rate_limit(request, "register", limit=30, window=60)
    _, tokens = auth_service.register(db, payload, background_tasks)
    return tokens


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login with email and password",
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Account or organization disabled"},
    },
)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    check_rate_limit(request, "login", limit=30, window=60)
    _, tokens = auth_service.login(db, payload.email, payload.password)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate a refresh token",
    description="Revokes the presented refresh token and issues a new pair.",
    responses={401: {"description": "Invalid, expired or revoked token"}},
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    return auth_service.refresh(db, payload.refresh_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Logout and revoke the refresh token",
    description="Revokes the presented refresh token. Idempotent.",
)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    auth_service.logout(db, payload.refresh_token)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user with roles and permissions",
)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return auth_service.current_user_payload(db, user)


class SwitchOrgRequest(BaseModel):
    organization_id: UUID


@router.post(
    "/switch-org",
    response_model=TokenPair,
    summary="Switch to another organization",
    description="Re-issues access and refresh tokens scoped to another "
    "organization the caller is an active member of.",
    responses={403: {"description": "Not a member of that organization"}},
)
def switch_org(
    payload: SwitchOrgRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TokenPair:
    return auth_service.switch_org(db, user, payload.organization_id)


@router.get(
    "/memberships",
    summary="List organizations the caller belongs to",
    description="Used by the organization switcher in the UI.",
)
def memberships(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return auth_service.list_memberships(db, user)


@router.post(
    "/forgot-password",
    status_code=200,
    summary="Request a password reset link",
    description="Sends a reset email when the account exists. Always returns 200 "
    "to avoid leaking which emails are registered.",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    check_rate_limit(request, "forgot_password", limit=5, window=300)
    auth_service.forgot_password(db, payload.email, background_tasks)
    return {"message": "If an account exists for that email, a reset link was sent"}


@router.post(
    "/reset-password",
    status_code=200,
    summary="Set a new password using a reset token",
    responses={
        400: {"description": "Invalid, expired or already-used token"},
        422: {"description": "Weak password"},
    },
)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    check_rate_limit(request, "reset_password", limit=5, window=300)
    auth_service.reset_password(db, payload.token, payload.new_password)
    return {"message": "Password updated. You can now sign in."}


@router.post(
    "/change-password",
    status_code=200,
    summary="Change password for current authenticated user",
    responses={
        400: {"description": "Incorrect current password or invalid new password"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    check_rate_limit(request, "change_password", limit=5, window=300)
    auth_service.change_password(
        db, user, payload.current_password, payload.new_password
    )
    return {"message": "Password updated successfully"}


@router.post(
    "/verify-email",
    status_code=200,
    summary="Verify the email address with a token",
    responses={400: {"description": "Invalid, expired or already-used token"}},
)
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    check_rate_limit(request, "verify_email", limit=5, window=300)
    auth_service.verify_email(db, payload.token)
    return {"message": "Email verified"}


@router.post(
    "/resend-verification",
    status_code=200,
    summary="Resend the email verification link",
)
def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    check_rate_limit(request, "resend_verification", limit=3, window=300)
    auth_service.resend_verification(db, payload.email, background_tasks)
    return {"message": "If the account is unverified, a new link was sent"}
