FROM python:3.11

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && \
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