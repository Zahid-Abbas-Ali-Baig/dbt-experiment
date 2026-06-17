with order_items as (

    select * from {{ ref('stg_ecommerce__order_items') }}

),

orders_with_refunds as (

    select * from {{ ref('int_orders__with_refunds') }}

),

products as (

    select * from {{ ref('stg_ecommerce__products') }}

),

categories as (

    select * from {{ ref('stg_ecommerce__categories') }}

),

order_line_totals as (

    select
        order_id,
        sum(line_revenue_amount) as order_line_revenue_total

    from order_items
    group by order_id

),

enriched as (

    select
        order_items.order_item_id,
        order_items.order_id,
        order_items.product_id,
        products.category_id,
        order_items.quantity,
        order_items.unit_price,
        order_items.line_revenue_amount,
        order_line_totals.order_line_revenue_total,
        orders_with_refunds.is_revenue_eligible,
        orders_with_refunds.total_refund_amount,
        case
            when orders_with_refunds.is_revenue_eligible
                and order_line_totals.order_line_revenue_total > 0
                then round(
                    orders_with_refunds.total_refund_amount
                    * order_items.line_revenue_amount
                    / order_line_totals.order_line_revenue_total,
                    2
                )
            else 0
        end as allocated_refund_amount,
        case
            when orders_with_refunds.is_revenue_eligible
                and order_line_totals.order_line_revenue_total > 0
                then round(
                    order_items.line_revenue_amount
                    - (
                        orders_with_refunds.total_refund_amount
                        * order_items.line_revenue_amount
                        / order_line_totals.order_line_revenue_total
                    ),
                    2
                )
            else 0
        end as net_line_revenue,
        products.sku,
        products.product_name,
        products.is_product_active,
        categories.category_name,
        orders_with_refunds.order_id is not null as has_valid_order_id,
        products.product_id is not null as has_valid_product_id,
        products.category_id is not null as has_valid_category_id

    from order_items
    inner join order_line_totals
        on order_items.order_id = order_line_totals.order_id
    inner join orders_with_refunds
        on order_items.order_id = orders_with_refunds.order_id
    inner join products
        on order_items.product_id = products.product_id
    inner join categories
        on products.category_id = categories.category_id

)

select * from enriched
