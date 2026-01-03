from urllib import response
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta, date
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

# leer el .env
load_dotenv()

# guardar las variables de entorno
api_key = os.getenv("COHERE_API_KEY")
user = os.getenv("MONGO_USERNAME")
pw = os.getenv("PASSWORD")

# conectar con Cohere
co = cohere.ClientV2(api_key=api_key)

app = Flask(__name__)

# función que genera una donación con Cohere
def get_donation():

    # prompt detallado para instruir a cohere
    prompt = """
    Eres un sistema de generación de donaciones para un comedor social.

    Tu tarea es generar UNA donación REALISTA que se insertará DIRECTAMENTE en un inventario existente.
    Debes RESPETAR ESTRICTAMENTE el formato indicado.
    NO expliques nada.
    NO incluyas texto adicional.
    DEVUELVE ÚNICAMENTE UN DICCIONARIO.

    ========================
    REGLAS GENERALES
    ========================
    - El producto DEBE EXISTIR en el catálogo proporcionado.
    - Usa exactamente uno de los productos disponibles.
    - Genera UN lote nuevo para ese producto.
    - Las fechas deben ser coherentes:
    - fecha_entrada = hoy
    - fecha_caducidad ≥ hoy + 30 días
    - Las unidades deben ser números enteros positivos razonables.
    - El donante puede ser anónimo o identificado.
    - No inventes campos.
    - No devuelvas listas, solo UN objeto.
    - El código de municipio DEBE SER VÁLIDO. Son de Valencia, España (a partir del 46001)

    =====================================
    CATÁLOGO DE PRODUCTOS Y SUS VARIANTES
    =====================================

    types_categories = {

            "CONSERVAS": ["en agua",
                        "en aceite",
                        "al natural",
                        "con salsa de tomate",
                        "bajo sodio",
                        "sin sal",
                        "en escabeche",
                        "vegetal",
                        "mixto"],

            "LEGUMBRES": ["secas",
                        "cocidas",
                        "integrales",
                        "partidas",
                        "precocidas"],

            "LÁCTEOS": ["enteros",
                        "desnatados",
                        "semidesnatados",
                        "sin lactosa",
                        "fortificada",
                        "en polvo" ],

            "CARNES": ["frescas",
                    "congeladas",
                        "refrigeradas",
                        "magro",
                        "procesado"],

            "PESCADOS": ["frescos",
                        "congelados",
                        "en conserva",
                        "refrigerados"],

            "FRUTAS Y VERDURAS": ["frescas",
                                "congeladas",
                                "en conserva",
                                "deshidratadas"],

            "PANADERÍA": ["integral",
                        "blanca",
                        "sin gluten",
                        "fortificada", 
                        "precocida"],

            "BEBIDAS": ["azucaradas",
                        "sin azúcar",
                        "naturales",
                        "con gas",
                        "fortificadas"],

            "ACEITES": ["oliva",
                        "girasol",
                        "maíz",
                        "coco",
                        "soja",
                        "mezcla"],

            "CEREALES": ["integrales",
                        "refinados",
                        "instantáneos",
                        "fortificados"],

            "OTROS": ["varios"]

        }

    ========================
    PRODUCTOS DISPONIBLES
    ========================
    {{PRODUCTOS_EXISTENTES}}

    {
    "nombre": "PESCADOS - Salmón congelados (1 x 1.0kg)",
    "categoria": "PESCADOS",
    "producto": "Salmón",
    "variante": "congelados",
    "formato": {
        "multipack": 1,
        "cantidad": 1,
        "unidad": "kg"
    },
    "lotes": [
        {
        "lote_id": "LOT-1-2026-SALMÓN-1",
        "fecha_entrada": {
            "$date": "2026-01-01T00:00:00.000Z"
        },
        "fecha_caducidad": {
            "$date": "2026-01-04T00:00:00.000Z"
        },
        "unidades": 1,
        "coste": 5.55
        }
    ],
    "stock_total": 1,
    "proxima_caducidad": {
        "$date": "2026-01-04T00:00:00.000Z"
    },
    "minimo_alerta": 1,
    "coste_total": 5.55,
    "audit": {
        "creado_en": {
        "$date": "2025-12-31T15:12:25.200Z"
        },
        "actualizado_en": {
        "$date": "2025-12-31T15:12:25.200Z"
        }
    },
    "Codigo_municipio": 46003
    }

    {
    "nombre": "CARNES - Lomo congeladas (1 x 2.0kg)",
    "categoria": "CARNES",
    "producto": "Lomo",
    "variante": "congeladas",
    "formato": {
        "multipack": 1,
        "cantidad": 2,
        "unidad": "kg"
    },
    "lotes": [
        {
        "lote_id": "LOT-12-2025-LOMO-1",
        "fecha_entrada": {
            "$date": "2025-12-31T00:00:00.000Z"
        },
        "fecha_caducidad": {
            "$date": "2026-01-29T00:00:00.000Z"
        },
        "unidades": 1,
        "coste": 5
        },
        {
        "fecha_entrada": {
            "$date": "2026-01-22T00:00:00.000Z"
        },
        "fecha_caducidad": {
            "$date": "2026-01-31T00:00:00.000Z"
        },
        "unidades": 9,
        "coste": 55
        }
    ],
    "stock_total": 10,
    "proxima_caducidad": {
        "$date": "2026-01-29T00:00:00.000Z"
    },
    "minimo_alerta": 1,
    "coste_total": 60,
    "audit": {
        "creado_en": {
        "$date": "2025-12-31T01:00:46.628Z"
        },
        "actualizado_en": {
        "$date": "2025-12-31T01:51:44.290Z"
        }
    },
    "Codigo_municipio": 46001
    }

    {
    "_id": {
        "$oid": "695477938b1f7ef5d23e3b01"
    },
    "nombre": "BEBIDAS - Coca Cola azucaradas (12 x 2.0L)",
    "categoria": "BEBIDAS",
    "producto": "Coca Cola",
    "variante": "azucaradas",
    "formato": {
        "multipack": 12,
        "cantidad": 2,
        "unidad": "L"
    },
    "lotes": [
        {
        "lote_id": "LOT-12-2025-COCA-1",
        "fecha_entrada": {
            "$date": "2025-12-31T00:00:00.000Z"
        },
        "fecha_caducidad": {
            "$date": "2026-03-27T00:00:00.000Z"
        },
        "unidades": 10,
        "coste": 45
        },
        {
        "lote_id": "LOT-1-2026-COCA-2",
        "fecha_entrada": {
            "$date": "2026-01-09T00:00:00.000Z"
        },
        "fecha_caducidad": {
            "$date": "2026-04-23T00:00:00.000Z"
        },
        "unidades": 32,
        "coste": 103
        }
    ],
    "stock_total": 42,
    "proxima_caducidad": {
        "$date": "2026-03-27T00:00:00.000Z"
    },
    "minimo_alerta": 1,
    "coste_total": 148,
    "audit": {
        "creado_en": {
        "$date": "2025-12-31T01:08:35.181Z"
        },
        "actualizado_en": {
        "$date": "2025-12-31T01:55:15.488Z"
        }
    },
    "Codigo_municipio": 46001
    }

    ========================
    FORMATO DE SALIDA (OBLIGATORIO)
    ========================

    {
    "producto": {
        "categoria": "...",
        "producto": "...",
        "variante": "...",
        "formato": {
        "multipack": 1,
        "cantidad": 0,
        "unidad": "..."
        },
        "minimo_alerta": 1,
        "Codigo_municipio": 46001
    },
    "lote": {
        "unidades": 0,
        "fecha_entrada": "YYYY-MM-DD",
        "fecha_caducidad": "YYYY-MM-DD",
        "origen": "donacion"
    },
    "donante": {
        "tipo": "anonimo | persona | organizacion",
        "nombre": "... o null",
        "contacto": "... o null"
    }
    }

    ========================
    NOTAS IMPORTANTES
    ========================
    - Si el donante es anónimo:
    - tipo = "anonimo"
    - nombre = null
    - contacto = null
    - Usa nombres humanos reales si no es anónimo.
    - Ajusta las unidades al tipo de producto (packs razonables).
    - Mantén coherencia semántica total.

    RESPONDE SOLO CON EL DICCIONARIO.
    """

    # envío del prompt a la ia y guardado de su respuesta
    response = co.chat(
    model="command-a-03-2025",
    messages=[{
        "role": "user",
        "content": {
            "type": "text",
            "text": prompt
        }
    }]
)

    return json.loads(response.message.content[0].text)


