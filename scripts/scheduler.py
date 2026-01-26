import os
import sys
import time
import subprocess
from datetime import datetime

# Definir el intervalo (1800 segundos = 30 minutos)
INTERVALO_SEGUNDOS = 600  # 10 minutos 

def ejecutar_maestro():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    maestro_path = os.path.join(base_dir, "pipeline_maestro.py")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando orquestación...")
    
    # Ejecutar el pipeline maestro como un proceso externo
    resultado = subprocess.run([sys.executable, maestro_path])
    
    if resultado.returncode == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo completado con éxito.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] El pipeline maestro reportó un error.")

if __name__ == "__main__":
    print(f"--- Programador de Vuelos Activo ---")
    print(f"Ejecución configurada cada {INTERVALO_SEGUNDOS / 60} minutos.")
    
    try:
        while True:
            ejecutar_maestro()
            
            proxima = time.time() + INTERVALO_SEGUNDOS
            print(f"En Pausa. Próxima actualización a las: {datetime.fromtimestamp(proxima).strftime('%H:%M:%S')}")
            
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("\nDeteniendo el programador...")