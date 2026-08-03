import streamlit as st
import pandas as pd
import json
from fpdf import FPDF
import os
import re
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# =============================================================================
# 1. CONFIGURACIÓN E INTERFAZ (AQUÍ METERÁS TU NUEVO DISEÑO DESPUÉS)
# =============================================================================
st.set_page_config(page_title="Horario ITS | Ago-Dic 2026", page_icon="🦅", layout="wide")

st.markdown("""
<style>
    :root { --guinda: #800000; --fondo-oscuro: #0e1117; }
    h1, h2, h3 { color: var(--guinda) !important; font-family: 'Arial', sans-serif; }
    /* Checkboxes tipo tarjeta */
    [data-testid="stCheckbox"] label span[role="checkbox"] { display: none !important; }
    [data-testid="stCheckbox"] label { border: 1px solid rgba(128, 128, 128, 0.4); padding: 5px; border-radius: 6px; width: 100%; min-height: 90px; display: flex; align-items: center; justify-content: center; text-align: center; transition: all 0.2s; cursor: pointer; }
    [data-testid="stCheckbox"] label:hover { border-color: var(--guinda); background-color: rgba(128, 0, 0, 0.15); }
    [data-testid="stCheckbox"]:has(input:checked) label { background-color: var(--guinda) !important; border-color: var(--guinda) !important; }
    [data-testid="stCheckbox"]:has(input:checked) div[data-testid="stMarkdownContainer"] p { color: white !important; font-weight: bold !important; }
    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p { font-size: 0.85em; margin: 0; color: #e0e0e0; }
    /* Botones y Alertas */
    .stButton>button { color: white !important; background-color: var(--guinda) !important; border: none; font-weight: bold; border-radius: 6px; }
    .stButton>button:hover { background-color: #a00000 !important; }
    .credit-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 10px; }
    .credit-ok { background-color: rgba(4, 95, 70, 0.3); color: #34d399; border: 1px solid #34d399; }
    .credit-error { background-color: rgba(153, 27, 27, 0.3); color: #f87171; border: 1px solid #f87171; }
    .semestre-header { color: var(--guinda) !important; font-weight: 900; font-size: 1em; text-align: center; border-bottom: 3px solid var(--guinda); margin-bottom: 10px; }
    /* Tabla */
    .horario-grid { width: 100%; border-collapse: collapse; text-align: center; font-size: 0.8em; background-color: #ffffff; color: black; border-radius: 8px; overflow: hidden; }
    .horario-grid th { background-color: var(--guinda); color: white; padding: 8px; border: 1px solid #444; }
    .horario-grid td { border: 1px solid #ddd; height: 45px; vertical-align: middle; padding: 2px; }
    .hora-col { background-color: #e0e0e0; font-weight: bold; width: 70px; }
    .clase-cell { border-radius: 4px; padding: 4px; color: #111; font-weight: 700; font-size: 0.95em; height: 100%; display: flex; flex-direction: column; justify-content: center; }
</style>
""", unsafe_allow_html=True)

COLORS = ['#FFCDD2', '#F8BBD0', '#E1BEE7', '#D1C4E9', '#C5CAE9', '#BBDEFB', '#B3E5FC', '#B2EBF2', '#B2DFDB', '#C8E6C9', '#DCEDC8', '#F0F4C3']

# =============================================================================
# 2. CONEXIÓN A GOOGLE SHEETS (WAZE ACADÉMICO Y OPINIONES)
# =============================================================================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_db_connection():
    if "gcp_service_account" not in st.secrets: return None
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info: creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        return gspread.authorize(creds)
    except: return None

db_client = get_db_connection()