# carga del modelo ONNX
onnx_session = ort.InferenceSession(
    r"modelo\boosting_comedor.onnx",
    providers=["CPUExecutionProvider"]
)

# se toma el primer input y la primera salida del modelo ONNX
onnx_input_name = onnx_session.get_inputs()[0].name
onnx_output_name = onnx_session.get_outputs()[0].name

# mapeo de la variable demanda
LABEL_TO_DEMAND = {
    1: "Muy baja",
    2: "Baja",
    3: "Normal",
    4: "Alta",
    5: "Crítica"
}

# función para conectar a la base de datos MongoDB
def get_db():

    # guardado de usuario y contraseña
    username = quote_plus(user)
    password = quote_plus(pw)

    # definición de la uri de mongo
    uri = f"mongodb+srv://{username}:{password}@clustersanti.etewqjo.mongodb.net/?appName=ClusterSanti"
    
    # configuración del cliente
    client = MongoClient(uri, server_api=ServerApi('1'))

    try:

        # lanzamos un 'ping' para asegurar que la conexión es real
        client.admin.command('ping')

        print("Conexión con MongoDB exitosa")

        return client['Comedor_Social']
    
    except Exception as e:

        print(f"Error conectando a MongoDB: {e}")

        raise

db = None

# conversión de string a datetime
def parse_date(s):

            if not s:

                return None
            try:
                # conversión a formato ISO
                return datetime.fromisoformat(s)
            
            except Exception:

                try:
                    # conversión a formato corto
                    return datetime.strptime(s, '%Y-%m-%d')
                
                except Exception:

                    return None

# función para generar alertas               
def generar_alerta():

    # definición de las colecciones a usar
    collection_alert = db['Alertas']
    collection_inv = db['Inventario']
    collection_don = db['Donaciones']
    alertas = []

    inventario = collection_inv.find()
    existente_docs = list(collection_alert.find({}))


    try:
        ignored_docs = list(db['AlertasIgnoradas'].find({}))
    except Exception:
        ignored_docs = []

    donaciones = collection_don.find()

    # construcción de sets de referencias id existentes para evitar alertas duplicadas
    existing_inventario_ids = set([a.get('inventario_id') for a in existente_docs if a.get('inventario_id') is not None])
    existing_donacion_ids = set([a.get('donacion_id') for a in existente_docs if a.get('donacion_id') is not None])

    # ignorar las referencias de id
    ignored_inventario_ids = set([d.get('ref_id') for d in ignored_docs if d.get('tipo') == 'inventario' and d.get('ref_id') is not None])
    ignored_donacion_ids = set([d.get('ref_id') for d in ignored_docs if d.get('tipo') == 'donacion' and d.get('ref_id') is not None])

    for item in inventario:
        # si no hay stock o queda 1 en sotck y el producto no está en ninguna lista (de ids)
        if item.get('stock_total', 0) <= item.get('minimo_alerta', 1) and item.get('_id') not in existing_inventario_ids and item.get('_id') not in ignored_inventario_ids:

            # se crea y guarda una alerta en la lista de alertas
            alerta = {
                'inventario_id': item.get('_id'),
                'producto': item.get('producto'),
                'categoria': item.get('categoria'),
                'stock_total': item.get('stock_total', 0),
                'minimo_alerta': item.get('minimo_alerta', 1),
                'generado_en': datetime.utcnow()
            }

            alertas.append(alerta)

        # comprobar la próxima caducidad dentro de los próximos 7 días (manejar tipos date/datetime/strings)
        pd_raw = item.get('proxima_caducidad')

        pd_dt = None

        # normalización de pd_raw para asegurar que pd_dt sea datetime
        if pd_raw:
            # de string a datetime
            if isinstance(pd_raw, str):
                pd_dt = parse_date(pd_raw)
            # ya es datetime
            elif isinstance(pd_raw, datetime):
                pd_dt = pd_raw
            # de date (sin hora) a datetime
            elif isinstance(pd_raw, date):
                pd_dt = datetime(pd_raw.year, pd_raw.month, pd_raw.day)

        if pd_dt:

            pd_date = pd_dt.date()
            # comprobación de la caducidad del producto (entre hoy y los próximos 7 días)
            # y que la alerta no este activa
            if datetime.utcnow().date() <= pd_date <= (datetime.utcnow().date() + timedelta(days=7)) and item.get('_id') not in existing_inventario_ids and item.get('_id') not in ignored_inventario_ids:
                alerta = {
                    'inventario_id': item.get('_id'),
                    'producto': item.get('producto'),
                    'categoria': item.get('categoria'),
                    'proxima_caducidad': pd_dt,
                    'generado_en': datetime.utcnow()
                }
                alertas.append(alerta)

    # genración de notificaciones para las donaciones entrantes y no procesadas
    for don in donaciones:
        if don.get('_id') not in existing_donacion_ids and don.get('_id') not in ignored_donacion_ids:
            alerta = {
                'donacion_id': don.get('_id'),
                'producto': don.get('producto', {}).get('producto'),
                'lote_id': don.get('lote', {}).get('lote_id'),
                'unidades': don.get('lote', {}).get('unidades', 0),
                'procesado_en': don.get('procesado_en'),
                'generado_en': datetime.utcnow()
            }
            alertas.append(alerta)

    # si se ha generado alguna alerta las insertamos
    if alertas:
        try:
            collection_alert.insert_many(alertas)
        except Exception:
            # si la insercción falla
            pass

