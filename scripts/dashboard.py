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

# Función para obtener conexión (evita bloqueos)
def get_connection():
    return duckdb.connect(db_path, read_only=True)

con = get_connection()

# --- SIDEBAR: FILTROS ---
st.sidebar.title("✈️ Controles")
st.sidebar.caption("Auto-refresco: cada 5 min")

try:
    paises_df = con.execute("SELECT DISTINCT origin_country FROM stg_flights WHERE origin_country IS NOT NULL ORDER BY 1").df()
    paises_sel = st.sidebar.multiselect("Filtrar por País:", options=paises_df['origin_country'].tolist())
except:
    paises_sel = []

filtro_sql = f"AND origin_country IN ({str(paises_sel)[1:-1]})" if paises_sel else ""

# --- CARGA DE DATOS ---
try:
    df_now = con.execute(f"SELECT * FROM stg_flights WHERE is_latest = true {filtro_sql}").df()
    df_alerts = con.execute(f"SELECT * FROM fct_flight_alerts WHERE is_latest = true AND alert_level != 'Normal' {filtro_sql}").df()
except Exception:
    st.warning("⚠️ Sincronizando base de datos... Por favor, espera al primer ciclo de carga.")
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.title("✈️ Sistema de Monitorización y Análisis Aéreo")

if not df_now.empty:
    last_ts = pd.to_datetime(df_now['time_position'].max(), unit='s')
    st.caption(f"Último snapshot procesado: {last_ts} UTC")

st.divider()

# --- SECCIÓN 1: MÉTRICAS Y MAPA ---
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Aeronaves Activas", len(df_now))
with m2: st.metric("✈️ En Vuelo", len(df_now[df_now['on_ground'] == False]))
with m3: st.metric("地面 En Tierra", len(df_now[df_now['on_ground'] == True]))
with m4:
    vel_med = round(df_now[df_now['on_ground'] == False]['velocity_kmh'].mean(), 1) if not df_now.empty else 0
    st.metric("💨 Velocidad Media", f"{vel_med} km/h")

col_map, col_alerts = st.columns([2, 1])

with col_map:
    df_now['color_r'] = df_now['on_ground'].apply(lambda x: 255 if x else 0)
    df_now['color_g'] = 128
    df_now['color_b'] = df_now['on_ground'].apply(lambda x: 0 if x else 255)

    layer_puntos = pdk.Layer(
        "ScatterplotLayer",
        df_now,
        get_position='[longitude, latitude]',
        get_color='[color_r, color_g, color_b, 160]',
        get_radius=30000,
        pickable=True, 
    )

    event = st.pydeck_chart(
        pdk.Deck(
            layers=[layer_puntos], 
            initial_view_state=pdk.ViewState(
                latitude=df_now['latitude'].mean() if not df_now.empty else 40,
                longitude=df_now['longitude'].mean() if not df_now.empty else -3,
                zoom=2
            ),
            tooltip={"html": "<b>Vuelo:</b> {callsign} <br/> <b>País:</b> {origin_country}"}
        ),
        on_select="rerun",
        selection_mode="single-object"
    )

with col_alerts:
    st.subheader("⚠️ Alertas de Seguridad")
    if not df_alerts.empty:
        st.dataframe(df_alerts[['callsign', 'alert_level', 'velocity_kmh']], use_container_width=True, hide_index=True)
    else:
        st.success("No hay alertas críticas.")

st.divider()

# --- SECCIÓN 2: ANÁLISIS ---
st.header("📊 Análisis de Tráfico")
c1, c2 = st.columns(2)

with c1:
    st.subheader("🔝 Top 10 Países")
    # Agregamos y renombramos la columna para el gráfico
    df_paises = df_now.groupby('origin_country').size().reset_index(name='Vuelos')
    df_paises = df_paises.rename(columns={'origin_country': 'País de Origen'})
    df_paises = df_paises.sort_values('Vuelos', ascending=False).head(10)

    chart_paises = alt.Chart(df_paises).mark_bar(color="#1f77b4").encode(
        x=alt.X('País de Origen:N', sort='-y'),
        # axis=alt.Axis(format='d') asegura que la escala sea de números enteros
        y=alt.Y('Vuelos:Q', title="Nº de Vuelos", axis=alt.Axis(tickMinStep=1, format='d')),
        tooltip=['País de Origen', 'Vuelos']
    ).properties(height=500)
    st.altair_chart(chart_paises, use_container_width=True)

