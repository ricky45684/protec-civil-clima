import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import pytz
import numpy as np
from io import BytesIO
import unicodedata

def normalize(s):
    """Devuelve el string en minúsculas, sin tildes ni espacios extras."""
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s

# --- CONFIGURACIÓN BÁSICA ---
API_KEY = "..."  # ← tu key de OpenWeather
ORANGE = "#ff9100"
DATA_FILE = "dashboard/data/Localidades_Santa_Cruz_Coordenadas_DD.xlsx"
LOGO_PC = "dashboard/assets/escudo_pc.png"
LOGO_RRD = "dashboard/assets/escudo_rrd.png"

st.markdown("""
<div style='text-align:center; margin-bottom:12px;'>
    <a href="https://www.agvp.gob.ar/PartesDiarios/PartesProvinciales.pdf" target="_blank" style="color:orange; background:black; border:2px solid orange; padding:10px 24px; margin:5px 10px; border-radius:12px; text-decoration:none; font-weight:bold; display:inline-block;">
        📄 Parte Provincial (PDF)
    </a>
    <a href="https://www.agvp.gob.ar/PartesDiarios/PartesNacionales.pdf" target="_blank" style="color:orange; background:black; border:2px solid orange; padding:10px 24px; margin:5px 10px; border-radius:12px; text-decoration:none; font-weight:bold; display:inline-block;">
        🛣️ Parte Nacional (PDF)
    </a>
</div>
""", unsafe_allow_html=True)

def limpiar_texto_pdf(txt):
    # Elimina acentos, reemplaza caracteres especiales, para evitar errores de PDF
    if not isinstance(txt, str):
        txt = str(txt)
    accents = "áéíóúÁÉÍÓÚñÑ"
    replaces = "aeiouAEIOUnN"
    for a, r in zip(accents, replaces):
        txt = txt.replace(a, r)
    txt = txt.replace("°", "o")
    return txt

