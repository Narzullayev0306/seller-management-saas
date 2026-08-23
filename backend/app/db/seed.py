"""Demo seed data.

Usage:
    python -m app.db.seed            # seed always
    python -m app.db.seed --if-empty # only when no organizations exist
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.customer import Customer
from app.models.order import Order
from app.models.organization import Organization
from app.models.product import Product
from app.models.role import Role
from app.models.sale import Sale
from app.models.seller import Seller
from app.models.storefront import (
    Brand,
    PriceHistory,
    ProductImage,
    Review,
)
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemInput
from app.services.auth_service import register
from app.services.order_service import OrderService

BRANDS = [
    ("TechCore", "https://picsum.photos/seed/brand-techcore/160/160", "Precision consumer electronics."),
    ("HomeWell", "https://picsum.photos/seed/brand-homewell/160/160", "Appliances that make home life effortless."),
    ("UrbanFit", "https://picsum.photos/seed/brand-urbanfit/160/160", "Sports and fitness essentials."),
    ("GreenTrail", "https://picsum.photos/seed/brand-greentrail/160/160", "Outdoor gear for modern explorers."),
    ("KitchenLab", "https://picsum.photos/seed/brand-kitchenlab/160/160", "Professional-grade kitchen tools."),
    ("ComfortLiving", "https://picsum.photos/seed/brand-comfortliving/160/160", "Furniture and home comfort."),
    ("BabyJoy", "https://picsum.photos/seed/brand-babyjoy/160/160", "Safe and joyful baby products."),
    ("ProToolz", "https://picsum.photos/seed/brand-protoolz/160/160", "Tools built for serious work."),
    ("GlowCare", "https://picsum.photos/seed/brand-glowcare/160/160", "Beauty and personal care."),
    ("PetNest", "https://picsum.photos/seed/brand-petnest/160/160", "Everything your pet loves."),
]

REVIEW_COMMENTS = [
    "Excellent quality, exactly as described.",
    "Great value for the price. Would buy again.",
    "Delivery was fast and the packaging was perfect.",
    "Good product but could be better.",
    "Very satisfied with this purchase.",
    "Works as expected, no complaints.",
    "Five stars! Highly recommended.",
    "Decent product for everyday use.",
    "Better than I expected, very happy.",
    "Solid build quality and fair price.",
]

PRODUCTS = [
    ("Wireless Noise-Cancelling Headphones", "AUD", "Electronics", 189, 112, 120),
    ("4K Ultra HD Smart TV 55", "TV4", "Electronics", 699, 540, 40),
    ("Espresso Machine Pro", "KOF", "Appliances", 349, 220, 25),
    ("Ergonomic Office Chair", "KRS", "Furniture", 249, 150, 60),
    ("Standing Desk 120cm", "DES", "Furniture", 399, 260, 18),
    ("Stainless Steel Water Bottle 1L", "SHI", "Kitchen", 24, 11, 300),
    ("Cast Iron Skillet 26cm", "SKA", "Kitchen", 42, 24, 90),
    ("Chef's Knife Set 5pc", "PIC", "Kitchen", 79, 45, 55),
    ("Induction Cooktop Dual Zone", "IND", "Appliances", 129, 78, 30),
    ("Robot Vacuum Cleaner X2", "ROB", "Appliances", 289, 195, 22),
    ("Air Fryer 5.5L", "AIR", "Appliances", 99, 58, 45),
    ("Electric Kettle 1.7L", "CHY", "Kitchen", 34, 18, 80),
    ("Bluetooth Speaker Mini", "BTS", "Electronics", 49, 26, 150),
    ("Mechanical Keyboard RGB", "KBM", "Accessories", 89, 52, 70),
    ("Wireless Mouse Pro", "MOU", "Accessories", 39, 20, 140),
    ("USB-C Hub 8-in-1", "HUB", "Accessories", 55, 30, 65),
    ("Laptop Stand Aluminium", "STD", "Accessories", 32, 16, 110),
    ("Webcam 1080p", "WEB", "Electronics", 69, 38, 35),
    ("Smart Watch Fitness S2", "SWT", "Electronics", 159, 95, 48),
    ("Fitness Tracker Band", "FTB", "Electronics", 45, 24, 90),
    ("Yoga Mat 6mm", "YOG", "Sports", 28, 14, 130),
    ("Adjustable Dumbbells 2x10kg", "GIR", "Sports", 119, 75, 20),
    ("Resistance Bands Set", "REZ", "Sports", 22, 10, 160),
    ("Camping Tent 4-person", "PAL", "Outdoor", 149, 92, 14),
    ("Hiking Backpack 40L", "RYU", "Outdoor", 85, 50, 38),
    ("LED Camping Lantern", "FON", "Outdoor", 26, 12, 75),
    ("Portable Power Bank 20000mAh", "PB2", "Electronics", 42, 24, 100),
    ("Solar Phone Charger", "SOL", "Outdoor", 55, 32, 28),
    ("Instant Camera Mini", "KAM", "Electronics", 129, 82, 16),
    ("Photo Printer Portable", "PRT", "Electronics", 149, 100, 12),
    ("Baby Monitor Video", "BAB", "Baby", 139, 88, 18),
    ("Car Seat 0-4 years", "AVT", "Baby", 219, 145, 15),
    ("Stroller Travel System", "KOL", "Baby", 289, 195, 10),
    ("Scented Candle Set 3pc", "SVE", "Home", 34, 16, 85),
    ("Luxury Bed Linen Set", "CHU", "Home", 99, 60, 40),
    ("Memory Foam Pillow 2pk", "YOS", "Home", 55, 30, 65),
    ("Cordless Drill 18V", "BUR", "Tools", 119, 74, 25),
    ("Screwdriver Set 100pc", "OTV", "Tools", 49, 26, 55),
    ("Toolbox 3-layer", "SUM", "Tools", 79, 44, 32),
    ("Garden Shovel Set", "BOG", "Garden", 38, 19, 44),
    ("Lawn Mower Electric", "MOW", "Garden", 179, 118, 12),
    ("Pressure Washer 1600W", "MIV", "Garden", 139, 88, 9),
    ("Makeup Brush Set 24pc", "MAK", "Beauty", 45, 22, 70),
    ("Hair Dryer Salon Pro", "FEN", "Beauty", 79, 48, 30),
    ("Electric Toothbrush", "TIS", "Beauty", 59, 34, 88),
    ("Skincare Gift Box", "KOS", "Beauty", 69, 38, 52),
    ("Pet Dry Food 10kg", "MUS", "Pets", 42, 27, 60),
    ("Cat Scratcher Tower", "MUS", "Pets", 58, 33, 25),
    ("Dog Leash Retractable", "IT", "Pets", 18, 9, 120),
    ("Aquarium Filter Set", "AKV", "Pets", 36, 20, 40),
]

FIRST_NAMES = [
    "Aziz", "Dilshod", "Jasur", "Farrux", "Sardor", "Bekzod", "Javohir",
    "Muhammadali", "Sunnat", "Ulugbek", "Shahzod", "Oybek", "Nodir", "Umid",
    "Kamron", "Akmal", "Islom", "Botir", "Rustam", "Elbek", "Sherzod", "Xurshid",
]
LAST_NAMES = [
    "Karimov", "Rahimov", "Yusupov", "Toshmatov", "Ergashev", "Saidov",
    "Aliyev", "Xolmatov", "Nazarov", "Olimov", "Sobirov", "Qodirov",
    "Abdullayev", "Ismoilov", "Rasulov", "Hamidov", "Buriyev", "Ganiyev",
]
FEMALE_FIRST = [
    "Aziza", "Dilnoza", "Malika", "Nilufar", "Zebo", "Gulnora", "Madina",
    "Shahnoza", "Laylo", "Durdona", "Feruza", "Kamola", "Mohira", "Sitora",
]
FEMALE_LAST = [
    "Yusupova", "Karimova", "Rahimova", "Saidova", "Aliyeva", "Qodirova",
    "Ismoilova", "Nazarova", "Xolmatova", "Ergasheva", "Sobirova", "Olimova",
]
CITIES = [
    ("Tashkent", "Amir Temur Avenue"),
    ("Samarkand", "Registan Street"),
    ("Bukhara", "Lyabi-Hauz Street"),
    ("Andijan", "Navoi Avenue"),
    ("Fergana", "Al-Fargani Street"),
    ("Nukus", "Dosnazarov Street"),
]
PHONE_PREFIXES = ["90", "91", "93", "94", "95", "97", "98", "99", "33", "88"]
STATUS_WEIGHTS = (
    ["pending"] * 10
    + ["confirmed"] * 10
    + ["processing"] * 12
    + ["shipped"] * 15
    + ["delivered"] * 55
    + ["cancelled"] * 8
)


def seed(if_empty: bool = False) -> None:
    db = SessionLocal()
    try:
        if if_empty:
            count = db.execute(select(func.count()).select_from(Organization)).scalar_one()
            if count > 0:
                print("Database already has data — skipping seed.")
                return

        rng = random.Random(42)

        print("Seeding organization and users...")
        owner_user, _ = register(
            db,
            SimpleNamespace(
                organization_name="TechMart Uzbekistan",
                full_name="Amin Karimov",
                email="owner@techmart.uz",
                password="DemoPass123!",
            ),
        )
        org = db.get(Organization, owner_user.organization_id)
        roles = {
            r.code: r
            for r in db.execute(select(Role).where(Role.organization_id == org.id)).scalars()
        }

        seeded_users = {}
        for email, full_name, role_code, password in [
            ("admin@techmart.uz", "Dilshod Rahimov", "admin", "AdminPass123!"),
            ("manager@techmart.uz", "Jasur Aliyev", "manager", "ManagerPass123!"),
            ("seller@techmart.uz", "Farrux Nazarov", "seller", "SellerPass123!"),
            ("viewer@techmart.uz", "Zebo Qodirova", "viewer", "ViewerPass123!"),
        ]:
            user = User(
                organization_id=org.id,
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                email_verified=True,
                status="active",
            )
            user.roles = [roles[role_code]]
            db.add(user)
            seeded_users[role_code] = user
        db.flush()
        owner_user.email_verified = True
        owner_user.status = "active"

        print("Seeding suppliers (12)...")
        for i, (sname, semail) in enumerate(
            [
                ("Global Electronics Distributors", "sales@gelectro.example"),
                ("HomeWell Appliances", "orders@homewell.example"),
                ("UrbanFit Sports Co", "info@urbanfit.example"),
                ("GreenTrail Outdoor", "hello@greentrail.example"),
                ("KitchenLab Imports", "supply@kitchenlab.example"),
                ("ComfortLiving Furniture", "sales@comfortliving.example"),
                ("BabyJoy Trading", "contact@babyjoy.example"),
                ("ProToolz Hardware", "sales@protoolz.example"),
                ("GlowCare Beauty", "orders@glowcare.example"),
                ("PetNest Supplies", "info@petnest.example"),
                ("TechCore Asia", "sales@techcore.example"),
                ("Central Asia Logistics", "ops@cal.example"),
            ],
        ):
            db.add(
                Supplier(
                    organization_id=org.id,
                    name=sname,
                    email=semail,
                    phone=f"+998{rng.choice(PHONE_PREFIXES)}{rng.randint(1000000, 9999999)}",
                    address=f"{rng.choice([c for c, _ in CITIES])}, Uzbekistan",
                    status="active" if i % 5 != 4 else "inactive",
                )
            )
        db.flush()

        print("Seeding sellers (20)...")
        sellers = []
        for i in range(20):
            first = rng.choice(FIRST_NAMES + FEMALE_FIRST)
            last = rng.choice(LAST_NAMES + FEMALE_LAST)
            status = rng.choices(["active", "active", "active", "inactive", "suspended"], k=1)[0]
            seller = Seller(
                organization_id=org.id,
                first_name=first,
                last_name=last,
                email=f"seller{i+1}@techmart.uz",
                phone=f"+998{rng.choice(PHONE_PREFIXES)}{rng.randint(1000000, 9999999)}",
                status=status,
                commission_rate=Decimal(rng.choice([3, 5, 5, 7, 8, 10])),
            )
            db.add(seller)
            sellers.append(seller)
        db.flush()
        sellers[0].user_id = seeded_users["seller"].id
        db.flush()

        print("Seeding products (100)...")
        products = []
        for i in range(100):
            name, sku, category, price, cost, base_qty = PRODUCTS[i % len(PRODUCTS)]
            suffix = " Pro" if i % 3 == 0 else ""
            suffix += " V2" if i % 4 == 0 else ""
            products.append(
                Product(
                    organization_id=org.id,
                    name=f"{name}{suffix}".strip(),
                    sku=f"{sku}-{1000 + i}",
                    description=f"High-quality {category.lower()} product — {name}",
                    category=category,
                    price=Decimal(price),
                    cost_price=Decimal(cost),
                    stock_quantity=max(0, base_qty + rng.randint(-8, 40)),
                    low_stock_threshold=rng.choice([3, 5, 10, 10, 15]),
                    status="active" if i % 10 != 7 else "inactive",
                )
            )
        db.add_all(products)
        db.flush()

        print("Seeding storefront (brands, images, reviews, price history)...")
        brands = []
        for bname, logo, bdesc in BRANDS:
            brand = Brand(
                organization_id=org.id,
                name=bname,
                logo_url=logo,
                description=bdesc,
            )
            db.add(brand)
            brands.append(brand)
        db.flush()
        brand_by_category = {
            "Electronics": "TechCore",
            "Appliances": "HomeWell",
            "Sports": "UrbanFit",
            "Outdoor": "GreenTrail",
            "Kitchen": "KitchenLab",
            "Furniture": "ComfortLiving",
            "Baby": "BabyJoy",
            "Tools": "ProToolz",
            "Beauty": "GlowCare",
            "Pets": "PetNest",
        }
        for p in products:
            brand = next(
                (b for b in brands if b.name == brand_by_category.get(p.category, "TechCore")),
                brands[0],
            )
            p.brand_id = brand.id
            p.image_url = f"https://picsum.photos/seed/{p.sku.lower()}/800/800"
            p.featured = p.id in [products[i].id for i in range(0, len(products), 7)]
            for shot in (1, 2):
                db.add(
                    ProductImage(
                        organization_id=org.id,
                        product_id=p.id,
                        url=f"https://picsum.photos/seed/{p.sku.lower()}-{shot}/800/800",
                        position=shot,
                    )
                )
            for _ in range(rng.randint(0, 4)):
                db.add(
                    Review(
                        organization_id=org.id,
                        product_id=p.id,
                        customer_name=(
                            f"{rng.choice(FIRST_NAMES + FEMALE_FIRST)} "
                            f"{rng.choice(LAST_NAMES + FEMALE_LAST)}"
                        ),
                        rating=rng.randint(3, 5),
                        comment=rng.choice(REVIEW_COMMENTS),
                    )
                )
            old_price = p.price * Decimal(rng.choice(["1.08", "1.15", "1.22"]))
            db.add(
                PriceHistory(
                    organization_id=org.id,
                    product_id=p.id,
                    old_price=old_price.quantize(Decimal("0.01")),
                    new_price=p.price,
                )
            )
        db.flush()

        print("Seeding customers (100)...")
        customers = []
        for i in range(100):
            if i % 2 == 0:
                first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            else:
                first, last = rng.choice(FEMALE_FIRST), rng.choice(FEMALE_LAST)
            city, street = rng.choice(CITIES)
            customers.append(
                Customer(
                    organization_id=org.id,
                    first_name=first,
                    last_name=last,
                    email=f"customer{i+1}@example.com",
                    phone=f"+998{rng.choice(PHONE_PREFIXES)}{rng.randint(1000000, 9999999)}",
                    address=f"{street}, {city}",
                )
            )
        db.add_all(customers)
        db.flush()

        print("Seeding orders (240) over the last 6 months...")
        order_service = OrderService(db)
        now = datetime.now(UTC)
        active_sellers = [s for s in sellers if s.status == "active"]

        for i in range(240):
            created = now - timedelta(
                days=rng.randint(0, 180),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )
            customer = rng.choice(customers)
            seller = rng.choice(active_sellers) if active_sellers else None
            chosen = rng.sample(products, rng.randint(1, 4))
            quantities = {}
            for p in chosen:
                qty = rng.randint(1, 5)
                quantities[p.id] = qty
                if p.stock_quantity < qty:
                    from app.models.inventory import InventoryMovement

                    restock = qty + rng.randint(10, 40)
                    p.stock_quantity += restock
                    db.add(
                        InventoryMovement(
                            organization_id=org.id,
                            product_id=p.id,
                            type="purchase",
                            quantity=restock,
                            reason="restock",
                        )
                    )
                    db.flush()
            items = [
                OrderItemInput(product_id=p.id, quantity=quantities[p.id])
                for p in chosen
            ]
            order = order_service.create_order(
                org.id,
                OrderCreate(
                    seller_id=seller.id if seller else None,
                    customer_id=customer.id,
                    discount=Decimal(rng.choice([0, 0, 0, 5, 10, 15])),
                    tax=Decimal("0"),
                    shipping_fee=Decimal(rng.choice([0, 0, 4, 6, 9, 12])),
                    payment_status=rng.choice(["pending", "pending", "paid", "paid", "paid", "refunded"]),
                    items=items,
                ),
                owner_user.id,
            )
            status = rng.choices(STATUS_WEIGHTS, k=1)[0]
            if status == "cancelled":
                order_service.delete_order(org.id, order.id, owner_user.id)
                _backdate(db, Order, order.id, created)
            elif status == "delivered":
                for step in ("confirmed", "processing", "shipped", "delivered"):
                    order_service.update_status(org.id, order.id, step, owner_user.id)
                _backdate(db, Order, order.id, created)
                _backdate(db, Sale, order.sale.id if order.sale else None, created)
            else:
                db.execute(
                    Order.__table__.update()
                    .where(Order.id == order.id)
                    .values(status=status, created_at=created, updated_at=created)
                )
            db.commit()
            if (i + 1) % 60 == 0:
                print(f"  {i+1}/240 orders done")

        print("\nSeed complete.")
        print("  owner:   owner@techmart.uz / DemoPass123!")
        print("  admin:   admin@techmart.uz / AdminPass123!")
        print("  manager: manager@techmart.uz / ManagerPass123!")
        print("  seller:  seller@techmart.uz / SellerPass123!")
        print("  viewer:  viewer@techmart.uz / ViewerPass123!")
    finally:
        db.close()


def _backdate(db, model, row_id, created: datetime) -> None:
    if row_id is None:
        return
    db.execute(
        model.__table__.update()
        .where(model.id == row_id)
        .values(created_at=created, updated_at=created)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--if-empty", action="store_true")
    args = parser.parse_args()
    seed(if_empty=args.if_empty)
