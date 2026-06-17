{{
    config(
        materialized='table',
    )
}}

with date_spine as (

    select
        generate_series(
            date '2024-01-01',
            date '2027-12-31',
            interval '1 day'
        )::date as date_day

),

final as (

    select date_day
    from date_spine

)

select * from final
