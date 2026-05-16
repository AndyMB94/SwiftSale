# Frontend Architecture — SwiftSale

## Roadmap

### Phase F1 — Project Setup & Auth
- [x] Next.js project with TypeScript and pnpm
- [x] TailwindCSS + shadcn/ui configured with custom color tokens
- [x] Plus Jakarta Sans font, global styles, base layout shell
- [x] Axios instance with cookie-based auth and refresh interceptor
- [x] Zustand authStore
- [x] Login page
- [x] `/auth/me` on load to rehydrate session
- [x] Role-based route guards in dashboard layout
- [x] Logout flow

**Deliverable:** Authenticated shell with role-aware navigation. All three roles can log in and see their correct sidebar.

---

### Phase F2 — Products & Inventory
- [x] Product list page with search and category filter
- [x] Create / edit product slide-over
- [x] Soft delete with confirmation dialog
- [x] Category management (inline within products page)
- [x] Inventory list with low stock highlight
- [x] Stock adjustment modal with reason dropdown
- [x] Stock movement history per product

**Deliverable:** Admin and supervisor can fully manage products and stock levels.

---

### Phase F3 — POS Interface ✅
- [x] Full-screen POS layout (no sidebar)
- [x] Product grid with search and barcode input
- [x] Cart: add, remove, update quantity
- [x] Discount input, IGV calculation, totals
- [x] Payment method selector (cash / card / Yape / Plin)
- [x] Cash flow: amount received → change calculator → confirm
- [x] Yape/Plin flow: QR screen + countdown timer
- [x] Sale submission (POST /sales/)
- [x] Success screen with sale summary

**Deliverable:** Cashier can complete a full sale end-to-end from product selection to payment confirmation.

---

### Phase F4 — Real-Time (WebSocket) ✅
- [x] `useWebSocket` hook with exponential backoff auto-reconnect (max 5 retries)
- [x] `payment.confirmed` event → auto-triggers checkout completion on POS QR step
- [x] `payment.failed` event → error toast on POS QR step
- [x] `inventory.low_stock` event → warning toast in dashboard layout (admin/supervisor only)
- [x] Backend: `NotificationConsumer` now joins `staff_notifications` group for admin/supervisor users
- [ ] REST fallback polling on WebSocket disconnect *(deferred — reconnect handles most cases)*

**Deliverable:** Cashier screen updates instantly on Yape/Plin payment confirmation without manual refresh.

---

### Phase F5 — Sales & Payments ✅
- [x] Sales history table with date range + status filter
- [x] Sale detail slide-over (items, totals, payment info)
- [x] Cancel sale action (supervisor/admin)
- [x] Link to billing documents from sale detail (navigates to /billing?sale_id=xxx)
- [x] Payments table with status badges

**Deliverable:** Supervisors can review and manage all sales and payment records.

---

### Phase F6 — Billing (SUNAT) ✅
- [x] Billing documents table with SUNAT status badges
- [x] Issue boleta modal (DNI/CE/Pasaporte customer data)
- [x] Issue factura modal (RUC + company address)
- [x] Document detail slide-over with SUNAT response code
- [x] Void document with confirmation (admin only)
- [x] Filter by sale_id from URL param (auto-applied when navigating from sales slide-over)
- [ ] Download XML (CDR) button *(requires backend CDR storage)*
- [ ] Download PDF receipt button *(requires Celery async task)*

**Deliverable:** Staff can issue legally valid boletas and facturas and track their SUNAT submission status.

---

### Phase F7 — Reports & Audit ✅
- [x] Revenue report with line chart (recharts) + summary cards
- [x] Best sellers report with horizontal bar chart + ranking table
- [x] Inventory valuation report table with total valuation badge
- [x] Date range picker on revenue and best sellers tabs
- [x] Audit log table with action, target type, and date range filters — admin only

**Deliverable:** Management has full visibility into revenue trends and sensitive system actions.

---

