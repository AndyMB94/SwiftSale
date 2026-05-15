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
- [ ] Docker Compose with PostgreSQL, Redis, Nginx
- [x] User management endpoints (create, update, deactivate)
- [x] Health check endpoints (DB, Redis)
- [ ] GitHub Actions CI (lint, type check, tests)

**Deliverable:** A secured, deployable API skeleton with working auth.

---

## Phase 2 — Product Catalog & Inventory
**Goal:** Full product management and real-time stock control.

- [ ] Category CRUD
- [ ] Product CRUD with SKU and barcode support
- [ ] Soft delete for products
- [ ] Inventory model with stock level per product
- [ ] Stock movement audit trail
- [ ] Low stock alerts
- [ ] Concurrency-safe stock updates (SELECT FOR UPDATE)
- [ ] Manual stock adjustments with reason tracking
- [ ] Unit tests for inventory business logic
- [ ] Integration tests for stock consistency

**Deliverable:** Products and inventory fully operational with race condition protection.

---

## Phase 3 — Sales & POS
**Goal:** Complete point-of-sale workflow.

- [ ] Cart / sale creation with multiple items
- [ ] Price snapshot on sale items
- [ ] Discount application
- [ ] Tax calculation (IGV 18%)
- [ ] Sale status transitions (pending → completed → cancelled)
- [ ] Inventory deduction on sale completion (atomic)
- [ ] Inventory rollback on sale cancellation
- [ ] Cashier-facing POS endpoints
- [ ] Unit tests for pricing and tax logic
- [ ] Integration tests for full checkout flow

**Deliverable:** End-to-end sale creation from cart to completion.

---

## Phase 4 — Payments
**Goal:** Reliable payment processing with idempotency and webhook safety.

- [ ] Payment model with idempotency key
- [ ] Cash payment flow
- [ ] Card payment flow
- [ ] Yape / Plin payment flow
- [ ] Payment status transitions
- [ ] Webhook receiver with signature validation
- [ ] Duplicate webhook detection via `provider_ref`
- [ ] Payment reconciliation
- [ ] Integration tests for payment flows
- [ ] Tests for duplicate webhook handling

**Deliverable:** Payments processed safely with no duplicate orders or inventory side effects.

---

## Phase 5 — SUNAT Electronic Billing
**Goal:** Legal electronic invoicing compliant with SUNAT via OSE.

- [ ] `billing_series` model with `SELECT FOR UPDATE` correlativo generation
- [ ] `billing_documents` model
- [ ] Boleta de Venta generation (XML UBL 2.1)
- [ ] Factura Electrónica generation (XML UBL 2.1)
- [ ] Digital signature integration
- [ ] OSE submission via Celery task (Nubefact or Facturalo)
- [ ] SUNAT CDR storage on acceptance
- [ ] Rejection handling with error code logging
- [ ] Document voiding (comunicación de baja) flow
- [ ] Billing endpoints (`/api/v1/billing/`)
- [ ] Integration tests for correlativo uniqueness under concurrency
- [ ] Integration tests for OSE submission flow

**Deliverable:** Every completed sale can issue a legally valid boleta or factura submitted to SUNAT.

---

## Phase 6 — Async Processing, WebSockets & Notifications
**Goal:** Offload heavy tasks to background workers and push real-time events to clients.

- [ ] Celery worker setup with Redis broker
- [ ] PDF receipt generation (async task)
- [ ] Email delivery for receipts (async task)
- [ ] Low stock email notifications
- [ ] Payment failure alerts
- [ ] Task retry logic with exponential backoff
- [ ] Dead letter queue for failed tasks
- [ ] Worker health check endpoint
- [ ] Django Channels setup (ASGI, Redis channel layer)
- [ ] WebSocket consumer for authenticated connections (`/ws/notifications/`)
- [ ] Push `payment.confirmed` event on successful Yape/Plin payment
- [ ] Push `payment.failed` event on payment failure
- [ ] Push `inventory.low_stock` event when stock drops below threshold
- [ ] Frontend reconnection handling with REST fallback

**Deliverable:** Heavy tasks run in background workers; payment and stock events are pushed to clients in real time.

---

## Phase 7 — Reports & Audit
**Goal:** Business intelligence and full traceability.

- [ ] Daily revenue report
- [ ] Best-selling products report
- [ ] Inventory valuation report
- [ ] Date range filtering for all reports
- [ ] Audit log for sensitive actions (price changes, stock edits, cancellations, failed logins)
- [ ] Admin-only audit log viewer endpoint

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
