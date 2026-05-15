# Database Design — SwiftSale

## Overview

SwiftSale uses **PostgreSQL** as its primary database.  
Design priorities: transactional integrity, concurrency safety, audit traceability.

---

## Tables

### `users`
Stores all employees with role-based access.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `email` | VARCHAR(255) | Unique, indexed |
| `full_name` | VARCHAR(255) | |
| `password_hash` | VARCHAR(255) | bcrypt |
| `role` | ENUM | `admin`, `supervisor`, `cashier` |
| `is_active` | BOOLEAN | Default true — soft deactivation |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

### `categories`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL | Primary key |
| `name` | VARCHAR(100) | Unique |
| `description` | TEXT | Nullable |

---

### `products`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `name` | VARCHAR(255) | |
| `sku` | VARCHAR(100) | Unique, indexed |
| `barcode` | VARCHAR(100) | Unique, nullable, indexed |
| `category_id` | INTEGER | FK → categories |
| `price` | DECIMAL(10,2) | Selling price |
| `cost_price` | DECIMAL(10,2) | Purchase cost |
| `is_active` | BOOLEAN | Soft delete |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Indexes:** `sku`, `barcode` (for fast POS barcode scanning)

---

### `inventory`
One row per product. Tracks current stock.

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL | Primary key |
| `product_id` | UUID | FK → products, unique |
| `quantity` | INTEGER | Current stock. Never negative |
| `min_stock_level` | INTEGER | Threshold for low-stock alert |
| `updated_at` | TIMESTAMPTZ | |

**Constraint:** `quantity >= 0` enforced at DB level.  
**Concurrency:** `SELECT FOR UPDATE` used during sales to prevent overselling.

---

### `inventory_movements`
Immutable audit trail for every stock change.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `product_id` | UUID | FK → products |
| `quantity_change` | INTEGER | Positive = in, Negative = out |
| `movement_type` | ENUM | `sale`, `purchase`, `adjustment`, `return` |
| `reference_id` | UUID | FK to related sale or adjustment |
| `created_by` | UUID | FK → users |
| `created_at` | TIMESTAMPTZ | |
| `notes` | TEXT | Nullable |

---

### `sales`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `cashier_id` | UUID | FK → users |
| `status` | ENUM | `pending`, `completed`, `cancelled` |
| `subtotal` | DECIMAL(10,2) | Before tax and discount |
| `discount` | DECIMAL(10,2) | Applied discount |
| `tax` | DECIMAL(10,2) | Calculated tax (IGV 18%) |
| `total` | DECIMAL(10,2) | Final amount |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Index:** `cashier_id`, `created_at` (for daily reports)

---

### `sale_items`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL | Primary key |
| `sale_id` | UUID | FK → sales |
| `product_id` | UUID | FK → products |
| `quantity` | INTEGER | |
| `unit_price` | DECIMAL(10,2) | Price at time of sale (snapshot) |
| `subtotal` | DECIMAL(10,2) | `quantity × unit_price` |

> `unit_price` is stored as a snapshot so historical sales remain accurate even if the product price changes later.

---

### `payments`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `sale_id` | UUID | FK → sales |
| `method` | ENUM | `cash`, `card`, `yape`, `plin` |
| `amount` | DECIMAL(10,2) | |
| `status` | ENUM | `pending`, `paid`, `failed`, `refunded` |
| `provider_ref` | VARCHAR(255) | External provider transaction ID |
| `idempotency_key` | VARCHAR(255) | Unique — prevents duplicate processing |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Unique constraint:** `idempotency_key`  
**Index:** `provider_ref` (for webhook lookup)

---

### `receipts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `sale_id` | UUID | FK → sales, unique |
| `pdf_url` | VARCHAR(500) | Path to generated PDF |
| `emailed_at` | TIMESTAMPTZ | Nullable — set when email is sent |
| `created_at` | TIMESTAMPTZ | |

---

### `billing_series`
Controls the correlativo counter per document type and series. Ensures no gaps or duplicates.

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL | Primary key |
| `series` | VARCHAR(4) | e.g. `B001`, `F001` |
| `document_type` | ENUM | `boleta`, `factura` |
| `last_correlativo` | INTEGER | Auto-incremented, never reset |
| `updated_at` | TIMESTAMPTZ | |

