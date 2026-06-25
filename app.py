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
                for hora_eval en range(h[1], h[2]):
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
    
    horario_ordenado = sorted(horario, key=lambda c: min([h[1] for h in c['horario']]) if c['horario'] else 24)
    for clase in horario_ordenado:
        materia_nome = clean_text(clase['materia'])
        profesor_nome = clean_text(clase['profesor'].split('(')[0])
        salon = clean_text(clase.get('salon', 'TBA'))
        creditos = str(CREDITOS.get(clase['materia'], 0))
        
        pdf.cell(w_mat, h_table, materia_nome, 1)
        pdf.cell(w_prof, h_table, profesor_nome, 1)
        pdf.cell(w_salon, h_table, salon, 1, 0, 'C')
        pdf.cell(w_cred, h_table, creditos, 1, 0, 'C')
        
        rango_dias = 6 if tiene_sabado else 5
        for d in range(rango_dias):
            txt_hora = ""
            for sesion in clase['horario']:
                if sesion[0] == d: txt_hora = f"{sesion[1]}:00-{sesion[2]}:00"
            pdf.cell(w_dia, h_table, txt_hora, 1, 0, 'C')
        pdf.ln()
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(w_mat + w_prof + w_salon, h_table, clean_text("TOTAL DE CRÉDITOS:"), 1, 0, 'R'); pdf.cell(w_cred, h_table, str(total_creditos), 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def create_timetable_html(horario):
    horas_ocupadas = []
    tiene_sabado = False
    for clase in horario:
        for sesion in clase['horario']: 
            horas_ocupadas.append(sesion[1]); horas_ocupadas.append(sesion[2])
            if sesion[0] == 5: tiene_sabado = True

    if not horas_ocupadas: return ""
    min_h, max_h = min(horas_ocupadas), max(horas_ocupadas)
    subject_colors = {clase['materia']: COLORS[i % len(COLORS)] for i, clase in enumerate(horario)}
    rango_dias = 6 if tiene_sabado else 5
    grid = {h: [None]*rango_dias for h in range(min_h, max_h)} 
    
    for clase in horario:
        mat_name = clase['materia'].split(' ')[1] if " " in clase['materia'] else clase['materia']
        if len(mat_name) > 20: mat_name = mat_name[:20] + "..."
        prof_parts = clase['profesor'].split('(')[0].split()
        prof_name = f"{prof_parts[0]} {prof_parts[1]}" if len(prof_parts) > 1 else prof_parts[0]
        color = subject_colors[clase['materia']]
        
        for sesion in clase['horario']:
            for h in range(sesion[1], sesion[2]):
                if h in grid and sesion[0] < rango_dias:
                    grid[h][sesion[0]] = f"<div class='clase-cell' style='background-color: {color};'><span>{mat_name}</span><span class='clase-prof'>{prof_name}</span><span class='clase-salon'>{clase.get('salon','TBA')}</span></div>"
    
    headers = ["Lun", "Mar", "Mié", "Jue", "Vie"]
    if tiene_sabado: headers.append("Sáb")
    html = f"<table class='horario-grid'><thead><tr><th class='hora-col'>Hora</th>" + "".join([f"<th>{h}</th>" for h in headers]) + "</tr></thead><tbody>"
    for h in range(min_h, max_h):
        html += f"<tr><td class='hora-col'>{h}-{h+1}</td>"
        for d in range(rango_dias): html += f"<td>{grid[h][d]}</td>" if grid[h][d] else "<td></td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

# -----------------------------------------------------------------------------
# 6. INICIALIZAR ESTADO E INTERFAZ
# -----------------------------------------------------------------------------
if 'step' not in st.session_state: st.session_state.step = 1
if 'materias_seleccionadas' not in st.session_state: st.session_state.materias_seleccionadas = []
if 'oferta_actual' not in st.session_state: st.session_state.oferta_actual = {}
if 'materias_por_semestre' not in st.session_state: st.session_state.materias_por_semestre = {}
if 'prefs' not in st.session_state: st.session_state.prefs = {}
if 'resultados' not in st.session_state: st.session_state.resultados = None
if 'carrera_seleccionada' not in st.session_state: st.session_state.carrera_seleccionada = ""

menu = st.sidebar.radio("Menú", ["📅 Generador de Horarios", "⭐ Evaluación Docente"])

if menu == "📅 Generador de Horarios":
    # --- PASO 1: SELECCIÓN DE CARRERA Y PERIODO ---
    if st.session_state.step == 1:
        st.markdown("<h1 style='text-align: center;'>Horario ITS 🦅</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Selecciona tu plan para cargar la oferta académica correspondiente.</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.container(border=True)
            periodo = st.selectbox("📌 Periodo Académico", ["2026_VERANO", "2026_AGO_DIC"])
            carrera = st.selectbox("🎓 Carrera", ["mecatronica", "industrial (Próximamente)", "sistemas (Próximamente)", "gestion (Próximamente)", "materiales (Próximamente)"])
            cant = st.number_input("📚 Materias a cursar (Máx 2 en Verano):", min_value=1, max_value=9, value=2)
            
            if st.button("Cargar Oferta ➡️", use_container_width=True, type="primary"):
                carrera_clean = carrera.split(" ")[0] 
                json_data = load_oferta_json(periodo, carrera_clean)
                
                if json_data:
                    of_clases, mat_sem = format_json_to_oferta(json_data)
                    st.session_state.oferta_actual = of_clases
                    st.session_state.materias_por_semestre = mat_sem
                    st.session_state.num_materias_deseadas = cant
                    st.session_state.carrera_seleccionada = carrera_clean
                    st.session_state.periodo_seleccionado = periodo
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error(f"❌ Aún no hay oferta cargada en el sistema para {carrera_clean.upper()} en {periodo}.")

    # --- PASO 2: SELECCIÓN DE MATERIAS ---
    elif st.session_state.step == 2:
        st.title("📚 Selección de Materias")
        st.caption("Oferta extraída directamente de la base de datos oficial.")
        
        cols = st.columns(9)
        selected_in_this_step = []
        
        for i in range(1, 10): # Semestres del 1 al 9
            with cols[i-1]:
                st.markdown(f"<div class='semestre-header'>{i}°</div>", unsafe_allow_html=True)
                for m in st.session_state.materias_por_semestre[i]:
                    cr = CREDITOS.get(m, 0)
                    if st.checkbox(f"{m} ({cr} Cr)", value=(m in st.session_state.materias_seleccionadas), key=f"chk_{m}"):
                        selected_in_this_step.append(m)
                    
        total_creditos = sum([CREDITOS.get(m, 0) for m in selected_in_this_step])
        num_selected = len(selected_in_this_step)
        
        st.write("---")
        limite_creditos = 36 if "AGO_DIC" in st.session_state.periodo_seleccionado else 12 
        
        c_info = st.container()
        msg_cred = f"✅ Créditos: {total_creditos}" if total_creditos <= limite_creditos else f"⛔ Exceso: {total_creditos}"
        style_cred = "credit-ok" if total_creditos <= limite_creditos else "credit-error"
        msg_cant = f"Materias: {num_selected} / {st.session_state.num_materias_deseadas}"
        
        if num_selected != st.session_state.num_materias_deseadas: style_cred = "credit-error"
        c_info.markdown(f"<div class='credit-box {style_cred}'>{msg_cred} | {msg_cant}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 1; st.rerun()
        
        bloqueo = False
        if num_selected != st.session_state.num_materias_deseadas: bloqueo = True
        
        for materia in selected_in_this_step:
            if materia in SERIACION:
                for req in SERIACION[materia]:
                    if req in selected_in_this_step:
                        st.error(f"❌ {materia} requiere haber aprobado {req}. No puedes llevar ambas.")
                        bloqueo = True
                        
        if bloqueo: st.warning("⚠️ Ajusta tu selección para continuar.")
        else:
            if col2.button("Siguiente ➡️", type="primary"):
                st.session_state.materias_seleccionadas = selected_in_this_step
                st.session_state.step = 3
                st.rerun()

    # --- PASO 3: DISPONIBILIDAD ---
    elif st.session_state.step == 3:
        st.title("⏰ Disponibilidad")
        col_rang, col_free = st.columns(2)
        with col_rang:
            st.subheader("Rango General")
            rango = st.slider("Horario Global:", 7, 22, (7, 22))
            st.session_state.rango_hora = rango
        with col_free:
            st.subheader("Huecos Libres")
            horas_posibles = [f"{h}:00-{h+1}:00" for h in range(7, 22)]
            libres = st.multiselect("Bloquear horas:", horas_posibles)
            st.session_state.horas_libres = libres
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 2; st.rerun()
        if col2.button("Siguiente ➡️", type="primary"): st.session_state.step = 4; st.rerun()

    # --- PASO 4: PROFESORES Y WAZE ---
    elif st.session_state.step == 4:
        st.title("👨‍🏫 Filtrado de Profesores")
        opiniones_reales_global = get_opiniones_data_cached("status_ok")
        reportes_global = get_group_reports_cached("status_ok")
        
        for mat in st.session_state.materias_seleccionadas:
            with st.container(border=True):
                st.subheader(f"{mat}")
                profes_validos = []
                all_profes = sorted(list(set([p['profesor'] for p in st.session_state.oferta_actual[mat]])))
                
                for p_name in all_profes:
                    sections = [s for s in st.session_state.oferta_actual[mat] if s['profesor'] == p_name]
                    fits = False
                    for s in sections:
                        section_fits = True
                        for h in s['horario']:
                            if h[1] < st.session_state.rango_hora[0] or h[2] > st.session_state.rango_hora[1]: section_fits = False; break
                        if section_fits: fits = True; break
                    if fits: profes_validos.append(p_name)
                    
                if not profes_validos: st.warning(f"⚠️ Sin profes en tu rango para {mat}.")
                cols = st.columns(3)
                for i, p in enumerate(profes_validos):
                    key = f"{mat}_{p}"
                    with cols[i % 3]:
                        st.write(f"**{p}**")
                        val = st.radio("P", ["✅", "➖", "❌"], index=1, key=key, horizontal=True, label_visibility="collapsed")
                        if val == "✅": st.session_state.prefs[key] = 100
                        elif val == "❌": st.session_state.prefs[key] = 0
                        else: st.session_state.prefs[key] = 50
                        
                        with st.expander("🕒 Horario y Reportes"):
                            teacher_sections = [s for s in st.session_state.oferta_actual[mat] if s['profesor'] == p]
                            for sec in teacher_sections:
                                spec_id = sec['id']
                                t_inicio = sec['horario'][0][1]
                                t_fin = sec['horario'][0][2]
                                rep_count = reportes_global.get(spec_id, 0)
                                
                                c_chk, c_warn, c_btn = st.columns([0.3, 0.4, 0.3])
                                with c_chk: st.checkbox(f"{t_inicio}:00-{t_fin}:00", value=True, key=f"time_{mat}_{p}_{t_inicio}")
                                with c_warn:
                                    if rep_count > 0: st.markdown(f"<span class='report-badge'>⚠️ {rep_count} reportes</span>", unsafe_allow_html=True)
                                with c_btn:
                                    if st.button("📢 Lleno", key=f"rep_{spec_id}"):
                                        if add_group_report(db_client, spec_id):
                                            st.toast("Reporte enviado.")
                                            time.sleep(1); st.rerun()

                        with st.expander("⭐ Opiniones"):
                            if p in opiniones_reales_global:
                                data = opiniones_reales_global[p]
                                prom = int(data["suma"]/data["votos"]) if data["votos"] > 0 else 0
                                color = "#e74c3c" if prom<60 else "#f1c40f" if prom<90 else "#2ecc71"
                                st.markdown(f"<div style='text-align:center; font-weight:bold; color:{color}; font-size:1.2em;'>{prom}/100</div>", unsafe_allow_html=True)
                            else: st.caption("Sin comentarios.")
                                
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 3; st.rerun()
        if col2.button("🚀 GENERAR HORARIOS", type="primary"): st.session_state.step = 5; st.session_state.resultados = None; st.rerun()

    # --- PASO 5: RESULTADOS ---
    elif st.session_state.step == 5:
        st.title("✅ Resultados Finales")
        if st.button("⬅️ Ajustar Filtros"): st.session_state.step = 4; st.rerun()
        
        with st.expander("📝 Datos del Alumno (Para el PDF)", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            st.session_state.alumno_nombre = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', c1.text_input("Nombre", st.session_state.alumno_nombre))
            st.session_state.alumno_nc = re.sub(r'\D', '', c2.text_input("No. Control", st.session_state.alumno_nc))
            st.session_state.alumno_sem = c3.selectbox("Semestre", range(1, 15), index=0)
            st.session_state.alumno_per = st.session_state.periodo_seleccionado
        
        if st.session_state.resultados is None:
            res, msg = generar_combinaciones_backtracking(st.session_state.materias_seleccionadas, st.session_state.rango_hora, st.session_state.prefs, st.session_state.horas_libres, st.session_state.oferta_actual)
            if not res and msg != "OK": st.error(msg); st.session_state.resultados = []
            else: st.session_state.resultados = res
            
        if st.session_state.resultados:
            res = st.session_state.resultados; st.success(f"¡{len(res)} opciones encontradas!")
            total_creditos_final = sum([CREDITOS.get(m, 0) for m in st.session_state.materias_seleccionadas])
            alumno_data = { "nombre": st.session_state.alumno_nombre, "nc": st.session_state.alumno_nc, "semestre": st.session_state.alumno_sem, "periodo": st.session_state.alumno_per }
            
            for i, (score, horario) in enumerate(res[:10]): 
                with st.container(border=True):
                    col_info, col_btn = st.columns([4, 1])
                    col_info.subheader(f"Opción {i+1}")
                    pdf_bytes = create_pro_pdf(horario, alumno_data, total_creditos_final, st.session_state.carrera_seleccionada)
                    col_btn.download_button("📄 PDF", data=pdf_bytes, file_name=f"Carga_Op{i+1}.pdf", mime="application/pdf", key=f"btn_{i}")
                    html_table = create_timetable_html(horario); st.markdown(html_table, unsafe_allow_html=True); st.write("")
        elif st.session_state.resultados is not None and len(st.session_state.resultados) == 0:
            st.warning("⚠️ No hay combinaciones. Intenta quitar restricciones.")
        if st.button("🔄 Inicio"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

# =============================================================================
# VISTA 2: EVALUACIÓN DOCENTE
# =============================================================================
elif menu == "⭐ Evaluación Docente":
    st.title("⭐ Califica a tu Maestro")
    st.info("Para evaluar, asegúrate de haber cargado primero la oferta académica en la pestaña principal.")
    
    if not st.session_state.oferta_actual:
        st.warning("⚠️ Ve a 'Generador de Horarios' y carga una carrera primero.")
    else:
        all_profs = sorted(list(set(p['profesor'] for mat in st.session_state.oferta_actual.values() for p in mat)))
        prof_selected = st.selectbox("Selecciona al profesor:", all_profs)
        st.write("---")
        
        opiniones_reales = get_opiniones_data_cached("status_ok")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader(f"Opina sobre: {prof_selected}")
            nuevo_comentario = st.text_area("Comentario (Anónimo):")
            nueva_calif = st.slider("Calificación (0-100):", 0, 100, 80)
            if st.button("Enviar Opinión"):
                if save_opinion(db_client, prof_selected, nuevo_comentario, nueva_calif):
                    st.success("¡Opinión registrada!"); time.sleep(1); st.rerun()
                else: st.error("Error de conexión.")

        with c2:
            if prof_selected in opiniones_reales:
                data = opiniones_reales[prof_selected]
                promedio = int(data["suma"] / data["votos"]) if data["votos"] > 0 else 0
                color_chart = "#e74c3c" if promedio < 60 else "#f1c40f" if promedio < 90 else "#2ecc71"
                st.markdown(f"""
                <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                    <div style="width: 150px; height: 150px; border-radius: 50%; background: conic-gradient({color_chart} {promedio}%, #444 0); display: flex; justify-content: center; align-items: center;">
                        <div style="width: 120px; height: 120px; border-radius: 50%; background: #1c1f26; display: flex; justify-content: center; align-items: center; color: white; font-weight: bold; font-size: 1.5em;">{promedio}/100</div>
                    </div>
                </div>
                <p style="text-align: center; color: #aaa;">Basado en {data['votos']} votos</p>""", unsafe_allow_html=True)
            else: st.info("Sin calificaciones aún.")

        st.write("---")
        st.subheader("💬 Comentarios Recientes")
        if prof_selected in opiniones_reales and opiniones_reales[prof_selected]["comentarios"]:
            for com in opiniones_reales[prof_selected]["comentarios"]:
                st.markdown(f"<div class='comment-bubble'>{com}</div>", unsafe_allow_html=True)
        else: st.write("No hay comentarios.")
