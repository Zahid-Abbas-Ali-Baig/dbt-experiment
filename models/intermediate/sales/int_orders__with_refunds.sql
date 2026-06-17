with orders as (

    select * from {{ ref('stg_ecommerce__orders') }}

),

refunds_by_order as (

    select * from {{ ref('int_refunds__aggregated_by_order') }}

),

joined as (

    select
        orders.order_id,
        orders.customer_id,
        orders.ordered_at,
        orders.order_status,
        orders.channel_id,
        orders.gross_revenue_amount,
        orders.discount_amount,
        orders.tax_amount,
        orders.shipping_amount,
        orders.is_revenue_eligible,
        coalesce(refunds_by_order.total_refund_amount, 0) as total_refund_amount,
        refunds_by_order.refunded_at,
        refunds_by_order.refund_reason,
        orders.order_status = 'Refunded' as is_fully_refunded,
        orders.order_status = 'Cancelled' as is_cancelled,
        (
            orders.order_status = 'Completed'
            and coalesce(refunds_by_order.total_refund_amount, 0) > 0
        ) as has_partial_refund,
        case
            when orders.is_revenue_eligible
                then orders.gross_revenue_amount - coalesce(refunds_by_order.total_refund_amount, 0)
            else 0
        end as net_order_revenue,
        date_trunc('month', orders.ordered_at) as order_month

    from orders
    left join refunds_by_order
        on orders.order_id = refunds_by_order.order_id

)

select * from joined
