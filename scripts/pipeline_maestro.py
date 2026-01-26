import subprocess
import os
import sys
import time
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))

def run_script(script_path):
    """Ejecuta un script de Python y espera a que termine."""
    print(f"Ejecutando: {script_path}...")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"{script_path} completado con éxito.")
    else:
        print(f"Error en {script_path}:")
        print(result.stderr)
        sys.exit(1)

def run_dbt():
    """Ejecuta los modelos de dbt."""
    print("Iniciando transformaciones en dbt...")
    # Cambiamos al directorio de dbt para ejecutarlo
    dbt_path = os.path.join(base_dir, "..", "dbt_flights")
    
    # Ejecutamos dbt run apuntando al perfil local
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", "."], 
        cwd=dbt_path, 
        capture_output=True, 
        text=True
    )
    
    if result.returncode == 0:
        print("dbt run completado exitosamente.")
        print(result.stdout)
    else:
        print("Error en dbt run:")
        print(result.stderr)
        sys.exit(1)

def main():
    start_time = datetime.now()
    print(f"--- Inicio del Pipeline: {start_time.strftime('%H:%M:%S')} ---")

    # 1. PASO: Ingesta de datos (descarga de API)
    # Ajusta el nombre exacto de tu script de descarga
    run_script("scripts/obtain-data.py") 

    # 2. PASO: Transformación con dbt
    run_dbt()

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"--- Pipeline finalizado con éxito en {duration.seconds}s ---")
    print("\nAhora puedes refrescar tu Dashboard de Streamlit.")

if __name__ == "__main__":
    main()