# API Design — SwiftSale

## Overview

SwiftSale exposes a REST API built with Django Ninja.  
All endpoints are versioned under `/api/v1/`.

---

## Base URL

```
/api/v1/
```

---

## Authentication

All endpoints (except login) require a valid JWT.  
The JWT is stored in an **httpOnly cookie** — never exposed to JavaScript.  
Token revocation is handled via a **Redis blacklist**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | Authenticate and receive JWT cookie |
| POST | `/auth/refresh/` | Refresh access token using refresh cookie |
| POST | `/auth/logout/` | Invalidate token (blacklist in Redis) |
| GET | `/auth/me/` | Return current authenticated user |

### Login request
```json
{
  "email": "cashier@store.com",
  "password": "secret"
}
```

### Login response
```json
{
  "user": {
    "id": 1,
    "email": "cashier@store.com",
    "full_name": "John Doe",
    "role": "cashier"
  }
}
```
JWT is set via `Set-Cookie` header (httpOnly, Secure, SameSite=Lax).

---

## Roles & Permissions

| Role | Access |
|------|--------|
| `admin` | Full access |
| `supervisor` | Read + manage products, inventory, reports |
| `cashier` | Sales and payments only |

---

## Products

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/products/` | List products (paginated, filterable) | All |
| POST | `/products/` | Create product | Admin, Supervisor |
| GET | `/products/{id}/` | Get product detail | All |
| PUT | `/products/{id}/` | Update product | Admin, Supervisor |
| DELETE | `/products/{id}/` | Soft delete product | Admin |
| GET | `/products/categories/` | List categories | All |
| POST | `/products/categories/` | Create category | Admin, Supervisor |

### Create product request
```json
{
  "name": "Coca-Cola 500ml",
  "sku": "CCL-500",
  "barcode": "7501055300685",
  "category_id": 3,
  "price": 3.50,
  "cost_price": 1.80
}
```

### Query parameters (GET /products/)
```
?search=coca
?category_id=3
?page=1&page_size=20
?ordering=-created_at
```

---

## Inventory

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/inventory/` | List stock levels | All |
| GET | `/inventory/{product_id}/` | Stock detail for a product | All |
| POST | `/inventory/adjustments/` | Manual stock adjustment | Admin, Supervisor |
| GET | `/inventory/movements/` | Audit trail of stock changes | Admin, Supervisor |
| GET | `/inventory/alerts/` | Products below minimum stock | All |

### Stock adjustment request
```json
{
  "product_id": 5,
  "quantity_change": -10,
  "reason": "damaged_goods",
  "notes": "Found 10 broken units during count"
}
```

### Movement types
- `sale` — deducted by a completed sale
- `purchase` — added by stock entry
- `adjustment` — manual correction
- `return` — returned by customer

---

## Sales

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/sales/` | Create a new sale | Cashier, Supervisor |
| GET | `/sales/` | List sales (paginated) | Admin, Supervisor |
| GET | `/sales/{id}/` | Sale detail | Admin, Supervisor |
| POST | `/sales/{id}/cancel/` | Cancel a sale | Admin, Supervisor |

### Create sale request
```json
{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 5, "quantity": 1 }
  ],
  "discount": 0.50,
  "payment_method": "cash"
}
```

### Sale response
```json
{
  "id": 120,
  "status": "completed",
  "subtotal": 10.50,
  "tax": 1.89,
  "discount": 0.50,
  "total": 11.89,
  "items": [...],
  "payment": { "method": "cash", "amount": 11.89, "status": "paid" },
  "created_at": "2025-08-01T14:32:00Z"
}
```

---

## Payments

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/payments/` | Process payment for a sale | Cashier, Supervisor |
| GET | `/payments/{id}/` | Payment detail | Admin, Supervisor |
| POST | `/payments/webhooks/{provider}/` | Receive webhook from provider | Public (verified) |

### Supported payment methods
- `cash`
- `card`
- `yape`
- `plin`

### Process payment request
```json
{
  "sale_id": 120,
  "method": "yape",
  "amount": 11.89,
  "idempotency_key": "sale-120-attempt-1"
}
```

> **Important:** Every payment request must include an `idempotency_key`.  
> Duplicate requests with the same key return the original response without reprocessing.