# función para procesar donaciones
def process_donation(donation):

    # colecciones a usar
    collection_inv = db['Inventario']
    collection_don = db['Donaciones']

    # información del producto, lote y donante de la donación a procesar
    producto_info = donation.get('producto', {})
    lote_info = donation.get('lote', {})
    donante_info = donation.get('donante', {})

    codigo = producto_info.get('Codigo_municipio')

    # chequeo de si el producto está ya en el inventario de ese municipio
    query = {'producto': producto_info.get('producto')}
    if codigo:
        query['Codigo_municipio'] = int(codigo)

    existing = collection_inv.find_one(query)

    # obtención de la información del lote (ponemos valores por defecto por si faltan datos)
    fecha_entrada = parse_date(lote_info.get('fecha_entrada')) or datetime.utcnow()
    fecha_cad = parse_date(lote_info.get('fecha_caducidad')) or (datetime.utcnow().date() + timedelta(days=30)).isoformat()
    unidades = int(lote_info.get('unidades', 0) or 0)
    coste = float(lote_info.get('coste', 0) or 0.0)

    year = fecha_entrada.year
    month = fecha_entrada.month
    lote_num = 1

    # generación de un id de lote 
    if existing and existing.get('lotes'):
        lote_num = len(existing.get('lotes', [])) + 1

    prod_short = (producto_info.get('producto') or 'ITEM').split()[0].upper()
    lote_id = lote_info.get('lote_id') or f"LOT-{month}-{year}-{prod_short}-{lote_num}"

    # información del lote a guardar
    lote_doc = {
        'lote_id': lote_id,
        'fecha_entrada': fecha_entrada,
        'fecha_caducidad': fecha_cad,
        'unidades': unidades,
        'coste': coste,
        'origen': lote_info.get('origen', 'donacion')
    }

    if existing:
        # si el producto existe actualizamos su stock y se añade al lote
        new_stock = existing.get('stock_total', 0) + unidades
        new_coste = existing.get('coste_total', 0.0) + coste

        # recálculo de su caducidad
        caducidades = [l.get('fecha_caducidad') for l in existing.get('lotes', []) if l.get('fecha_caducidad')]

        if fecha_cad:
            caducidades.append(fecha_cad)

        proxima = min(caducidades) if caducidades else None

        # adición del nuevo lote
        collection_inv.update_one(
            {'_id': existing.get('_id')},
            {
                '$push': {'lotes': lote_doc},
                '$set': {
                    'stock_total': new_stock,
                    'coste_total': new_coste,
                    'proxima_caducidad': proxima,
                    'audit.actualizado_en': datetime.utcnow()
                }
            }
        )

        inv_id = existing.get('_id')

    else:
        # si el producto no existe lo creamos
        new_doc = {
            'nombre': f"{producto_info.get('categoria','')} - {producto_info.get('producto','')} {producto_info.get('variante','')} ({producto_info.get('formato',{}).get('multipack',1)} x {producto_info.get('formato',{}).get('cantidad',0)}{producto_info.get('formato',{}).get('unidad','')})",
            'categoria': producto_info.get('categoria'),
            'producto': producto_info.get('producto'),
            'variante': producto_info.get('variante'),
            'Codigo_municipio': int(codigo) if codigo else None,
            'formato': producto_info.get('formato', {}),
            'lotes': [lote_doc],
            'stock_total': unidades,
            'proxima_caducidad': fecha_cad,
            'minimo_alerta': producto_info.get('minimo_alerta', 1),
            'coste_total': coste,
            'audit': {
                'creado_en': datetime.utcnow(),
                'actualizado_en': datetime.utcnow()
            }
        }
        res = collection_inv.insert_one(new_doc)
        inv_id = res.inserted_id

    # inserción de la donación
    donation_record = {
        'producto': producto_info,
        'lote': lote_doc,
        'donante': donante_info,
        'procesado_en': datetime.utcnow(),
        'mostrar': True,
        'inventario_id': inv_id
    }

    collection_don.insert_one(donation_record)

    return donation_record

# función que simula la entrada de una donación nueva
def simulate_donation_from_inventory():
    # colección a usar
    collection_inv = db['Inventario']

    try:
        # agregación de Mongo
        doc = collection_inv.aggregate([{'$sample': {'size': 1}}])
        doc = list(doc)

        if not doc:

            return None
        
        item = doc[0]

    except Exception:
        # se selecciona un item random si algo falla
        items = list(collection_inv.find({}))

        if not items:

            return None
        
        item = random.choice(items)

    # generación de fechas y unidades
    today = datetime.utcnow()
    days = random.randint(30, 365)
    fecha_cad = (today + timedelta(days=days)).date().isoformat()
    unidades = random.randint(1, max(1, int(item.get('formato', {}).get('multipack', 1) * 5)))

    # estructura de la donación
    donation = {
        'producto': {
            'categoria': item.get('categoria'),
            'producto': item.get('producto'),
            'variante': item.get('variante'),
            'formato': item.get('formato'),
            'minimo_alerta': item.get('minimo_alerta', 1),
            'Codigo_municipio': item.get('Codigo_municipio')
        },
        'lote': {
            'unidades': unidades,
            'fecha_entrada': today.date().isoformat(),
            'fecha_caducidad': fecha_cad,
            'origen': 'donacion'
        },
        'donante': {
            'tipo': random.choice(['anonimo', 'persona', 'organizacion']),
            'nombre': None,
            'contacto': None
        }
    }

    # relleno con nombres ficticios
    if donation['donante']['tipo'] == 'persona':
        names = ['Ana Garcia','Luis Martínez','María López','Carlos Sánchez','Sonia Ruiz']
        donation['donante']['nombre'] = random.choice(names)
        donation['donante']['contacto'] = f"{donation['donante']['nombre'].split()[0].lower()}@example.com"
    elif donation['donante']['tipo'] == 'organizacion':
        orgs = ['Banco de Alimentos Valencia','Empresa Solidaria SL','Asociación Voluntarios']
        donation['donante']['nombre'] = random.choice(orgs)

    return donation

# función para insertar en mongo las predicciones
def post_mongo(features, demanda):
    # colección en la que insertar
    collection = db['Predicciones']
    # código postal en el que insertar
    codigo = features["codigo_postal"]

    # búsqueda del código postal en la colección 'Municipios'
    datos_contexto = db["Municipios"].find_one({"Codigo_municipio": int(codigo)})

    if datos_contexto is None:
        datos_contexto = {} 
    
    # predicción a insertar (con la población, renta y paro del municipio)
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

# función para predecir la demanda esperada
def predict_demand(codigo_postal, temperatura):

    if db is None:
        return None, None, "Error: Base de datos no conectada."
    
    # búsqueda del código postal en la colección 'Municipios'
    datos_contexto = db["Municipios"].find_one({"Codigo_municipio": int(codigo_postal)})

    if not datos_contexto:
        return None, None, f"No se encontraron datos para el CP {codigo_postal}."
    
    # datos en float a usar para la predicción
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

    # ejecución del modelo ONNX
    outputs = onnx_session.run([onnx_output_name], {onnx_input_name: x})

    # normalmente la primera salida es la etiqueta predicha
    label_int = int(outputs[0][0])
    prediction_str = LABEL_TO_DEMAND.get(label_int, f"desconocida ({label_int})")
    
    return label_int, prediction_str, None

