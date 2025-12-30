from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv
import cohere
import json
import pickle
import pandas as pd
import os
from urllib.parse import urlparse, parse_qs, quote_plus
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import random
import onnxruntime as ort
import numpy as np


load_dotenv() #leer el .env

api_key = os.getenv("COHERE_API_KEY")
user = os.getenv("MONGO_USERNAME")
pw = os.getenv("PASSWORD")

co = cohere.ClientV2(api_key=api_key)

app = Flask(__name__)

# Cargar el modelo ONNX
onnx_session = ort.InferenceSession(
    r"modelo\boosting_comedor.onnx",
    providers=["CPUExecutionProvider"]
)

# Tomamos el primer input y la primera salida del modelo ONNX
onnx_input_name = onnx_session.get_inputs()[0].name
onnx_output_name = onnx_session.get_outputs()[0].name

LABEL_TO_DEMAND = {
    1: "Muy baja",
    2: "Baja",
    3: "Normal",
    4: "Alta",
    5: "Crítica"
}

#Creamos la función para conectar a la base de datos
def get_db():

    username = quote_plus(user)
    password = quote_plus(pw)

    uri = f"mongodb+srv://{username}:{password}@clustersanti.etewqjo.mongodb.net/?appName=ClusterSanti"
    
    client = MongoClient(uri, server_api=ServerApi('1'))

    try:

        client.admin.command('ping')

        print("Conexión con MongoDB exitosa")

        return client['Comedor_Social']
    
    except Exception as e:

        print(f"Error conectando a MongoDB: {e}")

        raise

db = None

def post_mongo(features, demanda):
    collection = db['Predicciones']
    codigo = features["codigo_postal"]

    # Buscamos en la colección 'Municipios'
    datos_contexto = db["Municipios"].find_one({"Codigo_municipio": int(codigo)})

    if datos_contexto is None:
        datos_contexto = {} 
    
    doc = {
        "demanda": demanda,
        "codigo_postal": features["codigo_postal"],
        "municipio": features["municipio"],
        "temperatura": features["temperatura"],
        "habitantes": datos_contexto.get("Poblacion_total", 0),
        "renta_media": datos_contexto.get("Renta_media", 0),
        "paro_registrado": datos_contexto.get("Total_paro_registrado", 0)
    }
    collection.insert_one(doc)
    print("💾 Guardado en Mongo")

def predict_demand(codigo_postal, temperatura):
    """
    Busca datos socioeconómicos en Mongo usando el CP, añade la temperatura
    y ejecuta el modelo ONNX.
    
    Returns: 
        - prediction_str (str): Texto de la predicción (ej: "Alta")
        - full_features (dict): Diccionario con todos los datos usados (para mostrar en web)
        - error (str): Mensaje de error si falla algo, o None si todo va bien.
    """
    if db is None:
        return None, None, "Error: Base de datos no conectada."
    
    # Buscamos en la colección 'Municipios'
    datos_contexto = db["Municipios"].find_one({"Codigo_municipio": int(codigo_postal)})

    if not datos_contexto:
        return None, None, f"No se encontraron datos para el CP {codigo_postal}."
    
    x = np.array([[
        float(temperatura),
        float(datos_contexto.get("Prec_max_invierno", 0)),
        float(datos_contexto.get("Calidad_vida_media", 0)),
        float(datos_contexto.get("Poblacion_total", 0)),
        float(datos_contexto.get("Renta_media", 0)),
        float(datos_contexto.get("Total_paro_registrado", 0)),
        float(datos_contexto.get("Paro_hombre_menor_25", 0)),
        float(datos_contexto.get("Paro_hombre_25_45", 0)),
        float(datos_contexto.get("Paro_hombre_45+", 0)),
        float(datos_contexto.get("Paro_mujer_menor_25", 0)),
        float(datos_contexto.get("Paro_mujer_25_45", 0)),
        float(datos_contexto.get("Paro_mujer_45+", 0)),
        float(datos_contexto.get("Paro_agricultura", 0)),
        float(datos_contexto.get("Paro_industria", 0)),
        float(datos_contexto.get("Paro_construccion", 0)),
        float(datos_contexto.get("Paro_servicios", 0))
    ]], dtype=np.float32)

    # Ejecutar inferencia ONNX
    outputs = onnx_session.run([onnx_output_name], {onnx_input_name: x})

    # Normalmente la primera salida es la etiqueta predicha
    label_int = int(outputs[0][0])
    prediction_str = LABEL_TO_DEMAND.get(label_int, f"desconocida ({label_int})")
    
    return label_int, prediction_str, None

#Antes de que se procese cada petición en la app, nos conectamos a la base de datos
@app.before_request
def connect_db():

    global db

    if db is None:
        
        db = get_db()

@app.route('/')
def index():
    return "<h1>Comedor Social Valencia - Todo Ok</h1>"

@app.route('/predict', methods = ["GET", "POST"])
def predict():

    prediccion = ""
    features = None
    error_ms = None

    if request.method == "GET":
        # Mostramos la página vacía, sin procesar nada
        return render_template("predict.html", prediction=None, features=None)
    
    codigo_postal = request.form.get("codigo_postal")
    municipio = request.form.get("municipio")
    temperatura = request.form.get("temperatura")

    features = {"codigo_postal": codigo_postal, "temperatura": temperatura, "municipio": municipio}

    if not codigo_postal or not temperatura:
        error_ms = "Faltan datos."

    else:
        # Llamada limpia a la lógica
        label_int, demanda, error_ms = predict_demand(codigo_postal, temperatura)

        prediccion = (
                f"La demanda esperada es {demanda} (Clase {label_int}). "
                f"Los datos usados son: Código postal {codigo_postal}, "
                f"Municipio {municipio} y Temperatura {temperatura}."
            )
        
        post_mongo(features, demanda)
    
    return render_template("predict.html", prediction=prediccion, features=features, error=error_ms)

@app.route('/history', methods = ["GET"])
def history():

    if db is None:
        return "Error: Base de datos no conectada"
    
    # ordenar registros de 'predicciones'
    registros = list(db['Predicciones'].find({}).sort("codigo_postal",1))
    return render_template("history.html", records=registros)

if __name__ == "__main__":
    app.run(debug = True, host = "localhost", port  = 5000)