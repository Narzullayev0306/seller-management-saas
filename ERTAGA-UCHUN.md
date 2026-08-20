# ERTAGA-UCHUN.md — muammolar.md audit holati (2026-08-19)

Manba: `muammolar.md` audit hujjati. Quyida hammasi: nimalar qilindi, qanday,
nimalar qoldi va qanday davom etish kerak.

---

## 1. TUGALLANGAN — PHASE 1 (kritik 10 muammo, 2 commit)

Commit'lar: `eb6b98f` (backend hardening) + `6f21360` (storefront slug/idempotency)

| # | Muammo | Nima qilindi |
|---|--------|--------------|
| 1 | Multi-tenant storefront | `GET /stores/{slug}/info` + `GET /storefront/info`, `resolve_storefront(slug)`, noto'g'ri slug 404 |
| 2 | Tenant-aware Redis cache | Cache kalitlariga org prefix, `cache_invalidate("sf:catalog:*")` |
| 3 | Role scoping (effective org) | `user.effective_roles` / `effective_organization_id` (DIQQAT: `user.roles = ...` yozilmasin — ORM assotsiativ jadvalni buzadi! `or` fallback emas, `is not None` tekshirish kerak) |
| 4 | Order state machine | `order_state_machine.py`, faqat ruxsat etilgan o'tishlar |
| 5 | Order audit from/to | `AuditLog.meta` da `from`/`to` |
| 6 | Checkout idempotency | `Idempotency-Key` header, `idempotency_service` (claim/wait/store), frontend `crypto.randomUUID()` |
| 7 | Customer unique | email case-insensitive unique + IntegrityError savepoint |
| 8 | Distributed rate limiting | Redis + in-memory fallback, trusted proxy/real IP |
| 9 | Trusted proxy/IP | `trusted_proxies` config |
| 10 | Inventory concurrency | `FOR UPDATE` row lock'lar |

Frontend: `frontend/lib/storefront-slug.ts` (`sfPath`), `api-client.ts` headers,
CheckoutModal idempotency. `tsc --noEmit` toza; eslint'da 12 muammo (6 error+6 warning)
**avvaldan bor edi** — biznikilar emas.

## 2. TUGALLANGAN — PHASE 2 (item 11-15, commit `10857ce`)