# función que crea un menú del día usando Cohere
def ai_chef(inventario, donaciones, demanda):

    # conversión de los diccionarios a string
    inventario_texto = json.dumps(inventario, indent=2, ensure_ascii=False, default=str)
    donaciones_texto = json.dumps(donaciones, indent=2, ensure_ascii=False)

    # prompt detallado para instruir a la IA
    prompt = f"""Actúa como un Chef Ejecutivo y experto en logística de alimentos para un comedor 
    social benéfico. Tu objetivo es diseñar un menú diario nutritivo, reconfortante y eficiente, 
    minimizando el desperdicio de alimentos.

    Te voy a proporcionar tres datos:
    1. INVENTARIO: Alimentos que ya tenemos almacenados (secos, latas, congelados).
    2. DONACIONES DEL DÍA: Alimentos frescos o perecederos que acaban de llegar.
    3. DEMANDA: la demanda que se espera que haya en el comedor (demanda muy baja, baja, normal, alta o crítica).

    Tus instrucciones son:
    - PRIORIDAD 1: Usa primero los productos cerca de vencer.
    - PRIORIDAD 2: Completa los platos con otros productos del inventario.
    - El menú debe constar de: Entrante/Primer plato, Plato Principal y Postre/Fruta.
    - Calcula las cantidades totales necesarias para cocinar para la demanda indicada.
    - Si faltan ingredientes críticos para una receta lógica, sugiere el sustituto más cercano del inventario.
    
    DATOS DE HOY:
    
    [INVENTARIO]
    {inventario_texto}

    [DONACIONES DEL DÍA]
    {donaciones_texto}

    [DEMANDA]
    {demanda}
    ---
    Genera la respuesta con el siguiente formato:

    ### 🍽️ MENÚ DEL DÍA PROPUESTO
    * **Primer Plato:** [Nombre del plato]
    * **Segundo Plato:** [Nombre del plato]
    * **Postre:** [Nombre del plato]
    * **Acompañamiento:** [Pan, bebida, etc.]

    ### 💡 JUSTIFICACIÓN DE APROVECHAMIENTO
    Explicación breve de por qué has elegido estos platos basándote en los productos perecederos o cerca de su vencimiento.

    ### 📝 LISTA DE PRODUCCIÓN (CANTIDADES A COCINAR)
    | Ingrediente | Origen (Donación/Inventario) | Cantidad por persona (aprox) | CANTIDAD TOTAL A USAR |
    |---|---|---|---|
    | [Ingrediente 1] | [Origen] | [gr/ml] | [Total Kg/L] |
    | [Ingrediente 2] | [Origen] | [gr/ml] | [Total Kg/L] |
    ..."""

    try: 
        # envío del prompt a la ia y guardado de su respuesta
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        return response.message.content[0].text

    except Exception as e:
        
        print(f"Error generando el menú: {e}")
        return f"<h3>Ocurrió un error al generar el menú:</h3><p>{str(e)}</p>"
    
