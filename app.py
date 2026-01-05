import streamlit as st
import pandas as pd
import itertools
from fpdf import FPDF
import os
import plotly.graph_objects as go # Necesario para la gráfica

# -----------------------------------------------------------------------------
# CONFIGURACIÓN VISUAL (MODO OSCURO NATIVO + TEMA ITS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Horario ITS", page_icon="🐴", layout="wide")

st.markdown("""
<style>
    /* VARIABLES DE COLOR */
    :root {
        --guinda: #800000;
    }

    /* TÍTULOS EN GUINDA (Se ven bien en dark y light) */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--guinda) !important;
        font-family: 'Arial', sans-serif;
    }

    /* ESTILO DE LOS CHECKBOXES (Adaptable) */
    .stCheckbox {
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        transition: all 0.2s;
        min-height: 80px; 
        display: flex;
        align-items: center;
    }
    
    /* Efecto Hover */
    .stCheckbox:hover {
        border-color: var(--guinda);
        background-color: rgba(128, 0, 0, 0.1); 
    }

    /* Ocultar palomita original y estilizar el contenedor cuando está activo */
    div[data-testid="stCheckbox"] label {
        width: 100%;
        cursor: pointer;
    }
    
    /* EFECTO SELECCIONADO: FONDO GUINDA, TEXTO BLANCO */
    div[data-testid="stCheckbox"]:has(input:checked) div[data-testid="stMarkdownContainer"] {
        background-color: var(--guinda);
        color: white !important;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
    
    /* ESTADO NORMAL */
    div[data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] {
        text-align: center;
        font-weight: 500;
    }

    /* ENCABEZADOS DE SEMESTRE */
    .semestre-header {
        color: var(--guinda) !important;
        font-weight: 900;
        font-size: 1.1em;
        text-align: center;
        border-bottom: 3px solid var(--guinda);
        margin-bottom: 15px;
        padding-bottom: 5px;
        text-transform: uppercase;
    }

    /* BIENVENIDA (Fondo sutil para que se lea en dark mode) */
    .welcome-box {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 25px;
        border-radius: 10px;
        border-left: 8px solid var(--guinda);
        margin-bottom: 20px;
    }
    .welcome-greeting {
        font-size: 1.3em;
        font-weight: bold;
        color: var(--guinda) !important;
        margin-bottom: 15px;
    }
    .welcome-lema {
        margin-top: 15px;
        font-style: italic;
        font-weight: bold;
        color: var(--guinda) !important;
        text-align: right;
        opacity: 0.8;
    }
    .developer-credit {
        margin-top: 20px;
        font-size: 0.85em;
        opacity: 0.6;
    }

    /* BOTONES */
    .stButton>button {
        color: white !important;
        background-color: var(--guinda) !important;
        border: none;
        font-weight: bold;
        border-radius: 6px;
    }
    .stButton>button:hover {
        background-color: #5c0000 !important;
        transform: scale(1.02);
    }

    /* TABLA VISUAL (Fondo blanco para contraste de colores pastel) */
    .horario-grid { width: 100%; border-collapse: collapse; text-align: center; font-family: 'Arial', sans-serif; font-size: 0.8em; background-color: #ffffff; color: black; border-radius: 8px; overflow: hidden; }
    .horario-grid th { background-color: var(--guinda); color: white; padding: 8px; border: 1px solid #444; }
    .horario-grid td { border: 1px solid #ddd; height: 45px; vertical-align: middle; padding: 2px; color: #333; }
    .hora-col { background-color: #e0e0e0; font-weight: bold; color: #000; width: 70px; }
    
    .clase-cell { 
        border-radius: 4px; padding: 4px; color: #111; 
        font-weight: 700; font-size: 0.95em; height: 100%; 
        display: flex; flex-direction: column; justify-content: center; 
        line-height: 1.2; box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    
    /* CREDIT BOXES */
    .credit-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    .credit-ok { background-color: rgba(4, 95, 70, 0.3); color: #34d399; border: 1px solid #34d399; }
    .credit-error { background-color: rgba(153, 27, 27, 0.3); color: #f87171; border: 1px solid #f87171; }

</style>
""", unsafe_allow_html=True)

