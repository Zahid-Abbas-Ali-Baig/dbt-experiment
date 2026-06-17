# Design Brief — ShopSphere

**Status:** approved

> **Approval:** Review all sections below. Correct any errors, then change status to `approved` before running Phase 2.
>
> Phases 2–7 read `DESIGN_BRIEF_DOC` from [`config.md`](config.md) — do not rely on chat history.

---

## 1. Domain Summary

**Business context (from requirements):** ShopSphere is an online retailer selling physical goods. Core operational flow is browse → cart → order → payment → fulfillment. Reporting must unify sales, customer, and product performance and replace ad-hoc SQL with governed dbt models.

**Pain points driving this work:**
- Inconsistent revenue definitions across teams
- No single source of truth for customer lifetime value (CLV)

**Reporting preferences:**
- Star schema for BI tools
- Semantic layer metrics for self-serve analytics
- Daily order grain with monthly executive rollups

**Constraints:**
- Exclude **cancelled** and **fully refunded** orders from revenue KPIs
- Currency assumed USD
- Source: PostgreSQL database `shopsphere`, schema `ecommerce` (operational OLTP; nightly batch load)

**Discovery snapshot (live schema, 2026-06-17):**

| Table | Rows | Classification |
|-------|------|----------------|
| categories | 20 | Dimension |
| customers | 100,000 | Dimension |
| marketing_channels | 6 | Dimension |
| products | 5,000 | Dimension |
| orders | 1,000,000 | Fact (order header) |
| order_items | 2,000,001 | Fact (line item) |
| payments | 1,000,000 | Fact (payment event) |
| refunds | 9,413 | Fact (refund event) |

**Order date range:** 2024-06-11 → 2026-06-11

**Critical data-quality finding:** `orders.gross_amount` does **not** reconcile to `SUM(order_items.line_amount)` for 999,983 of 1,000,000 orders. However, `payments.amount` matches `orders.gross_amount` 1:1 (one payment per order). **Governed revenue at order level must use `gross_amount` (net of refunds).** Category/product revenue must use `order_items.line_amount` at line grain with order-level eligibility filters applied upstream.

---

## 2. Business Questions → KPI Map

| # | Business Question | KPI / Metric | Grain | Inclusion Rules |
|---|-------------------|--------------|-------|-----------------|
| BQ1 | What is total revenue and order count by month? | `monthly_net_revenue`, `monthly_order_count` | Month | Exclude `Cancelled` and `Refunded` orders; subtract partial refunds on `Completed` orders |
| BQ2 | Who are the top customers by lifetime spend? | `customer_lifetime_net_spend` | Customer | Sum eligible order net revenue per customer; rank descending |
| BQ3 | Which product categories drive the most revenue? | `category_net_line_revenue` | Category × month (optional time) | Line revenue from eligible orders; allocate partial refunds proportionally by line share |

### KPI Traceability Matrix

| Business Question | Source Table(s) | Staging Model(s) | Intermediate Model(s) | Mart Model(s) | Semantic Metric |
|-------------------|-----------------|------------------|----------------------|---------------|-----------------|
| BQ1 — monthly revenue & order count | `orders`, `refunds` | `stg_ecommerce__orders`, `stg_ecommerce__refunds` | `int_orders__with_refunds` | `fct_orders` | `monthly_net_revenue`, `monthly_order_count` |
| BQ2 — top customers by lifetime spend | `orders`, `refunds`, `customers` | `stg_ecommerce__orders`, `stg_ecommerce__refunds`, `stg_ecommerce__customers` | `int_orders__with_refunds`, `int_customers__lifetime_metrics` | `fct_orders`, `dim_customers` | `customer_lifetime_net_spend` |
| BQ3 — category revenue drivers | `order_items`, `orders`, `products`, `categories`, `refunds` | `stg_ecommerce__order_items`, `stg_ecommerce__orders`, `stg_ecommerce__products`, `stg_ecommerce__categories`, `stg_ecommerce__refunds` | `int_orders__with_refunds`, `int_order_items__enriched` | `fct_order_items`, `dim_categories`, `dim_products` | `category_net_line_revenue` |

---

## 3. Source Inventory

**Source:** `ecommerce` (database: `shopsphere`, schema: `ecommerce`)

Codegen output captured 2026-06-17 via `dbt run-operation generate_source`. All 8 tables are in scope.

