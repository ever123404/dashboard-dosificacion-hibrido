# --- Importaciones ---
import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import splrep, splev, interp1d
import os
import base64
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# --- Configuración de página ---
st.set_page_config(
    page_title="Sistema de Dosificación Óptima | SEDACAJ",
    layout="wide",
    page_icon="💧"
)
# --- Encabezado corregido ---
st.markdown(
    """
    <div style='background: linear-gradient(90deg, #003366 0%, #336699 100%); padding: 1.5rem; border-radius: 0.75rem; margin-bottom: 2rem; text-align: center; color: white;'>
        <h1 style='margin-bottom: 0.5rem;'>Sistema de Dosificación de Coagulante (Sulfato de Aluminio)</h1>
        <h2 style='margin-bottom: 0.2rem;'>EPS SEDACAJ S.A.</h2>
        <h3 style='margin-bottom: 0.2rem;'>Planta de Tratamiento:</h3>
        <h2 style='font-style: italic; margin-bottom: 0.2rem;'>"El Milagro"</h2>
        <h3 style='margin-bottom: 0;'>Cajamarca</h3>
    </div>
    """,
    unsafe_allow_html=True
)
# --- Definición de colores ---
COLOR_PRIMARIO = "#003366"
COLOR_SECUNDARIO = "#336699"
COLOR_ACENTO = "#66A3D2"
COLOR_EXITO = "#28A745"
COLOR_ADVERTENCIA = "#FFC107"
COLOR_ERROR = "#DC3545"

# --- Definición de rutas ---
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "historial_pruebas.csv")

# Crear carpetas si no existen
os.makedirs(DATA_DIR, exist_ok=True)

