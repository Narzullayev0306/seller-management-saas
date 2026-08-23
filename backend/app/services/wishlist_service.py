from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.models.customer import Customer
from app.models.customer_account import CustomerAccount
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.wishlist import Wishlist, WishlistItem
from app.schemas.wishlist import WishlistItemRead, WishlistRead

WISHLIST_HEADER = "X-Wishlist-Token"


def resolve_wishlist_owner(
    db: Session,
    org_id: UUID,
    customer: CustomerAccount | None,
    session_token: str | None,
) -> tuple[Customer | None, str | None]:
    """Registered customer wins over a guest token (mirrors cart ownership)."""
    if customer is not None:
        if customer.organization_id != org_id:
            raise forbidden("WRONG_STORE", "This account belongs to another store")
        return db.get(Customer, customer.customer_id), (
            session_token[:64] if session_token else None
        )
    if session_token:
        return None, session_token[:64]
    return None, None


def get_or_create_wishlist(
    db: Session,
    org_id: UUID,
    *,
    customer: Customer | None = None,
    session_token: str | None = None,
) -> Wishlist:
    if customer is not None:
        wishlist = db.execute(
            select(Wishlist).where(
                Wishlist.organization_id == org_id,
                Wishlist.customer_id == customer.id,
            )
        ).scalar_one_or_none()
        if wishlist is not None:
            _merge_guest_wishlist(db, org_id, wishlist, session_token)
            return wishlist
        if session_token:
            guest = db.execute(
                select(Wishlist).where(
                    Wishlist.organization_id == org_id,
                    Wishlist.session_token == session_token,
                )
            ).scalar_one_or_none()
            if guest is not None:
                guest.customer_id = customer.id
                guest.session_token = None
                db.flush()
                return guest
        wishlist = Wishlist(organization_id=org_id, customer_id=customer.id)
        db.add(wishlist)
        db.flush()
        return wishlist

    if session_token:
        wishlist = db.execute(
            select(Wishlist).where(
                Wishlist.organization_id == org_id,
                Wishlist.session_token == session_token,
            )
        ).scalar_one_or_none()
        if wishlist is None:
            wishlist = Wishlist(organization_id=org_id, session_token=session_token)
            db.add(wishlist)
            db.flush()
        return wishlist

    raise bad_request(
        "WISHLIST_IDENTITY_REQUIRED",
        "Provide a customer login or an X-Wishlist-Token header",
    )


def _merge_guest_wishlist(
    db: Session, org_id: UUID, wishlist: Wishlist, session_token: str | None
) -> None:
    """Fold guest-wishlist items into the customer's wishlist once."""
    if not session_token:
        return
    guest = db.execute(
        select(Wishlist).where(
            Wishlist.organization_id == org_id,
            Wishlist.session_token == session_token,
        )
    ).scalar_one_or_none()
    if guest is None or guest.id == wishlist.id:
        return
    existing_keys = {
        (i.product_id, i.product_variant_id) for i in wishlist.items
    }
    for item in list(guest.items):
        if (item.product_id, item.product_variant_id) not in existing_keys:
            item.wishlist_id = wishlist.id
            existing_keys.add((item.product_id, item.product_variant_id))
    db.delete(guest)
    db.flush()


def add_item(
    db: Session, org_id: UUID, wishlist: Wishlist, product_id: UUID, variant_id: UUID | None
) -> WishlistRead:
    product = _get_active_product(db, org_id, product_id)
    if variant_id is not None:
        _get_active_variant(db, org_id, variant_id, product.id)
    existing = db.execute(
        select(WishlistItem).where(
            WishlistItem.wishlist_id == wishlist.id,
            WishlistItem.product_id == product_id,
            WishlistItem.product_variant_id == variant_id,
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            WishlistItem(
                wishlist_id=wishlist.id,
                product_id=product_id,
                product_variant_id=variant_id,
            )
        )
    db.commit()
    return wishlist_read(db, org_id, wishlist)


def remove_item(db: Session, wishlist: Wishlist, item_id: UUID) -> WishlistRead:
    item = db.execute(
        select(WishlistItem).where(
            WishlistItem.id == item_id, WishlistItem.wishlist_id == wishlist.id
        )
    ).scalar_one_or_none()
    if item is None:
        raise not_found("WishlistItem")
    db.delete(item)
    db.commit()
    return wishlist_read(db, wishlist.organization_id, wishlist)


def clear(db: Session, wishlist: Wishlist) -> WishlistRead:
    db.execute(delete(WishlistItem).where(WishlistItem.wishlist_id == wishlist.id))
    db.commit()
    return wishlist_read(db, wishlist.organization_id, wishlist)


def wishlist_read(db: Session, org_id: UUID, wishlist: Wishlist) -> WishlistRead:
    items = db.execute(
        select(WishlistItem)
        .where(WishlistItem.wishlist_id == wishlist.id)
        .order_by(WishlistItem.created_at)
    ).scalars().all()
    read_items: list[WishlistItemRead] = []
    for item in items:
        product = db.get(Product, item.product_id)
        if product is None or product.status != "active":
            continue
        variant = (
            db.get(ProductVariant, item.product_variant_id)
            if item.product_variant_id
            else None
        )
        price = variant.price if variant else product.price
        stock = variant.stock_quantity if variant else product.stock_quantity
        read_items.append(
            WishlistItemRead(
                id=item.id,
                product_id=item.product_id,
                product_variant_id=item.product_variant_id,
                name=product.name,
                sku=product.sku,
                price=price,
                image_url=product.image_url,
                variant_name=variant.name if variant else None,
                variant_attributes=variant.attributes if variant else None,
                in_stock=stock is None or stock > 0,
                created_at=item.created_at,
            )
        )
    return WishlistRead(
        wishlist_id=wishlist.id,
        items=read_items,
        item_count=len(read_items),
    )


# ---- helpers ----------------------------------------------------------

def _get_active_product(db: Session, org_id: UUID, product_id: UUID) -> Product:
    product = db.execute(
        select(Product).where(
            Product.organization_id == org_id,
            Product.id == product_id,
            Product.status == "active",
        )
    ).scalar_one_or_none()
    if product is None:
        raise not_found("Product")
    return product


def _get_active_variant(
    db: Session, org_id: UUID, variant_id: UUID, product_id: UUID
) -> ProductVariant:
    variant = db.execute(
        select(ProductVariant).where(
            ProductVariant.organization_id == org_id,
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
            ProductVariant.active.is_(True),
        )
    ).scalar_one_or_none()
    if variant is None:
        raise not_found("ProductVariant")
    return variant
