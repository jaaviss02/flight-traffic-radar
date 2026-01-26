{{ config(materialized='table') }}

with flight_history as (
    select
        icao24,
        callsign,
        origin_country,
        latitude,
        longitude,
        baro_altitude,
        velocity_kmh,
        time_position,
        -- Ordenamos las posiciones por tiempo para cada avión
        row_number() over (partition by icao24, callsign order by time_position asc) as position_order
    from {{ ref('stg_flights') }}
    where callsign is not null
)

select * from flight_history