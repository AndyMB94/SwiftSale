# SwiftSale

Modern Retail Management Platform

SwiftSale is a scalable retail management platform inspired by modern convenience store systems such as OXXO, Tambo+, and Mass.

The project focuses on real-world backend engineering practices including:
- modular architecture
- payment processing
- asynchronous workflows
- observability
- inventory management
- audit logging
- testing
- Docker-based infrastructure

---

# Goals

The main goal of SwiftSale is to simulate a production-grade retail platform rather than a simple CRUD application.

The system should demonstrate:
- scalable backend architecture
- clean code practices
- modular monolith design
- real payment workflows
- async processing
- reliability and fault tolerance
- modern DevOps practices

---

# Architecture Style

## Modular Monolith

The application will initially be built as a modular monolith to:
- simplify development
- maintain strong boundaries
- avoid premature microservices complexity
- allow future service extraction

Potential future microservices:
- payments
- notifications
- analytics

---

# Tech Stack

## Backend
- Python
- Django
- Django Ninja
- PostgreSQL
- Redis
- Celery
- JWT Authentication (stored in httpOnly cookies — not localStorage)
- Django Channels (WebSockets)
- pytest
- Ruff
- mypy

## Frontend
- Next.js
- TypeScript
- TailwindCSS
- shadcn/ui
- Zustand
- TanStack Query
- pnpm (package manager)

## Infrastructure
- Docker
- Docker Compose
- Nginx
- GitHub Actions

---

# Core Modules

## Authentication
Responsibilities:
- login
- refresh tokens
- permissions
- role management

Roles:
- Admin
- Cashier
- Supervisor

Token Strategy:
- JWT stored in httpOnly, Secure, SameSite=Lax cookies
- Access token: short-lived (15 min)
- Refresh token: longer-lived (7 days), rotated on use
- Token revocation via Redis blacklist (handles immediate logout and role changes)

---

## Users
Responsibilities:
- employee management
- profile management
- account status

---

## Products
Responsibilities:
- product registration
- SKU management
- categories
- barcode support
- pricing

---

## Inventory
Responsibilities:
- stock tracking
- stock movements
- low stock alerts
- inventory adjustments

Important considerations:
- race condition prevention
- transactional updates
- stock consistency

---

## Sales
Responsibilities:
- POS operations
- cart management
- discounts
- tax calculations
- receipts

---

## Payments
Responsibilities:
- payment processing
- payment status
- webhook handling
- idempotency
- payment reconciliation

Supported payment methods:
- cash
- card
- Yape
- Plin

Future integrations:
- Mercado Pago
- Culqi
- Niubiz

Important:
Webhook duplication must not duplicate orders or inventory updates.

---

## Receipts
Responsibilities:
- invoice generation
- PDF receipts
- email delivery

Async tasks:
- PDF generation
- email sending

---

## Billing
Responsibilities:
- electronic invoice generation (boleta and factura)
- series and correlativo management
- XML UBL 2.1 document construction
- digital signature
- OSE submission (Nubefact / Facturalo)
- SUNAT response handling and storage

Document types:
- Boleta de Venta (B001-XXXXXXXX) — for end consumers
- Factura Electrónica (F001-XXXXXXXX) — for businesses with RUC

Important:
- Series and correlativos must never have gaps or duplicates
- SUNAT CDR (Constancia de Recepción) must be stored per document
- Billing is async — the sale completes before the document is sent to SUNAT

---

## Notifications
Responsibilities:
- email notifications
- stock alerts
- payment alerts

Uses Celery workers.

---

## Reports
Responsibilities:
- sales analytics
- best-selling products
- daily revenue
- inventory valuation

---

## Audit Logs
Responsibilities:
- track important actions
- store user activity
- security auditing

Examples:
- price changes
- stock edits
- cancelled sales
- failed login attempts

---

# Backend Structure

```text
backend/
├── apps/
│   ├── auth/
│   ├── users/
│   ├── products/
│   ├── inventory/
│   ├── sales/
│   ├── payments/
│   ├── billing/
│   ├── receipts/
│   ├── notifications/
│   ├── reports/
│   └── audit/
│
├── core/
│   ├── config/
│   ├── database/
│   ├── security/
│   ├── middleware/
│   ├── exceptions/
│   ├── logging/
│   ├── services/
│   └── utils/
│
├── tests/
├── scripts/
├── docker/
└── manage.py
```

