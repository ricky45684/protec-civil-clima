import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone
from fpdf import FPDF

# --- CONFIGURACIÓN ---
API_KEY = "f003e87edb9944f319d5f706f0979fec"
DATA_FILE = "dashboard/data/Localidades_Santa_Cruz_Coordenadas_DD.xlsx"

# Logos desde URLs (para que funcionen en Streamlit Cloud)
LOGO_PC = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/LogoPC.png"
LOGO_RRD = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/logo_rrd_pc.png"

# IDs de Google My Maps
MAP1 = "1gxAel478mSuzOx3VrqXTJ4KTARtwG4k"
MAP2 = "17xfwk9mz4F96f8xvPp3sbZ-5whfbntI"
WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- CONFIG STREAMLIT ---
st.set_page_config(page_title="Protección Civil - Clima SC", layout="wide")

# Hora local y UTC
now_local = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
now_utc = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
st.markdown(f"<p style='text-align:right;color:lightgray;'>Última actualización: {now_local} (UTC {now_utc})</p>",
            unsafe_allow_html=True)

# --- ENCABEZADO ---
c1, c2, c3 = st.columns([1, 6, 1])
with c1:
    st.image(LOGO_PC, width=70)
with c2:
    st.markdown("""
      <h1 style='text-align:center;color:white;font-size:22px;'>
        Protección Civil y Abordaje Integral de Emergencias y Catástrofes<br>
        Dirección Provincial de Reducción de Riesgos de Desastres
      </h1>""", unsafe_allow_html=True)
with c3:
    st.image(LOGO_RRD, width=70)

# --- BOTÓN ALERTAS SMN ---
st.markdown("""
  <div style='text-align:center;margin:10px;'>
    <a href='https://www.smn.gob.ar/alertas' target='_blank'
       style='color:orange;background:black;border:2px solid orange;
              padding:10px 20px;border-radius:5px;text-decoration:none;
              font-weight:bold;'>🔔 Ver alertas del SMN</a>
  </div>""", unsafe_allow_html=True)

# --- VISOR WINDY ---
st.markdown("### 🛰️ Clima")
st.components.v1.iframe(
    "https://embed.windy.com/embed2.html?lat=-49.5&lon=-70&detailLat=-49.5&detailLon=-70&width=650&height=450&zoom=5"
    "&level=surface&overlay=wind&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates"
    "&detail=&metricWind=km/h&metricTemp=%C2%B0C&radarRange=-1",
    height=460, scrolling=False
)

# --- MAPA SANTA CRUZ ---
st.markdown("### 🗺️ Mapa Santa Cruz")
col1, col2 = st.columns(2)
with col1:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP1}&ehbc=2E312F", width=640, height=480)
with col2:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP2}&ehbc=2E312F", width=640, height=480)

# --- CARGA DE LOCALIDADES ---
try:
    df = pd.read_excel(DATA_FILE, engine="openpyxl")
except Exception as e:
    st.error("❌ Error al cargar el archivo de localidades.")
    st.stop()

def dir_cardinal(deg):
    if deg == "N/D": return "N/D"
    dirs = ['N','NE','E','SE','S','SO','O','NO']
    return dirs[int((deg + 22.5)//45) % 8]

def get_clima(lat, lon):
    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}"
        f"&appid={API_KEY}&units=metric&lang=es").json()
    return {
        "loc":  r.get("name", "N/D"),
        "icon": f"http://openweathermap.org/img/wn/{r['weather'][0]['icon']}@2x.png",
        "desc": r["weather"][0]["description"].capitalize(),
        "temp": r["main"]["temp"],
        "feel": round(r["main"]["feels_like"],1),
        "wind": round(r["wind"]["speed"]*3.6,1),
        "gust": round(r["wind"].get("gust",0)*3.6,1),
        "deg":  r["wind"].get("deg","N/D"),
        "hum":  r["main"]["humidity"],
        "pres": r["main"]["pressure"],
        "cloud":r["clouds"]["all"]
    }