### Phase F8 — Users & Polish
- [ ] User management table (admin only)
- [ ] Create user modal (email, role, password)
- [ ] Deactivate user with confirmation
- [ ] Loading skeletons on all data tables
- [ ] Empty states on all list pages
- [ ] Error boundaries and toast notifications
- [ ] Responsive layout (tablet support for supervisor dashboard)
- [ ] Favicon, page titles, meta tags

**Deliverable:** Complete, polished frontend ready for portfolio demonstration.

---

## Design Philosophy

SwiftSale targets three types of users in a retail environment:

- **Cashier** — operates the POS terminal under time pressure, standing, possibly touch screen
- **Supervisor** — monitors dashboards and reviews sales/inventory
- **Admin** — manages users, products, reports

The UI must be **fast to read, high contrast, and data-dense** — not decorative.
Inspired by: Stripe Dashboard, Linear, Vercel — clean professional tools, not consumer apps.

---

## Visual Style

**Theme:** Dark sidebar + light content area (hybrid approach).
Not full dark mode (hard to read in bright store environments).
Not full light mode (sidebar navigation loses hierarchy).

**Personality:** Professional, efficient, trustworthy — like a serious retail tool,
not a generic SaaS clone.

---

## Color Palette

### Brand Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#0D9488` (teal-600) | Primary actions, active nav items, links |
| `primary-dark` | `#0F766E` (teal-700) | Hover states on primary |
| `primary-light` | `#CCFBF1` (teal-100) | Badges, subtle highlights |

Rationale: Teal reads as "commerce + trust" without being the overused blue.
Distinct from shadcn defaults (zinc/blue), appropriate for a retail brand.

### Neutral Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `sidebar-bg` | `#0F172A` (slate-900) | Sidebar background |
| `sidebar-text` | `#94A3B8` (slate-400) | Inactive nav labels |
| `sidebar-active` | `#F1F5F9` (slate-100) | Active nav label |
| `content-bg` | `#F8FAFC` (slate-50) | Main content background |
| `card-bg` | `#FFFFFF` | Card backgrounds |
| `border` | `#E2E8F0` (slate-200) | Card borders, dividers |
| `text-primary` | `#0F172A` (slate-900) | Main text |
| `text-muted` | `#64748B` (slate-500) | Secondary text, labels |

### Semantic Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `success` | `#059669` (emerald-600) | Completed sales, paid |
| `warning` | `#D97706` (amber-600) | Low stock, pending payments |
| `danger` | `#DC2626` (red-600) | Cancelled, failed, errors |
| `info` | `#0284C7` (sky-600) | Informational badges |

### POS Screen (cashier-specific)
The POS screen uses a dedicated dark theme for focus:
- Background: `#111827` (gray-900)
- Product buttons: `#1E293B` (slate-800) with white text
- Total area: High contrast white on teal primary
- Action buttons: Larger than normal (48px height minimum)

---

## Typography

Font: **Inter** (Google Fonts) — clean, highly legible, standard for SaaS dashboards.

| Usage | Size | Weight |
|-------|------|--------|
| Page title | 24px | 600 |
| Section heading | 18px | 600 |
| Card title | 16px | 500 |
| Body text | 14px | 400 |
| Table cells | 14px | 400 |
| Labels / badges | 12px | 500 |
| POS product name | 15px | 500 |
| POS total | 32px | 700 |

---

## Layout

### Shell Structure
```
┌─────────────────────────────────────────────────┐
│  Sidebar (240px fixed) │  Main Content Area      │
│                        │  ┌─────────────────────┐│
│  Logo                  │  │ Top Bar (56px)       ││
│  ─────────────────     │  └─────────────────────┘│
│  Nav Items (role-based)│  │ Page Content         ││
│                        │  │                      ││
│  ─────────────────     │  │                      ││
│  User Info             │  │                      ││
│  Logout                │  └─────────────────────┘│
└─────────────────────────────────────────────────┘
```

The **POS screen** (`/pos`) is the exception: full screen, no sidebar,
maximizes space for the cashier workflow.

### Sidebar Navigation by Role

**Admin**
- Dashboard
- POS (link to cashier view)
- Products
- Inventory
- Sales
- Payments
- Billing
- Reports
- Users
- Audit Log

