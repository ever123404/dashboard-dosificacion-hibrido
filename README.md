# Dashboard de Dosificación Óptima - EPS SEDACAJ

Este sistema permite calcular la dosis óptima de sulfato de aluminio para el tratamiento de agua potable en la Planta El Milagro (EPS SEDACAJ), utilizando un modelo híbrido basado en:

- **Interpolación con Splines Cúbicos**
- **Lógica Difusa**
- **Ponderación adaptativa**

## Tecnologías utilizadas
- Streamlit
- Pandas
- NumPy
- SciPy
- Plotly
- scikit-fuzzy

## Estructura del proyecto
- `app.py`: Código principal de la aplicación.
- `data/tabla_dosificacion.csv`: Datos de calibración de dosificación.
- `data/historial_pruebas.csv`: Historial de pruebas generadas automáticamente.
- `requirements.txt`: Librerías necesarias.
- `README.md`: Descripción del proyecto.

## Uso
Para ejecutar la aplicación localmente:

```bash
streamlit run app.py
