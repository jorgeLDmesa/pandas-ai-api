FROM python:3.10

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar primero las dependencias base
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    numpy==1.23.5 \
    pandas==1.5.3 \
    matplotlib==3.5.3 \
    pyyaml==6.0.1 \
    beautifulsoup4==4.12.3 \
    python-multipart==0.0.9

# Luego instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p charts data

EXPOSE 5005
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.PandasAi:app", "--host", "0.0.0.0", "--port", "5005", "--reload"]