**Supervisor**
- Dashboard
- Products
- Inventory
- Sales
- Payments
- Billing
- Reports

**Cashier**
- POS (default landing page)
- Sales History (own sales only)

---

## Pages

### `/login`
Centered card on slate-50 background.
Logo + tagline at top.
Email + password fields.
No register link (internal tool — users created by admin).

### `/dashboard`
Stats cards row: revenue today, sales count, low stock alerts, pending payments.
Revenue chart (last 7 days) — recharts line chart.
Recent sales table (last 10).
Low stock alerts list.

### `/pos`
Full screen. No sidebar.
Left panel: product search + product grid (click to add to cart).
Right panel: cart items list + quantity controls + totals (subtotal, IGV 18%, discount, total).

**Payment flow by method:**
- **Cash**: cashier enters amount received → system shows change → confirm button
- **Card**: confirm button → mark as paid immediately (terminal handles it externally)
- **Yape / Plin**: show QR code screen with amount + countdown timer →
  customer scans → backend receives webhook → WebSocket pushes `payment.confirmed` →
  screen shows success banner automatically

Real-time: `payment.confirmed` → success banner with sale total.
Real-time: `payment.failed` → error banner with retry option.

### `/products`
Data table with search, category filter.
Create/edit product slide-over panel (shadcn Sheet).
Soft delete with confirmation dialog.

### `/inventory`
Low stock items highlighted in amber (from `/inventory/alerts/`).
Stock adjustment modal with reason field (dropdown: damaged_goods, purchase, return, correction).
Movement history per product: table with type, quantity change, date, actor.
Movement types: `sale`, `purchase`, `adjustment`, `return`.

### `/sales`
Data table with date range filter, status filter.
Sale detail slide-over.
Cancel sale action (supervisor/admin only).
Link to billing document if issued.

### `/payments`
Table of payments with status badges.
Webhook events visible on payment detail.

### `/billing`
Table of billing documents (boletas/facturas) with SUNAT status badges
(pending / sent / accepted / rejected / voided).
Issue boleta/factura modal: select document type → enter customer data (DNI/RUC) → submit.
Void document action with confirmation (admin only).
Download XML button (CDR stored by backend).
Download PDF receipt button (generated async by Celery).
Rejected documents show SUNAT error code and description.

### `/reports`
Three report cards: Revenue, Best Sellers, Inventory Valuation.
Date range picker.
Revenue: line/bar chart (recharts).
Best sellers: horizontal bar chart.
Inventory valuation: table.

### `/users`
Admin only. Data table of employees.
Create user modal (email, role, password).
Deactivate user action.

### `/audit`
Admin only. Filterable log table.
Filters: action type, actor, date range.

---

## Component Architecture

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── (auth)/
│   │   └── login/
│   ├── (dashboard)/
│   │   ├── layout.tsx            # Sidebar shell
│   │   ├── dashboard/
│   │   ├── products/
│   │   ├── inventory/
│   │   ├── sales/
│   │   ├── payments/
│   │   ├── billing/
│   │   ├── reports/
│   │   ├── users/
│   │   └── audit/
│   └── pos/                      # Full screen, no sidebar
│
├── components/
│   ├── ui/                       # shadcn/ui generated components
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── TopBar.tsx
│   │   └── PageHeader.tsx
│   ├── data-table/               # Reusable TanStack Table wrapper
│   │   └── DataTable.tsx
│   └── shared/
│       ├── StatusBadge.tsx       # Colored badges for statuses
│       ├── ConfirmDialog.tsx     # Reusable delete/action confirmation
│       └── DateRangePicker.tsx
│
├── features/                     # Feature-scoped components
│   ├── auth/
│   ├── products/
│   ├── inventory/
│   ├── sales/
│   ├── payments/
│   ├── billing/
│   ├── reports/
│   ├── pos/
│   └── users/
│
├── services/                     # API client functions
│   ├── api.ts                    # Axios instance with interceptors
│   ├── auth.ts
│   ├── products.ts
│   ├── inventory.ts
│   ├── sales.ts
│   ├── payments.ts
│   ├── billing.ts
│   ├── reports.ts
│   └── audit.ts
│
├── hooks/                        # Custom React hooks
│   ├── useAuth.ts
│   └── useWebSocket.ts
│
├── store/                        # Zustand stores
│   ├── authStore.ts              # User session, role
│   └── posStore.ts               # POS cart state
│
├── types/                        # TypeScript interfaces
│   ├── auth.ts
│   ├── products.ts
│   ├── sales.ts
│   └── payments.ts
│
└── utils/
    ├── formatters.ts             # Currency, date, number formatters
    └── constants.ts
