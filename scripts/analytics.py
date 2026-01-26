import duckdb
import os
import pandas as pd

def test_sql_suite():
    # Configuración de conexión
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, '..', 'flights_history.duckdb')
    con = duckdb.connect(db_path)

    # Diccionario de queries de prueba
    queries = {
        "1. TEST STAGING (Limpieza Básica)": """
            SELECT callsign, origin_country, velocity, (velocity * 3.6) as kmh 
            FROM main.stg_flights 
            WHERE velocity IS NOT NULL LIMIT 5
        """,
        
        "2. TEST TRAFFIC (Agregado por País)": """
            SELECT origin_country, COUNT(*) as total 
            FROM main.stg_flights 
            GROUP BY 1 ORDER BY 2 DESC LIMIT 5
        """,
        
        "3. TEST ALERTS (Lógica de Alertas)": """
            SELECT callsign, alert_level 
            FROM main.fct_flight_alerts 
            WHERE alert_level != 'Normal' LIMIT 5
        """,
        
        "4. EXPERIMENTAL (Densidad por Altitud)": """
            SELECT 
                floor(baro_altitude/5000)*5000 as piso, 
                count(*) as n_aviones 
            FROM main.stg_flights 
            GROUP BY 1 ORDER BY 1
        """
    }

    print("EJECUTANDO BATERÍA DE PRUEBAS SQL...")
    print("="*60)

    for nombre, sql in queries.items():
        try:
            print(f"\n{nombre}")
            df = con.execute(sql).df()
            if df.empty:
                print("Resultado vacío (Check: ¿Hay datos en los Parquets?)")
            else:
                print(df.to_string(index=False))
        except Exception as e:
            print(f"ERROR EN QUERY: {e}")
    
    print("\n" + "="*60)
    print("Pruebas finalizadas.")

if __name__ == "__main__":
    test_sql_suite()