# función que genera una campaña publicitaria con Cohere
def ai_campaign(inventario):

    # conversión del diccionario a string
    inventario_texto = json.dumps(inventario, indent=2, ensure_ascii=False, default=str)

    # prompt detallado para la IA
    prompt = f"""Actúa como un Director de Marketing experto en campañas sociales y ONGs.
    Tu objetivo es crear una campaña publicitaria de alto impacto para incentivar la donación 
    de una categoría específica de alimentos que es crítica ahora mismo en nuestro inventario.

    CONTEXTO:
    La gente suele donar siempre lo mismo (arroz, pasta, legumbres secas). Estamos muy agradecidos, 
    pero tenemos un exceso de carbohidratos y una carencia crítica de nutrientes esenciales o 
    productos básicos específicos. Necesitamos educar al donante para que su ayuda sea más efectiva.

    TU TAREA:
    Analiza el inventario y detecta qué **Categoría Esencial** está AUSENTE o es MUY ESCASA.
    No te centres en lo que va a caducar. Céntrate en lo que FALTA para una dieta digna.

    LISTA DE CONTROL (Prioridad de búsqueda):
    1. Proteínas (Huevos, Carne, Pescado, Legumbres).
    2. Lácteos y Calcio (Leche, Yogur, Queso).
    3. Grasas Saludables (Aceite de Oliva, Aceite de Girasol).
    4. Hidratación/Básicos (Agua, Leche en polvo).
    5. Vitaminas (Fruta fresca, Verdura fresca).

    INVENTARIO ACTUAL:
    {inventario_texto}

    PÚBLICO OBJETIVO:
    Vecinos del barrio, familias jóvenes y comercio local.

    INSTRUCCIONES:
    1. Compara el inventario con la lista de control.
    2. Si hay mucho carbohidrato (arroz/pasta) pero falta leche, huevos o aceite, TU ELECCIÓN DEBE SER EL PRODUCTO FALTANTE.
    3. Genera el contenido para un anuncio visual de Instagram.

    FORMATO DE RESPUESTA (Solo JSON válido, nada más):
    {{
        "producto_heroe": "Nombre del producto faltante (ej: Leche)",
        "slogan": "Frase impactante de 5 palabras máximo",
        "mensaje_principal": "Texto breve (2 frases) explicando el porque es importante que se done el producto faltante.",
        "color_fondo": "Código Hexadecimal que represente la emoción o el producto (ej: #FFFFFF para leche, #FFD700 para aceite)",
        "emoji_icono": "Un solo emoji que represente el producto (ej: 🥛, 🥚, 💧)"
    }}"""

    try: 
        # envío del promt a la IA y guardado de su respuesta
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=
            [
                {
                    "role": "user",
                    "content": 
                    [
                        {
                            "type": "text", 
                            "text": prompt
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"} # Forzamos modo JSON
        )

        texto_crudo = response.message.content[0].text

        # a veces la IA pone ```json al principio, por lo que se elimina
        texto_limpio = texto_crudo.replace("```json", "").replace("```", "").strip()
        
        # conversión del texto a diccionario
        datos_anuncio = json.loads(texto_limpio)

        return datos_anuncio
    
    except json.JSONDecodeError as e:
        print(f"ERROR JSON: La IA no devolvió un JSON válido.\nError: {e}")
        # devolvemos un producto para que se vea algo
        return {
            "producto_heroe": "Alimentos Frescos",
            "slogan": "Dona fresco, dona mejor",
            "mensaje_principal": "Los alimentos frescos como la fruta son esenciales para una dieta equilibrada.",
            "color_fondo": "#FF5733",
            "emoji_icono": "🐛"
        }
        
    except Exception as e:
        print(f"ERROR GENERAL: {e}")
        return {
            "producto_heroe": "Ayuda General",
            "slogan": "Dona lo que puedas",
            "mensaje_principal": "Cualquier donación es buena, aporta tu grano de arena.",
            "color_fondo": "#4CAF50",
            "emoji_icono": "❤️"
        }

# antes de que se procese cada petición en la app, nos conectamos a la base de datos
@app.before_request
def connect_db():

    global db

    if db is None:
        
        db = get_db()

# para que 'total_alertas' esté disponible en todos los html sin que haya que escribirlo en cada ruta
@app.context_processor
def inject_alerts():
    # 0 si la base de datos es None
    if db is None:
        return {'total_alertas': 0}
    
    try:
        count = db['Alertas'].count_documents({})
        return {'total_alertas': count}
    except Exception:
        return {'total_alertas': 0}

# ruta principal
@app.route('/')
def index():
    # conteo de alertas para las notificaciones
    collection_alert = db['Alertas']
    total_alertas = collection_alert.count_documents({})

    # simulación de donación cada vez que se carga el home
    choice =  random.randint(0, 1)
    if choice == 1:

        try:
            # obtención de una donación real (si la hay)
            record = get_donation()
        
        except Exception:
            # simulamos la donación si no hay una real
            record = simulate_donation_from_inventory()

    else:
        # simulamos una donación
        record = simulate_donation_from_inventory()

    # procesado de la donación y generación de alerta
    process_donation(record)
    generar_alerta()

    return render_template('index.html', total_alertas=total_alertas)

# ruta para las donaciones
@app.route('/donacion', methods=['GET'])
def donacion():
    # listamos todas las donaciones y las devolvemos
    collection = db['Donaciones']
    donations = list(collection.find({}))

    if not donations:
        return "<h1 style='color:red'>No hay donaciones registradas</h1>"

    for don in donations:
        don['id'] = str(don.get('_id'))

    return render_template('donaciones.html', donations=donations)

# ruta para el inventario
@app.route('/inventario', methods=['GET', 'POST'])
def inventario():

    collection = db['Inventario']
    
    selected_codigo = request.values.get('codigo', '')

    # carga de los municipios para rellenas el selector del html
    municipios = []
    try:
        municipios_col = db['Municipios']

        docs = list(municipios_col.find({}))

        for d in docs:

            code = d.get('Codigo_municipio')
            name = d.get('Municipios')

            if code:
                municipios.append({'code': str(code), 'name': name})

    except Exception:
        municipios = []

    # si hay código postal, se muestran unos pocos items para el municipio
    if selected_codigo:

        items = list(collection.find({'Codigo_municipio': int(selected_codigo)}))

    else:
        items = []

    for it in items:
        it['id'] = str(it.get('_id'))

    return render_template('inventario.html', items=items, municipios=municipios, selected_codigo=selected_codigo)

# ruta para crear un producto en el inventario
@app.route('/inventario/crear_producto', methods=['GET', 'POST'])
def crear_producto():

    collection = db['Inventario']

    # categorías a las que puede pertenecer el producto
    types_categories = {

        "CONSERVAS": ["en agua",
                      "en aceite",
                      "al natural",
                      "con salsa de tomate",
                      "bajo sodio",
                      "sin sal",
                      "en escabeche",
                      "vegetal",
                      "mixto"],

        "LEGUMBRES": ["secas",
                    "cocidas",
                    "integrales",
                    "partidas",
                    "precocidas"],

        "LÁCTEOS": ["enteros",
                    "desnatados",
                    "semidesnatados",
                    "sin lactosa",
                    "fortificada",
                    "en polvo" ],

        "CARNES": ["frescas",
                   "congeladas",
                    "refrigeradas",
                    "magro",
                    "procesado"],

        "PESCADOS": ["frescos",
                     "congelados",
                     "en conserva",
                     "refrigerados"],

        "FRUTAS Y VERDURAS": ["frescas",
                              "congeladas",
                              "en conserva",
                              "deshidratadas"],

        "PANADERÍA": ["integral",
                      "blanca",
                      "sin gluten",
                      "fortificada", 
                      "precocida"],

        "BEBIDAS": ["azucaradas",
                    "sin azúcar",
                    "naturales",
                    "con gas",
                    "fortificadas"],

        "ACEITES": ["oliva",
                    "girasol",
                    "maíz",
                    "coco",
                    "soja",
                    "mezcla"],

        "CEREALES": ["integrales",
                     "refinados",
                     "instantáneos",
                     "fortificados"],

        "OTROS": ["varios"]

    }

    categories = list(types_categories.keys())
    units = ['g', 'kg', 'ml', 'L']

    # guardar los filtros si hay
    category = request.values.get('category', '')
    unit = request.values.get('unit', '')
    type_category = types_categories.get(category, []) if category else []

    # obtener lista de municipios para el selector
    municipios = []
    try:
        municipios_col = db['Municipios']
        docs = list(municipios_col.find({}))
        for d in docs:
            code = d.get('Codigo_municipio') or d.get('codigo_municipio') or d.get('codigo') or d.get('postal_code')
            name = d.get('nombre') or d.get('Municipios') or d.get('name') or code
            if code:
                municipios.append({'code': str(code), 'name': name})
    except Exception:
        municipios = []


    if request.method == 'POST':
        # obtención del nombre y variante del producto
        item_name = request.form.get('item_name', '').strip()
        variante = request.form.get('variante', '').strip()

        # conversión a string
        try:
            multipack = int(request.form.get('multipack', 1))
        except (ValueError, TypeError):
            multipack = 1

        try:
            formato_cantidad = float(request.form.get('formato_cantidad', 0))
        except (ValueError, TypeError):
            formato_cantidad = 0

        formato_unidad = request.form.get('formato_unidad', unit or request.form.get('formato_unidad', '')).strip()

        # gestión de las fechas
        fecha_entrada_raw = request.form.get('fecha_entrada', '').strip()
        fecha_cad_raw = request.form.get('fecha_caducidad', '').strip()

        try:
            lote_unidades = int(request.form.get('lote_unidades', 0))
        except (ValueError, TypeError):
            lote_unidades = 0

        try:
            coste = float(request.form.get('coste', 0.0))
        except (ValueError, TypeError):
            coste = 0.0

        fecha_entrada = parse_date(fecha_entrada_raw)
        fecha_caducidad = parse_date(fecha_cad_raw)

        year = fecha_entrada.year if fecha_entrada else 'XXXX'
        month = fecha_entrada.month if fecha_entrada else 'XX'

        # verificación de la existencia de los lotes para el producto
        existing = collection.find_one({'producto': item_name})
        if not existing or not existing.get('lotes'):
            lote_num = 1
        else:
            lote_num = len(existing.get('lotes', [])) + 1

        lote_id = f"LOT-{month}-{year}-{item_name.split()[0].upper()}-{lote_num}"

        lotes = []

        # creación del lote
        if lote_id or lote_unidades or fecha_entrada or fecha_caducidad:

            lote_doc = {
                'lote_id': lote_id or None,
                'fecha_entrada': fecha_entrada,
                'fecha_caducidad': fecha_caducidad,
                'unidades': lote_unidades,
                'coste': coste
            }

            lotes.append(lote_doc)

        # cálculo del stock total
        stock_total = sum([l.get('unidades', 0) for l in lotes])

        # cálculo de la fecha de caducidad mínima
        cad_dates = [l.get('fecha_caducidad') for l in lotes if l.get('fecha_caducidad')]
        proxima_caducidad = min(cad_dates) if cad_dates else None

        coste_total = sum([l.get('coste', 0.0) for l in lotes])

        nombre = f"{category} - {item_name} {variante} ({multipack} x {formato_cantidad}{formato_unidad})"

        codigo_municipio = request.form.get('codigo_municipio') or request.values.get('codigo') or None

        # fallback: si no hay cp se intenta leer del referer
        if not codigo_municipio:
            ref = request.headers.get('Referer') or request.referrer
            if ref:
                try:
                    parsed = urlparse(ref)
                    qs = parse_qs(parsed.query)
                    if 'codigo' in qs and qs['codigo']:
                        codigo_municipio = qs['codigo'][0]
                except Exception:
                    pass

        # validación del municipio dado
        if not codigo_municipio:
            error = 'Debe seleccionar un Código postal / Municipio antes de crear el producto.'
            return render_template('crear_item.html', categories=categories, type_category=type_category, selected_category=category, units=units, selected_unit=unit, municipios=municipios, selected_codigo='', error_message=error)

        # crear el producto
        new_doc = {
            'nombre': nombre,
            'categoria': category,
            'producto': item_name,
            'variante': variante,
            'Codigo_municipio': int(codigo_municipio),
            'formato': {
                'multipack': multipack,
                'cantidad': formato_cantidad,
                'unidad': formato_unidad
            },
            'lotes': lotes,
            'stock_total': stock_total,
            'proxima_caducidad': proxima_caducidad,
            'minimo_alerta': 1,
            'coste_total': coste_total,
            'audit': {
                'creado_en': datetime.utcnow(),
                'actualizado_en': datetime.utcnow()
            }
        }

        collection.insert_one(new_doc)

        return redirect(url_for('inventario', codigo=codigo_municipio) if codigo_municipio else url_for('inventario'))
    
    selected_codigo = request.values.get('codigo', '')
    return render_template('crear_item.html', categories=categories, type_category=type_category, selected_category=category, units=units, selected_unit=unit, selected_codigo=selected_codigo, municipios=municipios)

# ruta para crear un lote para un producto existente
@app.route('/inventario/crear_lote/<string:item_id>', methods=['GET', 'POST'])
def crear_lote(item_id):

    collection = db['Inventario']

    # validación de la existencia del producto
    item = collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        return f"<h1 style='color:red'>Item no encontrado</h1>"

    if request.method == 'POST':
        # obtención de los datos del formulario
        fecha_entrada_raw = request.form.get('fecha_entrada', '').strip()
        fecha_cad_raw = request.form.get('fecha_caducidad', '').strip()

        try:
            lote_unidades = int(request.form.get('lote_unidades', 0))
        except (ValueError, TypeError):
            lote_unidades = 0

        try:
            coste = float(request.form.get('coste', 0.0))
        except (ValueError, TypeError):
            coste = 0.0

        fecha_entrada = parse_date(fecha_entrada_raw)
        fecha_caducidad = parse_date(fecha_cad_raw)

        year = fecha_entrada.year if fecha_entrada else 'XXXX'
        month = fecha_entrada.month if fecha_entrada else 'XX'

        # genración del id del lote
        existing = collection.find_one({'_id': ObjectId(item_id)})

        if not existing or not existing.get('lotes'):
            lote_num = 1
        else:
            lote_num = len(existing.get('lotes', [])) + 1

        lote_id = f"LOT-{month}-{year}-{item.get('producto','').split()[0].upper()}-{lote_num}"

        lote_doc = {
            'lote_id': lote_id or None,
            'fecha_entrada': fecha_entrada,
            'fecha_caducidad': fecha_caducidad,
            'unidades': lote_unidades,
            'coste': coste
        }

        # adición del nuevo coste/stock/caducidad al producto
        coste_total = item.get('coste_total', 0.0) + coste
        stock_total = item.get('stock_total', 0) + lote_unidades
        caducidad = [l.get('fecha_caducidad') for l in item.get('lotes', []) if l.get('fecha_caducidad')]

        # recálculo de la fecha de caducidad
        if fecha_caducidad:
            caducidad.append(fecha_caducidad)
        proxima_caducidad = min(caducidad) if caducidad else None

        collection.update_one(
            {'_id': ObjectId(item_id)},
            {
                '$push': {'lotes': lote_doc},
                '$set': {
                    'audit.actualizado_en': datetime.utcnow(),
                    'coste_total': coste_total,
                    'stock_total': stock_total,
                    'proxima_caducidad': proxima_caducidad
                }
            }
        )

        return redirect(url_for('inventario', codigo=item.get('codigo_municipio')))

    return render_template('crear_lote.html', item=item)

# ruta para ver los lotes de un producto
@app.route('/inventario/ver_lotes/<string:item_id>', methods=['GET'])
def ver_lotes(item_id):

    collection = db['Inventario']

    # comprobación de que el producto existe
    item = collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        return f"<h1 style='color:red'>Item no encontrado</h1>"

    lotes = item.get('lotes', [])

    return render_template('ver_lotes.html', item=item, lotes=lotes)

# ruta para editar los lotes de un producto
@app.route('/inventario/editar_lote/<string:item_id>', methods=['GET', 'POST'])
def editar_lote(item_id):

    collection = db['Inventario']

    item = collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        return f"<h1 style='color:red'>Item no encontrado</h1>"

    lotes = item.get('lotes', [])

    if request.method == 'POST':

        # iteración sobre los lotes que existen
        for index, lote in enumerate(lotes):
            # obtención de las fechas por índice
            fecha_entrada_raw = request.form.get(f'fecha_entrada_{index}', '').strip()
            fecha_cad_raw = request.form.get(f'fecha_caducidad_{index}', '').strip()

            try:
                lote_unidades = int(request.form.get(f'lote_unidades_{index}', 0))
            except (ValueError, TypeError):
                lote_unidades = 0

            try:
                coste = float(request.form.get(f'coste_{index}', 0.0))
            except (ValueError, TypeError):
                coste = 0.0

            fecha_entrada = parse_date(fecha_entrada_raw)
            fecha_caducidad = parse_date(fecha_cad_raw)

            # actualización varios campos del lote 
            lotes[index]['fecha_entrada'] = fecha_entrada
            lotes[index]['fecha_caducidad'] = fecha_caducidad
            lotes[index]['unidades'] = lote_unidades
            lotes[index]['coste'] = coste

        # actualizar el lote
        collection.update_one(
            {'_id': ObjectId(item_id)},
            {
                '$set': {
                    'lotes': lotes,
                    'audit.actualizado_en': datetime.utcnow()
                }
            }
        )

        return redirect(url_for('inventario', codigo=item.get('codigo_municipio')))

    return render_template('editar_lote.html', item=item, lotes=lotes)

# ruta para la predicción de demanda
@app.route('/predict', methods = ["GET", "POST"])
def predict():

    prediccion = ""
    features = None
    error_ms = None

    if request.method == "GET":
        # mostramos la página vacía, sin procesar nada
        return render_template("predict.html", prediction=None, features=None)
    
    # obtención del cp/municipio/temperatura
    codigo_postal = request.form.get("codigo_postal")
    municipio = request.form.get("municipio")
    temperatura = request.form.get("temperatura")

    # características a usar
    features = {"codigo_postal": codigo_postal, "temperatura": temperatura, "municipio": municipio}

    if not codigo_postal or not temperatura:
        error_ms = "Faltan datos."

    else:
        # llamada a la función
        label_int, demanda, error_ms = predict_demand(codigo_postal, temperatura)

        prediccion = (
                f"La demanda esperada es {demanda} (Clase {label_int}). "
                f"Los datos usados son: Código postal {codigo_postal}, "
                f"Municipio {municipio} y Temperatura {temperatura}."
            )
        
        # inserción de la predicción en mongo
        post_mongo(features, demanda)
    
    return render_template("predict.html", prediction=prediccion, features=features, error=error_ms)

# ruta para ver el historial
@app.route('/history', methods = ["GET"])
def history():

    if db is None:
        return "Error: Base de datos no conectada"
    
    # ordenar los registros de 'predicciones'
    registros = list(db['Predicciones'].find({}).sort("codigo_postal",1))
    
    return render_template("history.html", records=registros)

# ruta para ver las alertas
@app.route('/alertas', methods = ["GET"])
def alertas():

    # (re)generar las alertas primero para que la lista este actualizada
    generar_alerta()

    registros = list(db['Alertas'].find({}).sort("generado_en", -1))
    for r in registros:
        r['id'] = str(r.get('_id'))

    return render_template("alertas.html", records=registros)

# ruta para eliminar una alerta 
@app.route('/alertas/delete/<string:alert_id>', methods=['POST'])
def delete_alert(alert_id):

    collection_alert = db['Alertas']
    collection_ignored = db['AlertasIgnoradas']

    try:
        alert_doc = collection_alert.find_one({'_id': ObjectId(alert_id)})
        if alert_doc:
            # guardado de la eliminación para que la alerta no se recree
            if alert_doc.get('donacion_id'):
                collection_ignored.insert_one({'tipo': 'donacion', 'ref_id': alert_doc.get('donacion_id'), 'created_at': datetime.utcnow()})
            if alert_doc.get('inventario_id'):
                collection_ignored.insert_one({'tipo': 'inventario', 'ref_id': alert_doc.get('inventario_id'), 'created_at': datetime.utcnow()})
        
        # eliminación de la alerta
        collection_alert.delete_one({'_id': ObjectId(alert_id)})
    except Exception:
        pass

    return redirect(url_for('alertas'))

# ruta para ver las estadísticas
@app.route('/stats', methods = ["GET"])
def stats():
    # agregar predicciones por codigo postal
    pipeline_pred = [
        {"$group": 
        {  
            "_id": "$codigo_postal",  # agrupar por cp
            "num_predicciones":{"$sum":1}   # suma numero de pred
        }},
        {"$project": 
        {  
            "_id":0,  # ocular id mongo
            "codigo_postal":"$_id",  
            "num_predicciones":1
        }},
        {"$sort":{"num_predicciones":-1}}  # ordenar desc
    ]
    pred_por_cp = list(db["Predicciones"].aggregate(pipeline_pred))  

    # agregar donaciones por municipio
    pipeline_don = [
        {"$unwind": "$lote"},  # descomponer array lote para acceder a unidades
        {"$group":
        {  
            "_id": "$producto.Codigo_municipio",  
            "total_unidades":{"$sum":"$lote.unidades"}  # sumar unidades donada
        }},
        {"$project":{
            "_id":0,
            "municipio":"$_id",
            "total_unidades":1
        }},
        {"$sort": {"total_unidades":-1}}
    ]
    don_por_muni = list(db["Donaciones"].aggregate(pipeline_don))

    # agregar inventario por producto
    pipeline_inv = [
        {"$project":
        {  # solo campos necesarios
            "_id": 0,
            "nombre": 1,  
            "stock_total":1
        }},
        {"$sort": {"stock_total":-1}}
    ]
    inv_por_prod = list(db["Inventario"].aggregate(pipeline_inv))

    return render_template("stats.html", pred_por_cp=pred_por_cp, don_por_muni=don_por_muni, inv_por_prod=inv_por_prod)

# ruta para ver las estadísticas de las donaciones
@app.route("/stats/donaciones", methods=["GET"])
def stats_donaciones():
    # agregar donaciones por municipio
    pipeline_don = [
        {"$unwind": "$lote"},  # descomponer array lote para acceder a unidades
        {"$group":
        {  
            "_id": "$producto.Codigo_municipio",  
            "total_unidades":{"$sum":"$lote.unidades"}  # sumar unidades donada
        }},
        {"$project":{
            "_id":0,
            "municipio":"$_id",
            "total_unidades":1
        }},
        {"$sort": {"total_unidades":-1}}
    ]
    don_por_muni = list(db["Donaciones"].aggregate(pipeline_don))

    # agregar donaciones por fecha procesado
    pipeline_don_fecha = [
        {"$unwind": "$lote"},
        {"$group":{
            "_id": {"$dateToString":{"format":"%Y-%m-%d", "date":"$procesado_en"}},
            "total_unidades":{"$sum":"$lote.unidades"}
        }},
        {"$project":{
            "_id":0,
            "fecha": "$_id",
            "total_unidades":1
        }},
        {"$sort": {"fecha":1}}
    ]
    don_por_fecha = list(db["Donaciones"].aggregate(pipeline_don_fecha))

    # agregar donaciones por tipo de donante
    pipeline_don_donante = [
        {"$group": {
            "_id": "$donante.tipo",
            "total_donaciones": {"$sum": 1},
            "total_unidades": {"$sum": "$lote.unidades"}
        }},
        {"$project": {
            "_id":0,
            "tipo_donante":"$_id",
            "total_donaciones": 1,
            "total_unidades": 1   
        }},
        {"$sort":{"total_donaciones":-1}}
    ]
    don_por_donante = list(db["Donaciones"].aggregate(pipeline_don_donante))

    # agregar donaciones por categoria de producto
    pipeline_don_categoria = [
        { "$group":{
            "_id": "$producto.categoria",
            "total_donaciones": {"$sum":1},
            "total_unidades": {"$sum":"$lote.unidades"}
        }},
        {"$project": {
            "_id":0,
            "categoria":"$_id",
            "total_donaciones":1,
            "total_unidades":1
        }},
        {"$sort":{"total_unidades":-1}}
    ]
    don_por_categoria = list(db["Donaciones"].aggregate(pipeline_don_categoria))

    # agregar donaciones por producto
    pipeline_don_prod = [
        { "$group":{
            "_id": "$producto.producto",
            "total_donaciones": {"$sum":1},
            "total_unidades": {"$sum":"$lote.unidades"}
        }},
        {"$project": {
            "_id":0,
            "producto":"$_id",
            "total_donaciones":1,
            "total_unidades":1
        }},
        {"$sort":{"total_unidades":-1}}
    ]
    don_por_producto = list(db["Donaciones"].aggregate(pipeline_don_prod))  

    # agregar donaciones por caducidad
    pipeline_don_caducidad = [
        {"$unwind": "$lote"},
        {"$group":{
            "_id": "$lote.fecha_caducidad",
            "total_unidades":{"$sum":"$lote.unidades"}
        }},
        {"$project":{
            "_id":0,
            "fecha_caducidad":"$_id",
            "total_unidades":1
        }},
        {"$sort": {"fecha_caducidad":1}}
    ]
    don_por_caducidad = list(db["Donaciones"].aggregate(pipeline_don_caducidad))
    
    return render_template("stats_donaciones.html", don_por_muni=don_por_muni, don_por_fecha=don_por_fecha, don_por_donante=don_por_donante, don_por_categoria=don_por_categoria, don_por_producto=don_por_producto, don_por_caducidad=don_por_caducidad)

# ruta para ver las estadísticas del inventario
@app.route("/stats/inventario")
def stats_inventario():
    # agregar inventario por producto
    pipeline_inv = [
        {"$project":
        {  # solo campos necesarios
            "_id": 0,
            "nombre": 1,  
            "stock_total":1
        }},
        {"$sort": {"stock_total":-1}}
    ]
    inv_por_prod = list(db["Inventario"].aggregate(pipeline_inv))

    # agregar inventario por categoria
    pipeline_inv_cat = [
        {"$group":{
            "_id": "$categoria",
            "total_stock":{"$sum":"$stock_total"}
        }},
        {"$project":{
            "_id":0,
            "categoria":"$_id",
            "total_stock":1,
        }},
        {"$sort":{"total_stock":-1}}
    ]
    inv_por_cat = list(db["Inventario"].aggregate(pipeline_inv_cat))

    # agregar inventario por gastos por fecha
    pipeline_inv_coste = [
        {"$unwind":"$lotes"
        },
        {"$group":{
            "_id":{"$dateToString":{"format":"%Y-%m-%d", "date":"$lotes.fecha_entrada"}},
            "total_gasto":{"$sum": "$lotes.coste"}
        }},
        {"$project":{
            "_id":0,
            "fecha":"$_id",
            "total_gasto":1
        }},
        {"$sort":{"fecha":1}}
    ]
    inv_por_coste = list(db["Inventario"].aggregate(pipeline_inv_coste))

    # agregar inventario por donante/ proveedor
    pipeline_inv_proveedor = [
        {"$unwind":"$lotes"
        },
        {"$group":{
            "_id":{
                "$cond": {
                    "if": {"$eq": ["$lotes.coste", 0]},  # coste = 0 es donacion
                    "then": "donacion",
                    "else": "proveedor"  # fue comprado al proveedor
                }
            },
            "total_unidades":{"$sum": "$lotes.unidades"}
        }},
        {"$project":{
            "_id":0,
            "tipo":"$_id",
            "total_unidades":1
        }},
        {"$sort":{"total_unidades":-1}}
    ]
    inv_por_proveedor = list(db["Inventario"].aggregate(pipeline_inv_proveedor))

    # agregar inventario por proximas caducidades
    pipeline_inv_caducidad = [
        {"$unwind":"$lotes"
        },
        {"$match":{
            "lotes.fecha_caducidad":{"$ne":None}
        }},
        {"$group":{
            "_id":"$lotes.fecha_caducidad",
            "total_unidades":{"$sum": "$lotes.unidades"}
        }},
        {"$project":{
            "_id":0,
            "fecha_caducidad":"$_id",
            "total_unidades":1
        }},
        {"$sort":{"fecha_caducidad":1}}
    ]
    inv_por_caducidad = list(db["Inventario"].aggregate(pipeline_inv_caducidad))

    # agregar inventario por municipio
    pipeline_inv_muni = [
        {"$group":{
            "_id":"$Codigo_municipio",
            "total_stock":{"$sum":"$stock_total"}
        }},
        {"$project":{
            "_id":0,
            "municipio":"$_id",
            "total_stock":1,
        }},
        {"$sort":{"total_stock":-1}}
    ]
    inv_por_muni =  list(db["Inventario"].aggregate(pipeline_inv_muni))

    return render_template("stats_inventario.html", inv_por_prod=inv_por_prod, inv_por_muni=inv_por_muni, inv_por_cat=inv_por_cat, inv_por_coste=inv_por_coste, inv_por_proveedor=inv_por_proveedor, inv_por_caducidad=inv_por_caducidad)

# ruta para ver las estadísticas de las predicciones
@app.route("/stats/predicciones")
def stats_predicciones():
    # agregar predicciones por codigo postal
    pipeline_pred = [
        {"$group": 
        {  
            "_id": "$codigo_postal",  # agrupar por cp
            "num_predicciones":{"$sum":1}   # suma numero de pred
        }},
        {"$project": 
        {  
            "_id":0,  # ocular id mongo
            "codigo_postal":"$_id",  
            "num_predicciones":1
        }},
        {"$sort":{"num_predicciones":-1}}  # ordenar desc
    ]
    pred_por_cp = list(db["Predicciones"].aggregate(pipeline_pred))  

    # agregar predicciones por tipo de demanda
    pipeline_pred_tipo = [
        {"$group":
        {
            "_id":"$demanda",
            "total_predicciones":{"$sum":1}
        }},
        {"$project":{
            "_id":0,
            "tipo_demanda":"$_id",
            "total_predicciones":1
        }},
        {"$sort":{"total_predicciones":-1}}
    ]
    pred_por_tipo = list(db["Predicciones"].aggregate(pipeline_pred_tipo))

    # agregar promedio de renta por nivel de demanda
    pipeline_pred_renta_demanda = [
        {"$group":
        {
            "_id":"$demanda",
            "avg_renta":{"$avg":"$renta_media"}
        }},
        {"$project":{
            "_id":0,
            "tipo_demanda":"$_id",
            "avg_renta":1
        }},
        {"$sort":{"tipo_demanda":1}}
    ]
    pred_renta_demanda = list(db["Predicciones"].aggregate(pipeline_pred_renta_demanda))

    # agregar habitantes por municipio
    pipeline_pred_muni = [
        {"$group":
        {
            "_id":"$codigo_postal",
            "avg_habitantes":{"$avg":"$habitantes"}
        }},
        {"$project":{
            "_id":0,
            "codigo_postal":"$_id",
            "avg_habitantes":1
        }},
        {"$sort":{"avg_habitantes":-1}}
    ]
    pred_hab_muni = list(db["Predicciones"].aggregate(pipeline_pred_muni))

    # agregar renta media por municipio
    pipeline_pred_renta = [
        {"$group":
        {
            "_id":"$codigo_postal",
            "avg_renta":{"$avg":"$renta_media"}
        }},
        {"$project":{
            "_id":0,
            "codigo_postal":"$_id",
            "avg_renta":1
        }},
        {"$sort":{"avg_renta":-1}}
    ]
    pred_renta_muni = list(db["Predicciones"].aggregate(pipeline_pred_renta))

    # agregar promedio de renta por nivel de demanda
    pipeline_pred_renta_demanda = [
        {"$group":
        {
            "_id":"$demanda",
            "avg_renta":{"$avg":"$renta_media"}
        }},
        {"$project":{
            "_id":0,
            "tipo_demanda":"$_id",
            "avg_renta":1
        }},
        {"$sort":{"tipo_demanda":1}}
    ]
    pred_renta_demanda = list(db["Predicciones"].aggregate(pipeline_pred_renta_demanda))

    # agregar paro registrado por municipio
    pipeline_pred_paro = [
        {"$group":
        {
            "_id":"$codigo_postal",
            "avg_paro":{"$avg":"$paro_registrado"}
        }},
        {"$project":{
            "_id":0,
            "codigo_postal":"$_id",
            "avg_paro":1
        }},
        {"$sort":{"avg_paro":-1}}
    ]
    pred_paro_muni = list(db["Predicciones"].aggregate(pipeline_pred_paro))

    return render_template("stats_predicciones.html", pred_por_cp=pred_por_cp, pred_por_tipo=pred_por_tipo, pred_renta_demanda=pred_renta_demanda, pred_hab_muni=pred_hab_muni, pred_renta_muni=pred_renta_muni, pred_paro_muni=pred_paro_muni)

# ruta para la generación de menú y anuncio
@app.route('/generar')
def generar():
    return render_template('generar.html')

# ruta para generar menú
@app.route('/chef', methods = ["GET", "POST"])
def chef():

    menu = None

    # para método GET devolvemos el html vacío
    if request.method == 'GET':
        return render_template('chef.html', inventario=None, donaciones=None, demanda=None, menu=menu)
    
    # obtención del cp
    codigo = request.form.get("codigo_postal")
    
    if not codigo:
        return render_template("chef.html", menu="<h3>Error:</h3><p>Introduce un código postal.</p>")
    
    # obtención del inventario/donaciones/demanda para el cp
    inventario = list(db['Inventario'].find({"Codigo_municipio": int(codigo)}, {'_id': 0}))
    donaciones = list(db['Donaciones'].find({"Codigo_municipio": int(codigo)}, {'_id': 0}))
    # usar la última predicción de la demanda
    prediccion = db['Predicciones'].find_one(
                {"Codigo_municipio": int(codigo)}, 
                sort=[('_id', -1)])
    
    if prediccion:
        demanda = prediccion.get('demanda', 'Normal')
    else:
        demanda = 'Normal'

    menu = ai_chef(inventario, donaciones, demanda)

    return render_template("chef.html", menu=menu)

# ruta para generar el anuncio
@app.route('/anuncio', methods=['GET', 'POST'])
def anuncio():

    campaign = None
    error_msg = None

    # para método GET devolvemos el html vacío
    if request.method == 'GET':
        return render_template('anuncio.html', anuncio=campaign)
    
    # obtención del cp
    codigo = request.form.get("codigo_postal")
    
    if not codigo:
        return render_template("chef.html", menu="<h3>Error:</h3><p>Introduce un código postal.</p>")
    
    # obtención del inventario para el cp
    inventario = list(db['Inventario'].find({"Codigo_municipio": int(codigo)}, {'_id': 0}))
    
    if not inventario:
        error_msg = f"No hay inventario para el CP {int(codigo)}"
    else:
        campaign = ai_campaign(inventario)

    return render_template("anuncio.html", anuncio=campaign, error_msg=error_msg)

if __name__ == "__main__":
    app.run(debug = True, host = "localhost", port  = 5000)