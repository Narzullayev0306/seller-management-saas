from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.customer import Customer
from app.models.organization import Organization
from app.models.product import Product
from app.models.storefront import (
    BackInStockRequest,
    Brand,
    PriceHistory,
    ProductImage,
    Review,
)
from app.schemas.order import OrderCreate, OrderItemInput
from app.schemas.storefront import (
    BackInStockCreate,
    BrandRead,
    BrandWithCount,
    CatalogProduct,
    CategoryWithCount,
    CheckoutCreate,
    CheckoutResult,
    PricePoint,
    ProductDetail,
    ProductImageRead,
    ProductVariantRead,
    ReviewCreate,
    ReviewRead,
)
from app.services.order_service import OrderService
from app.services.payment_service import process_order_payment


def resolve_storefront(db: Session, slug: str | None = None) -> UUID:
    """Resolve the public storefront for an organization by its slug.

    When no slug is given (legacy URLs) the first enabled storefront is used.
    Unknown or disabled storefronts return 404.
    """
    if slug is not None:
        org_id = db.execute(
            select(Organization.id).where(
                Organization.slug == slug,
                Organization.is_active.is_(True),
                Organization.storefront_enabled.is_(True),
            )
        ).scalar_one_or_none()
        if org_id is None:
            raise not_found("Storefront")
        return org_id

    org_id = db.execute(
        select(Organization.id)
        .where(
            Organization.is_active.is_(True),
            Organization.storefront_enabled.is_(True),
        )
        .order_by(Organization.created_at)
        .limit(1)
    ).scalar_one_or_none()
    if org_id is None:
        raise bad_request("NO_ORGANIZATION", "No organization available for the storefront")
    return org_id


