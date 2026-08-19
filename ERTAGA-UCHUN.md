# ERTAGA-UCHUN.md — muammolar.md audit holati (2026-08-18 kechqurun)

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

## 3. Test holati

- `docker compose exec -T backend pytest -q` → **149 passed**
- `ruff check app tests` → clean
- Yangi test fayllar: test_outbox.py (3), test_payments.py (4), test_variants.py (7), test_coupons.py (11)
- Eski testlar outbox uchun yangilandi: test_security_features.py'da `_process_outbox()` helper (testlarda worker ishlamaydi, eventlarni sinxron yetkazadi)
- DIQQAT: `test_debug_tmp.py` o'chirilgan; `_clean_schema` Base.metadata bilan ishlaydi → model o'zgarishi test bazasida migratsiyasiz ishlaydi

## 4. LIVE MUHIT HOLATI (Supabase!)

- Backend/worker **Supabase PostgreSQL** ga ulanadi (`.env` → `DATABASE_URL` pooler.supabase.com) — LOCAL postgres konteyneri BO'SH, ishlatilmaydi
- Migratsiya: `e5f6a7b8c9d0` (head) — barcha 5 yangi revision qo'llangan (outbox, payments, variants, coupons)
- Worker konteyneri ishlayapti (`sms-worker Up`). MUHIM FIX: `worker.py` da `import app.models` + `organization_member` `models/__init__.py` ga qo'shildi (aks holda "OrganizationMember mapper failed" crash)
- Tekshirilgan: `/api/v1/storefront/info` → `techmart-uzbekistan` OK
- Alembic revision ID kolliziyasi bo'lsa: `a1b2c3d4e5f6` band (storefront) — yangi revision'lar boshqa ID bilan

## 5. QOLGAN ISHLAR (muammolar.md roadmap'i bo'yicha)

### PHASE 2 qoldiqlari (SaaS foundation)
- 11. Organization settings — qisman bor (`PATCH /organizations/me`); qolgan maydonlar (currency/timezone ishlaydi)
- 12. Storefront settings — admin UI uchun backend CRUD yetishmaydi
- 13. Store slug/domain — ✅ slug bor; custom domain yo'q
- 14. Customer accounts (storefront'da login/register)
- 15. Wishlist DB
- 16. Cart DB (hozir faqat localStorage frontend'da)
- 17. Session management (hozir JWT refresh bor; web session yo'q)
- 18. Notification preferences (#113 audit item)
- 19. Soft delete (hozir deactivate)
- 20. Timezone/currency global (hozir org-level)

### PHASE 3 (Ecommerce core)
- 22. Product attributes (variant attributes JSONB bor, alohida model yo'q)
- 23. Categories tree (hozir tekis category string)
- 25. Promotions (coupon bor, murakkab promolar yo'q)
- 26. Shipping (hozir faqat shipping_fee field)
- 28. Refunds / 29. Returns (faqat order cancel bor)
- 30. Purchase orders (supplier'lar bor, PO yo'q)

### PHASE 4 (Production infra)
- 34. Sentry (backend+frontend)
- 35. Metrics / 38. OpenTelemetry
- 36. Request IDs
- 37. Reverse proxy (nginx/traefik)
- 38. TLS (hozir dev http)
- 39. Database backups (Supabase managed, lekin config/verify kerak)
- 40. Migration job (deploy paytida avtomatik alembic)
- 41. Docker hardening (non-root, read-only FS)

### PHASE 5 (Professional SaaS)
- 42-43. Billing/Subscription (Stripe)
- 44. Plan limits (#114 audit item)
- 45. Feature flags
- 46. API keys
- 47. Webhooks
- 48. Custom domains
- 49. Organization branding (logo_url qisman bor)
- 50. Usage analytics

### PHASE 6 (Scale)
- 51. PostgreSQL FTS search (hozir LIKE)
- 52. Redis optimization
- 53. Background analytics
- 54. Cursor pagination (hozir offset)
- 55. Read replicas / 56. Object storage CDN / 57. Load testing

## 6. Keyingi sessiya uchun tavsiya (eng muhimlari)

1. **PHASE 2 qoldiqlari**: Customer accounts + Cart DB (storefront conversion uchun eng muhim)
2. **Sentry + Request IDs** (observability — auditda 🔴 deb belgilangan)
3. **Docker hardening + prod compose** (docker-compose.prod.yml bor, tekshirish kerak)
4. **Reverse proxy + TLS** (agar real deploy qilinsa)
5. **Billing** (SaaS pul topadigan bo'lsa)
6. Frontend'da yangi API'larga ulanish: coupons admin sahifasi, variants UI, payments ko'rinishi

## 7. Konventsiyalar (esdan chiqmasin)

- Commit: `feat(scope): ...` — faqat user so'raganda
- Test: `docker compose exec -T backend pytest -q`; lint: `ruff check app tests`
- `org_a` fixture'da `"organization"` kaliti YO'Q — org_id/slug `/api/v1/auth/me` dan
- `notify_new_order` actor_user_id'ni exclude qiladi — order'ni boshqa user (manager) yaratishi kerak testlarda
- Live DB Supabase — lokal psql bilan aralashtirmang