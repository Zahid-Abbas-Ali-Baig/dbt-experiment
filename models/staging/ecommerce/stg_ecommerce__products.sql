with source as (

    select * from {{ source('ecommerce', 'products') }}

),

renamed as (

    select
        product_id,
        sku,
        product_name,
        category_id,
        cast(unit_price as numeric(18, 2)) as unit_price,
        active_flag as is_product_active

    from source

)

select * from renamed
