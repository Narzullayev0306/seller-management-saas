# SELLER MANAGEMENT SAAS — FINAL UI/UX + MOTION PASS

You are a Staff Product Designer + Senior Frontend Engineer + Motion Designer.

Your ONLY responsibility in this task is:

1. UI/UX
2. Visual design
3. Responsive design
4. Animation
5. Motion
6. Micro-interactions
7. Frontend visual polish

DO NOT modify backend business logic.

DO NOT redesign the backend.

DO NOT add new backend features.

DO NOT change database architecture.

DO NOT change APIs unless absolutely required for an existing frontend bug.

This is a FRONTEND EXPERIENCE PASS.

==================================================
PROJECT
==================================================

Existing stack:

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS v4
- Recharts

The application is an existing Seller Management SaaS.

It already has:

- Dashboard
- Analytics
- Products
- Orders
- Customers
- Sellers
- Suppliers
- Inventory
- Coupons
- Shipping
- Returns
- Purchase Orders
- Notifications
- Team
- Billing
- API Keys
- Webhooks
- Domains
- Settings
- Storefront
- Cart
- Checkout

DO NOT remove any existing functionality.

==================================================
MAIN GOAL
==================================================

Transform the current interface from:

"good admin dashboard"

into:

"premium production SaaS product."

Design inspiration:

- Linear
- Stripe
- Vercel
- Shopify
- Raycast
- Notion

IMPORTANT:

Do NOT copy their interfaces.

Use their design principles:

- excellent spacing
- strong hierarchy
- subtle motion
- excellent typography
- clear information architecture
- minimal visual noise
- fast interactions
- predictable UX

Create a unique visual identity for Seller Management SaaS.

==================================================
DESIGN PHILOSOPHY
==================================================

The UI should feel:

- premium
- calm
- fast
- precise
- modern
- trustworthy
- professional

Avoid:

- excessive gradients
- excessive glassmorphism
- huge shadows
- excessive rounded cards
- childish animations
- unnecessary decorations
- excessive colors
- slow transitions

The application should look expensive without looking flashy.

==================================================
1. DESIGN SYSTEM
==================================================

Create or improve a centralized design system.

Standardize:

- colors
- typography
- spacing
- border radius
- shadows
- component heights
- transitions
- focus states
- icon sizing

Use design tokens.

Do NOT randomly choose values on individual pages.

Everything must feel like one coherent product.

==================================================
2. TYPOGRAPHY
==================================================

Improve typography hierarchy.

Create consistent styles for:

- Page title
- Section title
- Card title
- Body
- Secondary text
- Caption
- Labels
- Table text
- Numeric/KPI values

Make dashboards highly readable.

Important:

Large numbers such as revenue, orders and growth should have strong hierarchy.

Do not make everything bold.

Use typography to create visual hierarchy.

==================================================
3. SPACING
==================================================

Fix inconsistent spacing throughout the application.

Use a predictable spacing system.

Focus on:

- dashboard padding
- card spacing
- table spacing
- form spacing
- sidebar spacing
- modal spacing
- mobile spacing

The interface should breathe.

Avoid cramped layouts.

==================================================
4. SIDEBAR
==================================================

Redesign the sidebar visually.

Requirements:

- clean hierarchy
- clear active state
- elegant icons
- section labels
- hover states
- selected item animation
- collapsed state
- mobile drawer

Active navigation should have a subtle animated indicator.

Example:

background opacity transition

+ slight movement

+ icon transition

Keep it subtle.

==================================================
5. TOP NAVIGATION
==================================================

Polish:

- search
- notifications
- organization selector
- profile menu

Improve spacing and alignment.

Everything must feel intentional.

==================================================
6. COMMAND PALETTE
==================================================

If command palette already exists, polish it.

If it does not exist, implement a lightweight version.

Keyboard:

CTRL + K
CMD + K

Animation:

- backdrop fade
- panel scale from 0.97 → 1
- subtle blur
- fast entrance
- smooth exit

Do not make it slow.

==================================================
7. DASHBOARD
==================================================

Make the dashboard the strongest page.

Improve:

- KPI cards
- revenue chart
- order chart
- inventory information
- recent activity
- quick actions
- alerts

KPI cards:

When the page loads:

number should animate subtly.

Example:

$0 → $12,430

Do NOT use dramatic counting animations.

Use short, elegant number transitions.

==================================================
8. CHART ANIMATIONS
==================================================

Improve Recharts animations.

Charts should reveal smoothly.

Examples:

line chart:

draw from left to right

bar chart:

bars rise subtly

pie/donut:

progressive reveal

Tooltips:

fade + slight scale

Keep animations under approximately 500ms.

Charts must remain performant.

==================================================
9. CARDS
==================================================

