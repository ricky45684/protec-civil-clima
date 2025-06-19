import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import tempfile
from io import BytesIO
import pytz
import numpy as np
import html

# --- CONFIGURACIÓN ---
API_KEY = "f003e87edb9944f319d5f706f0979fec"
DATA_FILE = "dashboard/data/Localidades_Santa_Cruz_Coordenadas_DD.xlsx"

LOGO_PC = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/LogoPC.png"
LOGO_RRD = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/logo_rrd_pc.png"

MAP1 = "1gxAel478mSuzOx3VrqXTJ4KTARtwG4k"
MAP2 = "17xfwk9mz4F96f8xvPp3sbZ-5whfbntI"
WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- HORA LOCAL Y UTC ---
BA = pytz.timezone("America/Argentina/Buenos_Aires")
now_utc = datetime.now(timezone.utc)
now_ba = now_utc.astimezone(BA)
now_utc_str = now_utc.strftime("%d/%m/%Y %H:%M:%S")
now_local_str = now_ba.strftime("%d/%m/%Y %H:%M:%S")

st.set_page_config(page_title="Protección Civil - Clima SC", layout="wide")

st.markdown(
    f"<p style='text-align:right;color:lightgray;'>Última actualización: {now_local_str} (UTC {now_utc_str})</p>",
    unsafe_allow_html=True
)