---

# Frontend Structure

```text
frontend/
├── app/
├── components/
├── features/
├── services/
├── hooks/
├── store/
├── types/
└── utils/
```

---

# Infrastructure

## Dockerized Services

Containers:
- backend (Django HTTP + Django Ninja)
- websocket (Django Channels ASGI worker)
- frontend
- postgres
- redis
- celery
- nginx

---

# Async Processing

Celery will be used for:
- sending emails
- generating receipts
- processing notifications
- analytics updates
- submitting billing documents to SUNAT via OSE

Django Channels will be used for:
- real-time payment confirmation (cashier screen updates instantly on Yape/Plin confirmation)
- low-stock alerts pushed to supervisor dashboard

---

# Database

## PostgreSQL

Why:
- transactional integrity
- concurrency support
- production-grade reliability

---

# Redis

Used for:
- caching
- Celery broker
- Django Channels channel layer (WebSocket pub/sub)
- rate limiting
- temporary session storage
- JWT blacklist

---

# Security

Features:
- JWT stored in httpOnly cookies (XSS protection — token never accessible via JavaScript)
- Refresh token rotation
- Redis blacklist for immediate token revocation
- RBAC permissions
- Rate limiting on auth endpoints
- Secure password hashing (bcrypt)
- Request validation
- CORS protection
- CSRF protection (required when using cookies)

---

# Logging

Structured JSON logs.

Example:
```json
{
  "event": "payment_failed",
  "user_id": 25,
  "order_id": 120,
  "provider": "mercadopago"
}
```

---

# Observability

Future integrations:
- Prometheus
- Grafana
- Sentry

Health endpoints:
- database health
- redis health
- worker health

---

# Testing Strategy

## Unit Tests
- business logic
- pricing
- taxes
- discounts

## Integration Tests
- payment flows
- API endpoints
- inventory consistency

## E2E Tests
- complete checkout flow

---

# CI/CD

GitHub Actions pipeline:
- linting
- tests
- type checking
- Docker build

---

# API Design

REST API principles:
- versioned endpoints
- pagination
- filtering
- proper HTTP status codes

Example:
```text
/api/v1/products/
/api/v1/sales/
/api/v1/payments/
```

---

# Real-World Engineering Problems To Solve

## Payment Failures
Handle:
- timeout
- duplicate webhooks
- partial failures

---

## Inventory Concurrency
Prevent:
- overselling
- negative stock
- race conditions

---

## Reliability
Implement:
- retries
- idempotency
- transactions
- rollback strategies

---

## SUNAT Billing Compliance
Handle:
- correlativo gaps (must never skip a number)
- OSE submission failures with retry logic
- CDR storage for legal traceability
- document voiding (baja) when a sale is cancelled after billing

---

## WebSocket Reliability
Handle:
- reconnection on dropped connections
- missed events when client is offline (fallback to REST polling)

---

# Development Principles

- clean architecture
- SOLID principles
- separation of concerns
- modularity
- scalability
- maintainability

## Design Patterns

### Service Layer
Business logic lives in `services.py` within each app — not in views or models.
Views receive a request, validate input, and delegate to a service.
This keeps views thin and business rules testable in isolation.

### Repository Pattern (via Django ORM)
Django's ORM acts as the data access layer.
Direct queryset access is allowed within services but not in views.

### Idempotency Pattern
All payment operations require an `idempotency_key`.
Duplicate requests return the original response without reprocessing.

---

# Future Improvements

Potential future features:
- ecommerce support
- mobile app
- loyalty system
- AI analytics
- recommendation engine
- supplier integrations

---

# Branding

Project Name:
SwiftSale

Tagline:
"Modern Retail Management Platform"

---

# Repository Structure

```text
SwiftSale/
├── backend/
├── frontend/
├── infrastructure/
├── docs/
├── .github/
├── docker-compose.yml
└── README.md
```