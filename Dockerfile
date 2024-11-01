FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Actualizar pip e instalar wheel
RUN pip install --upgrade pip && \
    pip install --no-cache-dir wheel

# Instalar dependencias en orden específico para evitar conflictos
RUN pip install --no-cache-dir numpy==2.1.2 && \
    pip install --no-cache-dir pandas==1.5.3 && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p charts data

# Exponer el puerto
EXPOSE 5005

# Establecer PYTHONPATH
ENV PYTHONPATH=/app

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app.PandasAi:app", "--host", "0.0.0.0", "--port", "5005", "--reload"]