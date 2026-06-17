with source as (

    select * from {{ source('ecommerce', 'payments') }}

),

renamed as (

    select
        payment_id,
        order_id,
        cast(payment_date as timestamp without time zone) as paid_at,
        payment_method,
        payment_status,
        cast(amount as numeric(18, 2)) as payment_amount

    from source

)

select * from renamed
