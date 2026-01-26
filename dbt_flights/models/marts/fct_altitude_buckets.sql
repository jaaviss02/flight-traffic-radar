{{ config(materialized='table') }}

with flight_data as (
    select * from {{ ref('stg_flights') }}
)

select
    -- Agrupamos en bloques de 2000 metros
    floor(baro_altitude / 2000) * 2000 as altitude_range,
    count(*) as aircraft_count,
    avg(velocity_kmh) as avg_velocity_in_range
    
from flight_data
where baro_altitude is not null
group by 1
order by 1 asc