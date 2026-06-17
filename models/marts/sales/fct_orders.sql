with orders as (

    select * from {{ ref('int_orders__with_refunds') }}

),

final as (

    select
        order_id,
        customer_id,
        channel_id,
        ordered_at,
        order_month,
        order_status,
        gross_revenue_amount,
        total_refund_amount,
        net_order_revenue,
        is_revenue_eligible

    from orders

)

select * from final
