1. Projectning asosiy modeli

Seller Management SaaS'ni men multi-tenant SaaS qilgan bo‘lardim.

Ya'ni bitta platformada ko‘plab seller/businesslar bo‘ladi:

Platform
│
├── Company A
│   ├── Owner
│   ├── Manager
│   ├── Staff
│   └── Products
│
├── Company B
│   ├── Owner
│   ├── Manager
│   ├── Staff
│   └── Products
│
└── Company C
    ├── Owner
    ├── Manager
    └── Products

Eng muhim qoida:

Company A hech qachon Company B ma'lumotlarini ko‘ra olmasligi kerak.

Shuning uchun projectning yuragi tenant isolation bo‘ladi.

2. Userlar qanday bo‘ladi?

Men hozircha 4 ta role qilardim.

1. Owner

Company'ni yaratgan asosiy user.

Huquqlari:

barcha dashboard
barcha products
barcha orders
customers
inventory
reports
team management
billing
company settings
role management
manager/staff qo‘shish
userni o‘chirish
companyni o‘chirish

Owner — eng yuqori permission.

3. Admin kerakmi?

Bu yerda ehtiyot bo‘lish kerak.

Agar Owner va Admin bir xil huquqqa ega bo‘lsa, Admin yaratish shart emas.

Lekin portfolio projectni kuchliroq qilish uchun:

Owner

Company egasi.

Admin

Company ichidagi yuqori darajadagi administrator.

Admin:

users
products
orders
inventory
customers
reports

bilan ishlashi mumkin.

Lekin:

billing
ownership transfer
company deletion

kabi kritik funksiyalar faqat Owner'da bo‘ladi.

4. Manager

Manager kundalik biznesni boshqaradi.

Masalan:

Manager
├── Products
├── Orders
├── Inventory
├── Customers
└── Reports

Lekin:

❌ Delete company
❌ Transfer ownership
❌ Billing
❌ Manage Owner

qila olmaydi.

5. Staff

Oddiy employee.

Masalan:

Staff
├── View products
├── Create orders
├── Update order status
├── View customers
└── Manage inventory

Lekin:

❌ Delete products
❌ Delete users
❌ Reports
❌ Settings
❌ Billing

kabi cheklovlar bo‘lishi mumkin.

6. Yana Accountant kerakmi?

Hozircha yo‘q.

Agar keyinchalik accounting module qo‘shsang:

Accountant
├── Expenses
├── Revenue
├── Financial reports
└── Transactions

qilishing mumkin.

Lekin birinchi versiyada role sonini ko‘paytirib yuborma.

V1:
OWNER
ADMIN
MANAGER
STAFF

yetarli.

7. Auth qanday bo‘ladi?

Sen Supabase ishlatayotganing juda yaxshi.

Men:

Supabase Auth
+
Supabase PostgreSQL
+
RLS

dan foydalanardim.

Login:

Frontend
   ↓
Supabase Auth
   ↓
JWT
   ↓
User authenticated

Lekin role'ni frontendga ishonib topshirmaysan.

Masalan frontend:

role === "owner"

deb tekshirishi mumkin, lekin security shu bilan tugamaydi.

Backend/database ham tekshirishi kerak.

8. Authentication'da nimalar bo‘lishi kerak?

Kamida:

Register
email
password
name
company name
Login
email
password
Logout
Forgot password
Reset password
Email verification
Session management
Protected routes

Masalan:

/dashboard
/products
/orders
/customers
/settings

login qilmagan user kira olmaydi.

9. User va Company relationship

Mana bu joy juda muhim.

Buni:

users
---------
id
name
email
role
company_id

qilib qo‘yish mumkin, lekin men membership architecture ishlatishni afzal ko‘raman.

users/profiles
profiles
---------
id
email
full_name
avatar_url
created_at
companies
companies
---------
id
name
slug
logo_url
created_at
created_by
company_members
company_members
----------------
id
company_id
user_id
role
status
joined_at

Natijada:

User
  ↓
Membership
  ↓
Company

bo‘ladi.

Bu keyinchalik bitta userning bir nechta company'da ishlashiga ham imkon beradi.

Masalan:

Islom
│
├── Company A → OWNER
└── Company B → MANAGER

Bu SaaS uchun ancha professional architecture.

10. Database

Sen Supabase ishlatayotganing uchun:

