# ERTANGI REJA — 18-08-2026 (Session 2)

> Bugungi holat: V1 to'liq tugallandi — 122/122 backend test, tsc/eslint/build toza,
> barcha migratsiyalar Supabase'ga qo'llangan, backend ishlayapti.
> Bu fayl: ertaga nima qilamiz — kamchiliklar, tuzatishlar va yangi featurelar.

---

## 1. BUGUNGI QILGAN ISHLAR (yodda saqlash uchun)

| # | Ish | Holat |
|---|-----|-------|
| 1 | Dashboard vidjetlari: recent orders, low stock, status distribution (donut), revenue comparison | ✅ |
| 2 | Jamoa: rol o'zgartirish (owner himoyasi), invited userni hard-delete | ✅ |
| 3 | Mahsulot rasmi upload (signed-URL) — allaqachon bor edi, tasdiqlandi | ✅ |
| 4 | Billing (plan), ownership transfer, company close (owner-only) + Settings UI | ✅ |
| 5 | Email'lar FastAPI BackgroundTasks'ga o'tkazildi (5 ta joyda) | ✅ |
| 6 | Supabase RLS policy'lar (auth schema bor joyda avtomatik yoqiladi) | ✅ |
| 7 | docker-compose.prod.yml + Dockerfile.prod (Next standalone) + DEPLOYMENT.md | ✅ |
| 8 | Multi-org: organization_members jadvali, switch-org, memberships API, org switcher UI | ✅ |
| 9 | Hujjatlar: README, docs/API.md yangilandi; keraksiz fayllar o'chirildi | ✅ |

**O'chirilganlar:** `sellflow-luxury-storefront-&-admin-suite/` (boshqa loyiha),
`0` (junk fayl), `frontend/tsconfig.tsbuildinfo` (cache).
**Saqlangan:** `diqqat.md` (shaxsiy eslatmalar), `main.md` (spec).

---

## 2. MA'LUM KAMCHILIKLAR (bugun aniqlangan, ertaga tuzatamiz)

### 2.1. Live (Supabase) ma'lumotlarda bo'shliqlar — ENG MUHIM
- **Suppliers = 0** — seed live DB'da ishlamagan. Demo'da supplierlar yo'q.
  → Tuzatish: `backend/app/db/seed.py` ni live DB'ga qarshi ishga tushirish
  (yoki faqat suppliers/agar bo'sh bo'lsa, `--if-empty` flag bilan).
- **Eski orderlarda `created_by` bo'sh** — kolonna keyin qo'shilgan, eski
  orderlar "by:" ko'rsatmaydi → UI'da `created_by_name` empty.
  → Tuzatish: backfill SQL — eski orderlarga `created_by` ni owner'ga yozish
  (migratsiya yoki bir martalik skript).
- **Eski demo userlar `email_verified=False`** — owner@techmart.uz va boshqalar
  hali ham "Email not verified" bannerini ko'radi.
  → Tuzatish: backfill — seed'da yaratilgan userlarni `email_verified=True` qilish.

### 2.2. Multi-org arxitektura cheklovlari (ma'lum va hujjatlashtirilgan)
- **Rollar home-org'ga bog'liq**: org switcher'da almashtirganda rollar va
  permissions o'zgarmaydi (user_roles global join). Boshqa org'dagi user
  o'z home-org rollarini ishlatadi.
  → Qaror kerak: (a) per-org role mapping (organization_members'ga role qo'shish),
  yoki (b) cheklovni hujjatlashtirib qoldirish (hozircha demo uchun yetarli).