# --- Clase Modelo Híbrido ---
class ModeloHibridoDosificacion:
    def __init__(self):
        self.modelo_splines = None
        self.modelo_fuzzy = None
        self.datos_calibracion = None
        self.inicializado = False

    def inicializar_datos(self, data):
        self.datos_calibracion = data
        self._crear_modelo_splines()
        self._crear_modelo_fuzzy()
        self.inicializado = True

    def _crear_modelo_splines(self):
        caudales_disponibles = sorted(self.datos_calibracion['caudal'].unique())
        self.splines_por_caudal = {}
        for caudal in caudales_disponibles:
            data_caudal = self.datos_calibracion[self.datos_calibracion['caudal'] == caudal].copy()
            data_caudal = data_caudal.sort_values(by='turbiedad')
            x_values = data_caudal['turbiedad'].values
            y_values = data_caudal['dosis_mg_l'].values
            if len(np.unique(x_values)) < len(x_values):
                data_grouped = data_caudal.groupby('turbiedad')['dosis_mg_l'].mean().reset_index()
                x_values = data_grouped['turbiedad'].values
                y_values = data_grouped['dosis_mg_l'].values
            try:
                spl = splrep(x_values, y_values, k=3)
                self.splines_por_caudal[caudal] = spl
            except:
                interp_linear = interp1d(x_values, y_values, bounds_error=False, fill_value="extrapolate")
                self.splines_por_caudal[caudal] = {'tipo': 'lineal', 'interp': interp_linear}
        self.modelo_splines = {'caudales': caudales_disponibles, 'modelos': self.splines_por_caudal}

    def _crear_modelo_fuzzy(self):
        rango_turbiedad = np.arange(0, 4001, 1)
        rango_ph = np.arange(5, 9.6, 0.1)
        rango_caudal = np.arange(0, 301, 1)
        rango_dosis = np.arange(0, 301, 1)

        turbiedad = ctrl.Antecedent(rango_turbiedad, 'turbiedad')
        ph = ctrl.Antecedent(rango_ph, 'ph')
        caudal = ctrl.Antecedent(rango_caudal, 'caudal')
        dosis = ctrl.Consequent(rango_dosis, 'dosis')

        turbiedad['muy_baja'] = fuzz.trimf(rango_turbiedad, [0, 0, 10])
        turbiedad['baja'] = fuzz.trimf(rango_turbiedad, [0, 10, 50])
        turbiedad['media'] = fuzz.trimf(rango_turbiedad, [30, 100, 300])
        turbiedad['alta'] = fuzz.trimf(rango_turbiedad, [200, 500, 1000])
        turbiedad['muy_alta'] = fuzz.trapmf(rango_turbiedad, [800, 1500, 4000, 4000])

        ph['acido'] = fuzz.trimf(rango_ph, [5, 5, 6.5])
        ph['neutro'] = fuzz.trimf(rango_ph, [6, 7, 8])
        ph['alcalino'] = fuzz.trimf(rango_ph, [7.5, 9, 9.5])

        caudal['bajo'] = fuzz.trimf(rango_caudal, [0, 0, 200])
        caudal['medio'] = fuzz.trimf(rango_caudal, [150, 225, 300])
        caudal['alto'] = fuzz.trimf(rango_caudal, [250, 300, 300])

        dosis['muy_baja'] = fuzz.trimf(rango_dosis, [0, 0, 10])
        dosis['baja'] = fuzz.trimf(rango_dosis, [5, 15, 30])
        dosis['media'] = fuzz.trimf(rango_dosis, [25, 50, 80])
        dosis['alta'] = fuzz.trimf(rango_dosis, [70, 100, 150])
        dosis['muy_alta'] = fuzz.trapmf(rango_dosis, [130, 200, 300, 300])

        # --- Definir reglas difusas corregidas ---
        rules = [
            # Reglas principales basadas en turbiedad y pH
            ctrl.Rule(turbiedad['muy_baja'] & ph['neutro'], dosis['muy_baja']),
            ctrl.Rule(turbiedad['muy_baja'] & ph['acido'], dosis['baja']),
            ctrl.Rule(turbiedad['muy_baja'] & ph['alcalino'], dosis['baja']),
    
            ctrl.Rule(turbiedad['baja'] & ph['neutro'], dosis['baja']),
            ctrl.Rule(turbiedad['baja'] & ph['acido'], dosis['media']),
            ctrl.Rule(turbiedad['baja'] & ph['alcalino'], dosis['media']),
    
            ctrl.Rule(turbiedad['media'] & ph['neutro'], dosis['media']),
            ctrl.Rule(turbiedad['media'] & ph['acido'], dosis['alta']),
            ctrl.Rule(turbiedad['media'] & ph['alcalino'], dosis['alta']),
    
            ctrl.Rule(turbiedad['alta'] & ph['neutro'], dosis['alta']),
            ctrl.Rule(turbiedad['alta'] & ph['acido'], dosis['muy_alta']),
            ctrl.Rule(turbiedad['alta'] & ph['alcalino'], dosis['muy_alta']),
    
            ctrl.Rule(turbiedad['muy_alta'], dosis['muy_alta']),

            # --- Nuevas reglas específicas que incluyen caudal ---
            ctrl.Rule(caudal['alto'] & turbiedad['alta'], dosis['muy_alta']),
            ctrl.Rule(caudal['bajo'] & turbiedad['baja'], dosis['muy_baja']),
            ctrl.Rule(caudal['bajo'] & turbiedad['media'], dosis['media']),
            ctrl.Rule(caudal['medio'] & turbiedad['media'], dosis['media']),
            ctrl.Rule(caudal['medio'] & turbiedad['alta'], dosis['alta']),
        ]

        sistema_ctrl = ctrl.ControlSystem(rules)
        self.modelo_fuzzy = ctrl.ControlSystemSimulation(sistema_ctrl)

    def predecir_dosis(self, turbiedad, ph, caudal):
        if not self.inicializado:
            raise ValueError("El modelo no ha sido inicializado con datos.")
        dosis_splines, confianza_splines, metodo_splines = self._predecir_con_splines(turbiedad, caudal)
        dosis_fuzzy, confianza_fuzzy = self._predecir_con_fuzzy(turbiedad, ph, caudal)

        if confianza_splines > 0.8:
            peso_splines = 0.8
            peso_fuzzy = 0.2
            metodo = f"{metodo_splines} con ajuste difuso"
        elif confianza_fuzzy > 0.8:
            peso_splines = 0.2
            peso_fuzzy = 0.8
            metodo = "Lógica Difusa con ajuste por interpolación"
        else:
            peso_splines = 0.5
            peso_fuzzy = 0.5
            metodo = "Modelo Híbrido Equilibrado"

        dosis_optima = (dosis_splines * peso_splines) + (dosis_fuzzy * peso_fuzzy)
        dosis_optima = max(dosis_optima, 0)
        confianza = (confianza_splines * peso_splines) + (confianza_fuzzy * peso_fuzzy)

        return dosis_optima, metodo, confianza
    def _predecir_con_splines(self, turbiedad, caudal):
        if self.modelo_splines is None:
            return 0, 0, "Sin datos"

        caudales_disponibles = self.modelo_splines['caudales']
        caudal_calculo = min(caudales_disponibles, key=lambda x: abs(x - caudal))
        modelo = self.modelo_splines['modelos'].get(caudal_calculo)

        confianza_caudal = 1 - min(abs(caudal - caudal_calculo) / 100, 0.5)

        min_turb = min(self.datos_calibracion[self.datos_calibracion['caudal'] == caudal_calculo]['turbiedad'])
        max_turb = max(self.datos_calibracion[self.datos_calibracion['caudal'] == caudal_calculo]['turbiedad'])

        if turbiedad < min_turb:
            confianza_turbiedad = max(0, 1 - (min_turb - turbiedad) / min_turb)
        elif turbiedad > max_turb:
            confianza_turbiedad = max(0, 1 - (turbiedad - max_turb) / max_turb)
        else:
            confianza_turbiedad = 1

        if isinstance(modelo, dict) and modelo.get('tipo') == 'lineal':
            dosis = float(modelo['interp'](turbiedad))
            metodo = "Interpolación Lineal"
        else:
            dosis = float(splev(turbiedad, modelo))
            metodo = "Spline Cúbico"

        confianza = confianza_caudal * confianza_turbiedad
        return dosis, confianza, metodo

    def _predecir_con_fuzzy(self, turbidez, ph, caudal):
        if self.modelo_fuzzy is None:
            return 0, 0

        self.modelo_fuzzy.input['turbiedad'] = min(turbidez, 4000)
        self.modelo_fuzzy.input['ph'] = min(max(ph, 5.0), 9.5)
        self.modelo_fuzzy.input['caudal'] = min(caudal, 300)

        try:
            self.modelo_fuzzy.compute()
            dosis = self.modelo_fuzzy.output['dosis']
            confianza = 0.9
            return dosis, confianza
        except:
            return 0, 0

