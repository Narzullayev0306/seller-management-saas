from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, conflict, forbidden, unauthorized
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.customer import Customer
from app.models.customer_account import CustomerAccount, CustomerRefreshToken
from app.schemas.customer_auth import (
    CustomerLoginRequest,
    CustomerProfileUpdate,
    CustomerRegisterRequest,
    CustomerTokenPair,
)
from app.services.audit_service import log_action

MISSING_CREDENTIALS = unauthorized(
    "INVALID_CREDENTIALS", "Incorrect email or password"
)


def _issue_tokens(db: Session, account: CustomerAccount) -> CustomerTokenPair:
    access_token = create_access_token(
        account.id, account.organization_id, kind="customer"
    )
    raw_refresh = generate_refresh_token()
    db.add(
        CustomerRefreshToken(
            account_id=account.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expiry(),
        )
    )
    db.flush()
    return CustomerTokenPair(access_token=access_token, refresh_token=raw_refresh)


def register(
    db: Session, organization_id: UUID, payload: CustomerRegisterRequest
) -> CustomerTokenPair:
    email = payload.email.lower()
    existing = db.execute(
        select(CustomerAccount).where(
            CustomerAccount.organization_id == organization_id,
            CustomerAccount.email == email,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise conflict("EMAIL_TAKEN", "An account with this email already exists")

    customer = db.execute(
        select(Customer).where(
            Customer.organization_id == organization_id,
            func.lower(Customer.email) == email,
        )
    ).scalar_one_or_none()
    if customer is None:
        customer = Customer(
            organization_id=organization_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=email,
            phone=payload.phone,
        )
        db.add(customer)
        db.flush()
    elif payload.phone:
        customer.phone = payload.phone

    account = CustomerAccount(
        organization_id=organization_id,
        customer_id=customer.id,
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(account)
    db.flush()

    tokens = _issue_tokens(db, account)
    log_action(
        db,
        organization_id=organization_id,
        user_id=None,
        action="customer.register",
        entity_type="customer",
        entity_id=customer.id,
        meta={"email": email},
    )
    db.commit()
    return tokens


def login(
    db: Session, organization_id: UUID, payload: CustomerLoginRequest
) -> CustomerTokenPair:
    account = db.execute(
        select(CustomerAccount).where(
            CustomerAccount.organization_id == organization_id,
            CustomerAccount.email == payload.email.lower(),
        )
    ).scalar_one_or_none()
    if account is None or not verify_password(payload.password, account.password_hash):
        raise MISSING_CREDENTIALS
    if not account.is_active:
        raise forbidden("ACCOUNT_DISABLED", "This account has been disabled")

    tokens = _issue_tokens(db, account)
    log_action(
        db,
        organization_id=organization_id,
        user_id=None,
        action="customer.login",
        entity_type="customer",
        entity_id=account.customer_id,
        meta={"email": account.email},
    )
    db.commit()
    return tokens


def refresh(db: Session, raw_refresh: str) -> CustomerTokenPair:
    token_hash = hash_refresh_token(raw_refresh)
    token = db.execute(
        select(CustomerRefreshToken).where(
            CustomerRefreshToken.token_hash == token_hash
        )
    ).scalar_one_or_none()
    if token is None:
        raise unauthorized("INVALID_REFRESH_TOKEN", "Invalid refresh token")

    now = datetime.now(UTC)
    if token.revoked_at is not None:
        raise unauthorized("REFRESH_TOKEN_REVOKED", "Refresh token has been revoked")
    if token.expires_at < now:
        raise unauthorized("REFRESH_TOKEN_EXPIRED", "Refresh token has expired")
    if not token.account.is_active:
        raise forbidden("ACCOUNT_DISABLED", "This account has been disabled")

    token.revoked_at = now
    db.flush()
    new_tokens = _issue_tokens(db, token.account)
    db.commit()
    return new_tokens


def logout(db: Session, raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    token = db.execute(
        select(CustomerRefreshToken).where(
            CustomerRefreshToken.token_hash == token_hash
        )
    ).scalar_one_or_none()
    if token is not None:
        token.revoked_at = datetime.now(UTC)
        db.commit()


def account_payload(db: Session, account: CustomerAccount) -> dict:
    customer = db.get(Customer, account.customer_id)
    return {
        "id": str(account.id),
        "customer_id": str(account.customer_id) if customer else None,
        "email": account.email,
        "first_name": customer.first_name if customer else "",
        "last_name": customer.last_name if customer else "",
        "full_name": customer.full_name if customer else "",
        "phone": customer.phone if customer else None,
        "address": customer.address if customer else None,
        "is_active": account.is_active,
    }


def update_profile(
    db: Session, account: CustomerAccount, payload: CustomerProfileUpdate
) -> dict:
    customer = db.get(Customer, account.customer_id)
    if customer is None:
        raise bad_request("CUSTOMER_MISSING", "Linked customer record not found")
    if payload.first_name is not None:
        customer.first_name = payload.first_name
    if payload.last_name is not None:
        customer.last_name = payload.last_name
    if payload.phone is not None:
        customer.phone = payload.phone
    if payload.address is not None:
        customer.address = payload.address
    if payload.password is not None:
        if payload.current_password is None or not verify_password(
            payload.current_password, account.password_hash
        ):
            raise bad_request(
                "INVALID_PASSWORD", "Current password is incorrect"
            )
        account.password_hash = hash_password(payload.password)
    log_action(
        db,
        organization_id=account.organization_id,
        user_id=None,
        action="customer.profile_updated",
        entity_type="customer",
        entity_id=customer.id,
    )
    db.commit()
    return account_payload(db, account)