- **Mavjud userni boshqa org'ga qo'shish UI yo'q** — invite har doim YANGI
  akkaunt yaratadi. Dual-org userlar faqat DB insert orqali bo'ladi.
  → Yangi feature (3-bo'limga qarang): "Add to another organization".
- **RLS faqat defense-in-depth** — app user (postgres/service role) owner
  bo'lgani uchun RLS amalda qo'llanilmaydi (FORCE qilinmagan).
  → Tuzatish: hujjatlashtirish + (katta ish) alohida DB role + FORCE RLS.

### 2.3. Kichik sifat kamchiliklari
- **Parol o'zgartirish UI yo'q** — Settings'da "Change password" bo'limi yo'q
  (backend `POST /auth/reset-password` bor, lekin login bo'lgan holda eski
  parol bilan almashtirish endpoint'i yo'q).
- **window.confirm() ishlatilgan** — users va settings sahifalarida native
  confirm dialog. Professional modal confirm komponenti qilish kerak.
- **Dashboard CSV export** yangi vidjetlarni (recent_orders, low stock) o'z ichiga
  olmaydi.
- **Notification bell** 30 soniyada poll qiladi — real-time emas.
- **Audit log'da sana diapazon filtri va CSV export yo'q** (entity_type filtri bor).
- **Inventory history'da sana/type filtrlari cheklangan**, export yo'q.
- **Storefront** (public) UI to'liq emas: reviews/back-in-stock/checkout backend'da
  bor, lekin frontend'da qanchalik ishlatilgani tekshirilishi kerak.
- **Frontend testlari umuman yo'q** — faqat tsc/eslint. Vitest unit testlar yo'q,
  E2E (Playwright) yo'q.

---

## 3. TUZATILADIGANLAR (ertaga, priority tartibida)

| Pri | Ish | Fayllar | Izoh |
|-----|-----|---------|------|
| 🔴 1 | Live DB backfill: suppliers seed, created_by backfill, email_verified backfill | `backend/app/db/seed.py`, bir martalik SQL/migratsiya | Demo to'liq ishlaydigan bo'ladi |
| 🔴 2 | "Change password" — eski parolni tekshirib yangilash endpoint'i + Settings UI | `backend/app/api/v1/auth.py`, `backend/app/services/auth_service.py`, `frontend/app/dashboard/settings/page.tsx` | `POST /auth/change-password` (auth kerak, old_password + new_password) |
| 🟠 3 | ConfirmModal komponenti — window.confirm'ni almashtirish | `frontend/components/ui/modal.tsx`, users/settings sahifalari | UX professional bo'ladi |
| 🟠 4 | CSV export: dashboard vidjetlari + audit log + inventory | `frontend/app/dashboard/page.tsx`, audit, inventory | Export CSV helper'ni umumlashtirish |
| 🟠 5 | Audit log: sana diapazoni filtri + CSV export | `backend/app/schemas/audit_log.py`, `backend/app/api/v1/audit_logs.py`, frontend audit sahifasi | |
| 🟡 6 | Frontend Vitest unit testlar (lib/format, lib/utils) | `frontend/lib/*.test.ts` | Asosiy helper'larga |
| 🟡 7 | Storefront frontend'ni tekshirish va to'ldirish (reviews, back-in-stock) | `frontend/app/storefront/*` | Backend tayyor, UI tekshiriladi |
| 🟡 8 | README/DEPLOYMENT'ga multi-org cheklovlarini hujjatlashtirish | `README.md`, `docs/ARCHITECTURE.md` | Yolg'on va'da qilmaslik |

---

## 4. YANGI FEATURE'LAR (ertaga, priority tartibida)

| Pri | Feature | Tavsif | Baho |
|-----|---------|--------|------|
| 🔴 1 | **Redis worker (arq/Celery) + scheduled jobs** | Email retry, kunlik digest, low-stock email xabarnoma (main.md #24 talab) | O'rta |
| 🟠 2 | **Mavjud userni boshqa org'ga qo'shish (join flow)** | Org A useri Org B'ga invite → yangi akkaunt emas, memberships +1 | O'rta |
| 🟠 3 | **Per-org role mapping** | organization_members'ga role; switch-org'da rollar o'zgaradi | O'rta |
| 🟠 4 | **SSE/WebSocket real-time notifications** | Bell 30s poll o'rniga live push | O'rta |
| 🟠 5 | **Order PDF invoice** | Buyurtmadan chiroyli invoice PDF (print-friendly sahifa) | O'rta |
| 🟡 6 | **Accountant roli** | main.md #6: accountant + `reports.read` permissions, pul hisobotlari | Kichik |
| 🟡 7 | **Mahsulot rasmlar galereyasi** | `product_images` jadvali bor — admin UI'da bir nechta rasm | O'rta |
| 🟡 8 | **Company logo upload** | storage'ga yuklash (hozir URL input) | Kichik |
| 🟡 9 | **2FA (TOTP)** | Professional touch: totp secret + qr, login'da code | O'rta |
| 🟡 10 | **Sessiya boshqaruvi** | Faol sessiyalar ro'yxati (refresh_tokens), revoke qilish | Kichik |
| 🟡 11 | **CI/CD (GitHub Actions)** | pytest + ruff + tsc + eslint + build har push'da | Kichik |
| 🟡 12 | **Reverse proxy + HTTPS (Caddy/Traefik)** | DEPLOYMENT'ga qo'shimcha: Caddyfile | Kichik |
| 🟢 13 | **CSV import** (products/customers) | Katta jadval import | O'rta |
| 🟢 14 | **Sentry error tracking** | Backend + frontend | Kichik |
| 🟢 15 | **i18n (EN + UZ)** | next-intl yoki qo'lda dictionary | O'rta |

---

## 5. ERTAGA ISHLASH TARTIBI (checklist)

1. 🔴 **Backfill** — suppliers seed + `created_by` backfill + `email_verified` backfill
   → keyin live smoke test: suppliers ko'rinadi, orderlarda "by" bor, banner yo'q.
2. 🔴 **Change password** — backend endpoint + test (`test_auth.py` ga qo'shish) + Settings UI.
3. 🟠 **ConfirmModal** — users/settings'da window.confirm'ni almashtirish.
4. 🟠 **Export yaxshilash** — dashboard CSV + audit CSV.
5. 🟠 **Audit sana filtri**.
6. 🟡 **Vitest unit testlar** — format/helper'larga.
7. 🟡 **Storefront UI tekshirish** — reviews/back-in-stock ishlashini tekshirish.
8. 🟡 **Redis worker (arq)** — email retry + kunlik low-stock digest.
9. 🟡 **Join-flow / per-org rollar** (agar vaqt bo'lsa).
10. ✅ **Yakuniy tekshiruv** — pytest, ruff, tsc, eslint, build + README/API.md yangilash.

### Har doim ishlatiladigan tekshiruv buyruqlari
```bash
# Backend (testlar + lint):
docker compose exec -T backend pytest -q
docker compose exec -T backend ruff check app tests

# Frontend:
npx tsc --noEmit
npx eslint app lib components --max-warnings 0
npm run build

# Live DB migratsiya + restart:
docker compose exec -T backend alembic upgrade head
docker compose restart backend

# Smoke test (demo login):
# POST /api/v1/auth/login  → owner@techmart.uz / DemoPass123!
```

---

## 6. MUXIM ESLATMALAR

- **.env `DATABASE_URL` Supabase'ga qaratilgan** — har qanday migratsiya/seed
  live DB'ga tushadi. Ehtiyot bo'ling, avval test DB (pytest o'zi yaratadi) da
  tekshiring.
- **RLS migratsiyasi auth schema'ga bog'liq** — lokal Postgres'da avtomatik
  o'tkazib yuboriladi (migration ichida `_auth_schema_exists()` tekshiruvi bor).
- **Test DB** = `seller_management_test` (backend konteyneri ichida postgres
  service'ga ulanadi) — session oxirida o'chiriladi.
- **Yangi migratsiya qilganda** revision'ni keyingi tartibda yozing:
  `e2f3a4b5c6d7` dan keyin navbatdagisi `f3a4b5c6d7e8` va h.k.
- Eski backend qoidalari: hech qachon `user.organization_id`'ni to'g'ridan
  o'zgartirmang — faqat `effective_organization_id` (deps'da o'rnatiladi).
