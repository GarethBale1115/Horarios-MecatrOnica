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

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN VISUAL
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Horario ITS", page_icon="🦅", layout="wide")

st.markdown("""
<style>
    :root { --guinda: #800000; --fondo-oscuro: #0e1117; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--guinda) !important; font-family: 'Arial', sans-serif; }
    
    /* TARJETAS */
    [data-testid="stCheckbox"] label span[role="checkbox"] { display: none !important; }
    [data-testid="stCheckbox"] label {
        border: 1px solid rgba(128, 128, 128, 0.4); background-color: transparent;
        padding: 5px; border-radius: 6px; width: 100%; min-height: 90px;
        display: flex; align-items: center; justify-content: center; text-align: center;
        transition: all 0.2s; cursor: pointer;
    }
    [data-testid="stCheckbox"] label:hover { border-color: var(--guinda); background-color: rgba(128, 0, 0, 0.15); }
    [data-testid="stCheckbox"]:has(input:checked) label { background-color: var(--guinda) !important; border-color: var(--guinda) !important; }
    [data-testid="stCheckbox"]:has(input:checked) div[data-testid="stMarkdownContainer"] p { color: white !important; font-weight: bold !important; }
    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p { font-size: 0.85em; line-height: 1.3; margin: 0; color: #e0e0e0; text-align: center; }
    
    /* ALERTAS DE REPORTE */
    .report-badge { color: #d32f2f; background-color: #ffebee; border: 1px solid #d32f2f; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: bold; display: inline-block; margin-left: 5px; }

    /* CREDIT BOXES */
    .credit-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 10px; }
    .credit-ok { background-color: rgba(4, 95, 70, 0.3); color: #34d399; border: 1px solid #34d399; }
    .credit-error { background-color: rgba(153, 27, 27, 0.3); color: #f87171; border: 1px solid #f87171; }
    
    /* ENCABEZADOS DE SEMESTRE */
    .semestre-header { color: var(--guinda) !important; font-weight: 900; font-size: 1em; text-align: center; border-bottom: 3px solid var(--guinda); margin-bottom: 10px; text-transform: uppercase; }

    /* BOTONES */
    .stButton>button { color: white !important; background-color: var(--guinda) !important; border: none; font-weight: bold; border-radius: 6px; }
    .stButton>button:hover { background-color: #a00000 !important; }

    /* TABLA */
    .horario-grid { width: 100%; border-collapse: collapse; text-align: center; font-family: 'Arial', sans-serif; font-size: 0.8em; background-color: #ffffff; color: black; border-radius: 8px; overflow: hidden; }
    .horario-grid th { background-color: var(--guinda); color: white; padding: 8px; border: 1px solid #444; }
    .horario-grid td { border: 1px solid #ddd; height: 45px; vertical-align: middle; padding: 2px; color: #333; }
    .hora-col { background-color: #e0e0e0; font-weight: bold; color: #000; width: 70px; }
    .clase-cell { border-radius: 4px; padding: 4px; color: #111; font-weight: 700; font-size: 0.95em; height: 100%; display: flex; flex-direction: column; justify-content: center; line-height: 1.1; box-shadow: 0 1px 2px rgba(0,0,0,0.2); }
    .clase-prof { font-weight: 500; font-size: 0.75em; color: #444; margin-top: 2px; }
    .clase-salon { font-weight: 400; font-size: 0.7em; color: #666; margin-top: 1px; font-style: italic;}
</style>
""", unsafe_allow_html=True)

COLORS = ['#FFCDD2', '#F8BBD0', '#E1BEE7', '#D1C4E9', '#C5CAE9', '#BBDEFB', '#B3E5FC', '#B2EBF2', '#B2DFDB', '#C8E6C9', '#DCEDC8', '#F0F4C3']

# -----------------------------------------------------------------------------
# 2. CONEXIÓN A GOOGLE SHEETS
# -----------------------------------------------------------------------------
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

@st.cache_data(ttl=60)
def get_opiniones_data_cached(_client_status):
    client = get_db_connection()
    if not client: return {}
    try:
        sheet = client.open("opiniones_its").sheet1
        data = sheet.get_all_records()
        opiniones_dict = {}
        for row in data:
            prof = str(row.get('Profesor', '')).strip()
            if not prof: continue 
            if prof not in opiniones_dict:
                opiniones_dict[prof] = {"suma": 0, "votos": 0, "comentarios": []}
            calif = int(row.get('Calificacion', 0) or row.get('Calificación', 0) or 0)
            opiniones_dict[prof]["suma"] += calif
            opiniones_dict[prof]["votos"] += 1
            comentario = str(row.get('Comentario', '') or "").strip()
            if comentario: opiniones_dict[prof]["comentarios"].insert(0, comentario)
        return opiniones_dict
    except: return {}

