# 🍽️ Smart Social Canteen Manager

Aplicación web inteligente para la **gestión de comedores sociales en Valencia**, que combina **Machine Learning, análisis de datos e IA generativa** para predecir la demanda, optimizar el inventario y mejorar la distribución de donaciones.

---

## 🚀 Features

- 🔮 **Predicción de demanda** (baja / normal / crítica) por código postal  
- 📦 **Gestión de inventario** con control de stock, lotes y caducidades  
- 🧾 **Gestión de donaciones** por barrio, categoría y tipo de donante  
- 📈 **Estadísticas avanzadas** (donaciones, inventario y demanda)  
- 🧠 **IA para generación de menús** según inventario y demanda  
- 📣 **IA para campañas de donación** en zonas con déficit o exceso  
- ⚠️ **Sistema de alertas automáticas**  

---

## 🧠 Machine Learning

### Dataset
Se construye mediante un **ETL de CSVs** sacados de diferentes fuentes de datos abiertos, un CSV con información socioeconómica por barrio:

- Codigo_municipio
- Municipio
- Temp_min_invierno
- Prec_max_invierno
- Calidad_vida_media
- Poblacion_total
- Renta_media
- Total_paro_registrado
- Paro_hombre_menor_25
- Paro_hombre_25_45
- Paro_hombre_45+
- Paro_mujer_menor_25
- Paro_mujer_25_45
- Paro_mujer_45+
- Paro_agricultura
- Paro_industria
- Paro_construccion
- Paro_servicios
- Demanda_raw
- Demanda_score
- Demanda

### Modelo
- Clasificación de demanda: `baja`, `normal`, `crítica`
- Exportado a **ONNX** para inferencia rápida
- Integrado directamente en Flask

---

## 🤖 Inteligencia Artificial (Cohere)

- **AI Chef**  
  Genera menús equilibrados usando:
  - Inventario disponible
  - Nivel de demanda previsto
  - Priorización de productos próximos a caducar

- **AI Campaign Generator**  
  Crea campañas de donación personalizadas según:
  - Stock actual
  - Categorías deficitarias
  - Zona geográfica

---

## 🧱 Tech Stack

| Componente | Tecnología |
|----------|-----------|
| Backend | Flask (Python) |
| Database | MongoDB |
| ML | Scikit-learn / ONNX |
| IA Generativa | Cohere API |
| Frontend | HTML + Jinja2 |
| Analytics | MongoDB Aggregation |

---

## 📂 Project Structure

```text
.
├── app.py
├── modelo/
│   ├── boosting_comedor.onnx
│   ├── comedor_metadata.json
│   ├── training.ipynb
│   └── tree_comedor.onnx
├── templates/
│   ├── alertas.html
│   ├── anuncios.html
│   ├── base.html
│   ├── chef.html
│   ├── crear_item.html
│   ├── crear_lote.html
│   ├── donaciones.html
│   ├── editar_lote.html
│   ├── generar.html
│   ├── history.html
│   ├── index.html
│   ├── inventario.html
│   ├── predict.html
│   ├── stats_donaciones.html
│   ├── stats_inventario.html
│   ├── stats_predicciones.html
│   ├── stats.html
│   └── ver_lotes.html
├── data_vlc/
│   ├── FINAL_DATASET_V2.csv
│   ├── FINAL_DATASET.csv
│   ├── municipios_calidad_vida.csv
│   ├── municipios_con_invierno.csv
│   ├── MUNICIPIOS.csv
│   ├── paro_por_municipios.csv
│   ├── part-00000-74c76527-0545-4ecc-abea-8be1009b86a8-c000.csv
│   ├── Poblacion_municipal.csv
│   └── Renta_media.csv
├── ETL.ipynb
├── requirements.txt
└── README.md