**Constraint:** `series` is unique.  
**Concurrency:** `SELECT FOR UPDATE` used when generating a new correlativo to prevent duplicates under concurrent requests.

---

### `billing_documents`
Stores every electronic billing document issued, including SUNAT response.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `series_id` | INTEGER | FK → billing_series |
| `correlativo` | INTEGER | Sequential number, immutable after creation |
| `full_number` | VARCHAR(20) | e.g. `B001-00000042`, indexed |
| `document_type` | ENUM | `boleta`, `factura` |
| `sale_id` | UUID | FK → sales |
| `customer_name` | VARCHAR(255) | |
| `customer_document_type` | VARCHAR(10) | `DNI`, `RUC`, `CE` |
| `customer_document_number` | VARCHAR(20) | |
| `customer_address` | TEXT | Nullable (required for factura) |
| `subtotal` | DECIMAL(10,2) | |
| `tax` | DECIMAL(10,2) | IGV 18% |
| `total` | DECIMAL(10,2) | |
| `xml_content` | TEXT | Full UBL 2.1 XML sent to OSE |
| `sunat_cdr` | TEXT | CDR XML returned by SUNAT, nullable |
| `sunat_response_code` | VARCHAR(10) | SUNAT response code, nullable |
| `status` | ENUM | `pending`, `sent`, `accepted`, `rejected`, `voided` |
| `issued_at` | TIMESTAMPTZ | |
| `voided_at` | TIMESTAMPTZ | Nullable |

**Index:** `full_number`, `sale_id`, `status`  
Rows are never deleted — voided documents remain for legal audit trail.

---

### `audit_logs`
Immutable record of sensitive system actions.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → users (nullable for system actions) |
| `action` | VARCHAR(100) | e.g. `price_change`, `login_failed` |
| `entity` | VARCHAR(100) | e.g. `product`, `sale` |
| `entity_id` | UUID | ID of the affected record |
| `old_value` | JSONB | State before change |
| `new_value` | JSONB | State after change |
| `ip_address` | VARCHAR(45) | |
| `created_at` | TIMESTAMPTZ | |

**Index:** `user_id`, `action`, `entity`, `created_at`  
Rows in this table are never updated or deleted.

---

## Relationships

```
users ──< sales ──< sale_items >── products
                 └──< payments
                 └── receipts
                 └── billing_documents >── billing_series

products ──── inventory
         ──< inventory_movements

users ──< inventory_movements
users ──< audit_logs
```

---

## Key Design Decisions

### Concurrency & Overselling Prevention
When a sale is being created, inventory rows are locked with `SELECT FOR UPDATE` inside a database transaction. This ensures two simultaneous sales cannot both see the same stock level and both proceed.

```sql
-- Pseudo-logic inside atomic transaction
SELECT quantity FROM inventory WHERE product_id = $1 FOR UPDATE;
-- Check quantity >= requested
UPDATE inventory SET quantity = quantity - $2 WHERE product_id = $1;
```

### Price Snapshots
`sale_items.unit_price` stores the price at the moment of sale. If a product price is changed later, historical sales remain accurate.

### Soft Deletes
`products` and `users` use `is_active = false` instead of hard deletes to preserve referential integrity and audit history.

### Billing Correlativo Integrity
When a new billing document is created, `billing_series` is locked with `SELECT FOR UPDATE` to atomically read and increment `last_correlativo`. This prevents two concurrent requests from generating the same number.

```sql
-- Pseudo-logic inside atomic transaction
SELECT last_correlativo FROM billing_series WHERE series = 'B001' FOR UPDATE;
UPDATE billing_series SET last_correlativo = last_correlativo + 1 WHERE series = 'B001';
```

Voided documents retain their correlativo — SUNAT requires the gap to be documented via a "comunicación de baja", not erased.

### JSONB for Audit Changes
`audit_logs.old_value` and `new_value` use JSONB so any entity type can be logged without schema changes.

---

## Migrations

Managed by Django migrations.  
Migration files are version-controlled and reviewed before merging.  
No destructive migrations (DROP COLUMN, DROP TABLE) are merged without a rollback plan.
