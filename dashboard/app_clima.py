import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import pytz
import numpy as np
from io import BytesIO

# --- CONFIGURACIÓN ---
API_KEY = "f003e87edb9944f319d5f706f0979fec"
DATA_FILE = "dashboard/data/Localidades_Santa_Cruz_Coordenadas_DD.xlsx"

LOGO_PC = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/LogoPC.png"
LOGO_RRD = "https://raw.githubusercontent.com/ricky45684/protec-civil-clima/main/dashboard/assets/logos/logo_rrd_pc.png"

WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

ORANGE = "#FFA500"

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

# --- ESTILO CUSTOM ---
st.markdown(f"""
    <style>
        html, body, [class*="st-"] {{
            background-color: #141618;
        }}
        .orange-title, .orange-button {{
            color: {ORANGE} !important;
        }}
        .stButton>button, .orange-button, .semaforo-card-title {{
            background-color: {ORANGE} !important;
            color: #fff !important;
            font-weight: bold;
        }}
        .stDataFrame, .dataframe, .sismos-table, .css-1d391kg {{
            color: #fff !important;
            background-color: #232629 !important;
        }}
        .semaforo-card {{
            background: #232629;
            border-radius: 15px;
            box-shadow: 0 2px 8px #2229;
            padding: 18px;
            margin: 10px;
            display: inline-block;
            min-width: 230px;
            max-width: 250px;
            text-align: center;
            color: #fff;
            border: 2.5px solid {ORANGE};
        }}
        .semaforo-depto {{
            color: #fff;
            font-size: 1.12em;
            font-weight: bold;
        }}
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO ---
c1, c2, c3 = st.columns([1, 6, 1])
with c1:
    st.image(LOGO_PC, width=70)
with c2:
    st.markdown(f"""
      <h1 style='text-align:center;color:{ORANGE};font-size:22px;'>
        PROTECCIÓN CIVIL Y ABORDAJE INTEGRAL DE EMERGENCIAS Y CATÁSTROFES<br>
        DIRECCIÓN PROVINCIAL DE REDUCCIÓN DE RIESGOS DE DESASTRES
      </h1>""", unsafe_allow_html=True)
with c3:
    st.image(LOGO_RRD, width=70)

# --- BOTONES DE ACCESO RÁPIDO ---
st.markdown(f"""
<div style='text-align:center;margin:10px;'>
    <a href='https://www.smn.gob.ar/alertas' target='_blank'
       style='color:{ORANGE};background:#191c21;border:2px solid {ORANGE};padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin:5px;'>🔔 Alertas SMN</a>
    <a href='https://www.argentina.gob.ar/transporte/vialidad-nacional/estado-de-rutas' target='_blank'
       style='color:{ORANGE};background:#191c21;border:2px solid {ORANGE};padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin:5px;'>🛣️ Vialidad Nacional</a>
    <a href='https://www.dpvsc.gov.ar/index.php/rutas-2/estado-de-rutas/' target='_blank'
       style='color:{ORANGE};background:#191c21;border:2px solid {ORANGE};padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin:5px;'>🛣️ Vialidad Provincial</a>
    <a href='https://www.inpres.gob.ar/desktop/index.php' target='_blank'
       style='color:{ORANGE};background:#191c21;border:2px solid {ORANGE};padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin:5px;'>🌎 INPRES – Sismos</a>
    <a href='https://www.csn.uchile.cl/' target='_blank'
       style='color:{ORANGE};background:#191c21;border:2px solid {ORANGE};padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;margin:5px;'>🌎 CSN Chile</a>
</div>
""", unsafe_allow_html=True)

# --- VISOR WINDY Y MAPAS ---
st.markdown(f"### <span style='color:{ORANGE}'>🛰️ Clima (Windy)</span>", unsafe_allow_html=True)
st.components.v1.iframe(
    "https://embed.windy.com/embed2.html?lat=-49.5&lon=-70&detailLat=-49.5&detailLon=-70&width=650&height=450&zoom=5"
    "&level=surface&overlay=wind&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates"
    "&detail=&metricWind=km/h&metricTemp=%C2%B0C&radarRange=-1",
    height=460, scrolling=False
)
MAP1 = "1gxAel478mSuzOx3VrqXTJ4KTARtwG4k"
MAP2 = "17xfwk9mz4F96f8xvPp3sbZ-5whfbntI"
st.markdown(f"### <span style='color:{ORANGE}'>🗺️ Mapas de Santa Cruz</span>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP1}&ehbc=2E312F", width=640, height=480)
with col2:
    st.components.v1.iframe(f"https://www.google.com/maps/d/embed?mid={MAP2}&ehbc=2E312F", width=640, height=480)

# --- FUNCIONES AUXILIARES ---
def limpiar_texto_pdf(txt):
    txt = str(txt)
    txt = (txt.replace('á', 'a').replace('é', 'e').replace('í', 'i')
            .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            .replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
            .replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N'))
    txt = txt.replace('°', 'o')
    txt = txt.replace('’','\'')
    txt = txt.replace('\n', ' ').replace('\r', '')
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

# --- CARGA DE LOCALIDADES ---
if st.button("Generar parte diario PDF"):
    pdf = generar_parte_pdf(df_parte_viz, now_local_str, now_utc_str)
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    st.download_button(
        label="Descargar parte diario PDF",
        data=pdf_bytes,
        file_name=f"Clima_SC_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

try:
    df = pd.read_excel(DATA_FILE, engine="openpyxl")
except Exception as e:
    st.error("❌ Error al cargar el archivo de localidades.")
    st.stop()

# --- CLIMA POR LOCALIDAD ---
st.markdown(f"### <span style='color:{ORANGE}'>🌡️ Clima actual por localidad</span>", unsafe_allow_html=True)
cols = st.columns(2)
datos = []
for i, row in df.iterrows():
    c = get_clima(row["Latitud_DD"], row["Longitud_DD"])
    c["loc"] = row["localidad"]
    datos.append(c)
    with cols[i%2]:
        st.markdown(f"""
        <div style='background:rgba(0,0,0,0.7);padding:14px;border-radius:9px;margin-bottom:10px;'>
          <h4 style='color:{ORANGE};'>{c['loc']}</h4>
          <img src='{c['icon']}' width=40>
          <p style='color:#fff'>{c['desc']}</p>
          <p style='color:#fff'>Temp: {c['temp']}°C | Sens: {c['feel']}°C</p>
          <p style='color:#fff'>Viento: {c['wind']} km/h | Ráfagas: {c['gust']} km/h</p>
          <p style='color:#fff'>Dirección: {c['deg']}° ({dir_cardinal(c['deg'])})</p>
          <p style='color:#fff'>Humedad: {c['hum']}% | Presión: {c['pres']} hPa | Nubosidad: {c['cloud']}%</p>
        </div>""", unsafe_allow_html=True)

# --- PARTE DIARIO DEL CLIMA (TABLA + PDF) ---
st.markdown(f"### <span style='color:{ORANGE}'>📝 Parte diario del clima (todas las localidades)</span>", unsafe_allow_html=True)
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
        lambda x: f"{dir_cardinal(x)}" if x != "-" else "-")
    st.dataframe(df_parte_viz.style.set_properties(**{'color':'#fff','background-color':'#232629'}), use_container_width=True)
except Exception as e:
    st.error(f"ERROR al mostrar tabla: {e}")

def generar_parte_pdf(df, now_local, now_utc, logo_izq=LOGO_PC, logo_der=LOGO_RRD):
    cols_usar = [col for col in df.columns if col not in ["Presión (hPa)", "Nubosidad (%)"]]
    df = df[cols_usar].copy()
    if "Dirección (°)" in df.columns:
        df["Dirección"] = df["Dirección (°)"].apply(lambda x: x)
        df = df.drop("Dirección (°)", axis=1)
    orden = ['Localidad', 'Descripción', 'Temp (°C)', 'Sensación (°C)', 'Viento (km/h)', 'Ráfagas (km/h)', 'Dirección', 'Humedad (%)']
    df = df[[col for col in orden if col in df.columns]]
    col_widths = [48, 48, 26, 30, 30, 30, 30, 24]

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    def tabla_header():
        pdf.set_text_color(255, 165, 0)
        pdf.set_font("Arial", 'B', 10)
        for ix, col in enumerate(df.columns):
            pdf.cell(col_widths[ix], 8, limpiar_texto_pdf(str(col)), border=1, align='C')
        pdf.ln()
        pdf.set_text_color(0,0,0)

    filas_por_pagina = 20
    for idx, row in df.iterrows():
        if idx % filas_por_pagina == 0:
            pdf.add_page()
            pdf.set_y(30)  # Encabezado más arriba
            try:
                pdf.image(logo_izq, 20, 10, 18)
                pdf.image(logo_der, 250, 10, 18)
            except Exception:
                pass
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(255, 165, 0)
            pdf.cell(0, 12, "CLIMA ACTUAL POR LOCALIDAD - PROTECCION CIVIL", 0, 1, "C")
            pdf.set_text_color(0,0,0)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 7, limpiar_texto_pdf(f"Generado automaticamente (UTC {now_utc} / Local {now_local})"), 0, 1, "C")
            pdf.ln(2)
            tabla_header()
            pdf.set_font("Arial", '', 10)
        for ix, col in enumerate(df.columns):
            txt = str(row[col]) if row[col] is not None else ""
            txt = limpiar_texto_pdf(txt)
            if len(txt) > 20:
                txt = txt[:17] + "..."
            pdf.cell(col_widths[ix], 7, txt, border=1, align='C')
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(0, 8, limpiar_texto_pdf(
        "Generado automaticamente por la Direccion Provincial de Reduccion de Riesgos de Desastres"
    ), 0, 'C')
    return pdf


# --- PRONÓSTICO EXTENDIDO POR LOCALIDAD (VISUAL Y PDF) ---
st.markdown(f"### <span style='color:{ORANGE}'>📅 Pronóstico extendido 5 días por localidad</span>", unsafe_allow_html=True)

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

def icon_url(code): return f"http://openweathermap.org/img/wn/{code}@2x.png"

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
    dirs.append(f"{dir_cardinal(dir_prom)}")
    precips.append(f"{round(max(v['Precip']))}%")

st.markdown(f"#### <center style='color:{ORANGE}'>{localidad_sel}, Santa Cruz</center>", unsafe_allow_html=True)

col1, col2 = st.columns([2,8])
with col1:
    st.write("")
with col2:
    html_txt = "<table style='width:100%;text-align:center'><tr><th></th>"
    for d in dias:
        html_txt += f"<th style='color:{ORANGE};font-size:17px'>{d}</th>"
    html_txt += "</tr><tr><td style='color:#fff'><b>Estado</b></td>"
    for i in range(5):
        html_txt += f"<td style='color:#fff'><img src='{icon_url(iconos[i])}' width='48'><br>{descripciones[i]}</td>"
    html_txt += "</tr><tr><td style='color:#fff'><b>Temp máx/mín (°C)</b></td>"
    for i in range(5):
        html_txt += f"<td style='color:#fff'>{temp_maxs[i]}° / {temp_mins[i]}°</td>"
    html_txt += "</tr><tr><td style='color:#fff'><b>Viento (km/h)</b></td>"
    for i in range(5):
        html_txt += f"<td style='color:#fff'>{vientos[i]}</td>"
    html_txt += "</tr><tr><td style='color:#fff'><b>Ráfagas (km/h)</b></td>"
    for i in range(5):
        html_txt += f"<td style='color:#fff'>{rafagas[i]}</td>"
    html_txt += "</tr><tr><td style='color:#fff'><b>Dirección</b></td>"
    for i in range(5):
        html_txt += f"<td style='color:#fff'>{dirs[i]}</td>"
    html_txt += "</tr><tr><td style='color:#fff'><b>Prob. Precip (%)</b></td>"
    for i in range(5):
        html_txt += f"<td style='color:#fff'>{precips[i]}</td>"
    html_txt += "</tr></table>"
    st.markdown(html_txt, unsafe_allow_html=True)

class PronosticoPDF(FPDF):
    def header(self):
        try:
            self.image(LOGO_PC, 20, 8, 16)
            self.image(LOGO_RRD, 250, 8, 16)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(255,165,0)
        self.cell(0, 13, limpiar_texto_pdf(f'Pronostico extendido 5 dias  {localidad_sel} Santa Cruz'), 0, 1, 'C')
        self.set_text_color(0,0,0)
        self.set_font('Arial', '', 11)
        self.cell(0, 7, limpiar_texto_pdf(f"Generado automaticamente (UTC {now_utc_str} / Local {now_local_str})"), 0, 1, "C")
        self.ln(2)
    def footer(self):
        self.set_y(-12)
        self.set_font('Arial', 'I', 9)
        self.cell(0, 8, limpiar_texto_pdf("Generado automaticamente por la Direccion Provincial de Reduccion de Riesgos de Desastres"), 0, 0, 'C')
if st.button("Descargar pronóstico 5 días en PDF"):
    def completar(lst, relleno="-"):
        lst = list(lst)
        while len(lst) < 5:
            lst.append(relleno)
        return lst[:5]
    dias_corr = completar(dias, "-")
    descripciones_corr = completar(descripciones, "-")
    temp_maxs_corr = completar(temp_maxs, "-")
    temp_mins_corr = completar(temp_mins, "-")
    vientos_corr = completar(vientos, "-")
    rafagas_corr = completar(rafagas, "-")
    dirs_corr = completar(dirs, "-")
    precips_corr = completar(precips, "-")
    try:
        pdf = PronosticoPDF('L', 'mm', 'A4')
        pdf.add_page()
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(255, 165, 0)
        pdf.cell(45, 10, limpiar_texto_pdf(""), 1, 0, "C")
        for d in dias_corr:
            pdf.cell(40, 10, limpiar_texto_pdf(d), 1, 0, "C")
        pdf.set_text_color(0,0,0)
        pdf.ln()
        pdf.set_font('Arial', '', 10)
        pdf.cell(45, 10, limpiar_texto_pdf("Estado"), 1)
        for i in range(5):
            pdf.cell(40, 10, limpiar_texto_pdf(descripciones_corr[i]), 1, 0, "C")
        pdf.ln()
        pdf.cell(45, 10, limpiar_texto_pdf("Temp max/min (C)"), 1)
        for i in range(5):
            pdf.cell(40, 10, limpiar_texto_pdf(f"{temp_maxs_corr[i]} / {temp_mins_corr[i]}"), 1, 0, "C")
        pdf.ln()
        pdf.cell(45, 10, limpiar_texto_pdf("Viento (km/h)"), 1)
        for i in range(5):
            pdf.cell(40, 10, limpiar_texto_pdf(f"{vientos_corr[i]}"), 1, 0, "C")
        pdf.ln()
        pdf.cell(45, 10, limpiar_texto_pdf("Rafagas (km/h)"), 1)
        for i in range(5):
            pdf.cell(40, 10, limpiar_texto_pdf(f"{rafagas_corr[i]}"), 1, 0, "C")
        pdf.ln()
        pdf.cell(45, 10, limpiar_texto_pdf("Direccion"), 1)
        for i in range(5):
            pdf.cell(40, 10, limpiar_texto_pdf(dirs_corr[i]), 1, 0, "C")
        pdf.ln()
        pdf.cell(45, 10, limpiar_texto_pdf("Prob. Precip (%)"), 1)
        for i in range(5):
            pdf.cell(40, 10, limpiar_texto_pdf(f"{precips_corr[i]}"), 1, 0, "C")
        pdf.ln()
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name=f"Pronostico5dias_{localidad_sel.replace(' ','_')}.pdf",
            mime="application/pdf"
        )
    except Exception as err:
        st.error(f"No se pudo generar el PDF. Error: {err}")

# --- SEMÁFORO MULTICRITERIO POR DEPARTAMENTO (con explicación) ---
st.markdown(f"### <span style='color:{ORANGE}'>🚦 Semáforo meteorológico por departamento</span>", unsafe_allow_html=True)
deptos = [
    "Guer Aike", "Corpen Aike", "Magallanes", "Deseado",
    "Lago Buenos Aires", "Rio Chico", "Lago Argentino"
]
estado_deptos = {
    "Guer Aike": ("🟢 Normal", ""),
    "Corpen Aike": ("🟡 Precaución", "Precaución: Vientos fuertes <span style='font-size:1.3em;'>💨</span>"),
    "Magallanes": ("🟢 Normal", ""),
    "Deseado": ("🔴 Riesgo", "Riesgo: Posible inundación <span style='font-size:1.3em;'>🌊</span>"),
    "Lago Buenos Aires": ("🟢 Normal", ""),
    "Rio Chico": ("🟡 Precaución", "Precaución: Nevadas intensas <span style='font-size:1.3em;'>❄️</span>"),
    "Lago Argentino": ("🟢 Normal", ""),
}
colA, colB = st.columns(2)
for i, dep in enumerate(deptos):
    estado, causa = estado_deptos.get(dep, ("-", ""))
    card = f"""<div class="semaforo-card">
        <div class="semaforo-card-title" style="color:{ORANGE};font-weight:bold;font-size:1.15em;">{dep}</div>
        <div class="semaforo-depto">{estado}</div>"""
    # Si hay causa, la agrego
    if "Precaución" in estado:
        card += f"""<div style="margin-top:7px;color:{ORANGE};font-weight:bold;">{causa}</div>"""
    elif "Riesgo" in estado:
        card += f"""<div style="margin-top:7px;color:#FF3B3B;font-weight:bold;">{causa}</div>"""
    card += "</div>"
    if i < 4:
        colA.markdown(card, unsafe_allow_html=True)
    else:
        colB.markdown(card, unsafe_allow_html=True)


# --- SISMOS GLOBALES (USGS) ---
st.markdown(f"### <span style='color:{ORANGE}'>🌍 Últimos sismos globales (USGS)</span>", unsafe_allow_html=True)
try:
    r = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson", timeout=10)
    features = r.json()["features"][:10]
    data = []
    for f in features:
        props = f["properties"]
        coords = f["geometry"]["coordinates"]
        time_str = datetime.utcfromtimestamp(props["time"]/1000).strftime('%d/%m %H:%M')
        mag = props.get("mag","-")
        place = props.get("place","-")
        url = props.get("url","#")
        depth = coords[2] if len(coords) > 2 else "-"
        data.append([time_str, mag, place, depth, url])
    df_eq = pd.DataFrame(data, columns=["Fecha/hora UTC", "Magnitud", "Lugar", "Profundidad (km)", "Ver evento"])
    def make_clickable(val):
        return f'<a href="{val}" target="_blank" style="color:{ORANGE}">🔗 Link</a>' if val.startswith("http") else "-"
    df_eq["Ver evento"] = df_eq["Ver evento"].apply(make_clickable)
    st.write(df_eq.to_html(escape=False, index=False), unsafe_allow_html=True)
except Exception as e:
    st.warning("No se pudo cargar la lista de sismos globales.")

# --- FIN DEL SCRIPT ---
