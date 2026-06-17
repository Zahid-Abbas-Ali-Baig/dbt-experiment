with products as (

    select * from {{ ref('stg_ecommerce__products') }}

),

final as (

    select
        product_id,
        sku,
        product_name,
        category_id,
        unit_price,
        is_product_active

    from products

)

select * from final