# --- Funciones de soporte ---

@st.cache_data
def load_data():
    data_path = os.path.join(DATA_DIR, "tabla_dosificacion.csv")
    if not os.path.exists(data_path):
        st.error("No se encontró el archivo tabla_dosificacion.csv")
        st.stop()

    data = pd.read_csv(data_path)
    data['turbiedad'] = pd.to_numeric(data['turbiedad'], errors='coerce')
    data['caudal'] = pd.to_numeric(data['caudal'], errors='coerce')
    data['dosis_mg_l'] = pd.to_numeric(data['dosis_mg_l'], errors='coerce')

    return data.dropna(subset=['turbiedad', 'caudal', 'dosis_mg_l'])

def guardar_resultado_historial(turbidez, ph, caudal, dosis_sugerida, metodo, categoria):
    ahora = datetime.now()
    nuevo = pd.DataFrame({
        'fecha': [ahora.strftime('%Y-%m-%d')],
        'hora': [ahora.strftime('%H:%M:%S')],
        'turbidez': [turbidez],
        'ph': [ph],
        'caudal': [caudal],
        'dosis_mg_l': [dosis_sugerida],
        'metodo_calculo': [metodo],
        'categoria': [categoria]
    })

    if os.path.exists(HISTORY_FILE):
        historial = pd.read_csv(HISTORY_FILE)
        historial = pd.concat([historial, nuevo], ignore_index=True)
    else:
        historial = nuevo

    historial.to_csv(HISTORY_FILE, index=False)

