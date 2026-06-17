with marketing_channels as (

    select * from {{ ref('stg_ecommerce__marketing_channels') }}

),

final as (

    select
        channel_id,
        marketing_channel_name

    from marketing_channels

)

select * from final
