# Real-Time Flight Traffic Radar & Data Pipeline

Este proyecto es un ecosistema completo de Ingeniería de Datos que captura, procesa y visualiza el tráfico aéreo mundial en tiempo real. Utiliza la API de **OpenSky Network** para la ingesta, **DuckDB** como motor analítico, **dbt** para la transformación de datos y **Streamlit** para la visualización interactiva.



## Funcionalidades 
- **Radar Live:** Mapa interactivo con tooltips detallados por avión.
- **Rastreador de Trayectorias:** Al hacer clic en un avión, el sistema dibuja su ruta histórica completa mediante una `PathLayer` de Pydeck.
- **Alertas Inteligentes:** Monitorización automática de anomalías con visualización de valores reales (ej: velocidad exacta o altitud extrema).
- **Arquitectura Medallion:** Transformaciones SQL modulares en dbt (Staging -> Marts).
- **Orquestación Autónoma:** Un programador (Scheduler) que ejecuta el pipeline maestro cada 30 minutos para acumular puntos de ruta.

##  Stack Tecnológico
- **Base de Datos:** DuckDB (OLAP de alto rendimiento)
- **Transformación:** dbt (data build tool)
- **Visualización:** Streamlit, Pydeck & Altair
- **Lenguaje:** Python 3.11
- **Infraestructura:** Docker & Docker Compose

##  Estructura del Proyecto
```text
├── dbt_flights/          # Modelos de dbt, tests y profiles
├── scripts/              # Lógica de Python corregida para rutas relativas
│   ├── obtain-data.py    # Ingesta desde OpenSky API
│   ├── pipeline_maestro.py # Orquestador Ingesta + dbt
│   ├── scheduler.py      # Programador de ejecuciones cíclicas
│   └── dashboard.py      # Interfaz de usuario y mapas
├── flights_history.duckdb # Base de datos unificada 
├── Dockerfile            # Configuración de imagen Docker
└── docker-compose.yml    # Orquestación de contenedores