@st.cache_data(ttl=15) 
def get_group_reports_cached(_client_status):
    client = get_db_connection()
    if not client: return {}
    try:
        sheet = client.open("opiniones_its").worksheet("reportes_grupos")
        data = sheet.get_all_records()
        reports = {}
        for row in data:
            gid = str(row.get('ID_Grupo', '')).strip()
            count = int(row.get('Conteo', 0) or 0)
            if gid: reports[gid] = count
        return reports
    except: return {}

def add_group_report(client, group_id):
    if not client: return False
    try:
        try: sheet = client.open("opiniones_its").worksheet("reportes_grupos")
        except:
            sh = client.open("opiniones_its")
            sheet = sh.add_worksheet(title="reportes_grupos", rows=1000, cols=3)
            sheet.append_row(["ID_Grupo", "Conteo", "Ultimo_Reporte"])
        
        cell = sheet.find(group_id)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if cell:
            current_val = int(sheet.cell(cell.row, 2).value)
            sheet.update_cell(cell.row, 2, current_val + 1)
            sheet.update_cell(cell.row, 3, fecha)
        else: sheet.append_row([group_id, 1, fecha])
        get_group_reports_cached.clear()
        return True
    except: return False

def save_opinion(client, profesor, comentario, calificacion):
    if not client: return False
    try:
        sheet = client.open("opiniones_its").sheet1
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([profesor, comentario, calificacion, fecha])
        get_opiniones_data_cached.clear()
        return True
    except: return False

db_client = get_db_connection()

# -----------------------------------------------------------------------------
# 3. BASE DE DATOS LOCAL (REGLAS Y CRÉDITOS FIJOS)
# -----------------------------------------------------------------------------
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

SERIACION = {
    "Cálculo Integral": ["Cálculo Diferencial"], "Ciencia e Ingeniería de Materiales": ["Química"], "Cálculo Vectorial": ["Cálculo Integral"],
    "Procesos de Fabricación": ["Ciencia e Ingeniería de Materiales"], "Programación Avanzada": ["Programación Básica"], "Dinámica": ["Cálculo Vectorial"],
    "Ecuaciones Diferenciales": ["Cálculo Vectorial"], "Manufactura Avanzada": ["Procesos de Fabricación"], "Análisis de Circuitos Eléctricos": ["Electromagnetismo"],
    "Mecánica de Materiales": ["Estática"], "Taller de Investigación II": ["Taller de Investigación I"], "Mecanismos": ["Dinámica"],
    "Electrónica Analógica": ["Análisis de Circuitos Eléctricos"], "Diseño de Elementos Mecánicos": ["Mecánica de Materiales"], "Electrónica de Potencia Aplicada": ["Máquinas Eléctricas"],
    "Vibraciones Mecánicas": ["Mecanismos"], "Electrónica Digital": ["Electrónica Analógica"], "Controladores Lógicos Programables": ["Electrónica de Potencia Aplicada", "Circuitos Hidráulicos y Neumáticos"],
    "Microcontroladores": ["Electrónica Digital"], "Control": ["Dinámica de Sistemas"], "Tópicos Selectos de Automatización Industrial": ["Controladores Lógicos Programables"]
}

# -----------------------------------------------------------------------------
# 4. CARGA DE JSON Y MOTOR
# -----------------------------------------------------------------------------
@st.cache_data
def load_oferta_json(periodo, carrera):
    filepath = f"data/{periodo}/{carrera}.json"
    if not os.path.exists(filepath): return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_json_to_oferta(json_data):
    oferta_clases = {}
    materias_por_semestre = {i: [] for i in range(1, 10)}
    
    for mat_key, mat_info in json_data.get("materias", {}).items():
        nombre = mat_info["nombre"]
        semestre = int(mat_info.get("semestre", 1))
        
        if 1 <= semestre <= 9:
            materias_por_semestre[semestre].append(nombre)
            
        oferta_clases[nombre] = []
        for grupo in mat_info.get("grupos", []):
            formatted_horario = []
            for h in grupo.get("horario", []):
                formatted_horario.append((h["dia"], h["inicio"], h["fin"]))
            oferta_clases[nombre].append({
                "profesor": grupo["profesor"],
                "salon": grupo.get("salon", "TBA"),
                "horario": formatted_horario,
                "id": grupo.get("id", ""),
                "materia": nombre
            })
    return oferta_clases, materias_por_semestre

def traslape(horario1, horario2):
    for h1 in horario1:
        for h2 in horario2:
            if h1[0] == h2[0]:
                if max(h1[1], h2[1]) < min(h1[2], h2[2]): return True
    return False

