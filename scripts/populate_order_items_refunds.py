"""Populate ecommerce order_items, refunds, and payments with FK-valid reference data."""

import argparse
import time

import psycopg2

ORDER_ITEMS_SQL = """
INSERT INTO ecommerce.order_items (order_id, product_id, quantity, unit_price, line_amount)
SELECT
    o.order_id,
    p.product_id,
    (1 + (o.order_id % 5))::integer AS quantity,
    p.unit_price,
    ((1 + (o.order_id % 5))::numeric * p.unit_price) AS line_amount
FROM ecommerce.orders o
CROSS JOIN LATERAL generate_series(1, 1 + (o.order_id % 3)::integer) AS gs(line_num)
JOIN ecommerce.products p
  ON p.product_id = ((o.order_id * 17 + gs.line_num * 991) % 5000) + 1
"""

REFUNDS_FULL_SQL = """
INSERT INTO ecommerce.refunds (order_id, refund_date, refund_amount, refund_reason)
SELECT
    order_id,
    order_date + ((order_id % 14) + 1) * interval '1 day',
    gross_amount,
    CASE (order_id % 5)
        WHEN 0 THEN 'Customer return'
        WHEN 1 THEN 'Defective product'
        WHEN 2 THEN 'Late delivery'
        WHEN 3 THEN 'Duplicate charge'
        ELSE 'Changed mind'
    END
FROM ecommerce.orders
WHERE order_status = 'Refunded'
"""

REFUNDS_PARTIAL_SQL = """
INSERT INTO ecommerce.refunds (order_id, refund_date, refund_amount, refund_reason)
SELECT
    order_id,
    order_date + ((order_id % 30) + 1) * interval '1 day',
    ROUND((gross_amount * (0.10 + (order_id % 5) * 0.05))::numeric, 2),
    'Partial refund - item return'
FROM ecommerce.orders
WHERE order_status = 'Completed'
  AND order_id % 200 = 0
"""

PAYMENTS_SQL = """
INSERT INTO ecommerce.payments (order_id, payment_date, payment_method, payment_status, amount)
SELECT
    o.order_id,
    o.order_date + ((o.order_id % 3)) * interval '1 hour',
    CASE (o.order_id % 5)
        WHEN 0 THEN 'Credit Card'
        WHEN 1 THEN 'Debit Card'
        WHEN 2 THEN 'PayPal'
        WHEN 3 THEN 'Apple Pay'
        ELSE 'Google Pay'
    END,
    CASE o.order_status
        WHEN 'Completed' THEN 'Captured'
        WHEN 'Cancelled' THEN CASE WHEN o.order_id % 2 = 0 THEN 'Failed' ELSE 'Voided' END
        WHEN 'Refunded' THEN 'Refunded'
    END,
    o.gross_amount
FROM ecommerce.orders o
"""

VALIDATION_SQL = [
    ("orphan order_items (order_id)", """
        SELECT COUNT(*) FROM ecommerce.order_items oi
        LEFT JOIN ecommerce.orders o ON o.order_id = oi.order_id
        WHERE o.order_id IS NULL
    """),
    ("orphan order_items (product_id)", """
        SELECT COUNT(*) FROM ecommerce.order_items oi
        LEFT JOIN ecommerce.products p ON p.product_id = oi.product_id
        WHERE p.product_id IS NULL
    """),
    ("orphan refunds (order_id)", """
        SELECT COUNT(*) FROM ecommerce.refunds r
        LEFT JOIN ecommerce.orders o ON o.order_id = r.order_id
        WHERE o.order_id IS NULL
    """),
    ("orders without line items", """
        SELECT COUNT(*) FROM ecommerce.orders o
        LEFT JOIN ecommerce.order_items oi ON oi.order_id = o.order_id
        WHERE oi.order_item_id IS NULL
    """),
]

PAYMENT_VALIDATION_SQL = [
    ("orphan payments (order_id)", """
        SELECT COUNT(*) FROM ecommerce.payments p
        LEFT JOIN ecommerce.orders o ON o.order_id = p.order_id
        WHERE o.order_id IS NULL
    """),
    ("orders without payments", """
        SELECT COUNT(*) FROM ecommerce.orders o
        LEFT JOIN ecommerce.payments p ON p.order_id = o.order_id
        WHERE p.payment_id IS NULL
    """),
]

STEPS = {
    "order_items": ORDER_ITEMS_SQL,
    "refunds_full": REFUNDS_FULL_SQL,
    "refunds_partial": REFUNDS_PARTIAL_SQL,
    "payments": PAYMENTS_SQL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        choices=list(STEPS.keys()) + ["refunds", "all"],
        default="all",
        help="Run a subset of population steps (default: all)",
    )
    return parser.parse_args()


def resolve_steps(only: str) -> list[tuple[str, str]]:
    if only == "all":
        return [
            ("order_items", ORDER_ITEMS_SQL),
            ("refunds (full)", REFUNDS_FULL_SQL),
            ("refunds (partial)", REFUNDS_PARTIAL_SQL),
            ("payments", PAYMENTS_SQL),
        ]
    if only == "refunds":
        return [
            ("refunds (full)", REFUNDS_FULL_SQL),
            ("refunds (partial)", REFUNDS_PARTIAL_SQL),
        ]
    label = only.replace("_", " ")
    return [(label, STEPS[only])]


def main() -> None:
    args = parse_args()
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="shopsphere",
        user="postgres",
        password="admin99",
    )
    cur = conn.cursor()

    for label, sql in resolve_steps(args.only):
        t0 = time.time()
        cur.execute(sql)
        print(f"{label}: inserted {cur.rowcount:,} rows in {time.time() - t0:.1f}s")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM ecommerce.order_items")
    print(f"order_items total: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM ecommerce.refunds")
    print(f"refunds total: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM ecommerce.payments")
    print(f"payments total: {cur.fetchone()[0]:,}")

    for label, sql in VALIDATION_SQL + PAYMENT_VALIDATION_SQL:
        cur.execute(sql)
        print(f"{label}: {cur.fetchone()[0]:,}")

    cur.close()
    conn.close()
    print("done")


if __name__ == "__main__":
    main()