# =============================================================================
# 3. BASE DE DATOS LOCAL (REGLAS MECATRÓNICA)
# =============================================================================
CREDITOS = {
    "Química": 4, "Cálculo Diferencial": 5, "Taller de Ética": 4, "Dibujo Asistido por Computadora": 4, "Metrología y Normalización": 4, "Fundamentos de Investigación": 4,
    "Cálculo Integral": 5, "Álgebra Lineal": 5, "Ciencia e Ingeniería de Materiales": 5, "Programación Básica": 5, "Estadística y Control de Calidad": 4, "Administración y Contabilidad": 4,
    "Cálculo Vectorial": 5, "Procesos de Fabricación": 4, "Electromagnetismo": 5, "Estática": 4, "Métodos Numéricos": 4, "Desarrollo Sustentable": 5,
    "Ecuaciones Diferenciales": 5, "Fundamentos de Termodinámica": 4, "Mecánica de Materiales": 6, "Dinámica": 4, "Análisis de Circuitos Eléctricos": 6, "Taller de Investigación I": 4,
    "Máquinas Eléctricas": 5, "Electrónica Analógica": 6, "Mecanismos": 5, "Análisis de Fluidos": 4, "Taller de Investigación II": 4, "Programación Avanzada": 6,
    "Electrónica de Potencia Aplicada": 6, "Instrumentación": 5, "Diseño de Elementos Mecánicos": 5, "Electrónica Digital": 5, "Vibraciones Mecánicas": 5, "Administración del Mantenimiento": 4,
    "Manufactura Avanzada": 5, "Diseño Asistido por Computadora": 5, "Dinámica de Sistemas": 5, "Circuitos Hidráulicos y Neumáticos": 6, "Mantenimiento": 5, "Microcontroladores": 5,
    "Formulación y Evaluación de Proyectos": 3, "Controladores Lógicos Programables": 5, "Control": 6, "Sistemas Avanzados de Manufactura": 5, "Redes Industriales": 5,
    "Robótica": 5, "Tópicos Selectos de Automatización Industrial": 6
}

# =============================================================================
# 4. MOTOR LÓGICO (EL CEREBRO DEL SISTEMA)
# =============================================================================
@st.cache_data
def load_oferta_json(periodo, carrera):
    filepath = f"data/{periodo}/{carrera}.json"
    if not os.path.exists(filepath): return None
    with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)

def format_json_to_oferta(json_data):
    oferta = {}; mat_sem = {i: [] for i in range(1, 10)}
    for key, info in json_data.get("materias", {}).items():
        nombre = info["nombre"]; sem = int(info.get("semestre", 1))
        if 1 <= sem <= 9: mat_sem[sem].append(nombre)
        oferta[nombre] = []
        for g in info.get("grupos", []):
            oferta[nombre].append({
                "profesor": g["profesor"], "salon": g.get("salon", "TBA"),
                "horario": [(h["dia"], h["inicio"], h["fin"]) for h in g.get("horario", [])],
                "id": g.get("id", ""), "materia": nombre
            })
    return oferta, mat_sem

def traslape(h1, h2):
    for a in h1:
        for b in h2:
            if a[0] == b[0] and max(a[1], b[1]) < min(a[2], b[2]): return True
    return False

def generar_combinaciones(materias, rango, hrs_libres, oferta):
    bloqueos = [int(hl.split(":")[0]) for hl in hrs_libres]
    pools = []
    for mat in materias:
        if mat not in oferta: continue
        opciones = []
        for sec in oferta[mat]:
            dentro = True
            for h in sec['horario']:
                if h[1] < rango[0] or h[2] > rango[1]: dentro = False; break
                for he in range(h[1], h[2]):
                    if he in bloqueos: dentro = False; break
            if dentro: opciones.append(sec)
        if not opciones: return [], f"❌ {mat} no cuadra con tus bloqueos de tiempo."
        pools.append(opciones)

    validos = []
    def backtrack(idx, combo):
        if idx == len(pools):
            validos.append(list(combo)); return
        for sec in pools[idx]:
            if not any(traslape(sec['horario'], p['horario']) for p in combo):
                combo.append(sec); backtrack(idx + 1, combo); combo.pop()
    backtrack(0, [])
    return validos[:15], "OK" # Retorna max 15 opciones para no saturar