Redesign cards.

Cards should have:

- subtle border
- subtle shadow
- consistent radius
- consistent padding

Hover:

very small elevation

very small translateY

border transition

Do NOT make cards jump.

==================================================
10. TABLES
==================================================

Make tables feel premium.

Improve:

- header
- row height
- hover
- selected state
- sorting
- filters
- pagination
- actions

Row hover should be subtle.

Actions should appear naturally.

Avoid visual clutter.

==================================================
11. MOBILE TABLE UX
==================================================

IMPORTANT.

Do NOT squeeze desktop tables onto mobile.

For:

Products
Orders
Customers
Inventory
Sellers

create responsive card/list layouts when necessary.

Mobile cards should contain:

- primary information
- important status
- key number
- action menu

Everything must remain readable.

==================================================
12. BUTTON MOTION
==================================================

Buttons should have subtle interaction feedback.

States:

normal
hover
active
loading
disabled
success

Interaction:

hover:
slight visual transition

active:
very subtle scale-down

loading:
spinner or progress indicator

success:
subtle confirmation

Do not bounce buttons.

==================================================
13. INPUTS
==================================================

Improve input UX.

Focus:

- border transition
- subtle ring
- label clarity

Error:

- clear visual indication
- useful message

Success:

- subtle confirmation

Do not make inputs overly animated.

==================================================
14. MODALS
==================================================

All dialogs should feel premium.

Open:

backdrop fades in

dialog:

opacity 0 → 1

scale:

0.97 → 1

slight translateY

Close:

reverse animation.

Duration:

approximately 180–250ms.

==================================================
15. DRAWERS
==================================================

Sidebar/mobile drawers:

slide smoothly from edge.

Backdrop:

fade.

Content:

slight opacity transition.

Respect reduced motion.

==================================================
16. DROPDOWNS
==================================================

Dropdown menus:

- fade
- slight scale
- slight translate

Do not use large movement.

==================================================
17. TOASTS
==================================================

Create premium toast animation.

Entrance:

slide + fade

Exit:

fade + slide

Types:

success
error
warning
info

Keep duration appropriate.

==================================================
18. SKELETONS
==================================================

Create polished skeleton loading states.

Use subtle shimmer.

Apply to:

- dashboard
- products
- orders
- customers
- inventory
- analytics

Avoid excessive shimmer.

Skeleton should preserve layout dimensions.

No layout jumping.

==================================================
19. EMPTY STATES
==================================================

Improve empty states.

Each should have:

- simple visual
- title
- explanation
- primary action

Example:

"No products yet"

"Create your first product to start managing inventory."

[Create Product]

Animations should be subtle.

==================================================
20. ERROR STATES
==================================================

Improve error screens.

Need:

- clear explanation
- retry
- navigation option

Animation should NOT be dramatic.

==================================================
21. PAGE TRANSITIONS
==================================================

Implement subtle page transitions where appropriate.

Use:

opacity

+ small translate

Do NOT make every page transition slow.

Target:

150–250ms.

Respect:

prefers-reduced-motion.

==================================================
22. MICRO-INTERACTIONS
==================================================

Add subtle micro-interactions to:

- navigation
- cards
- buttons
- tables
- tabs
- dropdowns
- switches
- checkboxes
- copy buttons
- filters
- search

Examples:

Copy API key:

click
→ icon changes
→ "Copied"
→ subtle confirmation

Toggle:

smooth thumb movement

Tabs:

animated active indicator

Pagination:

subtle transition

==================================================
23. SEARCH UX
==================================================

Search should feel fast.

Improve:

- focus state
- keyboard shortcut
- suggestions
- loading
- empty result
- result selection

Keyboard navigation must work.

==================================================
24. FILTERS
==================================================

Filters should have clear states.

When filter is active:

show visual indicator.

Filter dropdown:

smooth entrance.

Clear filters:

simple animation.

==================================================
25. NOTIFICATION CENTER
==================================================

Improve notification experience.

Unread items:

subtle background difference.

Unread count:

small animated badge.

Opening notification panel:

smooth drawer/dropdown.

Avoid excessive animation.

==================================================
26. STORE FRONT
==================================================

The storefront should NOT look like the admin dashboard.

Give it a separate ecommerce visual personality while keeping the brand identity.

Improve:

- product cards
- hover states
- image transitions
- product detail
- cart
- checkout

Product cards:

image hover transition

small elevation

CTA appearance

==================================================
27. PRODUCT DETAIL
==================================================

Improve:

- image gallery
- product information
- variants
- quantity selector
- pricing
- stock status

Variant selection should have clear animation.

==================================================
28. CART
==================================================

Cart interactions:

quantity change

remove item

subtotal update

should update smoothly.

Avoid full page refresh feeling.

