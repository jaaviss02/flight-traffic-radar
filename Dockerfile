FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para dbt y DuckDB
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Exponer el puerto 8501 (usado por Streamlit por defecto)
EXPOSE 8501

# Por defecto, al arrancar el contenedor, lanzamos el Dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0"]