# --- FUNCIONES AUXILIARES ---
def limpiar_texto_pdf(txt):
    if not isinstance(txt, str):
        txt = str(txt)
    txt = (txt.replace('á', 'a').replace('é', 'e').replace('í', 'i')
            .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            .replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
            .replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N'))
    txt = txt.replace('°', 'o')
    txt = txt.replace('’','\'')
    txt = txt.encode("ascii", errors="ignore").decode()
    return txt

def dir_cardinal(deg):
    if deg == "N/D" or deg == "-" or deg == "" or deg is None:
        return "N/D"
    dirs = ['N','NE','E','SE','S','SO','O','NO']
    try:
        return dirs[int(((float(deg) + 22.5)%360)//45) % 8]
    except:
        return "N/D"

def get_clima(lat, lon):
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}"
            f"&appid={API_KEY}&units=metric&lang=es", timeout=6).json()
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
    except Exception as e:
        return {
            "loc": "N/D", "icon": "", "desc": "Error", "temp": "-", "feel": "-",
            "wind": "-", "gust": "-", "deg": "-", "hum": "-", "pres": "-", "cloud": "-"
        }

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

st.markdown("""
  <div style='text-align:center;margin:10px;'>
    <a href='https://www.smn.gob.ar/alertas' target='_blank'
       style='color:orange;background:black;border:2px solid orange;
              padding:10px 20px;border-radius:5px;text-decoration:none;
              font-weight:bold;'>🔔 Ver alertas del SMN</a>
  </div>""", unsafe_allow_html=True)

st.markdown("### 🛰️ Clima")
st.components.v1.iframe(
    "https://embed.windy.com/embed2.html?lat=-49.5&lon=-70&detailLat=-49.5&detailLon=-70&width=650&height=450&zoom=5"
    "&level=surface&overlay=wind&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates"
    "&detail=&metricWind=km/h&metricTemp=%C2%B0C&radarRange=-1",
    height=460, scrolling=False
)

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

# --- CLIMA POR LOCALIDAD ---
st.markdown("### 🌡️ Clima actual por localidad")
cols = st.columns(2)
datos = []
max_wind = 0
for i, row in df.iterrows():
    c = get_clima(row["Latitud_DD"], row["Longitud_DD"])
    c["loc"] = row["localidad"]
    datos.append(c)
    max_wind = max(max_wind, c["wind"] if isinstance(c["wind"], (int, float)) else 0)
    with cols[i%2]:
        st.markdown(f"""
        <div style='background:rgba(0,0,0,0.6);padding:12px;border-radius:8px;margin-bottom:8px;'>
          <h4 style='color:#58a6ff;'>{c['loc']}</h4>
          <img src='{c['icon']}' width=40>
          <p>{c['desc']}</p>
          <p>Temp: {c['temp']}°C | Sens: {c['feel']}°C</p>
          <p>Viento: {c['wind']} km/h | Ráfagas: {c['gust']} km/h</p>
          <p>Dirección: {c['deg']}° ({dir_cardinal(c['deg'])})</p>
          <p>Humedad: {c['hum']}% | Presión: {c['pres']} hPa | Nubosidad: {c['cloud']}%</p>
        </div>""", unsafe_allow_html=True)

# --- PARTE DIARIO DEL CLIMA (TABLA + PDF) ---
st.markdown("### 📝 Parte diario del clima (todas las localidades)")

df_parte = pd.DataFrame(datos)
columnas = [
    ("loc", "Localidad"),
    ("desc", "Descripción"),
    ("temp", "Temp (°C)"),
    ("feel", "Sensación (°C)"),
    ("wind", "Viento (km/h)"),
    ("gust", "Ráfagas (km/h)"),
    ("deg", "Dirección (°)"),
    ("hum", "Humedad (%)"),
    ("pres", "Presión (hPa)"),
    ("cloud", "Nubosidad (%)"),
]
try:
    df_parte_viz = df_parte[[c[0] for c in columnas]]
    df_parte_viz.columns = [c[1] for c in columnas]
    df_parte_viz["Dirección (°)"] = df_parte["deg"].apply(
        lambda x: f"{x}° ({dir_cardinal(x)})" if x != "-" else "-")
    st.dataframe(df_parte_viz, use_container_width=True)
except Exception as e:
    st.error(f"ERROR al mostrar tabla: {e}")

def generar_parte_pdf(df, now_local, now_utc, logo_izq=LOGO_PC, logo_der=LOGO_RRD):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    try:
        pdf.image(logo_izq, 12, 10, 24)
        pdf.image(logo_der, 265, 10, 24)
    except Exception:
        pass
    pdf.set_xy(0, 20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 18, "Clima Actual por Localidad - SC", 0, 1, "C")
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 7, limpiar_texto_pdf(f"Generado automaticamente (UTC {now_utc} / Local {now_local})"), 0, 1, "C")
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    col_widths = [36, 36, 18, 22, 22, 22, 27, 18, 22, 24]
    for ix, col in enumerate(df.columns):
        pdf.cell(col_widths[ix], 8, limpiar_texto_pdf(str(col)), border=1, align='C')
    pdf.ln()
    pdf.set_font("Arial", '', 10)
    for idx, row in df.iterrows():
        for ix, col in enumerate(df.columns):
            txt = str(row[col]) if row[col] is not None else ""
            txt = limpiar_texto_pdf(txt)
            if len(txt) > 20:
                txt = txt[:17] + "..."
            pdf.cell(col_widths[ix], 7, txt, border=1, align='C')
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 9)
    pdf.multi_cell(0, 8, limpiar_texto_pdf(
        "Generado automaticamente por la Direccion Provincial de Reduccion de Riesgos de Desastres"
    ), 0, 'C')
    return pdf

if st.button("Generar parte diario PDF"):
    pdf = generar_parte_pdf(df_parte_viz, now_local_str, now_utc_str)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        st.download_button(
            label="Descargar parte diario PDF",
            data=tmp.read(),
            file_name=f"Clima_SC_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# --- PRONÓSTICO EXTENDIDO POR LOCALIDAD (VISUAL Y PDF) ---
st.markdown("### 📅 Pronóstico extendido 5 días por localidad")

df_locs = pd.read_excel(DATA_FILE, engine="openpyxl")
localidades = df_locs["localidad"].sort_values().tolist()
localidad_sel = st.selectbox("Seleccioná una localidad", localidades)

lat_sel = float(df_locs[df_locs["localidad"] == localidad_sel]["Latitud_DD"])
lon_sel = float(df_locs[df_locs["localidad"] == localidad_sel]["Longitud_DD"])

with st.spinner("Buscando pronóstico..."):
    api_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat_sel}&lon={lon_sel}&appid={API_KEY}&units=metric&lang=es"
    r = requests.get(api_url, timeout=10)
    data = r.json()

