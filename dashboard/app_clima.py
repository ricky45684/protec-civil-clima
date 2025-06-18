import streamlit as st
import pandas as pd
import requests
import os
import base64
from fpdf import FPDF
from datetime import datetime, timezone

# --- CONFIGURACIÓN ---
API_KEY      = "f003e87edb9944f319d5f706f0979fec"
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_FILE    = os.path.join(BASE_DIR, "..", "data", "Localidades_Santa_Cruz_Coordenadas_DD.xlsx")
# LOGOS desde GitHub (para funcionar en Streamlit Cloud)
LOGO_PC = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/LogoPC.png"
LOGO_RRD = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/logo_rrd_pc.png"

# FONDO desde URL pública de GitHub
FONDO = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/fondo/fondo_proteccion.jpg"

# Función para aplicar fondo remoto
def set_background_url(img_url):
    st.markdown(f"""
        <style>
          .stApp {{
            background-image: url("{img_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
          }}
        </style>
    """, unsafe_allow_html=True)

# Aplicar el fondo
set_background_url(FONDO)

REPORTES_DIR = os.path.join(BASE_DIR, "..", "reportes_clima")
os.makedirs(REPORTES_DIR, exist_ok=True)

# IDs de tus Google My Maps
MAP1 = "1gxAel478mSuzOx3VrqXTJ4KTARtwG4k"
MAP2 = "17xfwk9mz4F96f8xvPp3sbZ-5whfbntI"

WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def set_background(img_path):
    try:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
              .stApp {{
                background-image: url("data:image/jpg;base64,{b64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
              }}
            </style>
        """, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

st.set_page_config(page_title="Protección Civil - Clima SC", layout="wide")
set_background(FONDO)

# Auto-refresh cada 15 minutos
st.components.v1.html("<script>setTimeout(()=>window.location.reload(),900000);</script>", height=0)

# Hora local y UTC
now_local = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
now_utc   = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
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

# --- BOTÓN SMN ---
st.markdown("""
  <div style='text-align:center;margin:10px;'>
    <a href='https://www.smn.gob.ar/alertas' target='_blank'
       style='color:orange;background:black;border:2px solid orange;
              padding:10px 20px;border-radius:5px;text-decoration:none;
              font-weight:bold;'>
      🔔 Ver alertas del SMN
    </a>
  </div>""", unsafe_allow_html=True)

# --- VISOR WINDY ---
st.markdown("### 🛰️ Clima")
st.components.v1.iframe(
    "https://embed.windy.com/embed2.html?lat=-49.5&lon=-70"
    "&detailLat=-49.5&detailLon=-70&width=650&height=450&zoom=5"
    "&level=surface&overlay=wind&menu=&message=true&marker="
    "&calendar=now&pressure=&type=map&location=coordinates"
    "&detail=&metricWind=km/h&metricTemp=%C2%B0C&radarRange=-1",
    height=460, scrolling=False
)

# --- MAPA SANTA CRUZ ---
st.markdown("### 🗺️ Mapa Santa Cruz")
col1, col2 = st.columns(2)
with col1:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP1}&ehbc=2E312F",
                            width=640, height=480)
with col2:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP2}&ehbc=2E312F",
                            width=640, height=480)

# --- CARGA DE LOCALIDADES ---
try:
    df = pd.read_excel(DATA_FILE)
except FileNotFoundError:
    st.error("❌ No se encontró el archivo de localidades.")
    st.stop()

def dir_cardinal(deg):
    if deg == "N/D":
        return "N/D"
    dirs = ['N','NE','E','SE','S','SO','O','NO']
    return dirs[int((deg + 22.5)//45) % 8]

def get_clima(lat, lon):
    r = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={API_KEY}"
        f"&units=metric&lang=es"
    ).json()
    return {
      "loc":  r["name"],
      "icon": f"http://openweathermap.org/img/wn/{r['weather'][0]['icon']}@2x.png",
      "desc": r["weather"][0]["description"].capitalize(),
      "temp": r["main"]["temp"],
      "feel": round(r["main"]["feels_like"],1),
      "wind": round(r["wind"]["speed"]*3.6,1),
      "gust": round(r["wind"].get("gust",0)*3.6,1),
      "deg":  r["wind"].get("deg","N/D"),
      "hum":  r["main"]["humidity"],
      "pres": r["main"]["pressure"],
      "cloud":r["clouds"]["all"],
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

# --- SEMÁFORO CLIMÁTICO PROVINCIAL ---
if max_wind > 50:
    nivel, color, texto = "Alerta grave (Rojo)", "red", "Viento muy fuerte en la provincia"
elif max_wind > 30:
    nivel, color, texto = "Alerta (Amarillo)", "orange", "Viento fuerte en la provincia"
else:
    nivel = None

if nivel:
    st.markdown(f"""
      <p>🚦 **Nivel de riesgo climático provincial**:<br>
         <span style='color:{color};font-weight:bold;'>{nivel}</span><br>
         <small>{texto}</small>
      </p>""", unsafe_allow_html=True)

# --- PRONÓSTICO SEMANAL (estilo SMN + lluvia, ráfagas y nieve) ---
choice = st.selectbox("Seleccioná la localidad", df["localidad"].unique())
sel    = df[df["localidad"] == choice].iloc[0]

st.markdown(f"""
  <h3 style='text-align:center;'>PRONÓSTICO SEMANAL – {choice}</h3>
  <p style='text-align:center;font-size:0.9em;'>Fecha y hora de emisión: {now_local}</p>
""", unsafe_allow_html=True)

resp = requests.get(
    f"https://api.openweathermap.org/data/2.5/forecast?"
    f"lat={sel['Latitud_DD']}&lon={sel['Longitud_DD']}"
    f"&appid={API_KEY}&units=metric&lang=es",
    timeout=5
).json()

forecast_items = []
for itm in resp["list"]:
    d = datetime.fromtimestamp(itm["dt"]).date()
    forecast_items.append({
        "fecha": d,
        "min":   itm["main"]["temp_min"],
        "max":   itm["main"]["temp_max"],
        "pop":   itm.get("pop", 0) * 100,
        "gust":  itm["wind"].get("gust", 0) * 3.6,
        "snow":  itm.get("snow", {}).get("3h", 0),
    })

fc = (
    pd.DataFrame(forecast_items)
      .groupby("fecha")
      .agg({
        "min":  "min",
        "max":  "max",
        "pop":  "max",
        "gust": "max",
        "snow": "max"
      })
      .reset_index()
)

fc["día"]     = fc["fecha"].apply(lambda d: f"{WEEKDAYS[d.weekday()]} {d.day}")
fc["Mín"]     = fc["min"].map(lambda x: f"{x:.1f}°")
fc["Máx"]     = fc["max"].map(lambda x: f"{x:.1f}°")
fc["Lluvia"]  = fc["pop"].map(lambda x: f"{x:.0f}%")
fc["Ráfagas"] = fc["gust"].map(lambda x: f"{x:.0f} km/h")
fc["Nieve"]   = fc["snow"].map(lambda x: f"{x:.1f} mm")

st.table(
    fc.set_index("día")[["Mín","Máx","Lluvia","Ráfagas","Nieve"]].T
)

# --- SISMOS (últimas 24h M≥2.5) ---
st.markdown("### 🌎 Sismos en el mundo últimas 24hs (M≥2.5)")
try:
    eq = requests.get(
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
        timeout=5
    ).json()
    rows = []
    for f in eq["features"]:
        p = f["properties"]
        t = datetime.utcfromtimestamp(p["time"]/1000).strftime("%d/%m %H:%M UTC")
        rows.append({"Lugar": p["place"], "Mag": p["mag"], "Hora": t})
    st.table(pd.DataFrame(rows).nlargest(10, "Mag"))
except requests.RequestException:
    st.warning("⚠️ No se pudo cargar los datos de sismos. Verifique su conexión.")

# --- EXPORTAR PDF + ENLACES RÁPIDOS ---
def export_pdf(data, path=None):
    pdf = FPDF(); pdf.set_auto_page_break(True,15)
    pdf.add_page(); pdf.set_font("Arial","B",12)
    pdf.image(LOGO_PC,10,8,25); pdf.image(LOGO_RRD,170,8,25)
    pdf.ln(20); pdf.cell(0,10,"Clima Actual por Localidad - SC",0,1,'C')
    pdf.ln(2); pdf.set_font("Arial","I",9)
    pdf.cell(0,8,f"Generado automáticamente (UTC {now_utc})",0,1,'C')
    pdf.ln(5); pdf.set_font("Arial","",11)
    for d in data:
        pdf.set_font("Arial","B",11); pdf.cell(0,8,d["loc"],0,1)
        pdf.set_font("Arial","",10)
        pdf.cell(0,6,f"{d['desc']} Temp:{d['temp']:.1f}°C Sens:{d['feel']:.1f}°C",0,1)
        pdf.cell(0,6,f"Viento:{d['wind']:.1f} km/h Raf:{d['gust']:.1f} km/h Dir:{d['deg']}°",0,1)
        pdf.cell(0,6,f"Humedad:{d['hum']}% Presión:{d['pres']} hPa Nubos:{d['cloud']}%",0,1)
        pdf.ln(3)
    if not path:
        path = os.path.join(BASE_DIR, f"Clima_SC_{datetime.now():%Y%m%d}.pdf")
    pdf.output(path); return path

hoy = datetime.now().strftime("%Y%m%d")
ruta = os.path.join(REPORTES_DIR, f"Clima_SC_{hoy}.pdf")
if not os.path.exists(ruta):
    export_pdf(datos, ruta)

st.markdown("---")
if st.button("🖨️ Exportar clima a PDF"):
    p = export_pdf(datos)
    with open(p, "rb") as f:
        st.download_button("📥 Descargar PDF", f, file_name=os.path.basename(p))

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