Primary database

PostgreSQL

Bu barcha asosiy ma'lumotlarning source of truthi.

Redis database o‘rnini bosmaydi.

11. Asosiy database tables

Men V1 uchun taxminan quyidagilarni qilardim:

profiles


companies


company_members


roles / permissions

Keyin business:

products


product_categories


product_images


inventory


inventory_transactions


orders


order_items


customers


suppliers

Keyin:

notifications


audit_logs



Analytics uchun kerak bo‘lsa:

expenses


payments
12. Products

products

id
company_id
category_id
name
sku
description
price
cost_price
stock_quantity
low_stock_threshold
status
created_at
updated_at

Lekin bu yerda bir muhim muammo bor.

Agar inventory'ni professional qilmoqchi bo‘lsang, stock_quantityni shunchaki qo‘yib qo‘yish yetarli emas.

13. Inventory

Masalan:

Product A
Stock = 100

Keyin 5 ta sotildi.

Shunchaki:

stock = 95

qilib qo‘yish mumkin.

Lekin professional systemda inventory transaction ham bo‘ladi.

inventory_transactions


id
company_id
product_id
type
quantity
reference_type
reference_id
created_by
created_at

Masalan:

+100 → Stock In
-5   → Order
+20  → Restock
-2   → Damaged

Shunda productning stock history'sini ko‘rish mumkin.

Bu juda yaxshi portfolio feature.

14. Orders

orders

id
company_id
customer_id
order_number
status
subtotal
discount
tax
shipping_fee
total
payment_status
created_by
created_at
updated_at

Status:

PENDING
CONFIRMED
PROCESSING
SHIPPED
DELIVERED
CANCELLED
15. Order Items

Alohida:

order_items


id
order_id
product_id
quantity
unit_price
total

Masalan:

Order #1001


iPhone Case
2 × $10 = $20


Keyboard
1 × $30 = $30


Total = $50

Order ichida bularni bitta JSON field qilib saqlashdan ko‘ra relational structure yaxshiroq.

16. Customer

customers

id
company_id
name
email
phone
address
created_at
updated_at

Customer:

Customer
 ├── Orders
 ├── Total spent
 ├── Last order
 └── Order count
17. Supplier

Seller business uchun supplier ham foydali:

suppliers


id
company_id
name
email
phone
address
status
created_at

Keyinchalik purchase system qo‘shish mumkin.

18. Dashboard

Dashboard oddiy 4 ta card bilan tugamasin.

Masalan:

Revenue
$24,530


Orders
1,248


Customers
823


Products
346

Keyin:

Sales chart
Today
7 days
30 days
12 months
Recent orders
Top products
Low-stock products
Order status distribution
Revenue comparison

Masalan:

This month
vs
Last month
19. Product management

Product CRUD:

Create
Read
Update
Delete

Lekin qo‘shimcha:

Search
Search product...
Filter
Category
Status
Stock
Price
Sort
Newest
Oldest
Price low → high
Price high → low
Pagination
1 2 3 4 5 Next

1000 ta productni bir paytda frontendga yuborma.

20. Product status

Masalan:

ACTIVE
DRAFT
ARCHIVED
OUT_OF_STOCK

DELETE qilish o‘rniga ba'zi hollarda ARCHIVED qilish yaxshiroq.

Bu real business systemlarda foydali.

21. Inventory alert

Masalan:

Stock = 4
Threshold = 10

System:

LOW STOCK

deb chiqaradi.

Keyinchalik notification:

⚠ Product "Keyboard" is running low.
Only 4 units remaining.
22. Notifications

notifications

id
user_id
company_id
type
title
message
read
created_at

Masalan:

Low stock
New order
Order cancelled
Team invitation
23. Redis'ni qayerda ishlatamiz?

Redis'ni allaqachon ishlatayotgan bo‘lsang, yaxshi.

Lekin hamma narsani Redisga tiqma.

PostgreSQL:

Haqiqiy ma'lumot.

Redis:

Tezkor vaqtinchalik ma'lumot.

Redis uchun:
1. Cache

Dashboard:

dashboard:company_id:30d

kabi cache.

2. Rate limiting

Masalan:

100 requests / minute
3. Background jobs

Masalan:

Order created
     ↓
Queue
     ↓
Worker
     ↓
Send notification
4. Temporary data