pronostico_diario = {}
for item in data["list"]:
    dt = datetime.fromtimestamp(item["dt"])
    fecha = dt.strftime("%Y-%m-%d")
    dia_semana = WEEKDAYS[dt.weekday()]
    if fecha not in pronostico_diario:
        pronostico_diario[fecha] = {
            "Día": dia_semana,
            "Fecha": fecha,
            "Iconos": [],
            "Descripción": [],
            "Temp_max": [],
            "Temp_min": [],
            "Viento": [],
            "Ráfagas": [],
            "Dir_viento": [],
            "Precip": [],
        }
    pronostico_diario[fecha]["Iconos"].append(item["weather"][0]["icon"])
    pronostico_diario[fecha]["Descripción"].append(item["weather"][0]["description"].capitalize())
    pronostico_diario[fecha]["Temp_max"].append(item["main"]["temp_max"])
    pronostico_diario[fecha]["Temp_min"].append(item["main"]["temp_min"])
    pronostico_diario[fecha]["Viento"].append(item["wind"]["speed"]*3.6)
    pronostico_diario[fecha]["Ráfagas"].append(item["wind"].get("gust", 0)*3.6)
    pronostico_diario[fecha]["Dir_viento"].append(item["wind"]["deg"])
    pronostico_diario[fecha]["Precip"].append(item.get("pop", 0)*100)

def cardinal(d):
    dirs = ['N','NE','E','SE','S','SO','O','NO']
    ix = int(((d + 22.5)%360)//45) % 8
    return dirs[ix]

dias = []
iconos = []
descripciones = []
temp_maxs = []
temp_mins = []
vientos = []
dirs = []
rafagas = []
precips = []

for fecha, v in list(pronostico_diario.items())[:5]:
    dias.append(f"{v['Día']} {fecha[8:10]}")
    icono = max(set(v["Iconos"]), key=v["Iconos"].count)
    iconos.append(icono)
    des = max(set(v["Descripción"]), key=v["Descripción"].count)
    descripciones.append(des)
    temp_maxs.append(round(max(v["Temp_max"]),1))
    temp_mins.append(round(min(v["Temp_min"]),1))
    vientos.append(round(sum(v["Viento"])/len(v["Viento"]),1))
    rafagas.append(round(max(v["Ráfagas"]),1))
    dir_prom = int(sum(v["Dir_viento"])/len(v["Dir_viento"]))
    dirs.append(f"{dir_prom}° ({cardinal(dir_prom)})")
    precips.append(f"{round(max(v['Precip']))}%")

def icon_url(code): return f"http://openweathermap.org/img/wn/{code}@2x.png"
st.markdown(f"#### <center>{localidad_sel}, Santa Cruz</center>", unsafe_allow_html=True)

col1, col2 = st.columns([2,8])
with col1:
    st.write("")

with col2:
    html_txt = "<table style='width:100%;text-align:center'><tr><th></th>"
    for d in dias:
        html_txt += f"<th style='font-size:17px'>{d}</th>"
    html_txt += "</tr><tr><td><b>Estado</b></td>"
    for i in range(5):
        html_txt += f"<td><img src='{icon_url(iconos[i])}' width='48'><br>{descripciones[i]}</td>"
    html_txt += "</tr><tr><td><b>Temp máx/mín (°C)</b></td>"
    for i in range(5):
        html_txt += f"<td>{temp_maxs[i]}° / {temp_mins[i]}°</td>"
    html_txt += "</tr><tr><td><b>Viento (km/h)</b></td>"
    for i in range(5):
        html_txt += f"<td>{vientos[i]}</td>"
    html_txt += "</tr><tr><td><b>Ráfagas (km/h)</b></td>"
    for i in range(5):
        html_txt += f"<td>{rafagas[i]}</td>"
    html_txt += "</tr><tr><td><b>Dirección</b></td>"
    for i in range(5):
        html_txt += f"<td>{dirs[i]}</td>"
    html_txt += "</tr><tr><td><b>Prob. Precip (%)</b></td>"
    for i in range(5):
        html_txt += f"<td>{precips[i]}</td>"
    html_txt += "</tr></table>"
    st.markdown(html_txt, unsafe_allow_html=True)

# --- BLOQUE PDF CORREGIDO ---
class PronosticoPDF(FPDF):
    def header(self):
        try:
            self.image(LOGO_PC, 10, 8, 18)
            self.image(LOGO_RRD, 180, 8, 18)
        except: pass
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, limpiar_texto_pdf(f'Pronostico extendido 5 dias – {localidad_sel}, Santa Cruz'), 0, 1, 'C')
        self.set_font('Arial', '', 11)
        self.cell(0, 7, limpiar_texto_pdf(f"Generado automaticamente (UTC {now_utc_str} / Local {now_local_str})"), 0, 1, "C")
        self.ln(3)
    def footer(self):
        self.set_y(-12)
        self.set_font('Arial', 'I', 9)
        self.cell(0, 8, limpiar_texto_pdf("Generado automaticamente por la Direccion Provincial de Reduccion de Riesgos de Desastres"), 0, 0, 'C')