def generar_combinaciones_backtracking(materias_nombres, rango, prefs, horas_libres, oferta_academica):
    bloqueos = [int(hl.split(":")[0]) for hl in horas_libres]
    
    pools = []
    for mat in materias_nombres:
        if mat not in oferta_academica: continue
        opciones = []
        for sec in oferta_academica[mat]:
            prof_name = sec['profesor']
            key = f"{mat}_{prof_name}"
            puntos = prefs.get(key, 50)
            if puntos == 0: continue 
            dentro = True
            for h in sec['horario']:
                # h[1] = inicio, h[2] = fin
                if h[1] < rango[0] or h[2] > rango[1]: dentro = False; break
                
                # Bloqueos por hora individual (sirve para clases de 1h o de 3h)
                for hora_eval in range(h[1], h[2]):
                    if hora_eval in bloqueos: dentro = False; break
                
                time_key = f"time_{mat}_{prof_name}_{h[1]}"
                if not st.session_state.get(time_key, True): dentro = False; break
            
            if dentro: 
                s = sec.copy()
                s['score'] = puntos
                opciones.append(s)
        if not opciones: return [], f"❌ **{mat}**: No tiene horarios disponibles con tus filtros."
        pools.append(opciones)

    validos = []
    def backtrack(index, current_combo, current_score):
        if index == len(pools):
            validos.append((current_score, list(current_combo)))
            return
        for sec in pools[index]:
            ok = True
            for prev_sec in current_combo:
                if traslape(sec['horario'], prev_sec['horario']): ok = False; break
            if ok:
                current_combo.append(sec)
                backtrack(index + 1, current_combo, current_score + sec['score'])
                current_combo.pop()

    backtrack(0, [], 0)
    validos.sort(key=lambda x: x[0], reverse=True)
    return validos, "OK"

# -----------------------------------------------------------------------------
# 5. CREACIÓN DE PDF Y HTML
# -----------------------------------------------------------------------------
def clean_text(text):
    return text.encode('latin-1', 'ignore').decode('latin-1')

class PDF(FPDF):
    def header(self):
        if os.path.exists("logo_tec.png"): self.image('logo_tec.png', 10, 5, 55)
        if os.path.exists("logo_its.png"): self.image('logo_its.png', 250, 5, 25)
        self.set_y(65)
        self.set_font('Arial', 'B', 16); self.set_text_color(128, 0, 0)
        self.cell(0, 10, 'TECNOLÓGICO NACIONAL DE MÉXICO', 0, 1, 'C')
        self.set_font('Arial', 'B', 12); self.set_text_color(0, 0, 0)
        self.cell(0, 8, 'INSTITUTO TECNOLÓGICO DE SALTILLO', 0, 1, 'C'); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, clean_text('Desarrollado por: Néstor Alexis Piña Rodríguez | Página ') + str(self.page_no()), 0, 0, 'C')

def create_pro_pdf(horario, alumno_data, total_creditos, carrera_nombre):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14); pdf.set_text_color(128, 0, 0)
    pdf.cell(0, 10, "Carga Académica", 0, 1, 'C'); pdf.ln(2)
    pdf.set_font("Arial", size=9); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(245, 245, 245)
    h_row = 6 
    pdf.cell(30, h_row, "No. Control:", 1, 0, 'L', 1); pdf.cell(40, h_row, clean_text(alumno_data.get("nc", "")), 1, 0, 'L')
    pdf.cell(30, h_row, "Nombre:", 1, 0, 'L', 1); pdf.cell(100, h_row, clean_text(alumno_data.get("nombre", "").upper()), 1, 0, 'L')
    pdf.cell(30, h_row, "Semestre:", 1, 0, 'L', 1); pdf.cell(30, h_row, str(alumno_data.get("semestre", "")), 1, 1, 'L')
    pdf.cell(30, h_row, "Carrera:", 1, 0, 'L', 1); pdf.cell(100, h_row, clean_text(carrera_nombre.upper()), 1, 0, 'L')
    pdf.cell(30, h_row, "Periodo:", 1, 0, 'L', 1); pdf.cell(100, h_row, clean_text(alumno_data.get("periodo", "").upper()), 1, 1, 'L'); pdf.ln(8)
    
    tiene_sabado = any(s[0] == 5 for c in horario for s in c['horario'])
    pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(128, 0, 0); pdf.set_text_color(255, 255, 255)
    w_mat, w_prof, w_salon, w_cred = 75, 60, 12, 10
    w_dia = 19 if not tiene_sabado else 16 
    h_table = 8 
    
    pdf.cell(w_mat, h_table, "Materia", 1, 0, 'C', 1)
    pdf.cell(w_prof, h_table, "Profesor", 1, 0, 'C', 1)
    pdf.cell(w_salon, h_table, "Salón", 1, 0, 'C', 1)
    pdf.cell(w_cred, h_table, "Créd.", 1, 0, 'C', 1)
    
    dias_header = ["Lun", "Mar", "Mié", "Jue", "Vie"]
    if tiene_sabado: dias_header.append("Sáb")
    for dia in dias_header: pdf.cell(w_dia, h_table, clean_text(dia), 1, 0, 'C', 1)
    pdf.ln(); pdf.set_font("Arial", size=7); pdf.set_text_color(0, 0, 0)
    
    horario_ordenado = sorted(horario, key=lambda c: min([h[1] for h in c['horario']]) if c['horario'] else