### 3.1 categories — Dimension

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per product category |
| **Primary key** | `category_id` (bigint, NOT NULL, unique — 20 rows, 20 distinct) |
| **Row count** | 20 |

**Sample values:** `Category-1` … `Category-20`

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| category_id | bigint | 0% | PK |
| category_name | varchar | 0% | Display name |

**Relationships:** Referenced by `products.category_id` (0 orphans)

---

### 3.2 customers — Dimension

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per registered customer |
| **Primary key** | `customer_id` (bigint, NOT NULL, unique — 100,000 rows) |
| **Row count** | 100,000 |

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| customer_id | bigint | 0% | PK |
| first_name | varchar | 0% | PII |
| last_name | varchar | 0% | PII |
| email | varchar | 0% | PII, unique in sample |
| country | varchar | 0% | Geo attribute |
| city | varchar | 0% | Geo attribute |
| signup_date | date | 0% | Customer acquisition date |
| customer_segment | varchar | 0% | Values: `Retail` (69,844), `VIP` (30,156) |

**Relationships:** Referenced by `orders.customer_id` (0 orphans). 1 customer has no orders; 99,999 customers have ≥1 order.

---

### 3.3 marketing_channels — Dimension

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per acquisition/marketing channel |
| **Primary key** | `channel_id` (bigint, NOT NULL, unique — 6 rows) |
| **Row count** | 6 |

**Values:** Google Ads, Facebook, Instagram, Email, Organic, Affiliate

**Relationships:** Referenced by `orders.channel_id` (0 orphans)

---

### 3.4 products — Dimension

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per SKU/product |
| **Primary key** | `product_id` (bigint, NOT NULL, unique — 5,000 rows) |
| **Row count** | 5,000 |

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| product_id | bigint | 0% | PK |
| sku | varchar | 0% | e.g. `SKU-1` |
| product_name | varchar | 0% | Descriptive name |
| category_id | bigint | 0% | FK → categories |
| unit_price | numeric | 0% | List/catalog price |
| active_flag | boolean | 0% | All 5,000 products active |

**Relationships:** Referenced by `order_items.product_id` (0 orphans); FK to `categories` (0 orphans)

---

### 3.5 orders — Fact (order header)

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per customer order |
| **Primary key** | `order_id` (bigint, NOT NULL, unique — 1,000,000 rows) |
| **Row count** | 1,000,000 |

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| order_id | bigint | 0% | PK |
| customer_id | bigint | 0% | FK → customers |
| order_date | timestamp | 0% | Order placement timestamp |
| order_status | varchar | 0% | `Completed` (900,027), `Cancelled` (95,081), `Refunded` (4,892) |
| channel_id | bigint | 0% | FK → marketing_channels |
| gross_amount | numeric | 0% | Order-level revenue; matches payment amount |
| discount_amount | numeric | — | Order-level discount |
| tax_amount | numeric | — | Tax component |
| shipping_amount | numeric | — | Shipping component |

**Relationships:**
- → `customers` (0 orphans)
- → `marketing_channels` (0 orphans)
- ← `order_items` (0 orphan FKs; every order has 1–3 line items, avg 2.0)
- ← `payments` (0 orphan FKs; 1:1, 0 orders without payment)
- ← `refunds` (0 orphan FKs)

**Data quality:**
- `gross_amount` ≠ `SUM(line_amount)` for 999,983 orders — do not use line sums for order-level revenue

---

### 3.6 order_items — Fact (line item)

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per product line on an order |
| **Primary key** | `order_item_id` (bigint, NOT NULL, unique — 2,000,001 rows) |
| **Row count** | 2,000,001 |

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| order_item_id | bigint | 0% | PK |
| order_id | bigint | 0% | FK → orders |
| product_id | bigint | 0% | FK → products |
| quantity | integer | 0% | Units ordered |
| unit_price | numeric | 0% | Price at time of sale |
| line_amount | numeric | 0% | `quantity × unit_price` in sample rows |

**Relationships:** FK to `orders` and `products` — 0 orphans each

---

### 3.7 payments — Fact (payment event)

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per order payment |
| **Primary key** | `payment_id` (bigint, NOT NULL, unique — 1,000,000 rows) |
| **Row count** | 1,000,000 |

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| payment_id | bigint | 0% | PK |
| order_id | bigint | 0% | FK → orders (1:1) |
| payment_date | timestamp | 0% | Capture timestamp |
| payment_method | varchar | 0% | Credit Card, Debit Card, PayPal, Apple Pay, Google Pay (evenly distributed) |
| payment_status | varchar | 0% | `Captured` (900,027), `Voided` (47,684), `Failed` (47,397), `Refunded` (4,892) |
| amount | numeric | 0% | Equals `orders.gross_amount` |