==================================================
29. CHECKOUT
==================================================

Checkout should feel trustworthy.

Improve:

- progress
- form layout
- validation
- loading
- success

Successful checkout:

show a polished confirmation state.

Do not use excessive confetti.

A subtle success animation is enough.

==================================================
30. MOBILE NAVIGATION
==================================================

Create excellent mobile navigation.

Use:

- mobile drawer
- bottom actions only where appropriate
- large touch targets
- clear hierarchy

No horizontal scrolling.

==================================================
31. RESPONSIVE DESIGN
==================================================

Audit every major page.

Test:

320px
375px
390px
430px
768px
1024px
1280px
1440px
1920px

Fix:

- overflow
- clipping
- bad wrapping
- oversized elements
- tiny text
- inaccessible buttons

Mobile should feel intentionally designed.

==================================================
32. ACCESSIBILITY
==================================================

Implement WCAG 2.2 AA principles.

Check:

- keyboard navigation
- focus states
- semantic HTML
- labels
- aria attributes
- contrast
- dialogs
- menus
- notifications

CRITICAL:

Implement:

prefers-reduced-motion

When reduced motion is enabled:

- remove page transitions
- remove transform-heavy animations
- minimize decorative animation

Functional feedback must still remain.

==================================================
33. MOTION SYSTEM
==================================================

Create a consistent motion system.

Use approximately:

FAST:
120–150ms

NORMAL:
180–250ms

SLOW:
300–400ms

Use consistent easing.

Motion hierarchy:

Micro interactions:
120–180ms

Dropdowns:
150–200ms

Modals:
180–250ms

Page transitions:
200–300ms

Large transitions:
300–400ms

Avoid anything unnecessarily slow.

==================================================
34. MOTION RULE
==================================================

Every animation must answer:

"What does this animation communicate?"

Good:

button feedback
state change
navigation
loading
success
focus
hierarchy

Bad:

random floating elements
constant movement
huge zoom
unnecessary bouncing
long transitions

If an animation does not improve UX:

REMOVE IT.

==================================================
35. PERFORMANCE
==================================================

Animations must not damage performance.

Prefer:

transform
opacity

Avoid animating:

width
height
top
left

when possible.

Use GPU-friendly properties.

Avoid unnecessary JavaScript animation loops.

Avoid excessive DOM animation.

==================================================
36. ICON SYSTEM
==================================================

Make iconography consistent.

All icons should have:

- consistent size
- consistent stroke
- consistent alignment

Do not mix random icon styles.

==================================================
37. DARK MODE
==================================================

Polish dark mode.

Check:

- contrast
- borders
- cards
- tables
- inputs
- charts
- dialogs
- sidebar

Dark mode should feel designed, not inverted.

==================================================
38. LIGHT MODE
==================================================

Polish light mode.

Avoid:

pure white everywhere

Use subtle surfaces and hierarchy.

==================================================
39. FINAL VISUAL AUDIT
==================================================

After implementation inspect every major screen:

Login
Register
Dashboard
Analytics
Products
Product detail
Orders
Order detail
Customers
Sellers
Suppliers
Inventory
Coupons
Shipping
Returns
Purchase Orders
Notifications
Team
Billing
API Keys
Webhooks
Domains
Settings
Storefront
Cart
Checkout

For every screen ask:

1. Is spacing consistent?
2. Is typography clear?
3. Is hierarchy obvious?
4. Is the UI responsive?
5. Are interactions animated?
6. Are animations subtle?
7. Are loading states polished?
8. Are empty states polished?
9. Are errors understandable?
10. Does it feel premium?

==================================================
40. DO NOT BREAK EXISTING FUNCTIONALITY
==================================================

Before finishing:

Run:

npm run lint

npm run typecheck

npm run build

Run existing tests if available.

Fix every regression caused by this UI/UX pass.

==================================================
41. FINAL QUALITY BAR
==================================================

The final interface should feel:

NOT:

"developer dashboard"

BUT:

"real SaaS product"

The visual quality target is:

Linear-level interaction quality
Stripe-level clarity
Vercel-level simplicity
Shopify-level usability

Again:

Do NOT copy these products.

Create an original design language.

==================================================
42. FINAL RULE
==================================================

This is a UI/UX + Motion pass.

Do not add random features.

Do not rewrite backend.

Do not modify business logic.

Do not over-engineer.

Do not over-animate.

Do not make the UI slower.

Focus entirely on:

UI
UX
Responsive design
Motion
Animation
Micro-interactions
Accessibility
Visual polish
Performance

When finished:

1. Verify the application.
2. Fix regressions.
3. Ensure build passes.
4. Ensure mobile works.
5. Ensure reduced motion works.
6. Give a concise summary of what changed.

Then STOP.