COLORS = ['#FFCDD2', '#F8BBD0', '#E1BEE7', '#D1C4E9', '#C5CAE9', '#BBDEFB', '#B3E5FC', '#B2EBF2', '#B2DFDB', '#C8E6C9', '#DCEDC8', '#F0F4C3', '#FFF9C4', '#FFECB3', '#FFE0B2', '#FFCCBC']

# Inicializar estado
if 'step' not in st.session_state: st.session_state.step = 1
if 'num_materias_deseadas' not in st.session_state: st.session_state.num_materias_deseadas = 6
if 'materias_seleccionadas' not in st.session_state: st.session_state.materias_seleccionadas = []
if 'rango_hora' not in st.session_state: st.session_state.rango_hora = (7, 22)
if 'horas_libres' not in st.session_state: st.session_state.horas_libres = []
if 'prefs' not in st.session_state: st.session_state.prefs = {}
if 'resultados' not in st.session_state: st.session_state.resultados = None
# Simulación de Base de Datos de Opiniones
if 'opiniones' not in st.session_state: 
    st.session_state.opiniones = {
        "Ana Gabriela Gomez Muñoz": {"suma": 450, "votos": 5, "comentarios": ["Excelente maestra", "Muy estricta pero aprendes"]},
        "Gerardo Jarquín Hernández": {"suma": 98, "votos": 1, "comentarios": ["El mejor para Robótica"]}
    }

# Datos alumno
if 'alumno_nombre' not in st.session_state: st.session_state.alumno_nombre = ""
if 'alumno_nc' not in st.session_state: st.session_state.alumno_nc = ""
if 'alumno_sem' not in st.session_state: st.session_state.alumno_sem = 1
if 'alumno_per' not in st.session_state: st.session_state.alumno_per = "ENE-JUN 2026"

# -----------------------------------------------------------------------------
# CRÉDITOS Y BASE DE DATOS
# -----------------------------------------------------------------------------
CREDITOS = {
    "🧪 Química": 4, "📐 Cálculo Diferencial": 5, "⚖️ Taller de Ética": 4, "💻 Dibujo Asistido por Computadora": 4, "📏 Metrología y Normalización": 4, "🔎 Fundamentos de Investigación": 4,
    "∫ Cálculo Integral": 5, "🧮 Álgebra Lineal": 5, "🧱 Ciencia e Ingeniería de Materiales": 5, "💾 Programación Básica": 5, "📊 Estadística y Control de Calidad": 4, "💰 Administración y Contabilidad": 4,
    "↗️ Cálculo Vectorial": 5, "🔨 Procesos de Fabricación": 4, "⚡ Electromagnetismo": 5, "🏗️ Estática": 4, "🔢 Métodos Numéricos": 4, "🌱 Desarrollo Sustentable": 5,
    "📉 Ecuaciones Diferenciales": 5, "🔥 Fundamentos de Termodinámica": 4, "🦾 Mecánica de Materiales": 6, "🏎️ Dinámica": 4, "🔌 Análisis de Circuitos Eléctricos": 6, "📝 Taller de Investigación I": 4,
    "⚙️ Máquinas Eléctricas": 5, "📟 Electrónica Analógica": 6, "🔗 Mecanismos": 5, "💧 Análisis de Fluidos": 4, "📑 Taller de Investigación II": 4, "💻 Programación Avanzada": 6,
    "⚡ Electrónica de Potencia Aplicada": 6, "🌡️ Instrumentación": 5, "🔩 Diseño de Elementos Mecánicos": 5, "👾 Electrónica Digital": 5, "〰️ Vibraciones Mecánicas": 5, "🛠️ Administración del Mantenimiento": 4,
    "🏭 Manufactura Avanzada": 5, "🖥️ Diseño Asistido por Computadora": 5, "🔄 Dinámica de Sistemas": 5, "🌬️ Circuitos Hidráulicos y Neumáticos": 6, "🔧 Mantenimiento": 5, "💾 Microcontroladores": 5,
    "📈 Formulación y Evaluación de Proyectos": 3, "🎛️ Controladores Lógicos Programables": 5, "🎮 Control": 6, "🤖 Sistemas Avanzados de Manufactura": 5, "🌐 Redes Industriales": 5,
    "🦾 Robótica": 5, "🏭 Tópicos Selectos de Automatización Industrial": 6
}

