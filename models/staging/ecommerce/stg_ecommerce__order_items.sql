with source as (

    select * from {{ source('ecommerce', 'order_items') }}

),

renamed as (

    select
        order_item_id,
        order_id,
        product_id,
        quantity,
        cast(unit_price as numeric(18, 2)) as unit_price,
        cast(line_amount as numeric(18, 2)) as line_revenue_amount

    from source

)

select * from renamed
