import streamlit as st
import duckdb
import os
import pandas as pd
import pydeck as pdk
import altair as alt

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Radar de Vuelos", page_icon="✈️", layout="wide")

# CONEXIÓN A LA BASE DE DATOS
base_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_path, '..', 'flights_history.duckdb')
con = duckdb.connect(db_path)

# --- SIDEBAR: FILTROS ---
st.sidebar.title("Filtros")
paises_df = con.execute("SELECT DISTINCT origin_country FROM stg_flights ORDER BY 1").df()
paises_sel = st.sidebar.multiselect("País:", options=paises_df['origin_country'].tolist())

filtro_sql = f"AND origin_country IN ({str(paises_sel)[1:-1]})" if paises_sel else ""
filtro_where = f"WHERE origin_country IN ({str(paises_sel)[1:-1]})" if paises_sel else ""

# --- CARGA DE DATOS ---
# scripts/dashboard.py
try:
    df_now = con.execute("SELECT * FROM stg_flights WHERE is_latest = true").df()
except Exception:
    st.warning("⚠️ La base de datos está siendo inicializada. Por favor, espera al primer ciclo de carga.")
    st.stop() # Detiene la ejecución del dashboard de forma elegante
    
df_alerts = con.execute(f"SELECT * FROM fct_flight_alerts WHERE is_latest = true AND alert_level != 'Normal' {filtro_sql}").df()

df_hist_paises = con.execute(f"""
    SELECT origin_country, SUM(num_flights) as total_vuelos 
    FROM fct_country_traffic 
    {filtro_where} 
    GROUP BY 1 ORDER BY total_vuelos DESC
""").df()

df_hist_alt = con.execute("SELECT * FROM fct_altitude_buckets WHERE altitude_range > 0 ORDER BY altitude_range DESC").df()

# --- INTERFAZ ---
st.title("✈️ Sistema de Monitorización y Análisis Aéreo")

if not df_now.empty:
    last_ts = pd.to_datetime(df_now['time_position'].max(), unit='s')
    st.caption(f"Último snapshot procesado: {last_ts} UTC")

st.divider()

# --- SECCIÓN 1: TIEMPO REAL ---
st.header("📍 Situación Actual")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Aeronaves Activas", len(df_now))
with m2:
    volando = len(df_now[df_now['on_ground'] == False]) if not df_now.empty else 0
    st.metric("✈️ Volando", volando)
with m3:
    en_tierra = len(df_now[df_now['on_ground'] == True]) if not df_now.empty else 0
    st.metric("En Tierra", en_tierra)
with m4:
    vel_med = round(df_now[df_now['on_ground'] == False]['velocity_kmh'].mean(), 1) if not df_now.empty else 0
    st.metric("💨 Vel. Media", f"{vel_med} km/h")

col_map, col_alerts = st.columns([2, 1])

with col_map:
    # Definición de colores: Naranja para tierra, Azul para en el aire
    df_now['color_r'] = df_now['on_ground'].apply(lambda x: 255 if x else 0)
    df_now['color_g'] = 128
    df_now['color_b'] = df_now['on_ground'].apply(lambda x: 0 if x else 255)

    # Definición de la capa de puntos
    layer_puntos = pdk.Layer(
        "ScatterplotLayer",
        df_now,
        get_position='[longitude, latitude]',
        get_color='[color_r, color_g, color_b, 160]',
        get_radius=40000,
        pickable=True, 
    )

    view_state = pdk.ViewState(
        latitude=df_now['latitude'].mean() if not df_now.empty else 0,
        longitude=df_now['longitude'].mean() if not df_now.empty else 0,
        zoom=2
    )

    # Renderizado del mapa con TOOLTIP explícito
    event = st.pydeck_chart(
        pdk.Deck(
            layers=[layer_puntos], 
            initial_view_state=view_state,
            tooltip={
                "html": "<b>Vuelo:</b> {callsign} <br/> <b>Origen:</b> {origin_country}",
                "style": {"background": "steelblue", "color": "white"}
            }
        ),
        on_select="rerun",
        selection_mode="single-object"
    )
    st.caption("🔵 Volando | 🟠 En Tierra")