**Relationships:** FK to `orders` — 0 orphans; 0 orders with multiple payments

**Note:** Not required for v1 KPI marts but staged for future payment-method analysis.

---

### 3.8 refunds — Fact (refund event)

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per refund transaction |
| **Primary key** | `refund_id` (bigint, NOT NULL, unique — 9,413 rows) |
| **Row count** | 9,413 |

**Column profile:**

| Column | Type | Null % | Notes |
|--------|------|--------|-------|
| refund_id | bigint | 0% | PK |
| order_id | bigint | 0% | FK → orders |
| refund_date | timestamp | 0% | Refund processed timestamp |
| refund_amount | numeric | 0% | USD refund value |
| refund_reason | varchar | 0% | See distribution below |

**Refund reason distribution:**
- Partial refund - item return: 4,521 (on `Completed` orders)
- Customer return / Changed mind / Late delivery / Defective product / Duplicate charge: ~940–1,009 each (on `Refunded` orders)

**Relationships:** FK to `orders` — 0 orphans; 0 orders with multiple refund rows

**Partial refund impact:** 4,521 completed orders have partial refunds totaling $234,953.10

---

## 4. Relationship Graph

```
marketing_channels (1) ──< orders (M) >── (1) customers
                              │
                              ├──< order_items (M) >── (1) products (M) >── (1) categories
                              │
                              ├──< payments (1:1)
                              │
                              └──< refunds (0..1)
```

### Join Keys & Cardinality

| Parent | Child | Join Key | Cardinality | Orphan FK Count |
|--------|-------|----------|-------------|-----------------|
| customers | orders | customer_id | 1:M | 0 |
| marketing_channels | orders | channel_id | 1:M | 0 |
| orders | order_items | order_id | 1:M (1–3 items) | 0 |
| products | order_items | product_id | 1:M | 0 |
| categories | products | category_id | 1:M | 0 |
| orders | payments | order_id | 1:1 | 0 |
| orders | refunds | order_id | 1:0..1 | 0 |

### Eligibility Flags (derived in intermediate layer)

| Flag | Logic |
|------|-------|
| `is_revenue_eligible` | `order_status NOT IN ('Cancelled', 'Refunded')` |
| `is_fully_refunded` | `order_status = 'Refunded'` |
| `is_cancelled` | `order_status = 'Cancelled'` |
| `has_partial_refund` | `order_status = 'Completed' AND total_refund_amount > 0` |
| `net_order_revenue` | `gross_amount - total_refund_amount` when revenue-eligible, else 0 |

---

## 5. Column Standardization Plan

Renames and casts use ShopSphere domain language from requirements (revenue, lifetime spend, eligibility) — not generic abbreviations.

### Global conventions
- Prefix surrogate keys in marts: `{entity}_key` (dbt_utils `generate_surrogate_key` where needed)
- Cast all monetary columns to `numeric(18,2)`
- Cast timestamps to `timestamp without time zone` (source is already tz-naive)
- Boolean flags prefixed with `is_`
- USD currency implicit; no currency column added (per requirements)

### Per-table staging transforms

| Source Table | Source Column | Staging Column | Transform |
|--------------|---------------|----------------|-----------|
| orders | order_id | order_id | cast bigint |
| orders | order_date | ordered_at | rename for clarity |
| orders | order_status | order_status | lower() + map to canonical case |
| orders | gross_amount | gross_revenue_amount | rename; cast numeric(18,2) |
| orders | discount_amount | discount_amount | cast numeric(18,2) |
| orders | tax_amount | tax_amount | cast numeric(18,2) |
| orders | shipping_amount | shipping_amount | cast numeric(18,2) |
| orders | — | is_revenue_eligible | derived: status not in (cancelled, refunded) |
| order_items | line_amount | line_revenue_amount | rename; cast numeric(18,2) |
| order_items | unit_price | unit_price | cast numeric(18,2) |
| refunds | refund_amount | refund_amount | cast numeric(18,2) |
| refunds | refund_date | refunded_at | rename |
| payments | payment_date | paid_at | rename |
| payments | amount | payment_amount | cast numeric(18,2) |
| customers | signup_date | customer_signup_date | rename |
| customers | customer_segment | customer_segment | preserve values (Retail, VIP) |
| products | active_flag | is_product_active | rename |
| categories | category_name | category_name | no change |
| marketing_channels | channel_name | marketing_channel_name | rename |