```

---

## State Management

### Zustand Stores

**authStore** — global user session
```typescript
{
  user: User | null
  isAuthenticated: boolean
  role: 'admin' | 'supervisor' | 'cashier' | null
  setUser: (user: User) => void
  clearAuth: () => void
}
```

**posStore** — POS cart (cashier screen only)
```typescript
{
  items: CartItem[]
  discount: number
  paymentMethod: PaymentMethod | null
  addItem: (product) => void
  removeItem: (productId) => void
  updateQuantity: (productId, qty) => void
  clearCart: () => void
}
```

### TanStack Query
All server data (products, sales, reports) fetched via TanStack Query.
Provides caching, background refetch, loading/error states.
No manual loading state management in components.

---

## API Layer

### Axios Instance (`services/api.ts`)
- Base URL: `NEXT_PUBLIC_API_URL` env variable
- `withCredentials: true` — sends httpOnly cookies automatically
- Response interceptor: on 401, attempt token refresh; on second 401, redirect to `/login`
- No manual token management in components — cookies handled by browser

### Pattern per feature
```typescript
// services/products.ts
export const getProducts = () =>
  api.get<Product[]>('/api/v1/products/')

export const createProduct = (data: ProductCreateInput) =>
  api.post<Product>('/api/v1/products/', data)
```

---

## Auth Flow

1. User submits login form → POST `/api/v1/auth/login/`
2. Backend sets `access_token` + `refresh_token` as httpOnly cookies
3. Frontend stores user info (not token) in Zustand authStore
4. All subsequent requests send cookies automatically via `withCredentials`
5. On 401: axios interceptor calls `/api/v1/auth/refresh/` to rotate token
6. On second 401: clear authStore, redirect to `/login`
7. Route guards check `authStore.role` for page-level access control

---

## Role-Based Route Guards

Implemented as a layout-level check in `app/(dashboard)/layout.tsx`.
Redirects to `/login` if not authenticated.
Redirects to `/pos` if cashier tries to access `/dashboard` or `/reports`.

---

## WebSocket (Real-Time)

`hooks/useWebSocket.ts` — connects to `ws://backend/ws/notifications/`
Reconnects automatically on disconnect (exponential backoff, max 5 attempts).
On `payment.confirmed` event: show success toast on POS screen.
On `inventory.low_stock` event: show alert badge on sidebar inventory item.
On connection failure: falls back to polling REST endpoint every 30s.

---

## Currency & Locale

All monetary values formatted as Peruvian Sol: `S/ 1,234.56`
Locale: `es-PE`
Utility: `formatters.ts → formatCurrency(amount: Decimal) → string`

---

## shadcn/ui Components Used

- `Button`, `Input`, `Label`, `Select` — forms
- `Table` — data tables (wrapped in DataTable component)
- `Dialog` — modals (create/edit)
- `Sheet` — slide-over panels (details)
- `Badge` — status labels
- `Card` — dashboard stats
- `Tabs` — report sections
- `Sonner` (toast) — success/error notifications
- `Separator`, `Skeleton`, `Spinner` — UI utilities

Charts: **Recharts** (not shadcn) — lightweight, React-native, no extra setup.

---

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Commit Conventions (Frontend)

Same Conventional Commits as backend:
```
feat(pos): add product search with barcode scan support
feat(dashboard): add revenue chart with 7-day range
fix(auth): handle expired refresh token redirect
feat(billing): add boleta issuance modal
style(ui): update sidebar active state color
```