database = {
    "Ingeniería Mecatrónica": {
        "Semestre 1": ["🧪 Química", "📐 Cálculo Diferencial", "⚖️ Taller de Ética", "💻 Dibujo Asistido por Computadora", "📏 Metrología y Normalización", "🔎 Fundamentos de Investigación"],
        "Semestre 2": ["∫ Cálculo Integral", "🧮 Álgebra Lineal", "🧱 Ciencia e Ingeniería de Materiales", "💾 Programación Básica", "📊 Estadística y Control de Calidad", "💰 Administración y Contabilidad"],
        "Semestre 3": ["↗️ Cálculo Vectorial", "🔨 Procesos de Fabricación", "⚡ Electromagnetismo", "🏗️ Estática", "🔢 Métodos Numéricos", "🌱 Desarrollo Sustentable"],
        "Semestre 4": ["📉 Ecuaciones Diferenciales", "🔥 Fundamentos de Termodinámica", "🦾 Mecánica de Materiales", "🏎️ Dinámica", "🔌 Análisis de Circuitos Eléctricos", "📝 Taller de Investigación I"],
        "Semestre 5": ["⚙️ Máquinas Eléctricas", "📟 Electrónica Analógica", "🔗 Mecanismos", "💧 Análisis de Fluidos", "📑 Taller de Investigación II", "💻 Programación Avanzada"],
        "Semestre 6": ["⚡ Electrónica de Potencia Aplicada", "🌡️ Instrumentación", "🔩 Diseño de Elementos Mecánicos", "👾 Electrónica Digital", "〰️ Vibraciones Mecánicas", "🛠️ Administración del Mantenimiento"],
        "Semestre 7": ["🏭 Manufactura Avanzada", "🖥️ Diseño Asistido por Computadora", "🔄 Dinámica de Sistemas", "🌬️ Circuitos Hidráulicos y Neumáticos", "🔧 Mantenimiento", "💾 Microcontroladores"],
        "Semestre 8": ["📈 Formulación y Evaluación de Proyectos", "🎛️ Controladores Lógicos Programables", "🎮 Control", "🤖 Sistemas Avanzados de Manufactura", "🌐 Redes Industriales"],
        "Semestre 9": ["🦾 Robótica", "🏭 Tópicos Selectos de Automatización Industrial"]
    }
}

