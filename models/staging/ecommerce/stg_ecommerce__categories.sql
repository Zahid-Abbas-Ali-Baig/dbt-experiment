with source as (

    select * from {{ source('ecommerce', 'categories') }}

),

renamed as (

    select
        category_id,
        category_name

    from source

)

select * from renamed
