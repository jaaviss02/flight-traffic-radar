import requests
import pandas as pd
import os
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def run_pipeline():
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # INGESTA
    print("Obtención de los datos mediante la API...")
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url, verify = False)
    data = response.json()
    
    full_cols = [
        'icao24', 'callsign', 'origin_country', 'time_position', 
        'last_contact', 'longitude', 'latitude', 'baro_altitude', 
        'on_ground', 'velocity', 'true_track', 'vertical_rate', 
        'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
    ]
    
    df = pd.DataFrame(data['states'], columns=full_cols)
    df.to_parquet(f"data/raw/raw_flights_{timestamp_str}.parquet")
    print('Datos guardados correctamente en la carpeta raw')

    
    # TRANSFORMACIÓN
    print("Transformando los datos")

    df['callsign'] = df['callsign'].str.strip()
    
    # Aeronaves en el suelo deben tener altitud y velocidad cero
    df.loc[(df['on_ground'] == True) & (df['baro_altitude'].isna()), 'baro_altitude'] = 0
    df.loc[(df['on_ground'] == True) & (df['velocity'].isna()), 'velocity'] = 0
    
    # La altitud no puede ser negativa, viendo los datos podemos asumir un rango máximo razonable
    df['baro_altitude'] = df['baro_altitude'].clip(lower=0, upper=22000)

    # Limpieza de variables y nulos
    cols_to_drop = ['squawk', 'sensors', 'vertical_rate', 'geo_altitude']
    df_final = df.drop(columns=cols_to_drop).dropna(subset=['longitude', 'latitude'])
    
    # Añadir timestamp de extracción
    df_final['extracted_at'] = pd.to_datetime(data['time'], unit='s')

    # Guardar versión final de los datos en parquet
    os.makedirs("data/curated", exist_ok=True)
    file_path = f"data/curated/flights_{timestamp_str}.parquet"
    df_final.to_parquet(file_path, index=False)
    
    print(f"Pipeline finalizado. Archivo guardado: {file_path}")

if __name__ == "__main__":
    run_pipeline()