with order_items as (

    select * from {{ ref('int_order_items__enriched') }}

),

orders as (

    select
        order_id,
        ordered_at

    from {{ ref('fct_orders') }}

),

final as (

    select
        order_items.order_item_id,
        order_items.order_id,
        order_items.product_id,
        order_items.category_id,
        orders.ordered_at,
        order_items.quantity,
        order_items.line_revenue_amount,
        order_items.allocated_refund_amount,
        order_items.net_line_revenue,
        order_items.is_revenue_eligible

    from order_items
    inner join orders
        on order_items.order_id = orders.order_id

)

select * from final
