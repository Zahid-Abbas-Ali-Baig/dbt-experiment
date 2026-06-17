with source as (

    select * from {{ source('ecommerce', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        cast(order_date as timestamp without time zone) as ordered_at,
        initcap(lower(order_status)) as order_status,
        channel_id,
        cast(gross_amount as numeric(18, 2)) as gross_revenue_amount,
        cast(discount_amount as numeric(18, 2)) as discount_amount,
        cast(tax_amount as numeric(18, 2)) as tax_amount,
        cast(shipping_amount as numeric(18, 2)) as shipping_amount,
        initcap(lower(order_status)) not in ('Cancelled', 'Refunded') as is_revenue_eligible

    from source

)

select * from renamed
