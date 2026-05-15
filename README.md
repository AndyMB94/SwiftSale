# SwiftSale

**Modern Retail Management Platform**

SwiftSale is a production-grade retail management system inspired by modern convenience store chains. Built as a portfolio project to demonstrate real-world backend engineering: modular architecture, payment processing, async workflows, inventory concurrency, and observability.

---

## Tech Stack

**Backend**
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.x-37814A?style=flat&logo=celery&logoColor=white)
![Django Channels](https://img.shields.io/badge/Django_Channels-4.x-092E20?style=flat&logo=django&logoColor=white)

**Frontend**
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?style=flat&logo=tailwindcss&logoColor=white)

**Infrastructure**
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=flat&logo=github-actions&logoColor=white)

---

## Features

- **Authentication** — JWT via httpOnly cookies, refresh token rotation, Redis-based revocation, role-based access (Admin / Supervisor / Cashier)
- **Products** — SKU and barcode management, categories, pricing
- **Inventory** — Real-time stock tracking with race condition protection (SELECT FOR UPDATE), movement audit trail, low-stock alerts
- **Sales / POS** — Cart management, discounts, tax calculation (IGV 18%), price snapshots
- **Payments** — Cash, card, Yape, Plin — with idempotency keys and duplicate webhook detection
- **Billing / SUNAT** — Electronic invoicing (boletas and facturas) via OSE integration, XML UBL 2.1, automatic series and correlativo management
- **WebSockets** — Real-time payment confirmation and low-stock alerts via Django Channels
- **Async Processing** — PDF receipt generation and email delivery via Celery workers
- **Reports** — Daily revenue, best-selling products, inventory valuation
- **Audit Logs** — Immutable record of sensitive actions (price changes, cancellations, failed logins)

---

## Architecture

Modular monolith with a service layer pattern. Each domain module (`auth`, `products`, `inventory`, `sales`, `payments`) is self-contained with its own models, services, and API endpoints. Shared infrastructure lives in `core/`.

Designed to allow future extraction of `payments`, `notifications`, and `analytics` into independent services.

```
SwiftSale/
├── backend/
│   ├── apps/          # Domain modules
│   ├── core/          # Shared infrastructure
│   └── tests/
├── frontend/
├── infrastructure/
├── docs/
└── docker-compose.yml
```

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- pnpm (frontend)

### Run with Docker

```bash
git clone https://github.com/AndyMB94/SwiftSale.git
cd SwiftSale
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000/api/v1/`  
The frontend will be available at `http://localhost:3000`

### Run backend locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Run tests

```bash
cd backend
pytest
```

---

## API

REST API versioned under `/api/v1/`.

| Module | Endpoints |
|--------|-----------|
| Auth | `/api/v1/auth/` |
| Products | `/api/v1/products/` |
| Inventory | `/api/v1/inventory/` |
| Sales | `/api/v1/sales/` |
| Payments | `/api/v1/payments/` |
| Billing | `/api/v1/billing/` |
| Reports | `/api/v1/reports/` |
| Audit | `/api/v1/audit/` |

See [docs/api-design.md](docs/api-design.md) for full endpoint documentation.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, tech stack, design patterns |
| [API Design](docs/api-design.md) | All endpoints with request/response examples |
| [Database Design](docs/database-design.md) | Schema, relationships, key design decisions |
| [Roadmap](docs/roadmap.md) | Development phases and future improvements |

---

## Real-World Engineering Problems

**Inventory concurrency** — Stock updates use `SELECT FOR UPDATE` inside atomic transactions to prevent overselling under concurrent requests.

**Payment idempotency** — Every payment requires an `idempotency_key`. Duplicate requests return the original response without reprocessing or double-charging.

**Webhook safety** — Incoming webhooks are validated by signature and deduplicated by `provider_ref`. A duplicate webhook never triggers a second inventory deduction or order creation.

**Token revocation** — JWTs are stateless by design, but a Redis blacklist allows immediate revocation (logout, role change, account deactivation) without waiting for token expiry.

**SUNAT electronic billing** — Boletas and facturas are generated as XML UBL 2.1 documents, signed digitally, and sent to SUNAT via an OSE (Operador de Servicios Electrónicos). Series and correlativos are managed automatically with no gaps or duplicates.

**Real-time notifications via WebSockets** — Django Channels pushes payment confirmations and low-stock alerts to connected clients instantly, without polling. The Redis channel layer scales the WebSocket layer independently of the HTTP workers.

---

## CI/CD

GitHub Actions pipeline runs on every push:
- Ruff (linting)
- mypy (type checking)
- pytest (unit + integration tests)
- Docker build validation

---

## License

MIT
