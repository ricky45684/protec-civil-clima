import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN ---
API_KEY      = "f003e87edb9944f319d5f706f0979fec"
DATA_FILE    = "data/Localidades_Santa_Cruz_Coordenadas_DD.xlsx"
LOGO_PC      = "assets/logos/LogoPC.png"
LOGO_RRD     = "assets/logos/logo_rrd_pc.png"
REPORTES_DIR = "reportes_clima"

WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Protección Civil - Clima SC", layout="wide")

# --- ENCABEZADO ---
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    pass
    # st.image(LOGO_PC, width=70)  # Comentado temporalmente hasta que el logo esté cargado
with col2:
    st.markdown("<h1 style='text-align: center;'>Clima Santa Cruz</h1>", unsafe_allow_html=True)
with col3:
    pass
    # st.image(LOGO_RRD, width=70)  # Comentado temporalmente hasta que el logo esté cargado

# --- FUNCIONES CLIMA ---
@st.cache_data(show_spinner=False)
def cargar_localidades():
    return pd.read_excel(DATA_FILE)

def obtener_clima(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Parte Diario - Clima Santa Cruz", ln=True, align="C")
    pdf.ln(10)

    for _, row in df.iterrows():
        linea = f"{row['Localidad']}: {row['Descripción'].capitalize()}, {row['Temperatura']}°C, Viento {row['Viento']} km/h"
        pdf.cell(200, 10, txt=linea, ln=True)

    nombre_archivo = f"{REPORTES_DIR}/Clima_SC_{datetime.now():%Y%m%d}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo

# --- APP ---
st.markdown("### Clima actual por localidad")

df_localidades = cargar_localidades()
datos_clima = []

for _, fila in df_localidades.iterrows():
    data = obtener_clima(fila["Latitud"], fila["Longitud"])
    if data:
        clima = {
            "Localidad": fila["Localidad"],
            "Temperatura": data["main"]["temp"],
            "Sensación térmica": data["main"]["feels_like"],
            "Descripción": data["weather"][0]["description"],
            "Viento": round(data["wind"]["speed"] * 3.6, 1)  # m/s a km/h
        }
        datos_clima.append(clima)

df_resultado = pd.DataFrame(datos_clima)
st.dataframe(df_resultado)

# --- EXPORTACIÓN A PDF ---
if st.button("Exportar PDF del parte diario"):
    archivo = export_pdf(df_resultado)
    with open(archivo, "rb") as f:
        st.download_button("Descargar parte diario", f, file_name=archivo.split("/")[-1])