if st.button("Descargar pronóstico 5 días en PDF"):
    pdf = PronosticoPDF('L', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 10, limpiar_texto_pdf(""), 1, 0, "C")
    for d in dias:
        pdf.cell(40, 10, limpiar_texto_pdf(d), 1, 0, "C")
    pdf.ln()
    pdf.set_font('Arial', '', 10)
    pdf.cell(45, 10, limpiar_texto_pdf("Estado"), 1)
    for i in range(5):
        pdf.cell(40, 10, limpiar_texto_pdf(descripciones[i]), 1, 0, "C")
    pdf.ln()
    pdf.cell(45, 10, limpiar_texto_pdf("Temp max/min (C)"), 1)
    for i in range(5):
        pdf.cell(40, 10, limpiar_texto_pdf(f"{temp_maxs[i]} / {temp_mins[i]}"), 1, 0, "C")
    pdf.ln()
    pdf.cell(45, 10, limpiar_texto_pdf("Viento (km/h)"), 1)
    for i in range(5):
        pdf.cell(40, 10, limpiar_texto_pdf(f"{vientos[i]}"), 1, 0, "C")
    pdf.ln()
    pdf.cell(45, 10, limpiar_texto_pdf("Rafagas (km/h)"), 1)
    for i in range(5):
        pdf.cell(40, 10, limpiar_texto_pdf(f"{rafagas[i]}"), 1, 0, "C")
    pdf.ln()
    pdf.cell(45, 10, limpiar_texto_pdf("Direccion"), 1)
    for i in range(5):
        pdf.cell(40, 10, limpiar_texto_pdf(dirs[i]), 1, 0, "C")
    pdf.ln()
    pdf.cell(45, 10, limpiar_texto_pdf("Prob. Precip (%)"), 1)
    for i in range(5):
        pdf.cell(40, 10, limpiar_texto_pdf(f"{precips[i]}"), 1, 0, "C")
    pdf.ln()
    tmp_pdf = BytesIO()
    pdf.output(tmp_pdf)
    st.download_button(
        label="Descargar PDF",
        data=tmp_pdf.getvalue(),
        file_name=f"Pronostico5dias_{localidad_sel.replace(' ','_')}.pdf",
        mime="application/pdf"
    )

# --- SEMÁFORO MULTICRITERIO POR DEPARTAMENTO Y TABLA DE SISMOS (pegá aquí el bloque actual de tu script, no es necesario modificarlo para unicode) ---