with c2:
    st.subheader("☁️ Perfil Vertical de la Atmósfera")
    if not df_now.empty:
        df_now['alt_low'] = (df_now['baro_altitude'] // 1000) * 1000
        df_actual = df_now.groupby('alt_low').size().reset_index(name='Aeronaves')
        
        cielo_completo = pd.DataFrame({'alt_low': [x * 1000 for x in range(16)]})
        df_cielo = pd.merge(cielo_completo, df_actual, on='alt_low', how='left').fillna(0)
        df_cielo['Rango'] = df_cielo['alt_low'].apply(lambda x: f"{int(x)}m - {int(x)+1000}m")

        chart_alt = alt.Chart(df_cielo).mark_bar(
            color="#4A90E2", 
            cornerRadiusTopRight=3,
            cornerRadiusBottomRight=3
        ).encode(
            y=alt.Y('Rango:N', 
                    sort=alt.EncodingSortField(field="alt_low", order="descending"), 
                    title="Altitud (Nivel del mar → Espacio)"),
            # axis=alt.Axis(format='d') evita que salgan 0.5, 1.5 aeronaves
            x=alt.X('Aeronaves:Q', 
                    title="Nº de Aeronaves", 
                    axis=alt.Axis(tickMinStep=1, format='d')),
            tooltip=['Rango', 'Aeronaves']
        ).properties(height=500)

        st.altair_chart(chart_alt, use_container_width=True)
        
# --- SECCIÓN 3: TRAYECTORIAS INCREMENTALES ---
st.divider()
st.header("🕵️ Rastreador de Trayectorias")

# Capturar selección del mapa
callsign_sel = ""
if event and event.selection and event.selection.get("objects"):
    obj = list(event.selection["objects"].values())[0]
    callsign_sel = obj[0].get("callsign", "")

vuelo_input = st.text_input("Introduce un Identificador (ej: IBE1234):", value=callsign_sel).upper()

if vuelo_input:
    # Consultamos la tabla fct_flight_tracks que ahora es INCREMENTAL
    df_track = con.execute(f"""
        SELECT latitude, longitude, baro_altitude, velocity_kmh, origin_country, time_position
        FROM fct_flight_tracks 
        WHERE callsign = '{vuelo_input}' 
        ORDER BY time_position ASC
    """).df()

    if not df_track.empty:
        c_v1, c_v2, c_v3 = st.columns(3)
        c_v1.metric("Puntos registrados", len(df_track))
        c_v2.metric("Altitud Actual", f"{int(df_track.iloc[-1]['baro_altitude'])} m")
        c_v3.metric("Velocidad", f"{round(df_track.iloc[-1]['velocity_kmh'], 1)} km/h")

        view_state = pdk.ViewState(latitude=df_track['latitude'].mean(), longitude=df_track['longitude'].mean(), zoom=5)
        
        # Capa de la línea de ruta
        path_layer = pdk.Layer(
            "PathLayer",
            [{"path": df_track[['longitude', 'latitude']].values.tolist()}],
            get_path="path",
            get_color=[0, 255, 128],
            get_width=3000,
        )
        
        # Capa del punto actual (avión)
        target_layer = pdk.Layer(
            "ScatterplotLayer",
            df_track.iloc[[-1]],
            get_position='[longitude, latitude]',
            get_color=[255, 255, 255],
            get_radius=10000,
        )

        st.pydeck_chart(pdk.Deck(layers=[path_layer, target_layer], initial_view_state=view_state))
    else:
        st.info("No hay historial acumulado para este vuelo todavía.")

con.close()
