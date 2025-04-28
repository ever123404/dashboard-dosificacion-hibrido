# Importaciones iniciales
import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import splrep, splev, interp1d
import os
import time
from datetime import datetime, timedelta
import base64
import plotly.express as px
import plotly.graph_objects as go
import json

# Importaciones para lógica difusa
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Configurar la página
st.set_page_config(
    page_title="Sistema de Dosificación | SEDACAJ",
    layout="wide",
    page_icon="💧",
    initial_sidebar_state="collapsed"
)

# Definir colores institucionales
COLOR_PRIMARIO = "#003366"  # Azul oscuro institucional
COLOR_SECUNDARIO = "#336699"  # Azul medio
COLOR_ACENTO = "#66A3D2"  # Azul claro
COLOR_TEXTO = "#333333"  # Gris oscuro para texto
COLOR_FONDO = "#F8F9FA"  # Gris muy claro para fondo
COLOR_EXITO = "#28A745"  # Verde para éxito
COLOR_ADVERTENCIA = "#FFC107"  # Amarillo para advertencias
COLOR_ERROR = "#DC3545"  # Rojo para errores

# Definir rutas de carpetas
DATA_DIR = "data"
IMAGES_DIR = os.path.join(DATA_DIR, "images")
HISTORY_FILE = os.path.join(DATA_DIR, "historial_pruebas.csv")

# Crear directorios de datos si no existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
