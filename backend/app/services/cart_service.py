from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.models.cart import Cart, CartItem
from app.models.customer import Customer
from app.models.customer_account import CustomerAccount
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.schemas.cart import CartItemInput, CartItemRead, CartRead

MAX_QUANTITY = 100


def resolve_cart_owner(
    db: Session,
    org_id: UUID,
    customer: CustomerAccount | None,
    session_token: str | None,
) -> tuple[Customer | None, str | None]:
    """Pick the cart identity: a registered customer wins over a guest token.

    The guest session token is still returned so a logged-in customer's cart
    can absorb items from a pre-login guest cart.
    """
    if customer is not None:
        if customer.organization_id != org_id:
            raise forbidden("WRONG_STORE", "This account belongs to another store")
        return db.get(Customer, customer.customer_id), (
            session_token[:64] if session_token else None
        )
    if session_token:
        return None, session_token[:64]
    return None, None


def get_or_create_cart(
    db: Session,
    org_id: UUID,
    *,
    customer: Customer | None = None,
    session_token: str | None = None,
) -> Cart:
    if customer is not None:
        cart = db.execute(
            select(Cart).where(
                Cart.organization_id == org_id,
                Cart.customer_id == customer.id,
            )
        ).scalar_one_or_none()
        if cart is not None:
            _merge_guest_cart(db, org_id, cart, session_token)
            return cart
        if session_token:
            guest = db.execute(
                select(Cart).where(
                    Cart.organization_id == org_id,
                    Cart.session_token == session_token,
                )
            ).scalar_one_or_none()
            if guest is not None:
                guest.customer_id = customer.id
                guest.session_token = None
                db.flush()
                return guest
        cart = Cart(organization_id=org_id, customer_id=customer.id)
        db.add(cart)
        db.flush()
        return cart

    if session_token:
        cart = db.execute(
            select(Cart).where(
                Cart.organization_id == org_id,
                Cart.session_token == session_token,
            )
        ).scalar_one_or_none()
        if cart is None:
            cart = Cart(organization_id=org_id, session_token=session_token)
            db.add(cart)
            db.flush()
        return cart

    raise bad_request(
        "CART_IDENTITY_REQUIRED",
        "Provide a customer login or an X-Cart-Token header",
    )


def _merge_guest_cart(
    db: Session, org_id: UUID, cart: Cart, session_token: str | None
) -> None:
    """Fold any guest-cart items into the customer's cart once."""
    if not session_token:
        return
    guest = db.execute(
        select(Cart).where(
            Cart.organization_id == org_id,
            Cart.session_token == session_token,
        )
    ).scalar_one_or_none()
    if guest is None or guest.id == cart.id:
        return
    for item in list(guest.items):
        existing = _find_item(db, cart.id, item.product_id, item.product_variant_id)
        if existing is not None:
            existing.quantity = min(MAX_QUANTITY, existing.quantity + item.quantity)
        else:
            item.cart_id = cart.id
    db.delete(guest)
    db.flush()


def add_item(
    db: Session,
    org_id: UUID,
    cart: Cart,
    payload: CartItemInput,
) -> CartRead:
    product = _get_active_product(db, org_id, payload.product_id)
    variant = None
    stock = product.stock_quantity
    if payload.product_variant_id is not None:
        variant = _get_active_variant(db, org_id, payload.product_variant_id, product.id)
        stock = variant.stock_quantity

    existing = _find_item(db, cart.id, payload.product_id, payload.product_variant_id)
    quantity = payload.quantity + (existing.quantity if existing else 0)
    quantity = min(quantity, MAX_QUANTITY)
    if stock is not None and quantity > stock:
        raise bad_request(
            "INSUFFICIENT_STOCK",
            f"Only {stock} units available for this product",
        )
    if existing is not None:
        existing.quantity = quantity
    else:
        db.add(
            CartItem(
                cart_id=cart.id,
                product_id=payload.product_id,
                product_variant_id=payload.product_variant_id,
                quantity=quantity,
            )
        )
    db.commit()
    return cart_read(db, org_id, cart)


def update_item(
    db: Session,
    org_id: UUID,
    cart: Cart,
    item_id: UUID,
    quantity: int,
) -> CartRead:
    item = _get_cart_item(db, cart, item_id)
    stock = item.product.stock_quantity
    if item.product_variant_id is not None:
        stock = item.variant.stock_quantity
    if quantity > stock:
        raise bad_request(
            "INSUFFICIENT_STOCK",
            f"Only {stock} units available for this product",
        )
    item.quantity = quantity
    db.commit()
    return cart_read(db, org_id, cart)


def remove_item(db: Session, cart: Cart, item_id: UUID) -> CartRead:
    item = _get_cart_item(db, cart, item_id)
    db.delete(item)
    db.commit()
    return cart_read(db, cart.organization_id, cart)


def clear(db: Session, cart: Cart) -> CartRead:
    db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    db.commit()
    return cart_read(db, cart.organization_id, cart)


def cart_read(db: Session, org_id: UUID, cart: Cart) -> CartRead:
    items = db.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.created_at)
    ).scalars().all()
    read_items: list[CartItemRead] = []
    for item in items:
        product = db.get(Product, item.product_id)
        variant = (
            db.get(ProductVariant, item.product_variant_id)
            if item.product_variant_id
            else None
        )
        if product is None or product.status != "active":
            continue
        price = variant.price if variant else product.price
        stock = variant.stock_quantity if variant else product.stock_quantity
        read_items.append(
            CartItemRead(
                id=item.id,
                product_id=item.product_id,
                product_variant_id=item.product_variant_id,
                name=product.name,
                sku=product.sku,
                price=price,
                image_url=product.image_url,
                variant_name=variant.name if variant else None,
                variant_attributes=variant.attributes if variant else None,
                quantity=item.quantity,
                stock_quantity=stock,
                subtotal=price * item.quantity,
                created_at=item.created_at,
            )
        )
    return CartRead(
        cart_id=cart.id,
        items=read_items,
        item_count=sum(i.quantity for i in read_items),
        subtotal=sum(i.subtotal for i in read_items),
    )


def find_customer_cart(db: Session, org_id: UUID, customer_id: UUID) -> Cart | None:
    return db.execute(
        select(Cart).where(
            Cart.organization_id == org_id,
            Cart.customer_id == customer_id,
        )
    ).scalar_one_or_none()


def find_session_cart(db: Session, org_id: UUID, session_token: str | None) -> Cart | None:
    if not session_token:
        return None
    return db.execute(
        select(Cart).where(
            Cart.organization_id == org_id,
            Cart.session_token == session_token[:64],
        )
    ).scalar_one_or_none()


# ---- helpers ----------------------------------------------------------

def _find_item(
    db: Session, cart_id: UUID, product_id: UUID, variant_id: UUID | None
) -> CartItem | None:
    return db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
            CartItem.product_variant_id == variant_id,
        )
    ).scalar_one_or_none()


def _get_cart_item(db: Session, cart: Cart, item_id: UUID) -> CartItem:
    item = db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    ).scalar_one_or_none()
    if item is None:
        raise not_found("CartItem")
    return item


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
