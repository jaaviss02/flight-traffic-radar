{{ config(
    materialized='incremental',
    unique_key='track_id'
) }}

with current_snapshot as (
    select
        -- Creamos un ID único combinando el avión y el segundo exacto
        (icao24 || '_' || time_position::VARCHAR) as track_id,
        icao24,
        callsign,
        origin_country,
        latitude,
        longitude,
        baro_altitude,
        velocity_kmh,
        time_position
    from {{ ref('stg_flights') }}
    where callsign is not null
)

select * from current_snapshot

{% if is_incremental() %}
  -- Este bloque es el que impide que se borren los datos viejos
  -- Solo insertamos puntos que NO existan ya en la tabla histórica
  where track_id not in (select track_id from {{ this }})
{% endif %}
