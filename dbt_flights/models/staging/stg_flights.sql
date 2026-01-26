with curated_flights as (
    -- Aquí usamos la fuente de tus parquets
    select * from {{ source('opensky_api', 'curated_flights') }}
),

final as (
    select
        *,
        (velocity * 3.6) as velocity_kmh,
        -- Buscamos el valor máximo de time_position en todo el dataset
        -- y creamos una marca verdadera (true) solo para los que coincidan con ese máximo
        case 
            when time_position = max(time_position) over() then true 
            else false 
        end as is_latest
    from curated_flights
)

select * from final