### Derived metrics (intermediate / mart)

| Derived Column | Definition |
|----------------|------------|
| total_refund_amount | `SUM(refund_amount)` per order from refunds |
| net_order_revenue | `gross_revenue_amount - total_refund_amount` where `is_revenue_eligible` |
| allocated_refund_amount | `total_refund_amount × (line_revenue_amount / order_line_revenue_total)` for category allocation |
| net_line_revenue | `line_revenue_amount - allocated_refund_amount` where order is revenue-eligible |
| customer_lifetime_net_spend | `SUM(net_order_revenue)` per customer |
| order_month | `date_trunc('month', ordered_at)` for monthly rollups |

---

## 6. Staging Model List

All staging models materialized as **views** in schema `staging` (per `dbt_project.yml`).

| Staging Model | Source Table | Purpose |
|---------------|--------------|---------|
| `stg_ecommerce__categories` | categories | Clean category dimension attributes |
| `stg_ecommerce__customers` | customers | PII-preserving customer attributes |
| `stg_ecommerce__marketing_channels` | marketing_channels | Channel lookup |
| `stg_ecommerce__products` | products | Product attributes + category FK |
| `stg_ecommerce__orders` | orders | Order header with eligibility flag + renamed revenue columns |
| `stg_ecommerce__order_items` | order_items | Line-level revenue quantities |
| `stg_ecommerce__payments` | payments | Payment events (future use) |
| `stg_ecommerce__refunds` | refunds | Refund events |

**YAML colocation:** `models/staging/ecommerce/_ecommerce__sources.yml` (Phase 2) + `_ecommerce__models.yml`

---

## 7. Relationship Resolution Plan (Intermediate)

Intermediate models materialized as **views** in schema `intermediate`.

| Intermediate Model | Inputs | Grain | Resolves |
|--------------------|--------|-------|----------|
| `int_refunds__aggregated_by_order` | `stg_ecommerce__refunds` | order_id | Total refund amount per order; partial vs full indicator |
| `int_orders__with_refunds` | `stg_ecommerce__orders`, `int_refunds__aggregated_by_order` | order_id | Net order revenue, eligibility flags, refund totals |
| `int_order_items__enriched` | `stg_ecommerce__order_items`, `int_orders__with_refunds`, `stg_ecommerce__products`, `stg_ecommerce__categories` | order_item_id | Line revenue with product/category denormalized; proportional refund allocation; inherits order eligibility |
| `int_customers__lifetime_metrics` | `int_orders__with_refunds`, `stg_ecommerce__customers` | customer_id | Lifetime net spend, order count, first/last order dates |

**Build order:**
1. `int_refunds__aggregated_by_order`
2. `int_orders__with_refunds`
3. `int_order_items__enriched` (parallel with step 4 after step 2)
4. `int_customers__lifetime_metrics`

---

## 8. Mart Star Schema

All mart models materialized as **tables** in schema `marts`.

### Subject area: `sales`

| Mart Model | Type | Grain | Key Columns | Business Use |
|------------|------|-------|-------------|--------------|
| `fct_orders` | Fact | One row per order | order_id, customer_id, channel_id, ordered_at, order_month, gross_revenue_amount, total_refund_amount, net_order_revenue, is_revenue_eligible, order_status | BQ1 monthly rollups; order-level analysis |
| `fct_order_items` | Fact | One row per order line | order_item_id, order_id, product_id, category_id, quantity, line_revenue_amount, allocated_refund_amount, net_line_revenue, is_revenue_eligible | BQ3 category revenue drivers |

### Subject area: `core`

| Mart Model | Type | Grain | Key Columns | Business Use |
|------------|------|-------|-------------|--------------|
| `dim_customers` | Dimension | One row per customer | customer_id, name, email, country, city, customer_signup_date, customer_segment, lifetime_net_spend, lifetime_order_count | BQ2 top customers; customer segmentation |
| `dim_products` | Dimension | One row per product | product_id, sku, product_name, category_id, unit_price, is_product_active | Product analysis |
| `dim_categories` | Dimension | One row per category | category_id, category_name | Category rollups |
| `dim_marketing_channels` | Dimension | One row per channel | channel_id, marketing_channel_name | Acquisition channel analysis |

