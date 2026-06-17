with source as (

    select * from {{ source('ecommerce', 'customers') }}

),

renamed as (

    select
        customer_id,
        first_name,
        last_name,
        email,
        country,
        city,
        signup_date as customer_signup_date,
        customer_segment

    from source

)

select * from renamed