def cargar_historial():
    if os.path.exists(HISTORY_FILE):
        historial = pd.read_csv(HISTORY_FILE)
        historial['fecha'] = pd.to_datetime(historial['fecha'])
        return historial
    else:
        return pd.DataFrame(columns=['fecha', 'hora', 'turbidez', 'ph', 'caudal', 'dosis_mg_l', 'metodo_calculo', 'categoria'])

# --- Inicialización de datos y modelo ---
try:
    data = load_data()
    modelo_hibrido = ModeloHibridoDosificacion()
    modelo_hibrido.inicializar_datos(data)
except Exception as e:
    st.error(f"Error en la inicialización de datos: {str(e)}")
    st.stop()

# --- Encabezado general ---
st.title("💧 Sistema de Dosificación Óptima de Coagulantes")
st.subheader("EPS SEDACAJ - Planta El Milagro")

# --- Formulario de entrada de parámetros ---
st.header("📋 Ingreso de parámetros del agua")

with st.form(key="formulario_parametros"):
    col1, col2, col3 = st.columns(3)
    with col1:
        turbidez = st.number_input("Turbidez (NTU)", min_value=0.0, max_value=4000.0, value=0.0)
    with col2:
        ph = st.number_input("pH", min_value=5.0, max_value=9.5, value=7.2)
    with col3:
        caudal = st.number_input("Caudal Operativo (L/s)", min_value=0.0, max_value=300.0, value=0.0)

    guardar_historial = st.checkbox("¿Guardar resultado en historial?", value=True)
    submit = st.form_submit_button("Calcular Dosis Óptima")

# --- Procesar parámetros ---
if submit:
    with st.spinner("Calculando dosis óptima..."):
        try:
            dosis_sugerida, metodo, confianza = modelo_hibrido.predecir_dosis(turbidez, ph, caudal)
            dosis_sugerida = max(dosis_sugerida, 0)

            if turbidez < 10:
                categoria = "Turbidez Baja"
                color_categoria = COLOR_ADVERTENCIA
            elif turbidez > 1000:
                categoria = "Turbidez Muy Alta"
                color_categoria = COLOR_ERROR
            else:
                categoria = "Turbidez Normal"
                color_categoria = COLOR_EXITO

            if guardar_historial:
                guardar_resultado_historial(turbidez, ph, caudal, dosis_sugerida, metodo, categoria)

            st.success(f"Dosis sugerida: {dosis_sugerida:.2f} mg/L")
            st.info(f"Método utilizado: {metodo} (confianza: {confianza:.2f})")

        except Exception as e:
            st.error(f"Error en el cálculo: {str(e)}")

# --- Mostrar historial ---
st.header("📈 Historial de Cálculos y Tendencias")
historial = cargar_historial()

if historial.empty:
    st.info("No hay datos históricos registrados.")
else:
    st.dataframe(historial, use_container_width=True)
# --- Pie de página corregido ---
st.markdown(
    """
    <div style='background-color: #003366; padding: 1.5rem; border-radius: 0.75rem; margin-top: 3rem; text-align: center; color: white; font-size: 1rem;'>
        <div style='font-weight: 600; margin-bottom: 0.5rem;'>Universidad Nacional de Cajamarca</div>
        <div style='font-weight: 500; margin-bottom: 1rem;'>Escuela de Posgrado - 2025</div>
        <div style='font-weight: 600; margin-bottom: 0.5rem;'>Investigadores:</div>
        <div style='margin-bottom: 0.5rem;'>MSc. Ever Rojas Huamán</div>
        <div style='font-size: 0.9rem; margin-bottom: 1rem;'>Responsable de la Investigación</div>
        <div style='margin-bottom: 0.5rem;'>Dr. Glicerio Eduardo Torres Carranza</div>
        <div style='font-size: 0.9rem;'>Asesor de Investigación</div>
    </div>
    """,
    unsafe_allow_html=True
)

