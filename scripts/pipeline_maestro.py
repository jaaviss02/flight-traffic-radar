import subprocess
import os
import sys
import time
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))

def create_folders():
    folders = ["data/raw", "data/curated", "logs"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Directorio verificado: {folder}")

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
    """Ejecuta dbt localizando el ejecutable en las rutas de Codespaces y GitHub."""
    print("Iniciando transformaciones en dbt...")
    
    dbt_project_path = os.path.abspath(os.path.join(base_dir, "..", "dbt_flights"))
    
    # Lista de rutas donde dbt suele esconderse en la nube
    posibles_rutas = [
        "/home/codespace/.local/lib/python3.12/site-packages/bin/dbt", # La que encontraste
        "/home/runner/.local/bin/dbt",                                # GitHub Actions
        "dbt"                                                         # Path global
    ]
    
    dbt_exec = "dbt" 
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            dbt_exec = ruta
            break

    print(f"Usando dbt desde: {dbt_exec}")

    # Ejecutamos dbt deps primero para asegurar conectores
    subprocess.run([dbt_exec, "deps", "--profiles-dir", "."], cwd=dbt_project_path)

    # Ejecutamos el run
    result = subprocess.run(
        [dbt_exec, "run", "--profiles-dir", "."], 
        cwd=dbt_project_path, 
        capture_output=True, 
        text=True
    )
    
    if result.returncode == 0:
        print("dbt completado con éxito.")
        print(result.stdout)
    else:
        print("Error en dbt run:")
        print(result.stdout)
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
    create_folders()
    main()