# =============================================================================
# 5. GENERACIÓN HTML Y PDF
# =============================================================================
def create_timetable_html(horario):
    if not horario: return ""
    horas = [h for c in horario for s in c['horario'] for h in (s[1], s[2])]
    if not horas: return ""
    min_h, max_h = min(horas), max(horas)
    tiene_sabado = any(s[0] == 5 for c in horario for s in c['horario'])
    dias = 6 if tiene_sabado else 5
    grid = {h: [None]*dias for h in range(min_h, max_h)}
    
    colores = {c['materia']: COLORS[i % len(COLORS)] for i, c in enumerate(horario)}
    for c in horario:
        for s in c['horario']:
            for h in range(s[1], s[2]):
                if s[0] < dias:
                    grid[h][s[0]] = f"<div class='clase-cell' style='background-color:{colores[c['materia']]}'><span>{c['materia']}</span><br><small>{c['profesor']}</small></div>"
    
    headers = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"][:dias]
    html = "<table class='horario-grid'><thead><tr><th class='hora-col'>Hora</th>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>"
    for h in range(min_h, max_h):
        html += f"<tr><td class='hora-col'>{h}-{h+1}</td>" + "".join(f"<td>{grid[h][d] or ''}</td>" for d in range(dias)) + "</tr>"
    return html + "</tbody></table>"

# =============================================================================
# 6. FLUJO DE NAVEGACIÓN
# =============================================================================
if 'step' not in st.session_state: st.session_state.step = 1

if st.session_state.step == 1:
    st.markdown("<h1 style='text-align: center;'>Horario ITS 🦅</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.container(border=True)
        st.text_input("📌 Periodo Académico", "AGOSTO - DICIEMBRE 2026", disabled=True)
        carrera = st.selectbox("🎓 Carrera", ["MECATRÓNICA", "INDUSTRIAL", "SISTEMAS"])
        cant = st.number_input("📚 Materias a cursar:", min_value=1, max_value=9, value=6)
        if st.button("Cargar Oferta ➡️", use_container_width=True, type="primary"):
            carrera_clean = carrera.split(" ")[0].lower().replace("ó", "o")
            data = load_oferta_json("2026_AGO_DIC", carrera_clean)
            if data:
                st.session_state.oferta, st.session_state.mat_sem = format_json_to_oferta(data)
                st.session_state.cant_deseada = cant
                st.session_state.carrera = carrera_clean
                st.session_state.step = 2; st.rerun()
            else: st.error(f"❌ Falta el archivo /data/2026_AGO_DIC/{carrera_clean}.json")

elif st.session_state.step == 2:
    st.title("📚 Selección de Materias")
    cols = st.columns(9)
    seleccion = []
    if 'seleccion' not in st.session_state: st.session_state.seleccion = []
    
    for i in range(1, 10):
        with cols[i-1]:
            st.markdown(f"<div class='semestre-header'>{i}°</div>", unsafe_allow_html=True)
            for m in st.session_state.mat_sem.get(i, []):
                if st.checkbox(f"{m} ({CREDITOS.get(m, 0)} Cr)", value=(m in st.session_state.seleccion)): seleccion.append(m)
    
    creditos_totales = sum([CREDITOS.get(m, 0) for m in seleccion])
    st.write("---")
    c_info = st.container()
    style = "credit-ok" if creditos_totales <= 36 and len(seleccion) == st.session_state.cant_deseada else "credit-error"
    c_info.markdown(f"<div class='credit-box {style}'>Créditos: {creditos_totales}/36 | Materias: {len(seleccion)}/{st.session_state.cant_deseada}</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1,1])
    if col1.button("⬅️ Volver"): st.session_state.step = 1; st.rerun()
    if len(seleccion) != st.session_state.cant_deseada or creditos_totales > 36: st.warning("⚠️ Ajusta tus materias y créditos para continuar.")
    else:
        if col2.button("Siguiente ➡️", type="primary"): st.session_state.seleccion = seleccion; st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.title("⏰ Disponibilidad y Resultados")
    col_rang, col_free = st.columns(2)
    with col_rang: rango = st.slider("Horario Global:", 7, 22, (7, 22))
    with col_free: libres = st.multiselect("Bloquear horas:", [f"{h}:00-{h+1}:00" for h in range(7, 22)])
    
    col1, col2 = st.columns([1,1])
    if col1.button("⬅️ Atrás"): st.session_state.step = 2; st.rerun()
    
    res, msg = generar_combinaciones(st.session_state.seleccion, rango, libres, st.session_state.oferta)
    if not res: st.error(msg)
    else:
        st.success(f"¡Se encontraron {len(res)} opciones!")
        for i, horario in enumerate(res):
            with st.expander(f"Opción {i+1}", expanded=(i==0)):
                st.markdown(create_timetable_html(horario), unsafe_allow_html=True)
