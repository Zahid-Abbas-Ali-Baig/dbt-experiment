with refunds as (

    select * from {{ ref('stg_ecommerce__refunds') }}

),

aggregated as (

    select
        order_id,
        sum(refund_amount) as total_refund_amount,
        max(refunded_at) as refunded_at,
        max(refund_reason) as refund_reason

    from refunds
    group by order_id

)

select * from aggregated