### Webhook endpoint
Providers call `POST /api/v1/payments/webhooks/yape/` with their payload.  
Webhook signatures are validated before processing.  
Duplicate webhooks are detected by `provider_ref` and silently ignored.

---

## Billing

Electronic invoice generation and SUNAT submission.

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/billing/boleta/` | Issue a boleta for a completed sale | Cashier, Supervisor |
| POST | `/billing/factura/` | Issue a factura for a completed sale | Cashier, Supervisor |
| GET | `/billing/{id}/` | Billing document detail and SUNAT status | Admin, Supervisor |
| GET | `/billing/` | List billing documents | Admin, Supervisor |
| POST | `/billing/{id}/void/` | Void (baja) a billing document | Admin |

### Issue boleta request
```json
{
  "sale_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "boleta",
  "customer": {
    "name": "Cliente General",
    "document_type": "DNI",
    "document_number": "12345678"
  }
}
```

### Issue factura request
```json
{
  "sale_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "factura",
  "customer": {
    "name": "Empresa SAC",
    "document_type": "RUC",
    "document_number": "20512345678",
    "address": "Av. Javier Prado 123, Lima"
  }
}
```

### Billing document response
```json
{
  "id": "abc123",
  "series": "B001",
  "correlativo": "00000042",
  "full_number": "B001-00000042",
  "document_type": "boleta",
  "sale_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 11.89,
  "status": "accepted",
  "sunat_cdr_url": "/media/cdr/B001-00000042.xml",
  "issued_at": "2025-08-01T14:35:00Z"
}
```

### Document statuses
- `pending` — created, waiting for OSE submission
- `sent` — submitted to OSE, awaiting SUNAT response
- `accepted` — SUNAT accepted the document
- `rejected` — SUNAT rejected (includes error code and message)
- `voided` — document has been cancelled via baja

> Billing is triggered asynchronously after sale completion. The cashier does not wait for SUNAT's response to complete the sale.

---

## WebSockets

SwiftSale uses Django Channels for real-time push notifications.  
Connections are authenticated via the same JWT cookie used for REST endpoints.

### Connection

```
ws://localhost:8000/ws/notifications/
```

### Events pushed by the server

**Payment confirmed**
```json
{
  "type": "payment.confirmed",
  "payload": {
    "sale_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "yape",
    "amount": 11.89,
    "confirmed_at": "2025-08-01T14:34:58Z"
  }
}
```

**Payment failed**
```json
{
  "type": "payment.failed",
  "payload": {
    "sale_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "yape",
    "reason": "timeout"
  }
}
```

**Low stock alert**
```json
{
  "type": "inventory.low_stock",
  "payload": {
    "product_id": "abc",
    "product_name": "Coca-Cola 500ml",
    "current_stock": 3,
    "min_stock_level": 10
  }
}
```

> If the client disconnects and reconnects, missed events are not replayed.  
> The frontend should fall back to REST polling for state recovery on reconnect.

---

## Reports

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/reports/sales/daily/` | Daily revenue summary | Admin, Supervisor |
| GET | `/reports/sales/top-products/` | Best-selling products | Admin, Supervisor |
| GET | `/reports/inventory/valuation/` | Total inventory value | Admin, Supervisor |

### Query parameters
```
?date=2025-08-01
?from=2025-07-01&to=2025-07-31
```

---

## Audit Logs

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/audit/` | List audit log entries | Admin |

### Query parameters
```
?user_id=5
?action=price_change
?entity=product
?from=2025-08-01
```

---

## Error Format

All errors follow a consistent structure:

```json
{
  "error": {
    "code": "insufficient_stock",
    "message": "Product 'Coca-Cola 500ml' has only 3 units available.",
    "details": {
      "product_id": 1,
      "requested": 5,
      "available": 3
    }
  }
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (delete) |
| 400 | Bad Request — validation error |
| 401 | Unauthorized — missing or invalid JWT |
| 403 | Forbidden — insufficient role |
| 404 | Not Found |
| 409 | Conflict — duplicate / idempotency violation |
| 422 | Unprocessable Entity — business rule violation |
| 500 | Internal Server Error |

---

## Pagination

All list endpoints return paginated responses:

```json
{
  "count": 150,
  "page": 1,
  "page_size": 20,
  "results": [...]
}
```

---

## Versioning

The current API version is `v1`.  
Breaking changes will be introduced under `/api/v2/` without removing `v1`.
