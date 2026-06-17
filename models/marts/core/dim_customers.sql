with customer_metrics as (

    select * from {{ ref('int_customers__lifetime_metrics') }}

),

ranked as (

    select
        customer_metrics.*,
        case
            when lifetime_order_count > 0
                then percent_rank() over (order by lifetime_net_spend desc)
        end as lifetime_spend_percentile

    from customer_metrics

),

final as (

    select
        customer_id,
        trim(first_name || ' ' || last_name) as name,
        email,
        country,
        city,
        customer_signup_date,
        customer_segment,
        lifetime_net_spend,
        lifetime_order_count,
        case
            when lifetime_order_count = 0 then 'No Eligible Orders'
            when lifetime_spend_percentile <= 0.10 then 'Top 10% by Lifetime Spend'
            when lifetime_spend_percentile <= 0.25 then 'Top 25% by Lifetime Spend'
            else 'Standard'
        end as lifetime_value_segment

    from ranked

)

select * from final
