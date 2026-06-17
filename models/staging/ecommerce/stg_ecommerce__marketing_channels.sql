with source as (

    select * from {{ source('ecommerce', 'marketing_channels') }}

),

renamed as (

    select
        channel_id,
        channel_name as marketing_channel_name

    from source

)

select * from renamed