class StorefrontService:
    def __init__(self, db: Session, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    # ---- catalog ---------------------------------------------------------

    def catalog(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        category: str | None = None,
        brand: str | None = None,
        featured: bool | None = None,
        sort_by: str | None = None,
    ) -> tuple[list[CatalogProduct], int, list[str], list[str]]:
        org_id = self.organization_id

        rating_subq = (
            select(
                Review.product_id.label("product_id"),
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("review_count"),
            )
            .where(Review.organization_id == org_id)
            .group_by(Review.product_id)
            .subquery()
        )

        stmt = (
            select(
                Product,
                Brand.name,
                rating_subq.c.avg_rating,
                rating_subq.c.review_count,
            )
            .outerjoin(Brand, Brand.id == Product.brand_id)
            .outerjoin(
                rating_subq,
                rating_subq.c.product_id == Product.id,
            )
            .where(
                Product.organization_id == org_id,
                Product.status == "active",
            )
        )
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Product.name).like(like))
        if category:
            stmt = stmt.where(Product.category == category)
        if brand:
            stmt = stmt.where(Brand.name == brand)
        if featured is not None:
            stmt = stmt.where(Product.featured.is_(featured))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        if sort_by == "price_asc":
            stmt = stmt.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            stmt = stmt.order_by(Product.price.desc())
        elif sort_by == "newest":
            stmt = stmt.order_by(Product.created_at.desc())
        elif sort_by == "popular":
            stmt = stmt.order_by(
                func.coalesce(rating_subq.c.review_count, 0).desc(),
                Product.created_at.desc(),
            )
        else:
            stmt = stmt.order_by(Product.featured.desc(), Product.name)

        rows = self.db.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        ).all()

        items = [
            CatalogProduct(
                id=p.id,
                name=p.name,
                category=p.category,
                price=p.price,
                stock_quantity=p.stock_quantity,
                stock_status=p.stock_status,
                image_url=p.image_url,
                brand_name=brand_name,
                rating=_quantize(avg_rating),
                review_count=int(review_count or 0),
                featured=p.featured,
            )
            for p, brand_name, avg_rating, review_count in rows
        ]

        categories = self.db.execute(
            select(Product.category)
            .where(Product.organization_id == org_id, Product.status == "active")
            .distinct()
            .order_by(Product.category)
        ).scalars().all()
        brands = self.db.execute(
            select(Brand.name)
            .join(Product, Product.brand_id == Brand.id)
            .where(Brand.organization_id == org_id, Product.status == "active")
            .distinct()
            .order_by(Brand.name)
        ).scalars().all()
        return items, total, list(categories), list(brands)

    # ---- detail ----------------------------------------------------------

    def product_detail(self, product_id: UUID) -> ProductDetail:
        org_id = self.organization_id
        row = self.db.execute(
            select(Product, Brand)
            .outerjoin(Brand, Brand.id == Product.brand_id)
            .where(
                Product.organization_id == org_id,
                Product.id == product_id,
                Product.status == "active",
            )
        ).first()
        if row is None:
            raise not_found("Product")
        product, brand = row

        rating, review_count = self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.organization_id == org_id,
                Review.product_id == product_id,
            )
        ).one()
        images = self.db.execute(
            select(ProductImage)
            .where(
                ProductImage.organization_id == org_id,
                ProductImage.product_id == product_id,
            )
            .order_by(ProductImage.position)
        ).scalars().all()
        reviews = self.db.execute(
            select(Review)
            .where(Review.organization_id == org_id, Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .limit(20)
        ).scalars().all()
        history = self.db.execute(
            select(PriceHistory)
            .where(
                PriceHistory.organization_id == org_id,
                PriceHistory.product_id == product_id,
                PriceHistory.changed_at
                >= datetime.now(UTC) - timedelta(days=90),
            )
            .order_by(PriceHistory.changed_at.desc())
            .limit(30)
        ).scalars().all()

        return ProductDetail(
            id=product.id,
            name=product.name,
            description=product.description,
            category=product.category,
            price=product.price,
            stock_quantity=product.stock_quantity,
            stock_status=product.stock_status,
            image_url=product.image_url,
            featured=product.featured,
            brand=BrandRead(
                id=brand.id, name=brand.name, logo_url=brand.logo_url, description=brand.description
            )
            if brand
            else None,
            images=[
                ProductImageRead(id=i.id, url=i.url, position=i.position) for i in images
            ],
            reviews=[ReviewRead.model_validate(r) for r in reviews],
            price_history=[
                PricePoint(old_price=h.old_price, new_price=h.new_price, changed_at=h.changed_at)
                for h in history
            ],
            variants=[
                ProductVariantRead(
                    id=v.id,
                    name=v.name,
                    sku=v.sku,
                    attributes=v.attributes,
                    price=v.price,
                    stock_quantity=v.stock_quantity,
                    active=v.active,
                )
                for v in product.variants
                if v.active
            ],
            rating=_quantize(rating),
            review_count=int(review_count),
        )

    # ---- brands / categories --------------------------------------------

    def brands(self) -> list[BrandWithCount]:
        org_id = self.organization_id
        rows = self.db.execute(
            select(
                Brand,
                func.count(Product.id),
            )
            .outerjoin(Product, Product.brand_id == Brand.id)
            .where(
                Brand.organization_id == org_id,
                (Product.id.is_(None)) | (Product.status == "active"),
            )
            .group_by(Brand.id)
            .order_by(Brand.name)
        ).all()
        return [
            BrandWithCount(
                id=b.id,
                name=b.name,
                logo_url=b.logo_url,
                description=b.description,
                product_count=int(count),
            )
            for b, count in rows
        ]

    def categories(self) -> list[CategoryWithCount]:
        org_id = self.organization_id
        rows = self.db.execute(
            select(Product.category, func.count(Product.id))
            .where(Product.organization_id == org_id, Product.status == "active")
            .group_by(Product.category)
            .order_by(Product.category)
        ).all()
        return [
            CategoryWithCount(category=cat, product_count=int(count))
            for cat, count in rows
        ]

    # ---- reviews / back-in-stock -----------------------------------------

    def add_review(self, product_id: UUID, payload: ReviewCreate) -> ReviewRead:
        org_id = self.organization_id
        self._get_active_product(org_id, product_id)
        review = Review(
            organization_id=org_id,
            product_id=product_id,
            customer_name=payload.customer_name,
            rating=payload.rating,
            comment=payload.comment,
        )
        self.db.add(review)
        self.db.commit()
        return ReviewRead.model_validate(review)

    def request_back_in_stock(self, product_id: UUID, payload: BackInStockCreate) -> None:
        org_id = self.organization_id
        self._get_active_product(org_id, product_id)
        existing = self.db.execute(
            select(BackInStockRequest).where(
                BackInStockRequest.organization_id == org_id,
                BackInStockRequest.product_id == product_id,
                BackInStockRequest.email == payload.email,
                BackInStockRequest.notified_at.is_(None),
            )
        ).scalar_one_or_none()
        if existing is None:
            self.db.add(
                BackInStockRequest(
                    organization_id=org_id,
                    product_id=product_id,
                    email=payload.email,
                )
            )
            self.db.commit()

    # ---- checkout ---------------------------------------------------------

    def checkout(self, payload: CheckoutCreate) -> CheckoutResult:
        org_id = self.organization_id
        customer = self._find_customer(org_id, payload.email)
        if customer is None:
            customer = self._create_customer(org_id, payload)

        order_create = OrderCreate(
            seller_id=None,
            customer_id=customer.id,
            discount=payload.discount,
            tax=payload.tax,
            coupon_code=payload.coupon_code,
            items=[
                OrderItemInput(
                    product_id=i.product_id,
                    product_variant_id=i.product_variant_id,
                    quantity=i.quantity,
                )
                for i in payload.items
            ],
        )
        order = OrderService(self.db).create_order(
            org_id, order_create, actor_user_id=None
        )
        payment = process_order_payment(self.db, org_id, order)
        self.db.commit()
        items_count = sum(i.quantity for i in payload.items)
        return CheckoutResult(
            order_id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_status=order.payment_status,
            total=order.total,
            discount=order.discount,
            coupon_code=payload.coupon_code,
            items_count=items_count,
            payment_id=payment.id,
        )

    # ---- helpers ----------------------------------------------------------

    def _find_customer(self, org_id: UUID, email: str) -> Customer | None:
        return self.db.execute(
            select(Customer).where(
                Customer.organization_id == org_id,
                func.lower(Customer.email) == email.lower(),
            )
        ).scalar_one_or_none()

    def _create_customer(self, org_id: UUID, payload: CheckoutCreate) -> Customer:
        """Insert a customer; on a concurrent-duplicate unique violation,
        roll back to a savepoint and re-fetch the winner instead of failing."""
        customer = Customer(
            organization_id=org_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
        )
        self.db.add(customer)
        try:
            with self.db.begin_nested():
                self.db.flush()
        except IntegrityError:
            existing = self._find_customer(org_id, payload.email)
            if existing is not None:
                return existing
            raise
        return customer

    def _get_active_product(self, org_id: UUID, product_id: UUID) -> Product:
        product = self.db.execute(
            select(Product).where(
                Product.organization_id == org_id,
                Product.id == product_id,
                Product.status == "active",
            )
        ).scalar_one_or_none()
        if product is None:
            raise not_found("Product")
        return product


def _quantize(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value).quantize(Decimal("0.1"))
