{{ config(materialized='table') }}

with flight_data as (
    select * from {{ ref('stg_flights') }}
)

select
    callsign,
    origin_country,
    velocity_kmh,
    baro_altitude,
    is_latest,
    case 
        -- Ignoramos errores absurdos de la API (> 1500 km/h)
        when velocity_kmh > 1500 then 'Posible Error de sensor ' || ROUND(velocity_kmh, 1) || ' km/h'
        
        when velocity_kmh > 1200 then 'Velocidad inusual ' || ROUND(velocity_kmh, 1) || ' km/h'
        
        -- Altitud a 42,000 pies (aprox 13,000m)
        when baro_altitude > 13000 then 'Altitud técnica extrema ' || ROUND(baro_altitude, 0) || ' m'
        
        -- Mantenemos la alerta de seguridad en descensos
        when baro_altitude < 500 and velocity_kmh > 450 then 'Descenso a alta velocidad ' || ROUND(baro_altitude, 0) || ' m' || ' - ' || ROUND(velocity_kmh, 1) || ' km/h'

        else 'Normal'
    end as alert_level
from flight_data
where on_ground = false