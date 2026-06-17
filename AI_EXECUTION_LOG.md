# AI Execution Log — ShopSphere

Track every phase run. Documenting AI reliability is part of the deliverable.

| Phase | Skill(s) Used | Output | Hallucinations Found | Manual Corrections |
| ----- | ------------- | ------ | -------------------- | ------------------ |
| 0 | analytics-eng + run-commands | Minimal bootstrap (`config.md`, `dbt_project.yml`, `profiles.yml`, folder scaffold, `dbt deps`) | — | — |
| 1 | analytics-eng + run-commands | `design_brief.md` (discovery via codegen + SQL profiling) | — | User approved design brief (`Status: approved`) |
| 2 | run-commands + analytics-eng | `models/staging/ecommerce/_ecommerce__sources.yml` | — | — |
| 3 | run-commands + analytics-eng | 8 `stg_ecommerce__*` models + `_ecommerce__models.yml` | — | — |
| 4 | analytics-eng | 4 `int_*` intermediate models + `_int_sales__models.yml` | — | — |
| 5 | analytics-eng | 6 mart models (`fct_orders`, `fct_order_items`, 4 `dim_*`) | `dim_customers` gained `lifetime_value_segment` / `lifetime_spend_percentile` beyond design brief §8 | Accepted as enrichment for BQ2 ranking |
| 6 | semantic-layer + run-commands + analytics-eng | `models/semantic/semantic_models.yml`, `_marts__models.yml`, `README.md`, `time_spine_daily` | Semantic YAML path in design brief §9 (`models/marts/sales/_sales__semantic_models.yml`) vs actual `models/semantic/`; `ordered_at` on `fct_order_items` semantic model (column not on mart until Phase 6 fix); `monthly_order_count` spec says `count(order_id)` but implementation uses `count_distinct` | Removed invalid `ordered_at` time dimension from `fct_order_items` semantic model; added `time_spine_daily` for MetricFlow compile; placed semantic config under `models/semantic/` |
| 7 | run-commands + analytics-eng | **`dbt build --select staging+` PASS** (129/129: 18 models + 111 tests, 63.6s); grain checks; semantic compile | None new — prior drift validated against live data (see Phase 5–6 rows). `fct_order_items` now includes `ordered_at` via join to `fct_orders` (not in design brief §8 column list but consistent with semantic join-path note) | None required — all tests passed without code changes |

## Phase 7 Validation Evidence

**Build** (`dbt build --select staging+`, 2026-06-17 16:26:21):

```
Done. PASS=129 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=129
Finished running 6 table models, 111 data tests, 12 view models in 63.59s
```

**Grain checks** (`dbt show --inline`):

| Mart | Expected grain (design brief §8) | row_count | distinct PK | Match |
| ---- | -------------------------------- | --------- | ----------- | ----- |
| `fct_orders` | One row per order | 1,000,000 | 1,000,000 `order_id` | Yes |
| `dim_customers` | One row per customer | 100,000 | 100,000 `customer_id` | Yes |

**Semantic layer compile** (`dbt compile --quiet`, 2026-06-17 16:26:44):

```
Found 19 models, 111 data tests, 8 sources, 7 metrics, 6 semantic models
Command `dbt compile` succeeded
```

`target/semantic_manifest.json` written with all 6 semantic models and 7 metrics.

**Blockers:** None.
