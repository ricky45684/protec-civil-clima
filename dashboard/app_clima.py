import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN ---
API_KEY      = "f003e87edb9944f319d5f706f0979fec"
DATA_FILE    = "data/Localidades_SC_Dep.xlsx"
LOGO_PC      = "assets/logos/LogoPC.png"
LOGO_RRD     = "assets/logos/logo_rrd_pc.png"
REPORTES_DIR = "reportes_clima"

# --- PÁGINA ---
st.set_page_config(page_title="Protección Civil - Clima SC", layout="wide")

# --- ENCABEZADO ---
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    pass
    # st.image(LOGO_PC, width=70)
with col2:
    st.markdown("<h1 style='text-align: center;'>Clima Santa Cruz</h1>", unsafe_allow_html=True)
with col3:
    pass
    # st.image(LOGO_RRD, width=70)

# --- FUNCIONES ---
@st.cache_data(show_spinner=False)
def cargar_localidades():
    return pd.read_excel(DATA_FILE)

def obtener_clima(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def evaluar_riesgo(temp, sens_term, viento):
    riesgo = []
    if viento >= 80:
        riesgo.append("viento fuerte")
    if sens_term <= -10:
        riesgo.append("frío extremo")
    if temp >= 35 or temp <= -15:
        riesgo.append("temperatura extrema")
    return riesgo

def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Parte Diario - Clima Santa Cruz", ln=True, align="C")
    pdf.ln(10)

    for _, row in df.iterrows():
        linea = f"{row['Localidad']} ({row['Departamento']}): {row['Descripción'].capitalize()}, {row['Temperatura']}°C, Viento {row['Viento']} km/h"
        pdf.cell(200, 10, txt=linea, ln=True)

    nombre_archivo = f"{REPORTES_DIR}/Clima_SC_{datetime.now():%Y%m%d}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo

# --- CARGA Y PROCESAMIENTO ---
st.markdown("### Clima actual por localidad")

df_localidades = cargar_localidades()
datos = []

for _, fila in df_localidades.iterrows():
    data = obtener_clima(fila["Latitud_DD"], fila["Longitud_DD"])
    if data:
        temp     = data["main"]["temp"]
        sens     = data["main"]["feels_like"]
        viento_k = round(data["wind"]["speed"] * 3.6, 1)  # m/s a km/h
        riesgo   = evaluar_riesgo(temp, sens, viento_k)

        datos.append({
            "Localidad": fila["localidad"],
            "Departamento": fila["departamento"].title(),
            "Temperatura": temp,
            "Sensación térmica": sens,
            "Viento": viento_k,
            "Descripción": data["weather"][0]["description"],
            "Riesgos": ", ".join(riesgo) if riesgo else "ninguno"
        })

df_clima = pd.DataFrame(datos)
st.dataframe(df_clima)

# --- SEMÁFORO POR DEPARTAMENTO ---
st.markdown("### Semáforo climático por departamento")

def determinar_nivel(riesgos):
    if any("fuerte" in r for r in riesgos) or any("extrema" in r for r in riesgos):
        return "🔴 Rojo"
    elif any(r != "ninguno" for r in riesgos):
        return "🟡 Amarillo"
    else:
        return "🟢 Verde"

df_semaforo = (
    df_clima.groupby("Departamento")
    .agg({"Riesgos": lambda x: list(x)})
    .reset_index()
)

df_semaforo["Nivel de riesgo"] = df_semaforo["Riesgos"].apply(determinar_nivel)
df_semaforo["Variables activadas"] = df_semaforo["Riesgos"].apply(lambda x: ", ".join(set([i for i in x if i != "ninguno"])))

df_semaforo_mostrar = df_semaforo[["Departamento", "Nivel de riesgo", "Variables activadas"]]
st.dataframe(df_semaforo_mostrar)

# --- EXPORTACIÓN A PDF ---
if st.button("Exportar PDF del parte diario"):
    archivo = export_pdf(df_clima)
    with open(archivo, "rb") as f:
        st.download_button("Descargar parte diario", f, file_name=archivo.split("/")[-1])