Masalan verification/temporary state.

24. Redis + Worker

Agar FastAPI ishlatayotgan bo‘lsang:

FastAPI
   ↓
Redis
   ↓
Worker

qilishing mumkin.

Masalan:

Generate monthly report

bu 10 sekund vaqt olsa, user requestni kutib turmasin.

POST /reports/generate
        ↓
Queue job
        ↓
202 Accepted
        ↓
Worker processes
        ↓
Notification

Bu production-style architecture bo‘ladi.

25. Supabase Storage

Supabase'dan faqat Auth + PostgreSQL emas, Storage ham ishlatishing mumkin.

Masalan:

company-assets/
    company-logo.png


product-images/
    product-1.webp
    product-2.webp


avatars/
    user-1.webp

Database'ga image'ning o‘zini emas:

image_url

saqlaysan.

26. RBAC

Bu projectdagi eng muhim portfolio featurelardan biri.

Frontend:

Can user see this button?

Backend/database:

Can user actually perform this operation?

ikkalasi boshqa-boshqa.

Masalan Staff frontendda:

Delete Product

buttonini ko‘rmasligi mumkin.

Lekin kimdir API'ni qo‘lda chaqirsa:

DELETE /products/123

backend:

403 Forbidden

qaytarishi kerak.

27. Permission systemni yanada professional qilish

Role'ni faqat:

if role == "owner"

qilib everywhere yozib tashlama.

Permission concept qil:

products.read
products.create
products.update
products.delete


orders.read
orders.create
orders.update
orders.cancel


inventory.read
inventory.update


customers.read
customers.create
customers.update


reports.read


team.read
team.invite
team.remove


settings.update
billing.manage

Keyin role → permissions:

OWNER
→ *


ADMIN
→ almost everything


MANAGER
→ products.*
→ orders.*
→ inventory.*
→ customers.*
→ reports.read


STAFF
→ products.read
→ orders.read
→ orders.create
→ inventory.read

Bu juda professional ko‘rinadi.

28. RLS — Supabase'da juda muhim

Agar Supabase PostgreSQL ishlatayotgan bo‘lsang, Row Level Securityni jiddiy qil.

Masalan:

Company A user:

company_id = A

faqat:

WHERE company_id = A

ma'lumotlarni ko‘ra olishi kerak.

Company B:

company_id = B

Shuning uchun:

SELECT * FROM products

degan query ham RLS orqali boshqa company's productsni qaytarmasligi kerak.

Bu projectning security foundationi.

29. Audit Logs

Buni albatta qo‘shishni tavsiya qilaman.

audit_logs

id
company_id
user_id
action
entity_type
entity_id
old_data
new_data
created_at

Masalan:

Manager changed Product #52 price
$20 → $25

yoki:

Admin removed user John

Bu enterprise/business applicationga juda yaxshi taassurot beradi.

30. Team Management

Owner/Admin:

Team

sahifasiga kiradi.

Ko‘radi:

John
john@email.com
MANAGER
Active

Actions:

Change role
Deactivate
Remove

Invite:

Email
Role
Send invitation
31. Account status

User faqat:

active

bo‘lmasin.

Masalan:

INVITED
ACTIVE
SUSPENDED
REMOVED

Bu real SaaS'ga yaqinlashtiradi.

32. Company Settings

Company:

Name
Logo
Currency
Timezone
Address
Phone
Email

Masalan currency:

USD
UZS
KRW
EUR
33. Pagination + Filtering + Search

Bularni deyarli hamma listlarda qil:

Products
Orders
Customers
Suppliers
Users

Backend:

?page=1
&limit=20
&search=keyboard
&sort=created_at
&order=desc
34. API structure

FastAPI projectni ham tartibli qil.

Masalan:

app/
├── main.py
│
├── api/
│   ├── auth.py
│   ├── products.py
│   ├── orders.py
│   ├── customers.py
│   ├── inventory.py
│   ├── suppliers.py
│   ├── dashboard.py
│   ├── team.py
│   └── notifications.py
│
├── models/
│
├── schemas/
│
├── services/
│
├── repositories/
│
├── dependencies/
│
├── core/
│
└── workers/

Business logicni route ichiga tiqib tashlama.

Yaxshiroq:

Router
 ↓
Service
 ↓
Repository
 ↓
Database
35. Frontend architecture

