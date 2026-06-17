with order_items as (

    select * from {{ ref('int_order_items__enriched') }}

),

final as (

    select
        order_item_id,
        order_id,
        product_id,
        category_id,
        quantity,
        line_revenue_amount,
        allocated_refund_amount,
        net_line_revenue,
        is_revenue_eligible

    from order_items

)

select * from final
