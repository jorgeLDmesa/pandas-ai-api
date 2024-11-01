from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Union, Dict
import os
import pandas as pd
import boto3
from pandasai import SmartDataframe
from pandasai.llm import OpenAI
from pandasai.helpers.openai_info import get_openai_callback
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="PandasAI API", description="API para análisis de datos con PandasAI")

# Configuración de API Key
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key")

class QueryRequest(BaseModel):
    queries: List[str]
    dataframe_url: str

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403,
        detail="Could not validate API Key"
    )

def configurar_aws():
    """Configura las credenciales de AWS"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )

def configurar_llm():
    """Configura el modelo de OpenAI"""
    return OpenAI(api_token=os.getenv('OPENAI_API_KEY'))

# def cargar_dataframe(ruta_archivo):
#     return pd.read_excel(ruta_archivo)

def configurar_smart_dataframe(df, llm, ruta_guardado):
    os.makedirs(ruta_guardado, exist_ok=True)
    return SmartDataframe(
        df, 
        config={
            "llm": llm,
            "conversational": False,
            "save_charts": True,
            "save_charts_path": ruta_guardado,
            "save_logs": False,
            "open_charts": False,
            "enable_cache": False
        },
    )

def subir_a_s3(archivo_local, bucket_name, s3_key):
    try:
        s3_client = configurar_aws()
        s3_client.upload_file(archivo_local, bucket_name, s3_key)
        print(f"Archivo {archivo_local} subido exitosamente a S3://{bucket_name}/{s3_key}")
        os.remove(archivo_local)
        return True
    except Exception as e:
        print(f"Error al subir archivo a S3: {str(e)}")
        return False

def procesar_consulta(sdf, consulta: str, bucket_name: str, ruta_charts: str) -> Dict:
    with get_openai_callback() as cb:
        respuesta = sdf.chat(consulta)
        
        # Si la respuesta es una ruta de archivo (gráfica)
        if isinstance(respuesta, str) and respuesta.startswith(ruta_charts):
            nombre_archivo = os.path.basename(respuesta)
            s3_key = f"graficas/{nombre_archivo}"
            
            # Subir a S3
            if subir_a_s3(respuesta, bucket_name, s3_key):
                # Construir URL de S3
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                return {
                    "type": "graph",
                    "url": s3_url,
                    "query": consulta,
                    "cost": f"${cb.total_cost:.6f}"
                }
        
        return {
            "type": "text",
            "content": str(respuesta),
            "query": consulta,
            "cost": f"${cb.total_cost:.6f}"
        }

@app.post("/analyze", response_model=List[Dict])
async def analyze_data(request: QueryRequest, api_key: str = Depends(get_api_key)):
    try:
        # Configuraciones desde variables de entorno
        # RUTA_ARCHIVO = os.getenv('RUTA_ARCHIVO')
        RUTA_GUARDADO = os.getenv('RUTA_CHARTS')
        BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
        
        # Inicialización
        llm = configurar_llm()
        # df = cargar_dataframe(RUTA_ARCHIVO)
        sdf = configurar_smart_dataframe(request.dataframe_url, llm, RUTA_GUARDADO)
        
        # Procesar todas las consultas
        resultados = []
        for query in request.queries:
            resultado = procesar_consulta(sdf, query, BUCKET_NAME, RUTA_GUARDADO)
            resultados.append(resultado)
            
        return resultados
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}