| # | Muammo | Nima qilindi |
|---|--------|--------------|
| 11 | Outbox + worker | `models/outbox.py`, `services/outbox_service.py` (emit, claim FOR UPDATE SKIP LOCKED, MAX_ATTEMPTS=5), `worker.py` (`python -m app.worker`), docker-compose `worker` servisi. Hodisalar: order.created, order.cancelled, stock.low, inventory.restocked (back-in-stock email). Order/inventory endi direct notify qilmaydi |
| 12 | Payments | `models/payment.py`, `services/payment_providers.py` (PaymentProvider ABC + mock + decline), `payment_service.process_order_payment()` — checkout'da order bilan bir transaksiyada to'lov. `GET /orders/{id}/payments`. Config: `PAYMENT_PROVIDER=mock`. Payme/Click/Stripe qo'shish = yangi klass |
| 13 | Product variants | `models/product_variant.py` (org-unique SKU, JSONB attributes, o'z price/cost/stock), products API create/update sync, OrderItem.product_variant_id, order/checkout variant narxi+stock (FOR UPDATE), cancel'da qaytarish, storefront detail'da variants |
| 14 | Coupons | `models/coupon.py` (Coupon + CouponRedemption), `coupons.py` API (CRUD + `GET /coupons/validate`), checkout'da `coupon_code` — percent/fixed, min_subtotal, max_redemptions, max_per_customer, FOR UPDATE bilan race-safe. Permission'lar: `coupons.*` (owner/admin/manager; startup `sync_system_role_permissions` da avtomatik qo'shiladi) |
| 15 | CI/CD | `.github/workflows/ci.yml` (backend: ruff+pip-audit+pytest postgres/redis services; frontend: tsc+eslint+npm audit+build; docker build job), `.github/dependabot.yml` (pip/npm/github-actions haftalik) |

Qo'shimcha kichik narsalar: `MeResponse` ga `organization_slug` qo'shildi (frontend
uchun), OrderItemRead ga `product_variant_id`, CheckoutResult ga
`payment_status/payment_id/discount/coupon_code`.

## 3. TUGALLANGAN — PHASE 2 qoldiqlari: Customer accounts + Cart DB (commit `7a18384`)

### Customer accounts (item 14)
- Backend: `models/customer_account.py` (`CustomerAccount` + `CustomerRefreshToken`), auth zanjiri `customer_auth_service.py`, JWT `kind="customer"` claim (`create_access_token(kind=...)`); `get_current_user` endi `kind != "user"` ni rad etadi; `get_current_customer` / `optional_current_customer` (`api/deps.py`)
- API (slug + legacy router'da ham): `POST /stores/{slug}/auth/register|login|refresh|logout`, `GET|PATCH /stores/{slug}/auth/me`, `GET /stores/{slug}/auth/orders`
- Frontend: `lib/customer-auth.tsx` (provider, `customerRequest` — 401'da refresh rotatsiyasi), `app/storefront/auth/login|register/page.tsx`, `StorefrontShell` customer dropdown, `app/storefront/account/profile/page.tsx` haqiqiy API bilan (setState-in-effect xatosi key-based remount bilan tuzatildi), `app/storefront/orders/page.tsx` customer orders API + localStorage fallback
- `CustomerAuthProvider` root `app/layout.tsx` da (AuthProvider ichida) o'rnatilgan

### Cart DB (item 16)
- Backend: `models/cart.py` (`Cart` + `CartItem`), `services/cart_service.py`, `schemas/cart.py`
- Cart 2 xil identifikatsiya: `customer_id` (ro'yxatdan o'tgan) yoki `session_token` (mehmon, `X-Cart-Token` header, frontend `sms_cart_token` localStorage)
- API: `GET /stores/{slug}/cart`, `POST /stores/{slug}/cart/items`, `PATCH|DELETE /stores/{slug}/cart/items/{item_id}`, `DELETE /stores/{slug}/cart`
- Mehmon cart customer account bilan bog'langanda merge qilinadi (`resolve_cart_owner` — session_token'ni uzatish xatosi tuzatildi)
- Checkout: `customer_account` optional qabul qiladi, order account'ga bog'lanadi, cart tozalanadi
- Frontend: `storefront-context.tsx` cart API bilan sinxronlanadi (optimistic + server replace, mount'da merge), `CheckoutModal` cart headers yuboradi
- Migratsiya: `f6a7b8c9d0e1` (head)

### Test holati
- **164 passed** (149 + 15 yangi: test_customer_accounts.py 7, test_cart.py 8); `ruff check app tests` clean
- DIQQAT: testlar THROWAWAY konteynerda ishlaydi: `docker compose run --rm -T backend pytest -q --tb=short` (`docker compose exec`'dagi process uvicorn --reload crash'ida o'ladi — watchfiles Windows bind mount bilan turg'un emas)
- Frontend: `tsc --noEmit` toza; yangi fayllar eslint'da toza (eslint'da qolgan 12 muammo (6 error+6 warning) **avvaldan bor** — masalan `checkout/success/page.tsx` Math.random, `QuickViewModal.tsx` setState-in-effect)

### LIVE muhit (Supabase!)
- Supabase pooler vaqtincha unreachable edi ("server closed the connection unexpectedly") — `f6a7b8c9d0e1` migratsiya live DB'ga qo'llanganmi NOANIQLIK (backend start'da alembic upgrade head ishlashi kerak edi); qaytadan `docker compose logs sms-backend` bilan tekshirish
- Live DB'da customer account borligini `curl` bilan tekshirish mumkin: `POST /api/v1/storefront/auth/register`

## 4. Test holati (eski, PHASE 2 ustidagi)

- Commit `10857ce` dan: **149 passed**

## 5. LIVE MUHIT HOLATI (Supabase!)

- Backend/worker **Supabase PostgreSQL** ga ulanadi (`.env` → `DATABASE_URL` pooler.supabase.com) — LOCAL postgres konteyneri BO'SH, ishlatilmaydi
- Migratsiya: `e5f6a7b8c9d0` (head) — barcha 5 yangi revision qo'llangan (outbox, payments, variants, coupons)
- Worker konteyneri ishlayapti (`sms-worker Up`). MUHIM FIX: `worker.py` da `import app.models` + `organization_member` `models/__init__.py` ga qo'shildi (aks holda "OrganizationMember mapper failed" crash)
- Tekshirilgan: `/api/v1/storefront/info` → `techmart-uzbekistan` OK
- Alembic revision ID kolliziyasi bo'lsa: `a1b2c3d4e5f6` band (storefront) — yangi revision'lar boshqa ID bilan

## 6. QOLGAN ISHLAR (muammolar.md roadmap'i bo'yicha)

### PHASE 2 qoldiqlari (SaaS foundation)
- 11. Organization settings — qisman bor (`PATCH /organizations/me`); qolgan maydonlar (currency/timezone ishlaydi)
- 12. Storefront settings — admin UI uchun backend CRUD yetishmaydi
- 13. Store slug/domain — ✅ slug bor; custom domain yo'q
- 15. Wishlist DB — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 17. Session management — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 18. Notification preferences — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 19. Soft delete (hozir deactivate)
- 20. Timezone/currency global (hozir org-level)

### PHASE 3 (Ecommerce core)
- 22. Product attributes (variant attributes JSONB bor, alohida model yo'q)
- 23. Categories tree — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 25. Promotions (coupon bor, murakkab promolar yo'q)
- 26. Shipping — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 28-29. Refunds / Returns — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 30. Purchase orders — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)

### PHASE 4 (Production infra)
- 34. Sentry (backend+frontend) — ✅ TUGALLANDI (sessiya: 2026-08-20, quyida) — DSN qo'yish qoldi
- 35. Metrics / 38. OpenTelemetry
- 36. Request IDs — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 37. Reverse proxy (nginx/traefik) — ✅ TUGALLANDI (sessiya: 2026-08-20, Caddy)
- 38. TLS (hozir dev http) — ✅ TUGALLANDI (Caddy auto-HTTPS, DOMAIN qo'yish kerak)
- 39. Database backups (Supabase managed, lekin config/verify kerak)
- 40. Migration job — ✅ TUGALLANDI: alohida `migrate` servisi (dev+prod compose), backend/worker `service_completed_successfully` ga bog'lanadi
- 41. Docker hardening — ✅ TUGALLANDI: non-root `appuser`, read-only FS + tmpfs /tmp, init, no-new-privileges, cap_drop ALL (backend/worker/migrate)

### PHASE 5 (Professional SaaS)
- 42-43. Billing/Subscription (Stripe) — ✅ TUGALLANDI (sessiya: 2026-08-20, local billing) — real Stripe hali ulash kerak
- 44. Plan limits (#114 audit item) — ✅ TUGALLANDI (sessiya: 2026-08-20, quyida)
- 45. Feature flags — ✅ TUGALLANDI (billing_service.require_feature)
- 46. API keys — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 47. Webhooks — ✅ TUGALLANDI (sessiya: 2026-08-19, quyida)
- 48. Custom domains — ✅ TUGALLANDI (sessiya: 2026-08-20, backend+admin UI) — storefrontga bog'lash qoldi
- 49. Organization branding (logo_url qisman bor)
- 50. Usage analytics

### PHASE 6 (Scale)
- 51. PostgreSQL FTS search (hozir LIKE)
- 52. Redis optimization
- 53. Background analytics
- 54. Cursor pagination (hozir offset)
- 55. Read replicas / 56. Object storage CDN / 57. Load testing

## 7. SESSIYA 2026-08-19 KECH (audit qoldiqlari, backend)

- **214 passed** (164 + 50 yangi: wishlist 6, categories 10, shipping 7, refunds 6, purchase_orders 5, webhooks 4, api_keys 5, notification_preferences qayta + boshqalar); `ruff check app tests` clean (60 xato topilib tuzatildi); frontend qolgan (pastga qarang)
- **Wishlist (15)**: `models/wishlist.py` (customer_id yoki session_token, org-scoped), `services/wishlist_service.py` (merge, X-Wishlist-Token), slug+legacy API, migratsiya `f8c9d0e1f2a3`
- **Categories tree (23)**: `models/category.py` (parent_id self-FK, slug, sort_order), `services/category_service.py` (cycle guard, rename→product.category sync), recursive `CategoryTreeNode` (`model_rebuild()` kerak!), Product.category_id FK, migratsiya `f9d0e1f2a3b4` + backfill (id `gen_random_uuid()`, sort_order=0, is_active=true — aks holda real DB'da NOT NULL yiqiladi!)
- **Shipping (26)**: `models/shipping_method.py`, checkout `shipping_method_id` → shipping_fee, storefront slug+legacy endpoint, migratsiya `f0e1f2a3b4c5`
- **Refunds/Returns (28-29)**: `models/refund.py` (ReturnRequest + Refund), `refund_service.py` (eligible: shipped/delivered; approve→auto refund), admin+storefront API, migratsiya `f1e2f3a4b5c6`
- **Purchase orders (30)**: `models/purchase_order.py` (PO-######), receive→stock+purchase movement, migratsiya `f2e3f4a5b6c7`
- **Webhooks (47)**: `models/webhook.py` (endpoint+delivery), HMAC-SHA256 sign (X-Webhook-Signature/Timestamp/Event), `worker.handle_event` → `deliver_event`, test ping + delivery history, secret faqat create'da to'liq (keyin mask), migratsiya `f3e4f5a6b7c8`
- **API keys (46)**: `models/api_key.py` (faqat SHA-256 hash, prefix smk_, scopes, expires_at, last_used_at), `api/deps.py` da `require_api_key_scopes`, read-only public endpoint'lar (`/api/v1/public/products|inventory`), migratsiya `f4e5f6a7b8c9`
- **Migration job (40)**: alohida `migrate` servisi; backend/worker `depends_on: migrate: condition: service_completed_successfully`. DIQQAT: dev compose'da migrate DATABASE_URL **qattiq local postgres**ga yozilgan (`.env` dagi Supabase URL'ini olib, unreachable bo'lib test'ni to'sib qo'ygan); prod'da `${DATABASE_URL}`
- **Docker hardening (41)**: backend Dockerfile non-root `appuser`, `RUFF_CACHE_DIR=/tmp/.ruff_cache` + `PYTEST_ADDOPTS=-p no:cacheprovider` (read-only FS uchun), `read_only: true` + tmpfs /tmp + init + no-new-privileges + cap_drop ALL
- **BOSHQA FIX'lar**: `RequestIdMiddleware` response-freeze bug (try/except); categories backfill migratsiyasi id+sort_order+is_active; prod compose'ga `worker` servisi qo'shildi
- **Alembic chain**: ... → f7b8c9d0e1f2 (sessions) → f8c9d0e1f2a3 (wishlists) → f9d0e1f2a3b4 (categories) → f0e1f2a3b4c5 (shipping) → f1e2f3a4b5c6 (refunds) → f2e3f4a5b6c7 (POs) → f3e4f5a6b7c8 (webhooks) → f4e5f6a7b8c9 (api_keys) ← HEAD

## 8. SESSIYA 2026-08-20 (frontend wiring — admin sahifalar + wishlist DB)

- **4 yangi admin sahifa** (hammasi eslint/tsc toza, permission-gated):
  - `frontend/app/dashboard/refunds/page.tsx` — return requests (approve/reject/receive/complete), refunds (process/fail), manual refund modal (order select)
  - `frontend/app/dashboard/purchase-orders/page.tsx` — PO list + create modal (supplier, line items product/qty/unit_cost), draft→ordered→received, cancel/delete
  - `frontend/app/dashboard/webhooks/page.tsx` — CRUD + event checkboxes (order.created, order.cancelled, order.status_changed, product.created, product.updated, stock.low, inventory.restocked), secret create'da bir marta, test ping, deliveries history modal
  - `frontend/app/dashboard/api-keys/page.tsx` — CRUD + scope checkboxes (user permission'lariga filterlangan), key bir marta ko'rsatiladi + copy, revoke/activate, expiry
- `layout.tsx` NAV ga qo'shildi: Purchase Orders (`inventory.read`), Refunds (`orders.read`), Webhooks (`settings.read`), API Keys (`settings.read`); `components/command-search.tsx` ACTIONS ga ham
- **Wishlist storefront → DB wiring**: `customer-auth.tsx` da `WISHLIST_TOKEN_KEY` (`sms_wishlist_token`) + `wishlistHeaders()` (`X-Wishlist-Token`), `customerRequest` hammasiga header qo'shadi; `storefront-context.tsx` da mount'da server'dan merge, `toggleWishlist` optimistic + POST `/wishlist/items` / DELETE `/wishlist/items/{id}` (serverId), `WishlistItem[]` internal state, kontekst sirti `StorefrontProduct[]` o'zgarmadi (WishlistDrawer/ProductCard/QuickViewModal ishlaydi)
- **Tekshiruv**: `npx tsc --noEmit` toza; yangi fayllar eslint toza; `npx next build` OK (37/37 route). DIQQAT: eslint'da qolgan 11 muammo (6 error+5 warning) hammasi eski storefront fayllarda
- Backend testlari o'zgarmagan: **214 passed**

## 9. SESSIYA 2026-08-20 (billing + domains + Sentry frontend + Caddy)

- **Billing/Subscription (42-43)**: `models/billing.py` (Subscription + Invoice), `services/billing_service.py` — `PLAN_CATALOG` (free/pro/enterprise, narx 0.00/29.00/99.00 USD, features: webhooks/api_keys/custom_domain/advanced_analytics/export/priority_support), `check_usage_limit` (402 PLAN_LIMIT), `require_feature` (403 PLAN_FEATURE), `change_plan` (invoice + audit `organization.plan_changed`), `get_or_create_subscription`; API: `GET /billing/plans`, `GET /billing/summary`, `POST /billing/change-plan` (owner-only), `GET /billing/invoices`; permissions `billing.read`/`billing.manage` (owner/admin avtomatik); migratsiya `f5e6f7a8b9c0` (subscriptions/invoices/organization_domains + mavjud org'larga subscription backfill)
- **Plan limits (44)**: free=users 25/products 500/orders 2000 oyiga; pro=100/5000/50000; enterprise=cheksiz. Enforcement: `users.create_user`, `auth_service.invite_user`, `products.create_product`, `orders.create_order`, `storefront.checkout` + `legacy_checkout`. Testlar `PLAN_CATALOG` monkeypatch qiladi (eski testlarni buzmaslik uchun)
- **Custom domains (48)**: `models/domain.py` (OrganizationDomain, TXT verification token), `services/domain_service.py` (add/verify/remove + `resolve_org_by_host`), API `GET/POST /domains`, `POST /{id}/verify`, `DELETE /{id}`; free plan'da 403 PLAN_FEATURE. DIQQAT: pydantic v2 Rust regex — lookahead ishlamaydi, domain pattern `^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$`
- **Frontend billing sahifasi**: `frontend/app/dashboard/billing/page.tsx` — plan kartalari (current ring), usage bar'lar (users/products/orders vs limit), change-plan (ConfirmDialog, owner-only), invoices ro'yxati, custom domains (add modal → TXT token → verify/remove); `lib/types.ts` ga Plan/BillingSummary/Invoice/OrganizationDomain; NAV + command-search ga `Billing` (billing.read); tsc+eslint toza
- **Sentry frontend (34)**: `@sentry/nextjs@10.70.0` o'rnatildi; `instrumentation-client.ts` (client init + `onRouterTransitionStart = Sentry.captureRouterTransitionStart`), `sentry.server.config.ts`, `instrumentation.ts` (`register` + `onRequestError = Sentry.captureRequestError`), `app/global-error.tsx`, `next.config.ts` → `withSentryConfig` (org/project/sourcemaps.deleteSourcemapsAfterUpload/widenClientFileUpload). DSN optional: `SENTRY_DSN`/`NEXT_PUBLIC_SENTRY_DSN` bo'lmasa init o'tkazib yuboriladi. DIQQAT: `hideSourceMaps` v10 da yo'q → `sourcemaps.deleteSourcemapsAfterUpload`
- **Reverse proxy + TLS (37-38)**: `deploy/Caddyfile` + `caddy` servisi prod compose'da (`/api/*` → backend:8000, qolgani → frontend:3000, gzip, security headers, auto-HTTPS `DOMAIN` env bilan, `{$DOMAIN:http://localhost}` — DOMAIN bo'lmasa http). `caddy validate` OK. `.env.example` ga SENTRY_DSN/SENTRY_ORG/SENTRY_PROJECT/NEXT_PUBLIC_SENTRY_DSN/DOMAIN
- **Tekshiruv**: backend **222 passed** (214 + 8 billing/domains), ruff clean; frontend tsc+eslint toza, `npx next build` OK (38 route, billing qo'shildi); `docker compose -f docker-compose.prod.yml config` OK
- Alembic chain: ... → f4e5f6a7b8c9 (api_keys) → f5e6f7a8b9c0 (billing+domains) ← HEAD

## 10. Keyingi sessiya uchun tavsiya (eng muhimlari)

1. **Live Supabase'ni tekshirish**: backend konteyneri ishga tushganmi, yangi migratsiyalar (f8c9d0e1f2a3..f5e6f7a8b9c0) live DB'ga qo'llanganmi (`docker compose logs sms-backend` / `docker compose run --rm -T migrate`); pooler hali ham vaqtincha unreachable edi
2. ~~Frontend wiring (KATTA BLOCK)~~ — ✅ TUGALLANDI (sessiya: 2026-08-20, quyida)
3. ~~Sentry frontend + DSN config~~ — ✅ TUGALLANDI (sessiya: 2026-08-20, quyida) — endi faqat DSN qo'yish qoldi
4. ~~Billing (SaaS pul topadigan bo'lsa)~~ — ✅ TUGALLANDI (sessiya: 2026-08-20, quyida) — backend+frontend; Stripe real ulash hali kerak bo'lsa
5. ~~Reverse proxy + TLS (agar real deploy qilinsa)~~ — ✅ TUGALLANDI (sessiya: 2026-08-20, quyida) — Caddy tayyor, DOMAIN qo'yish qoldi
6. Real Stripe integratsiyasi (hali local billing — invoice/manual), custom domain'ni storefront'ga bog'lash (resolve_org_by_host tayyor)

## 11. Konventsiyalar (esdan chiqmasin)

- Commit: `feat(scope): ...` — faqat user so'raganda
- Test: `docker compose run --rm -T backend pytest -q --tb=short`; lint: `ruff check app tests`
- Frontend: `npx tsc --noEmit`; eslint yangi fayllarda toza bo'lishi kerak (eski 12 muammoga tegmaymiz)
- `org_a` fixture'da `"organization"` kaliti YO'Q — org_id/slug `/api/v1/auth/me` dan
- `notify_new_order` actor_user_id'ni exclude qiladi — order'ni boshqa user (manager) yaratishi kerak testlarda
- Live DB Supabase — lokal psql bilan aralashtirmang