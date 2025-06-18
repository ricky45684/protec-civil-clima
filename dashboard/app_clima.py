import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone

# URL del fondo desde GitHub
FONDO = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/fondo/fondo_proteccion.jpg"
LOGO_PC = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/LogoPC.png"
LOGO_RRD = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/logo_rrd_pc.png"

# Función para aplicar fondo
def set_background_url(img_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{img_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_url(FONDO)

# Título con logos
c1, c2, c3 = st.columns([1, 6, 1])
with c1:
    st.image(LOGO_PC, width=70)
with c2:
    st.markdown("<h2 style='text-align: center; color: white;'>Protección Civil y Abordaje Integral de Emergencias y Catástrofes<br>Dirección Provincial de Reducción de Riesgos de Desastres</h2>", unsafe_allow_html=True)
with c3:
    st.image(LOGO_RRD, width=70)

# Fecha y hora actual
now_local = datetime.now(timezone.utc).astimezone()
st.markdown(f"**Última actualización:** {now_local.strftime('%d/%m/%Y %H:%M:%S')} (UTC {now_local.strftime('%z')})")

st.subheader("🌍 Mapa Santa Cruz")

# Mapas embebidos
MAP1 = "1gxAel478mSuzOx3VrqXTJ4KTARtwG4k"
MAP2 = "17xfwk9mz4F96f8xvPp3sbZ-5whfbntI"

col1, col2 = st.columns(2)
with col1:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP1}&ehbc=2E312F", width=640, height=480)
with col2:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP2}&ehbc=2E312F", width=640, height=480)

st.markdown("---")

# Carga de localidades
try:
    df = pd.read_excel("dashboard/data/Localidades_Santa_Cruz_Coordenadas_DD.xlsx", engine="openpyxl")
except Exception as e:
    st.error(f"No se pudo cargar el archivo de localidades. Detalles: {e}")
    st.stop()

st.markdown("### 📌 Seleccioná la localidad")
localidad = st.selectbox("Localidades", df["Nombre"].unique())
data = df[df["Nombre"] == localidad].iloc[0]

st.markdown(f"**Localidad seleccionada:** {localidad}")
st.markdown(f"📍 Coordenadas: {data['Lat']}, {data['Lon']}")