Next.js:

app/
├── (auth)/
│   ├── login/
│   └── register/
│
├── dashboard/
│
├── products/
├── orders/
├── customers/
├── inventory/
├── suppliers/
├── team/
├── reports/
└── settings/

Components:

components/
├── dashboard/
├── products/
├── orders/
├── tables/
├── forms/
├── charts/
└── ui/
36. Loading / Error / Empty states

Buni ko‘pchilik unutadi.

Masalan Products:

Loading
Loading products...
Empty
No products found.


+ Add Product
Error
Failed to load products.


Try again
Success
Product created successfully.

Professional UI aynan shunday detallardan chiqadi.

37. Validation

Frontend:

price > 0
name required
SKU required

Backend ham xuddi shuni tekshiradi.

Frontend validationga hech qachon security sifatida ishonma.

38. Security checklist

Buni alohida tekshir:

Supabase RLS
Authentication
Authorization
Password security
JWT/session handling
CORS
Rate limiting
Input validation
File upload validation
SQL injection protection
XSS protection
CSRF consideration
.env secrets
No API keys in frontend
Audit logs
Tenant isolation

Ayniqsa:

company_id ni frontend yuborgani uchun unga ishonma.

User:

{
  "company_id": "company-B"
}

deb yuborib, Company B ma'lumotiga kirib ketmasligi kerak.

Company membership server-side aniqlanishi kerak.

39. Testing

Portfolio uchun kamida:

Backend
Auth tests
Permission tests
Product CRUD
Order creation
Inventory update
Tenant isolation

Eng muhim test:

Company A user
      ↓
Try accessing Company B product
      ↓
403 / 404

Bu juda yaxshi security test.

40. Docker

Final projectda:

frontend
backend
postgres
redis

containerized bo‘lishi yaxshi.

Supabase ishlatayotganing uchun production'da alohida Postgres container shart emas. Local architecture'ni ham Supabase bilan ishlatish mumkin.

41. Projectning ideal architecture'si

Sening holatingda men quyidagini tanlagan bo‘lardim:

                    USER
                     │
                     ▼
              ┌─────────────┐
              │   Next.js   │
              │ TypeScript  │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │   FastAPI   │
              │   Backend   │
              └──────┬──────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
     Supabase      Redis     Storage
       Auth       Cache/      Files
       RLS        Queue
          │
          ▼
    PostgreSQL
          │
          ▼
     Business Data

Agar background processing kerak bo‘lsa:

FastAPI
   ↓
Redis Queue
   ↓
Worker
42. V1 uchun men qiladigan featurelar

Scope'ni nazorat qilish uchun birinchi versiyani quyidagicha qil:

Authentication
Register
Login
Logout
Email verification
Forgot/reset password
Protected routes
Company
Create company
Company profile
Company settings
Team
Invite member
Roles
Activate/deactivate
Remove member
Products
CRUD
Categories
Search
Filter
Sort
Pagination
Product image
Inventory
Stock
Stock in/out
Low stock
Inventory history
Orders
Create order
Order items
Status
Payment status
Order history
Customers
CRUD
Customer orders
Customer statistics
Dashboard
Revenue
Orders
Products
Customers
Sales chart
Recent orders
Low stock
Security
RBAC
RLS
Tenant isolation
Validation
System
Notifications
Audit logs
Error handling
Loading states
Empty states

Shu V1ning o‘zi yetarlicha katta va professional.

43. Hozir sen nimani qilishing kerak?

Sen projectni allaqachon boshlaganing uchun yana kod yozishga shoshilma.

Avval mavjud projectni quyidagi 10 ta punkt bo‘yicha tekshir:

1. Authentication
2. Multi-tenancy
3. Roles / Permissions
4. Database schema
5. RLS
6. Products
7. Inventory
8. Orders
9. Customers
10. Dashboard

Keyin:

11. Team management
12. Notifications
13. Audit logs
14. Redis
15. Background jobs
16. Validation
17. Error handling
18. Testing
19. Docker
20. Deployment

Ayniqsa 2, 3, 5-bandlar — Multi-tenancy, RBAC va RLS — sening hozirgi projectda eng avval tekshirilishi kerak. Chunki UI chiroyli bo‘lib, security architecture noto‘g‘ri bo‘lsa, portfolio projectning eng muhim professional qismi yo‘qoladi.