# ShopSphere dbt Project

Governed analytics pipeline for ShopSphere e-commerce: staging → intermediate → marts → semantic layer.

## Problem Statement

ShopSphere is an online retailer selling physical goods (browse → cart → order → payment → fulfillment). Teams need unified reporting for sales, customers, and product performance, replacing inconsistent ad-hoc SQL with governed dbt models. Key pain points:

- Inconsistent revenue definitions across teams
- No single source of truth for customer lifetime value (CLV)

**Constraints:** Exclude cancelled and fully refunded orders from revenue KPIs; currency assumed USD.

## KPI Traceability Matrix

| Business Question | Source Table(s) | Staging Model(s) | Intermediate Model(s) | Mart Model(s) | Semantic Metric |
|-------------------|-----------------|------------------|----------------------|---------------|-----------------|
| BQ1 — monthly revenue & order count | `orders`, `refunds` | `stg_ecommerce__orders`, `stg_ecommerce__refunds` | `int_orders__with_refunds` | `fct_orders` | `monthly_net_revenue`, `monthly_order_count` |
| BQ2 — top customers by lifetime spend | `orders`, `refunds`, `customers` | `stg_ecommerce__orders`, `stg_ecommerce__refunds`, `stg_ecommerce__customers` | `int_orders__with_refunds`, `int_customers__lifetime_metrics` | `fct_orders`, `dim_customers` | `customer_lifetime_net_spend` |
| BQ3 — category revenue drivers | `order_items`, `orders`, `products`, `categories`, `refunds` | `stg_ecommerce__order_items`, `stg_ecommerce__orders`, `stg_ecommerce__products`, `stg_ecommerce__categories`, `stg_ecommerce__refunds` | `int_orders__with_refunds`, `int_order_items__enriched` | `fct_order_items`, `dim_categories`, `dim_products` | `category_net_line_revenue` |

**Supporting semantic metrics:** `gross_revenue`, `total_refunds`, `units_sold`

## Layer Map

```
ecommerce (source)
    └── staging/ecommerce/          stg_ecommerce__*          (views, schema: staging)
            └── intermediate/sales/ int_*                     (views, schema: intermediate)
                    └── marts/
                          ├── core/   dim_customers, dim_products, dim_categories, dim_marketing_channels
                          └── sales/  fct_orders, fct_order_items
                                └── semantic/semantic_models.yml   (MetricFlow metrics)
```

| Layer | Schema | Materialization | Models |
|-------|--------|-----------------|--------|
| Staging | `staging` | view | 8 `stg_ecommerce__*` models |
| Intermediate | `intermediate` | view | 4 `int_*` models |
| Marts | `marts` | table | 2 facts + 4 dimensions + `time_spine_daily` |
| Semantic | — | YAML config | 6 semantic models, 7 metrics |

## Environment Setup

### Prerequisites

- Python 3.10+
- PostgreSQL with `shopsphere` database and `ecommerce` schema loaded
- dbt Core 1.11+ with `dbt-postgres` adapter (use project venv; see below)

### Project root

```
PROJECT_ROOT=.
```

### Install dependencies

```bash
dbt deps
```

Installs `dbt-labs/codegen` (0.14.0) and `dbt-labs/dbt_utils` (1.3.3).

### profiles.yml

Create or copy `profiles.yml` in the project root (or `~/.dbt/profiles.yml`):

```yaml
shopsphere:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      password: <your-password>
      dbname: shopsphere
      schema: ecommerce
      threads: 4
```

> Do not commit real passwords. Use environment variables or a local-only profiles file.

### Postgres adapter note

The system `dbt` binary (dbt Fusion 2.0 alpha) does not support the Postgres adapter. Use the project virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\pip install "dbt-core==1.11.0" "dbt-postgres==1.9.0"
.\.venv\Scripts\dbt deps
```

## Execution Commands

```bash
# Build all models and run tests
.\.venv\Scripts\dbt build --quiet --warn-error-options '{"error": ["NoNodesForSelectionCriteria"]}'

# Run models only
.\.venv\Scripts\dbt run --select marts.*

# Run tests only
.\.venv\Scripts\dbt test --select marts.*

# Build + test in one step (preferred during development)
.\.venv\Scripts\dbt build --select fct_orders+

# Compile project (validates SQL and semantic YAML)
.\.venv\Scripts\dbt compile
```

## Agent Skills and Phase Sequence

| Phase | Skill | Deliverable |
|-------|-------|-------------|
| 0 | `configuring-dbt-mcp-server` | `config.md`, `profiles.yml`, `dbt_project.yml` |
| 1 | `using-dbt-for-analytics-engineering` | Schema discovery, `design_brief.md` |
| 2 | `using-dbt-for-analytics-engineering` | Staging models + `_sources.yml` |
| 3 | `using-dbt-for-analytics-engineering` | Intermediate models |
| 4 | `using-dbt-for-analytics-engineering` | Mart star schema (facts + dimensions) |
| 6 | `building-dbt-semantic-layer` | `models/semantic/semantic_models.yml` |
| 6 | `using-dbt-for-analytics-engineering` | `models/marts/_marts__models.yml` |
| 6 | `running-dbt-commands` | `dbt compile` validation |

## Codegen Macro Reference

### Generate source YAML

```bash
dbt run-operation generate_source --args '{"schema_name": "ecommerce", "database_name": "shopsphere", "generate_columns": true}'
```

### Generate base staging model

```bash
dbt run-operation generate_base_model --args '{"source_name": "ecommerce", "table_name": "orders"}'
```

### Generate model YAML (marts documentation)

```bash
dbt run-operation generate_model_yaml --args '{
  "model_names": [
    "fct_orders", "fct_order_items",
    "dim_customers", "dim_products", "dim_categories", "dim_marketing_channels"
  ]
}'
```

Output was captured into `models/marts/_marts__models.yml` and enriched with semantic descriptions, KPI linkage, and data tests.

## Semantic Layer

`ENABLE_SEMANTIC_LAYER: true` — metrics defined in `models/semantic/semantic_models.yml`.

| Metric | Type | Measure | Filter | Answers |
|--------|------|---------|--------|---------|
| `monthly_net_revenue` | simple | `sum(net_order_revenue)` | `is_revenue_eligible = true` | BQ1 |
| `monthly_order_count` | simple | `count_distinct(order_id)` | `is_revenue_eligible = true` | BQ1 |
| `gross_revenue` | simple | `sum(gross_revenue_amount)` | `is_revenue_eligible = true` | Supporting |
| `total_refunds` | simple | `sum(total_refund_amount)` | — | Supporting |
| `customer_lifetime_net_spend` | simple | `sum(net_order_revenue)` via customer entity join | `is_revenue_eligible = true` | BQ2 |
| `category_net_line_revenue` | simple | `sum(net_line_revenue)` | `is_revenue_eligible = true` | BQ3 |
| `units_sold` | simple | `sum(quantity)` | `is_revenue_eligible = true` | Supporting |

**Join paths:** Shared MetricFlow entities (`customer`, `order`, `product`, `category`, `channel`) link facts to dimensions for slice-and-dice queries.
