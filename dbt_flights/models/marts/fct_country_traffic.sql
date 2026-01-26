{{ config(materialized='table') }}

with base_flights as (
    select * from {{ ref('stg_flights') }}
)

select
    origin_country,
    on_ground,
    is_latest,
    count(*) as num_flights,
    count(*) over(partition by origin_country) as country_total_weight
from base_flights
group by 
    origin_country, 
    on_ground, 
    is_latest
order by 
    country_total_weight desc, 
    origin_country asc, 
    on_ground desc