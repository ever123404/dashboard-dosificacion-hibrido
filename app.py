import streamlit as st
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Sistema de Dosificación - SEDACAJ",
    layout="wide",
    page_icon="💧"
)

# Estilos básicos
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .header-container {
        background: linear-gradient(90deg, #003366 0%, #336699 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        font-size: 0.9rem;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Encabezado
st.markdown(
    """
    <div class="header-container">
        <h1>Sistema de Dosificación Óptima</h1>
        <h3>Planta El Milagro - EPS SEDACAJ</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Formulario de parámetros
st.header("📋 Ingreso de Parámetros de Agua Cruda")

with st.form(key="form_parametros"):
    col1, col2, col3 = st.columns(3)
    with col1:
        turbidez = st.number_input("Turbidez (NTU)", min_value=0.0, max_value=4000.0, value=0.0, step=1.0)
    with col2:
        ph = st.number_input("pH", min_value=5.0, max_value=9.5, value=7.2, step=0.1)
    with col3:
        caudal = st.number_input("Caudal Operativo (L/s)", min_value=0.0, max_value=300.0, value=0.0, step=1.0)
    
    submit = st.form_submit_button(label="Enviar parámetros")

# --- Mostrar resultados básicos
if submit:
    st.success("Parámetros recibidos correctamente.")
    st.write(f"**Turbidez:** {turbidez} NTU")
    st.write(f"**pH:** {ph}")
    st.write(f"**Caudal:** {caudal} L/s")
    st.info(f"Fecha y Hora de registro: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- Pie de página
st.markdown(
    """
    <div class="footer">
        Sistema desarrollado por MSc. Ever Rojas Huamán | Universidad Nacional de Cajamarca | 2025
    </div>
    """,
    unsafe_allow_html=True
)