# --- CLIMA POR LOCALIDAD ---
st.markdown("### 🌡️ Clima actual por localidad")
cols = st.columns(2)
datos = []
max_wind = 0
for i, row in df.iterrows():
    c = get_clima(row["Latitud_DD"], row["Longitud_DD"])
    c["loc"] = row["localidad"]
    datos.append(c)
    max_wind = max(max_wind, c["wind"])
    with cols[i%2]:
        st.markdown(f"""
        <div style='background:rgba(0,0,0,0.6);padding:12px;border-radius:8px;margin-bottom:8px;'>
          <h4 style='color:#58a6ff;'>{c['loc']}</h4>
          <img src='{c['icon']}' width=40>
          <p>{c['desc']}</p>
          <p>Temp: {c['temp']:.1f}°C | Sens: {c['feel']:.1f}°C</p>
          <p>Viento: {c['wind']:.1f} km/h | Ráfagas: {c['gust']:.1f} km/h</p>
          <p>Dirección: {c['deg']}° ({dir_cardinal(c['deg'])})</p>
          <p>Humedad: {c['hum']}% | Presión: {c['pres']} hPa | Nubosidad: {c['cloud']}%</p>
        </div>""", unsafe_allow_html=True)

# --- SEMÁFORO CLIMÁTICO ---
if max_wind > 50:
    nivel, color, texto = "Alerta grave (Rojo)", "red", "Viento muy fuerte en la provincia"
elif max_wind > 30:
    nivel, color, texto = "Alerta (Amarillo)", "orange", "Viento fuerte en la provincia"
else:
    nivel = None

if nivel:
    st.markdown(f"""<p>🚦 <b>Nivel de riesgo climático provincial</b>:<br>
    <span style='color:{color};font-weight:bold;'>{nivel}</span><br><small>{texto}</small></p>""",
    unsafe_allow_html=True)

# --- ENLACES FINALES ---
st.markdown("""---""")
st.markdown("""
  <div style='text-align:center;margin-top:10px;'>
    <a href='https://www.agvp.gob.ar/PartesDiarios/PartesProvinciales.pdf' target='_blank'
       style='background:black;color:orange;border:2px solid orange;padding:6px 12px;
              margin:0 4px;border-radius:4px;text-decoration:none;font-weight:bold;'>
      🚧 Partes Provinciales Vialidad
    </a>
    <a href='https://www.agvp.gob.ar/PartesDiarios/PartesNacionales.pdf' target='_blank'
       style='background:black;color:orange;border:2px solid orange;padding:6px 12px;
              margin:0 4px;border-radius:4px;text-decoration:none;font-weight:bold;'>
      🚧 Partes Nacionales Vialidad
    </a>
    <a href='https://www.inpres.gob.ar/desktop/' target='_blank'
       style='background:black;color:orange;border:2px solid orange;padding:6px 12px;
              margin:0 4px;border-radius:4px;text-decoration:none;font-weight:bold;'>
      🌐 INPRES – Sismos
    </a>
    <a href='https://www.csn.uchile.cl/' target='_blank'
       style='background:black;color:orange;border:2px solid orange;padding:6px 12px;
              margin:0 4px;border-radius:4px;text-decoration:none;font-weight:bold;'>
      🌎 CSN Chile – Sismos
    </a>
  </div>""", unsafe_allow_html=True)
# -----------------------------------------------------------
# 📥 Botón de descarga del pronóstico extendido a 5 días (.xlsx)
# -----------------------------------------------------------
st.markdown("---")
st.markdown("### 📥 Pronóstico extendido")

try:
    with open("dashboard/reportes_clima/pronostico_5_dias.xlsx", "rb") as file:
        st.download_button(
            label="Descargar pronóstico 5 días (.xlsx)",
            data=file,
            file_name="pronostico_5_dias.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
except FileNotFoundError:
    st.error("⚠️ Archivo de pronóstico no encontrado. Verificá si fue subido correctamente al repositorio.")
