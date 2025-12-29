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


load_dotenv() #leer el .env

api_key = os.getenv("COHERE_API_KEY")
user = os.getenv("MONGO_USERNAME")
pw = os.getenv("PASSWORD")

co = cohere.ClientV2(api_key=api_key)

app = Flask(__name__)

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

#Antes de que se procese cada petición en la app, nos conectamos a la base de datos
@app.before_request
def connect_db():

    global db

    if db is None:
        
        db = get_db()

@app.route('/')
def index():
    return "<h1>Comedor Social Valencia - Todo Ok</h1>"