def dir_cardinal(grados):
    # Convierte grados en puntos cardinales
    try:
        grados = float(grados)
    except: return "-"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    ix = int((grados+11.25)//22.5)%16
    return dirs[ix]

# --- CARGA DE LOCALIDADES ---
try:
    df = pd.read_excel(DATA_FILE, engine="openpyxl")
    df.columns = df.columns.str.strip()

except Exception as e:
    st.error("❌ Error al cargar el archivo de localidades.")
    st.stop()

# --- CLIMA POR LOCALIDAD ---
st.markdown(f"### <span style='color:{ORANGE}'>📍 Clima actual por localidad</span>", unsafe_allow_html=True)
localidades = df["Localidad"].tolist()
datos = []

now_utc = datetime.utcnow()
now_local = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
now_utc_str = now_utc.strftime("%d/%m/%Y %H:%M:%S")
now_local_str = now_local.strftime("%d/%m/%Y %H:%M:%S")

for idx, row in df.iterrows():
    nombre = row["Localidad"]
    lat, lon = row["Latitud"], row["Longitud"]
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        resp = requests.get(url, timeout=8)
        j = resp.json()
        temp = j["main"].get("temp","-")
        feel = j["main"].get("feels_like","-")
        wind = j["wind"].get("speed","-")
        gust = j["wind"].get("gust", "-")
        deg = j["wind"].get("deg","-")
        hum = j["main"].get("humidity","-")
        desc = j["weather"][0].get("description","-").capitalize()
        pres = j["main"].get("pressure","-")
        cloud = j.get("clouds",{}).get("all","-")
    except Exception:
        temp = feel = wind = gust = deg = hum = pres = cloud = desc = "-"
    datos.append({
        "loc": nombre,
        "desc": desc,
        "temp": temp,
        "feel": feel,
        "wind": round(float(wind)*3.6,1) if wind!="-" else "-",
        "gust": round(float(gust)*3.6,1) if gust!="-" else "-",
        "deg": deg,
        "hum": hum,
        "pres": pres,
        "cloud": cloud,
    })

columnas = [
    ("loc", "Localidad"),
    ("desc", "Descripción"),
    ("temp", "Temp (°C)"),
    ("feel", "Sensación (°C)"),
    ("wind", "Viento (km/h)"),
    ("gust", "Ráfagas (km/h)"),
    ("deg", "Dirección (°)"),
    ("hum", "Humedad (%)"),
]

# --- PARTE DIARIO DEL CLIMA (TABLA + PDF) ---
st.markdown(f"### <span style='color:{ORANGE}'>📝 Parte diario del clima (todas las localidades)</span>", unsafe_allow_html=True)
df_parte = pd.DataFrame(datos)
try:
    df_parte_viz = df_parte[[c[0] for c in columnas]]
    df_parte_viz.columns = [c[1] for c in columnas]
    df_parte_viz["Dirección (°)"] = df_parte["deg"].apply(
        lambda x: f"{dir_cardinal(x)}" if x != "-" else "-")
    st.dataframe(df_parte_viz.style.set_properties(**{'color':'#fff','background-color':'#232629'}), use_container_width=True)

    # Botón PDF bien ubicado, solo aparece si la tabla existe:
    if st.button("Generar parte diario PDF"):
        try:
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.set_left_margin(12)
            pdf.set_right_margin(12)
            filas_por_pagina = 20

            def encabezado():
                pdf.set_font("Arial", 'B', 16)
                pdf.set_text_color(255, 165, 0)
                pdf.cell(0, 10, "Clima Actual por Localidad - SC", 0, 1, 'C')
                pdf.set_font("Arial", '', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, f"Generado automáticamente (UTC {now_utc_str} / Local {now_local_str})", 0, 1, 'C')
                pdf.ln(4)
                pdf.set_font("Arial", 'B', 10)
                for col in df_parte_viz.columns:
                    pdf.cell(28, 10, limpiar_texto_pdf(str(col)), 1, 0, 'C')
                pdf.ln()
                pdf.set_font("Arial", '', 10)

            for i, (_, row) in enumerate(df_parte_viz.iterrows()):
                if i % filas_por_pagina == 0:
                    pdf.add_page()
                    encabezado()
                for val in row:
                    nombre = limpiar_texto_pdf(str(val if pd.notnull(val) else "-"))
                    pdf.cell(28, 10, nombre, 1, 0, 'C')
                pdf.ln()
            pdf.ln(2)
            pdf.set_font("Arial", 'I', 9)
            pdf.multi_cell(0, 8, limpiar_texto_pdf(
                "Generado automaticamente por la Direccion Provincial de Reduccion de Riesgos de Desastres"
            ), 0, 'C')
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            st.download_button(
                label="Descargar parte diario PDF",
                data=pdf_bytes,
                file_name=f"Clima_SC_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        except Exception as err:
            st.error(f"No se pudo generar el PDF. Error: {err}")

except Exception as e:
    st.error(f"ERROR al mostrar tabla: {e}")

# --- PRONÓSTICO EXTENDIDO POR LOCALIDAD (VISUAL Y PDF) ---

st.markdown(f"### <span style='color:{ORANGE}'>📅 Pronóstico extendido 5 días por localidad</span>", unsafe_allow_html=True)

df_locs = pd.read_excel(DATA_FILE, engine="openpyxl")
df_locs["localidad_norm"] = df_locs["localidad"].apply(normalize)
localidades = df_locs["localidad"].sort_values().tolist()
localidad_sel = st.selectbox("Seleccioná una localidad", localidades)

# Usar normalize para buscar la localidad seleccionada
mask = df_locs["localidad_norm"] == normalize(localidad_sel)
lat_sel = float(df_locs.loc[mask, "Latitud_DD"])
lon_sel = float(df_locs.loc[mask, "Longitud_DD"])

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
