# Roadmap — SwiftSale

## Overview

This roadmap defines the development phases for SwiftSale.  
Each phase delivers a vertical slice of working functionality — no half-built modules.

---

## Phase 1 — Foundation
**Goal:** Runnable project with authentication and infrastructure.

- [x] Project structure setup (backend + frontend + docs)
- [x] Django project with modular app structure (base / dev / prod settings)
- [x] ASGI server configured with Daphne + Django Channels
- [x] Custom User model with role-based access (Admin, Supervisor, Cashier)
- [x] JWT + token blacklist configured (djangorestframework-simplejwt)
- [x] Structured JSON logging
- [x] pytest + ruff + mypy configured (pyproject.toml)
- [x] Initial migrations applied (User model + token blacklist)
- [x] JWT authentication endpoints (login, refresh, logout, me)
- [x] httpOnly cookie implementation in auth views
- [x] Refresh token rotation + Redis blacklist in endpoints
- [x] Docker Compose with PostgreSQL, Redis, Nginx
- [x] User management endpoints (create, update, deactivate)
- [x] Health check endpoints (DB, Redis)
- [ ] GitHub Actions CI (lint, type check, tests)

**Deliverable:** A secured, deployable API skeleton with working auth.

---

## Phase 2 — Product Catalog & Inventory
**Goal:** Full product management and real-time stock control.

- [x] Category CRUD
- [x] Product CRUD with SKU and barcode support
- [x] Soft delete for products
- [x] Inventory model with stock level per product
- [x] Stock movement audit trail
- [x] Low stock alerts
- [x] Concurrency-safe stock updates (SELECT FOR UPDATE)
- [x] Manual stock adjustments with reason tracking
- [x] Unit tests for inventory business logic
- [x] Integration tests for stock consistency

**Deliverable:** Products and inventory fully operational with race condition protection.

---

## Phase 3 — Sales & POS
**Goal:** Complete point-of-sale workflow.

- [x] Cart / sale creation with multiple items
- [x] Price snapshot on sale items
- [x] Discount application
- [x] Tax calculation (IGV 18%)
- [x] Sale status transitions (pending → completed → cancelled)
- [x] Inventory deduction on sale completion (atomic)
- [x] Inventory rollback on sale cancellation
- [x] Cashier-facing POS endpoints
- [x] Unit tests for pricing and tax logic
- [x] Integration tests for full checkout flow

**Deliverable:** End-to-end sale creation from cart to completion.

---

## Phase 4 — Payments
**Goal:** Reliable payment processing with idempotency and webhook safety.

- [x] Payment model with idempotency key
- [x] Cash payment flow
- [x] Card payment flow
- [x] Yape / Plin payment flow
- [x] Payment status transitions
- [x] Webhook receiver with signature validation
- [x] Duplicate webhook detection via `provider_ref`
- [x] Payment reconciliation
- [x] Integration tests for payment flows
- [x] Tests for duplicate webhook handling

**Deliverable:** Payments processed safely with no duplicate orders or inventory side effects.

---

## Phase 5 — SUNAT Electronic Billing ✅
**Goal:** Legal electronic invoicing compliant with SUNAT via OSE.

- [x] `billing_series` model with `SELECT FOR UPDATE` correlativo generation
- [x] `billing_documents` model
- [x] Boleta de Venta generation (XML UBL 2.1)
- [x] Factura Electrónica generation (XML UBL 2.1)
- [x] OSE client interface with MockOseClient (dev/test) and NubefactOseClient stub (prod)
- [x] SUNAT CDR storage on acceptance
- [x] Rejection handling with error code logging
- [x] Document voiding (comunicación de baja) flow
- [x] Billing endpoints (`/api/v1/billing/`)
- [x] Integration tests for correlativo uniqueness under concurrency
- [x] Integration tests for OSE submission and rejection flows
- [ ] Digital signature (XMLDSig) — deferred to production hardening

**Deliverable:** Every completed sale can issue a legally valid boleta or factura submitted to SUNAT.