# --- OFERTA ACADÉMICA COMPLETA ---
oferta_academica = {
    # ... (Pega aquí TU DICCIONARIO COMPLETO que usaste en la versión anterior para que funcione la generación)
    # Por brevedad en la respuesta, asumo que tienes el diccionario V18.
    # SI NO LO TIENES, DIME Y TE LO VUELVO A PONER COMPLETO.
    # Usaré un dummy para que el código corra, PERO TÚ PEGA EL TUYO.
    "🦾 Robótica": [{"profesor": "Gerardo Jarquín Hernández", "horario": [(d,7,8) for d in range(5)], "id":"ROB1"}],
    "🏭 Tópicos Selectos de Automatización Industrial": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"TS1"}],
    "🎛️ Controladores Lógicos Programables": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,8,9) for d in range(5)], "id":"PLC1"}],
    "🎮 Control": [{"profesor": "Cesar Gerardo Martinez Sanchez", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"CTRL1"}],
    "🤖 Sistemas Avanzados de Manufactura": [{"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,9,10) for d in range(5)], "id":"SAM1"}],
    "💾 Microcontroladores": [{"profesor": "Pedro Quintanilla Contreras", "horario": [(d,11,12) for d in range(5)], "id":"MICRO1"}, {"profesor": "Jozef Jesus Reyes Reyna", "horario": [(d,17,18) for d in range(5)], "id":"MICRO2"}]
}
# (Asegúrate de pegar el diccionario `oferta_academica` completo que te di en la V17 o V18 aquí)

# -----------------------------------------------------------------------------
# FUNCIONES PDF Y HTML
# -----------------------------------------------------------------------------
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo_tec.png"): self.image('logo_tec.png', 10, 5, 55)
        if os.path.exists("logo_its.png"): self.image('logo_its.png', 250, 5, 25)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(128, 0, 0)
        self.set_y(12)
        self.cell(0, 10, 'TECNOLÓGICO NACIONAL DE MÉXICO', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, 'INSTITUTO TECNOLÓGICO DE SALTILLO', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def clean_text(text): return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pro_pdf(horario, alumno_data, total_creditos):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14); pdf.set_text_color(128, 0, 0)
    pdf.cell(0, 10, "Carga Académica", 0, 1, 'C'); pdf.ln(2)
    pdf.set_font("Arial", size=9); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(245, 245, 245)
    h_row = 6 
    pdf.cell(30, h_row, "No. Control:", 1, 0, 'L', 1); pdf.cell(40, h_row, clean_text(alumno_data.get("nc", "")), 1, 0, 'L')
    pdf.cell(30, h_row, "Nombre:", 1, 0, 'L', 1); pdf.cell(100, h_row, clean_text(alumno_data.get("nombre", "").upper()), 1, 0, 'L')
    pdf.cell(30, h_row, "Semestre:", 1, 0, 'L', 1); pdf.cell(30, h_row, str(alumno_data.get("semestre", "")), 1, 1, 'L')
    especialidad = "SIN ESPECIALIDAD"
    try:
        if int(alumno_data.get("semestre", 1)) >= 6: especialidad = "AUTOMATIZACIÓN DE PROCESOS DE MANUFACTURA"
    except: pass
    pdf.cell(30, h_row, "Carrera:", 1, 0, 'L', 1); pdf.cell(100, h_row, "INGENIERÍA MECATRÓNICA", 1, 0, 'L')
    pdf.cell(30, h_row, "Especialidad:", 1, 0, 'L', 1); pdf.cell(100, h_row, clean_text(especialidad), 1, 1, 'L'); pdf.ln(8)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(128, 0, 0); pdf.set_text_color(255, 255, 255)
    w_mat, w_prof, w_dia, w_cred = 70, 60, 22, 15; h_table = 8
    pdf.cell(w_mat, h_table, "Materia", 1, 0, 'C', 1); pdf.cell(w_prof, h_table, "Profesor", 1, 0, 'C', 1); pdf.cell(w_cred, h_table, "Créd.", 1, 0, 'C', 1)
    for dia in ["Lun", "Mar", "Mié", "Jue", "Vie"]: pdf.cell(w_dia, h_table, clean_text(dia), 1, 0, 'C', 1)
    pdf.ln(); pdf.set_font("Arial", size=8); pdf.set_text_color(0, 0, 0)
    
    def get_start_hour(clase):
        if not clase['horario']: return 24
        return min([h[1] for h in clase['horario']])
    horario_ordenado = sorted(horario, key=get_start_hour)
    
    for clase in horario_ordenado:
        materia_nome = clean_text(clase['materia'])
        if len(materia_nome) > 38: materia_nome = materia_nome[:35] + "..."
        profesor_nome = clean_text(clase['profesor'].split('(')[0][:30])
        creditos = str(CREDITOS.get(clase['materia'], 0))
        pdf.cell(w_mat, h_table, materia_nome, 1); pdf.cell(w_prof, h_table, profesor_nome, 1); pdf.cell(w_cred, h_table, creditos, 1, 0, 'C')
        for d in range(5):
            txt_hora = ""
            for sesion in clase['horario']:
                if sesion[0] == d: txt_hora = f"{sesion[1]}:00-{sesion[2]}:00"
            pdf.cell(w_dia, h_table, txt_hora, 1, 0, 'C')
        pdf.ln()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(w_mat + w_prof, h_table, clean_text("TOTAL DE CRÉDITOS:"), 1, 0, 'R'); pdf.cell(w_cred, h_table, str(total_creditos), 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def generar_combinaciones(materias, rango, prefs, horas_libres):
    bloqueos = []
    for hl in horas_libres: inicio = int(hl.split(":")[0]); bloqueos.append(inicio)
    pool = []
    for mat in materias:
        if mat not in oferta_academica: continue
        opciones = []
        for sec in oferta_academica[mat]:
            key = f"{mat}_{sec['profesor']}"
            puntos = prefs.get(key, 50)
            if puntos == 0: continue 
            dentro = True
            for h in sec['horario']:
                if h[1] < rango[0] or h[2] > rango[1]: dentro = False; break
                for b in bloqueos:
                    if max(h[1], b) < min(h[2], b+1): dentro = False; break
                if not dentro: break
            if dentro: s = sec.copy(); s['materia'] = mat; s['score'] = puntos; opciones.append(s)
        if not opciones: return [], f"❌ **{mat}**: No tiene horarios disponibles con tus filtros."
        pool.append(opciones)
    combos = list(itertools.product(*pool))
    validos = []
    for c in combos:
        ok = True; score = 0
        for i in range(len(c)):
            score += c[i]['score']
            for j in range(i+1, len(c)):
                # Lógica simplificada de traslape
                h1 = c[i]['horario']; h2 = c[j]['horario']
                for ses1 in h1:
                    for ses2 in h2:
                        if ses1[0] == ses2[0]: # Mismo dia
                            if max(ses1[1], ses2[1]) < min(ses1[2], ses2[2]): ok=False; break
                    if not ok: break
            if not ok: break
        if ok: validos.append((score, c))
    validos.sort(key=lambda x: x[0], reverse=True)
    return validos, "OK"

def create_timetable_html(horario):
    horas_ocupadas = []
    for clase in horario:
        for sesion in clase['horario']: horas_ocupadas.append(sesion[1]); horas_ocupadas.append(sesion[2])
    if not horas_ocupadas: return ""
    min_h = min(horas_ocupadas); max_h = max(horas_ocupadas)
    subject_colors = {}; 
    for i, clase in enumerate(horario): subject_colors[clase['materia']] = COLORS[i % len(COLORS)]
    grid = {h: [None]*5 for h in range(min_h, max_h)} 
    for clase in horario:
        full_name = clase['materia']
        if "Controladores Lógicos" in full_name: mat_name = "PLC"
        elif "Formulación y Evaluación" in full_name: mat_name = "Formulación"
        elif "Sistemas Avanzados" in full_name: mat_name = "Sistemas Av. Man."
        else:
            mat_name = full_name.split(' ')[1] if " " in full_name else full_name
            if len(mat_name) > 20: mat_name = mat_name[:20] + "..."
        parts = clase['profesor'].split('(')[0].split()
        prof_name = f"{parts[0]} {parts[1]}" if len(parts) > 1 else parts[0]
        color = subject_colors[clase['materia']]
        for sesion in clase['horario']:
            dia = sesion[0]; hora_ini = sesion[1]
            if hora_ini in grid:
                grid[hora_ini][dia] = {'text': f"<div class='clase-cell' style='background-color: {color};'><span>{mat_name}</span><span class='clase-prof'>{prof_name}</span></div>"}
    html = """<table class="horario-grid"><thead><tr><th class='hora-col'>Hora</th><th>Lun</th><th>Mar</th><th>Mié</th><th>Jue</th><th>Vie</th></tr></thead><tbody>"""
    for h in range(min_h, max_h):
        html += f"<tr><td class='hora-col'>{h}-{h+1}</td>"
        for d in range(5):
            cell = grid[h][d]
            html += f"<td>{cell['text']}</td>" if cell else "<td></td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def get_donut_chart(score):
    # Color dinámico: Rojo (0) -> Amarillo (50) -> Verde (100)
    if score < 50:
        # Rojo a Amarillo
        r = 255
        g = int(255 * (score / 50))
    else:
        # Amarillo a Verde
        r = int(255 * (1 - (score - 50) / 50))
        g = 255
    color_hex = f"rgb({r},{g},0)"
    
    fig = go.Figure(data=[go.Pie(
        values=[score, 100-score],
        hole=.7,
        marker_colors=[color_hex, '#e0e0e0'],
        textinfo='none',
        hoverinfo='none'
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=150,
        width=150,
        annotations=[dict(text=f"{score}/100", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig

# -----------------------------------------------------------------------------
# MENÚ LATERAL
# -----------------------------------------------------------------------------
menu = st.sidebar.radio("Menú", ["📅 Generador de Horarios", "⭐ Evaluación Docente"])

if os.path.exists("burro.png"):
    st.sidebar.image("burro.png", use_container_width=True)

# =============================================================================
# VISTA 1: GENERADOR
# =============================================================================
if menu == "📅 Generador de Horarios":
    # --- PASO 1: BIENVENIDA ---
    if st.session_state.step == 1:
        col_tec, col_centro, col_its = st.columns([1.5, 3, 1.5], gap="medium")
        with col_tec:
            if os.path.exists("logo_tec.png"): st.image("logo_tec.png", width=180)
        with col_centro:
            if os.path.exists("horarioits.png"): st.image("horarioits.png", use_container_width=True)
            else: st.markdown("<h1 style='text-align: center;'>Horario ITS</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; margin-top: -10px;'>Ingeniería Mecatrónica - Enero Junio 2026</h3>", unsafe_allow_html=True)
        with col_its:
            if os.path.exists("logo_its.png"): st.image("logo_its.png", width=150)
        st.write("---")
        col_texto, col_mascota = st.columns([3, 1])
        with col_texto:
            st.markdown("""
            <div class="welcome-box">
                <div class="welcome-greeting">¡Bienvenido, futuro ingeniero! 🦅</div>
                <div class="welcome-text-content">
                    <p>Esta herramienta ha sido diseñada PARA la comunidad estudiantil de Ingeniería Mecatrónica del ITS. Su objetivo es ayudarte a visualizar todas las posibles opciones de horario, facilitando la toma de decisiones.</p>
                    <div class="developer-credit">Desarrollado por: Néstor Alexis Piña Rodríguez</div>
                </div>
                <div class="welcome-lema">"La Técnica por la Grandeza de México"</div>
            </div>""", unsafe_allow_html=True)
        with col_mascota:
            st.write(""); st.write("")
            if os.path.exists("burro.png"): st.image("burro.png", width=120)
        st.write(""); st.write("")
        col_btn, _ = st.columns([1, 2])
        with col_btn:
            cant = st.number_input("Materias a cursar:", min_value=1, max_value=9, value=6, label_visibility="collapsed")
            if st.button("Comenzar ➡️", use_container_width=True):
                st.session_state.num_materias_deseadas = cant; st.session_state.step = 2; st.rerun()

    # --- PASO 2: MATERIAS (GRID 2 FILAS) ---
    elif st.session_state.step == 2:
        st.title("📚 Selección de Materias")
        cols_top = st.columns(5); selected_in_this_step = []
        all_semesters = list(database["Ingeniería Mecatrónica"].items())
        for i in range(5):
            sem_name, materias = all_semesters[i]
            with cols_top[i]:
                st.markdown(f"<div class='semestre-header'>{i+1}°</div>", unsafe_allow_html=True)
                for m in materias:
                    if st.checkbox(m, value=(m in st.session_state.materias_seleccionadas), key=f"chk_{m}"): selected_in_this_step.append(m)
        st.write("---")
        cols_bottom = st.columns(4)
        for i in range(4):
            idx_real = i + 5; sem_name, materias = all_semesters[idx_real]
            with cols_bottom[i]:
                st.markdown(f"<div class='semestre-header'>{idx_real+1}°</div>", unsafe_allow_html=True)
                for m in materias:
                    if st.checkbox(m, value=(m in st.session_state.materias_seleccionadas), key=f"chk_{m}"): selected_in_this_step.append(m)
        total_creditos = sum([CREDITOS.get(m, 0) for m in selected_in_this_step])
        st.write("---")
        c_info = st.container()
        if total_creditos <= 36: c_info.markdown(f"<div class='credit-box credit-ok'>✅ Créditos Acumulados: {total_creditos} / 36</div>", unsafe_allow_html=True); st.progress(total_creditos / 36)
        else: c_info.markdown(f"<div class='credit-box credit-error'>⛔ ¡EXCESO DE CRÉDITOS! ({total_creditos} / 36)</div>", unsafe_allow_html=True); st.progress(1.0)
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 1; st.rerun()
        if total_creditos > 36: col2.button("🚫 Límite Excedido", disabled=True)
        else:
            if col2.button("Siguiente ➡️", type="primary"):
                if total_creditos == 0: st.error("Selecciona al menos una materia.")
                else: st.session_state.materias_seleccionadas = selected_in_this_step; st.session_state.step = 3; st.rerun()

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

    # --- PASO 4: PROFESORES ---
    elif st.session_state.step == 4:
        st.title("👨‍🏫 Filtrado de Profesores")
        st.info("✅ Preferencia Alta | ➖ Normal | ❌ Descartar")
        for mat in st.session_state.materias_seleccionadas:
            if mat in oferta_academica:
                with st.container(border=True):
                    st.subheader(f"{mat} ({CREDITOS.get(mat,0)} Cr)")
                    profes_validos = []
                    all_profes = sorted(list(set([p['profesor'] for p in oferta_academica[mat]])))
                    for p_name in all_profes:
                        sections = [s for s in oferta_academica[mat] if s['profesor'] == p_name]
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
                        key = f"{mat}_{p}"; c = cols[i % 3]; c.write(f"**{p}**")
                        val = c.radio("P", ["✅", "➖", "❌"], index=1, key=key, horizontal=True, label_visibility="collapsed")
                        if val == "✅": st.session_state.prefs[key] = 100
                        elif val == "❌": st.session_state.prefs[key] = 0
                        else: st.session_state.prefs[key] = 50
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 3; st.rerun()
        if col2.button("🚀 GENERAR HORARIOS", type="primary"): st.session_state.step = 5; st.session_state.resultados = None; st.rerun()

    # --- PASO 5: RESULTADOS ---
    elif st.session_state.step == 5:
        st.title("✅ Resultados Finales")
        col_back, _ = st.columns([1, 4])
        if col_back.button("⬅️ Ajustar Filtros"): st.session_state.step = 4; st.rerun()
        with st.expander("📝 Datos del Alumno (Para el PDF)", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            st.session_state.alumno_nombre = c1.text_input("Nombre", st.session_state.alumno_nombre)
            st.session_state.alumno_nc = c2.text_input("No. Control", st.session_state.alumno_nc)
            st.session_state.alumno_sem = c3.selectbox("Semestre", range(1, 15), index=0)
            st.session_state.alumno_per = c4.text_input("Periodo", st.session_state.alumno_per)
        if st.session_state.resultados is None:
            res, msg = generar_combinaciones(st.session_state.materias_seleccionadas, st.session_state.rango_hora, st.session_state.prefs, st.session_state.horas_libres)
            if not res and msg != "OK": st.error(msg); st.session_state.resultados = []
            else: st.session_state.resultados = res
        if st.session_state.resultados:
            res = st.session_state.resultados; st.success(f"¡{len(res)} opciones encontradas!")
            total_creditos_final = sum([CREDITOS.get(m, 0) for m in st.session_state.materias_seleccionadas])
            alumno_data = { "nombre": st.session_state.alumno_nombre, "nc": st.session_state.alumno_nc, "semestre": st.session_state.alumno_sem, "periodo": st.session_state.alumno_per }
            for i, (score, horario) in enumerate(res):
                with st.container(border=True):
                    col_info, col_btn = st.columns([4, 1])
                    col_info.subheader(f"Opción {i+1}")
                    pdf_bytes = create_pro_pdf(horario, alumno_data, total_creditos_final)
                    col_btn.download_button("📄 PDF", data=pdf_bytes, file_name=f"Carga_Op{i+1}.pdf", mime="application/pdf", key=f"btn_{i}")
                    html_table = create_timetable_html(horario); st.markdown(html_table, unsafe_allow_html=True); st.write("")
        elif st.session_state.resultados is not None and len(st.session_state.resultados) == 0:
            st.warning("⚠️ No hay combinaciones. Intenta quitar restricciones.")
        if st.button("🔄 Inicio"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

# =============================================================================
# VISTA 2: EVALUACIÓN DOCENTE (NUEVO)
# =============================================================================
elif menu == "⭐ Evaluación Docente":
    st.title("⭐ Califica a tu Maestro")
    st.markdown("Tu opinión ayuda a otros compañeros. ¡Sé honesto!")
    
    # 1. Obtener lista plana de todos los profes
    all_profs = set()
    for lista in oferta_academica.values():
        for grupo in lista:
            all_profs.add(grupo['profesor'])
    all_profs = sorted(list(all_profs))
    
    # 2. Selección de Profe
    prof_selected = st.selectbox("Selecciona al profesor:", all_profs)
    
    # 3. Interfaz de Calificación
    st.write("---")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader(f"Opina sobre: {prof_selected}")
        nuevo_comentario = st.text_area("Deja tu comentario (Anónimo):")
        nueva_calif = st.slider("Calificación General (0 - 100):", 0, 100, 80)
        
        if st.button("Enviar Opinión"):
            # Guardar en "Simulación de Base de Datos"
            if prof_selected not in st.session_state.opiniones:
                st.session_state.opiniones[prof_selected] = {"suma": 0, "votos": 0, "comentarios": []}
            
            db = st.session_state.opiniones[prof_selected]
            db["suma"] += nueva_calif
            db["votos"] += 1
            db["comentarios"].insert(0, nuevo_comentario) # El más reciente arriba
            st.success("¡Gracias! Tu opinión ha sido registrada.")
            st.rerun()

    with c2:
        # 4. Mostrar Estadísticas (Gráfica de Donut)
        if prof_selected in st.session_state.opiniones:
            data = st.session_state.opiniones[prof_selected]
            promedio = int(data["suma"] / data["votos"])
            st.markdown(f"<h3 style='text-align: center;'>Promedio: {promedio}</h3>", unsafe_allow_html=True)
            
            # Gráfica Plotly
            fig = get_donut_chart(promedio)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.caption(f"Basado en {data['votos']} opiniones.")
        else:
            st.info("Este profesor aún no tiene calificaciones. ¡Sé el primero!")

    # 5. Muro de Comentarios
    st.write("---")
    st.subheader("💬 Comentarios Recientes")
    if prof_selected in st.session_state.opiniones and st.session_state.opiniones[prof_selected]["comentarios"]:
        for com in st.session_state.opiniones[prof_selected]["comentarios"]:
            st.markdown(f"""
            <div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid #800000;">
                {com}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No hay comentarios escritos aún.")