**Folder structure:**
```
models/
  staging/ecommerce/
  intermediate/sales/
  marts/
    core/
      dim_customers.sql
      dim_products.sql
      dim_categories.sql
      dim_marketing_channels.sql
    sales/
      fct_orders.sql
      fct_order_items.sql
```

**Bridge tables:** None required — all relationships are straightforward FK hierarchies.

**Out of scope for v1 marts:** `fct_payments`, `fct_refunds` (staged but not promoted until payment/refund subject-area questions arise).

---

## 9. Semantic Metrics List

`ENABLE_SEMANTIC_LAYER: true` — define in `models/marts/sales/_sales__semantic_models.yml` (Phase 6).

### Semantic model: `fct_orders_semantic`

| Metric | Type | Measure | Filters | Answers |
|--------|------|---------|---------|---------|
| `monthly_net_revenue` | simple | `sum(net_order_revenue)` | `is_revenue_eligible = true` | BQ1 |
| `monthly_order_count` | simple | `count(order_id)` | `is_revenue_eligible = true` | BQ1 |
| `gross_revenue` | simple | `sum(gross_revenue_amount)` | `is_revenue_eligible = true` | Supporting |
| `total_refunds` | simple | `sum(total_refund_amount)` | — | Supporting |

**Time dimension:** `ordered_at` (day grain); default aggregation month for executive rollups.

### Semantic model: `dim_customers_semantic`

| Metric | Type | Measure | Filters | Answers |
|--------|------|---------|---------|---------|
| `customer_lifetime_net_spend` | simple | `sum(net_order_revenue)` via entity join | `is_revenue_eligible = true` | BQ2 |

### Semantic model: `fct_order_items_semantic`

| Metric | Type | Measure | Dimensions | Filters | Answers |
|--------|------|---------|------------|---------|---------|
| `category_net_line_revenue` | simple | `sum(net_line_revenue)` | category_name | `is_revenue_eligible = true` | BQ3 |
| `units_sold` | simple | `sum(quantity)` | category_name, product_name | `is_revenue_eligible = true` | Supporting |

---

## 10. Work Batches

Codegen `generate_source` was run once for the full schema (all 8 tables). For Phase 2 staging model codegen (`generate_base_model`), batch tables in groups of **3 max**:

| Batch | Tables | Codegen Command (Phase 2) |
|-------|--------|---------------------------|
| 1 | categories, customers, marketing_channels | `generate_base_model` per table |
| 2 | orders, order_items, products | `generate_base_model` per table |
| 3 | payments, refunds | `generate_base_model` per table |

**Phase 2 build order within batches:**
- Batch 1 → write `_ecommerce__sources.yml` first, then staging SQL for dims
- Batch 2 → staging for facts (orders, order_items) + products
- Batch 3 → staging for payments, refunds
- Then intermediate → marts per Section 7–8 build order

---

## Appendix A: Discovery Evidence Log

| Check | Method | Result |
|-------|--------|--------|
| Codegen source inventory | `dbt run-operation generate_source` | 8 tables, all columns typed |
| PK uniqueness (all tables) | SQL profiling | 0 duplicates on all PKs |
| FK orphan counts (7 relationships) | `dbt show --inline` + SQL | 0 orphans on all FKs |
| Orders without line items | SQL | 0 |
| Orders without payments | SQL | 0 |
| Order status distribution | `dbt show --inline` | Completed 900,027 / Cancelled 95,081 / Refunded 4,892 |
| gross_amount vs line_amount reconciliation | SQL | 999,983 mismatches — documented |
| Partial refunds on completed orders | SQL | 4,521 orders, $234,953.10 total |
| Prerequisites | `dbt deps` | codegen 0.14.0, dbt_utils 1.3.3 installed |

---

## Appendix B: Table Classification Rationale

| Table | Classification | Rationale |
|-------|----------------|-----------|
| categories | Dimension | Descriptive hierarchy for products; low cardinality (20) |
| customers | Dimension | Entity with slowly changing attributes (segment, location) |
| marketing_channels | Dimension | Lookup for acquisition channel |
| products | Dimension | Product catalog entity |
| orders | Fact | Transaction header at order grain with monetary measures |
| order_items | Fact | Transaction detail at line grain with quantity/revenue measures |
| payments | Fact | Payment event (1:1 with order); deferred from v1 marts |
| refunds | Fact | Refund event; aggregated into order facts for v1 KPIs |

**Bridge tables:** Not needed — no unresolved many-to-many relationships.