with col_alerts:
    st.subheader("⚠️ Alertas actuales")
    if not df_alerts.empty:
        st.dataframe(
            df_alerts[['callsign', 'alert_level']], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.write("No hay alertas activas.")

st.divider()

# --- SECCIÓN 2: HISTÓRICO ---
st.header("📊 Datos Históricos")

c1, c2 = st.columns(2)

with c1:
    st.subheader("🔝 Países con mayor número de vuelos")
    top_5 = df_hist_paises.head(5)
    
    if not top_5.empty:
        chart_paises = alt.Chart(top_5).mark_bar(color="#1f77b4").encode(
            x=alt.X('origin_country:N', sort=None, title="País de Origen"),
            y=alt.Y('total_vuelos:Q', title="Total Vuelos"),
            tooltip=['origin_country', 'total_vuelos']
        ).properties(height=400)
        st.altair_chart(chart_paises, use_container_width=True)
    else:
        st.write("Sin datos históricos.")

with c2:
    st.subheader("☁️ Pasillos de Altitud")
    if not df_hist_alt.empty:
        chart_alt = alt.Chart(df_hist_alt).mark_bar(color="#ff7f0e").encode(
            y=alt.Y('altitude_range:N', sort=None, title="Altitud (metros)"),
            x=alt.X('aircraft_count:Q', title="Nº Aeronaves"),
            tooltip=['altitude_range', 'aircraft_count']
        ).properties(height=400)
        st.altair_chart(chart_alt, use_container_width=True)
    else:
        st.write("Sin datos de altitud.")

# --- SECCIÓN 3: TRAYECTORIAS ---
st.divider()
st.header("🕵️ Rastreador de Trayectorias")

# Capturar clic del mapa
callsign_sel = ""
if event and event.selection and event.selection.get("objects"):
    obj_dict = event.selection["objects"]
    # Extraer el primer objeto seleccionado del diccionario
    callsign_sel = list(obj_dict.values())[0][0].get("callsign", "")

vuelo_input = st.text_input("Buscador de vuelo (clic en mapa o escribe):", value=callsign_sel).upper()

if vuelo_input:
    # 1. Obtener el histórico para el mapa
    df_track = con.execute(f"""
        SELECT latitude, longitude, baro_altitude, velocity_kmh, origin_country 
        FROM fct_flight_tracks 
        WHERE callsign = '{vuelo_input}' 
        ORDER BY time_position ASC
    """).df()

    if not df_track.empty:
        # 2. Extraemos el último estado conocido para las métricas
        ultimo_punto = df_track.iloc[-1]
        
        # Mostramos la ficha técnica con métricas
        c_v1, c_v2, c_v3, c_v4 = st.columns(4)
        with c_v1:
            st.metric("País de Origen", ultimo_punto['origin_country'])
        with c_v2:
            st.metric("Velocidad Actual", f"{round(ultimo_punto['velocity_kmh'], 1)} km/h")
        with c_v3:
            st.metric("Altitud", f"{int(ultimo_punto['baro_altitude'])} m")
        with c_v4:
            st.metric("Puntos en Ruta", len(df_track))

        # 3. Dibujamos el mapa de la trayectoria
        capas_trayectoria = []

        # Si hay más de un punto, dibujamos la línea
        if len(df_track) > 1:
            capas_trayectoria.append(
                pdk.Layer(
                    "PathLayer", 
                    [{"path": df_track[['longitude', 'latitude']].values.tolist()}], 
                    get_path="path", 
                    get_color=[0, 255, 128], 
                    get_width=2000,
                    width_min_pixels=3
                )
            )
        
        # Dibujamos el punto de la posición actual
        # Esto sirve para ver el punto único o el final de la línea
        capas_trayectoria.append(
            pdk.Layer(
                "ScatterplotLayer",
                df_track.iloc[[-1]],
                get_position='[longitude, latitude]',
                get_color=[0, 255, 128],
                get_radius=20000,
            )
        )

        st.pydeck_chart(pdk.Deck(
            layers=capas_trayectoria, 
            initial_view_state=pdk.ViewState(
                latitude=df_track['latitude'].mean(), 
                longitude=df_track['longitude'].mean(), 
                zoom=5
            )
        ))
    else:
        st.warning(f"No hay datos históricos para el vuelo {vuelo_input}. Asegúrate de que el nombre es correcto.")

con.close()