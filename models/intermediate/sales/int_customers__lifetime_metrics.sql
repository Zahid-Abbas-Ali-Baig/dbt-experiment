with orders_with_refunds as (

    select * from {{ ref('int_orders__with_refunds') }}

),

customers as (

    select * from {{ ref('stg_ecommerce__customers') }}

),

order_metrics as (

    select
        customer_id,
        sum(net_order_revenue) as lifetime_net_spend,
        count(*) filter (where is_revenue_eligible) as lifetime_order_count,
        min(ordered_at) as first_order_at,
        max(ordered_at) as last_order_at

    from orders_with_refunds
    group by customer_id

),

joined as (

    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customers.email,
        customers.country,
        customers.city,
        customers.customer_signup_date,
        customers.customer_segment,
        coalesce(order_metrics.lifetime_net_spend, 0) as lifetime_net_spend,
        coalesce(order_metrics.lifetime_order_count, 0) as lifetime_order_count,
        order_metrics.first_order_at,
        order_metrics.last_order_at,
        order_metrics.customer_id is not null as has_valid_customer_id

    from customers
    left join order_metrics
        on customers.customer_id = order_metrics.customer_id

)

select * from joined