---

## Phase 6 — Async Processing, WebSockets & Notifications ✅
**Goal:** Offload heavy tasks to background workers and push real-time events to clients.

- [x] Celery worker setup with Redis broker and named queues (receipts, notifications, maintenance)
- [x] PDF receipt generation with ReportLab (async task)
- [x] Email delivery for receipts (async task, console backend in dev / Anymail in prod)
- [x] Low stock email notifications
- [x] Payment failure alerts
- [x] Task retry logic with exponential backoff (`max_retries`, `default_retry_delay`)
- [x] `acks_late` + `reject_on_worker_lost` for reliable task delivery
- [x] Celery worker health check endpoint
- [x] WebSocket consumer for authenticated connections (`/ws/notifications/`) with JWT cookie auth
- [x] Push `payment.confirmed` event on successful Yape/Plin payment
- [x] Push `payment.failed` event on payment failure
- [x] Push `inventory.low_stock` event when stock drops below threshold
- [x] `transaction.on_commit` dispatch — tasks never fire on rolled-back transactions
- [ ] Frontend reconnection handling with REST fallback (deferred to frontend track)

**Deliverable:** Heavy tasks run in background workers; payment and stock events are pushed to clients in real time.

---

## Phase 7 — Reports & Audit ✅
**Goal:** Business intelligence and full traceability.

- [x] Daily revenue report with avg ticket per day
- [x] Best-selling products report sorted by quantity sold
- [x] Inventory valuation report (quantity × unit price per product)
- [x] Date range filtering for all reports (defaults to current month)
- [x] Audit log for sensitive actions: price changes, stock edits, sale cancellations, failed logins, user deactivations, document voiding
- [x] Admin-only audit log viewer endpoint with filters (action, actor, target, date range)

**Deliverable:** Managers can track revenue trends and audit any sensitive system action.

---

## Phase 8 — Observability & DevOps
**Goal:** Production-grade monitoring and deployment pipeline.

- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboard setup
- [ ] Sentry error tracking integration
- [ ] Rate limiting on auth endpoints
- [ ] CORS and security headers configuration
- [ ] Production Docker Compose configuration
- [ ] Environment-based settings (dev / staging / prod)
- [ ] Database backup strategy

**Deliverable:** System is observable, protected, and ready for a production-like environment.

---

---

## Frontend (parallel track)

- [ ] Next.js project setup with TypeScript and pnpm
- [ ] TailwindCSS + shadcn/ui component library
- [ ] Authentication flow (login, refresh, logout)
- [ ] Product catalog and inventory views
- [ ] POS interface for cashiers
- [ ] Sales history for supervisors
- [ ] Payments UI with method selection
- [ ] Real-time payment confirmation screen (WebSocket)
- [ ] Billing document issuance UI (boleta / factura selection)
- [ ] Reports dashboard
- [ ] Role-based route guards

---

## Future Improvements

These are intentionally out of scope for the initial build.

| Feature | Notes |
|---------|-------|
| Mercado Pago integration | Real payment gateway |
| Culqi / Niubiz | Local Peruvian processors |
| SUNAT ticket mode | For boletas > S/ 700 |
| E-commerce module | Online sales channel |
| Loyalty / points system | Customer retention |
| Mobile app | React Native or Flutter |
| AI analytics | Demand forecasting, recommendations |
| Supplier integrations | Automated purchase orders |
| Prometheus + Grafana (full) | Extended observability |

---

## Commit Conventions

All commits follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(auth): implement JWT authentication with httpOnly cookies
feat(products): add product CRUD with barcode support
feat(inventory): add SELECT FOR UPDATE to prevent overselling
fix(payments): prevent duplicate webhook processing
feat(billing): add boleta generation with UBL 2.1 XML
feat(billing): integrate OSE submission via Celery task
feat(websocket): push payment confirmation to cashier screen
test(sales): add integration tests for checkout flow
test(billing): add concurrency tests for correlativo generation
chore(docker): add Redis and Celery services to compose
```
