with source as (

    select * from {{ source('ecommerce', 'refunds') }}

),

renamed as (

    select
        refund_id,
        order_id,
        cast(refund_date as timestamp without time zone) as refunded_at,
        cast(refund_amount as numeric(18, 2)) as refund_amount,
        refund_reason

    from source

)

select * from renamed
