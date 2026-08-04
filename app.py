import base64
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import count
import heapq
import json
import mimetypes
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import gspread
import streamlit as st
from fpdf import FPDF
from google.oauth2.service_account import Credentials

# =============================================================================
# 1. IDENTIDAD Y CONFIGURACIÓN
# =============================================================================
APP_NAME = "Horario ITS"
APP_SUBTITLE = "Generador inteligente de horarios académicos"
AUTOR = "Néstor Alexis Piña Rodríguez"
PERIODO_CODIGO = "2026_AGO_DIC"
PERIODO_TEXTO = "AGOSTO - DICIEMBRE 2026"
MAX_CREDITOS = 36
MAX_RESULTADOS = 15
RESIDENCIA = "Residencia Profesional"
MAX_MATERIAS_ADICIONALES_RESIDENCIA = 2

CARRERAS = {
    "INGENIERÍA MECATRÓNICA": "mecatronica",
    "INGENIERÍA INDUSTRIAL": "industrial",
    "INGENIERÍA MECÁNICA": "mecanica",
    "INGENIERÍA ELÉCTRICA": "electrica",
    "INGENIERÍA ELECTRÓNICA": "electronica",
    "INGENIERÍA EN SISTEMAS COMPUTACIONALES": "sistemas",
    "INGENIERÍA EN MATERIALES": "materiales",
    "INGENIERÍA QUÍMICA": "quimica",
    "INGENIERÍA EN GESTIÓN EMPRESARIAL": "gestion_empresarial",
}

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

st.set_page_config(
    page_title=f"{APP_NAME} | Ago-Dic 2026",
    page_icon="🫏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    r"""
<style>
    :root {
        --guinda-900: #4f0717;
        --guinda-800: #681026;
        --guinda-700: #7b1028;
        --guinda-600: #951a35;
        --guinda-500: #a61b36;
        --fondo: #0e1117;
        --panel: #151922;
        --panel-2: #1c212c;
        --borde: rgba(225, 229, 238, 0.16);
        --texto: #f4f5f7;
        --texto-suave: #aeb4c0;
        --verde: #3ddc97;
        --rojo: #ff6b76;
        --ambar: #f7c66b;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 16% -10%, rgba(123, 16, 40, 0.22), transparent 32rem),
            radial-gradient(circle at 96% 2%, rgba(196, 154, 86, 0.07), transparent 24rem),
            var(--fondo);
    }

    [data-testid="stHeader"] { background: transparent; }

    [data-testid="stMainBlockContainer"] {
        max-width: 1780px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: var(--texto) !important;
        font-family: Arial, Helvetica, sans-serif;
        letter-spacing: -0.02em;
    }

    .brand-header {
        display: grid;
        grid-template-columns: minmax(120px, .75fr) minmax(420px, 2.5fr) minmax(120px, .75fr);
        gap: 24px;
        align-items: center;
        padding: 16px 22px;
        border: 1px solid var(--borde);
        border-top: 4px solid var(--guinda-600);
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(29, 33, 44, .97), rgba(17, 20, 28, .98));
        box-shadow: 0 18px 48px rgba(0, 0, 0, .23);
        margin-bottom: 12px;
    }

    .institution-logo {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70px;
    }

    .institution-logo img {
        width: 100%;
        max-width: 170px;
        max-height: 75px;
        object-fit: contain;
    }

    .institution-fallback {
        min-height: 66px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px dashed rgba(255,255,255,.22);
        border-radius: 12px;
        color: var(--texto-suave);
        font-weight: 850;
        letter-spacing: .08em;
    }

    .project-logo { display: flex; justify-content: center; align-items: center; }
    .project-logo img { width: min(100%, 670px); max-height: 116px; object-fit: contain; }

    .progress-track {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 9px;
        margin: 0 0 20px 0;
    }

    .progress-step {
        min-height: 43px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        padding: 8px 10px;
        border-radius: 11px;
        border: 1px solid var(--borde);
        background: rgba(22, 26, 35, .92);
        color: var(--texto-suave);
        font-size: .78rem;
        font-weight: 800;
        text-align: center;
    }

    .progress-step.done {
        color: #ffdce4;
        border-color: rgba(166, 27, 54, .55);
        background: rgba(123, 16, 40, .26);
    }

    .progress-step.active {
        color: white;
        border-color: var(--guinda-500);
        background: linear-gradient(135deg, var(--guinda-700), var(--guinda-500));
        box-shadow: 0 8px 20px rgba(123, 16, 40, .27);
    }

    .hero-panel {
        padding: 27px 30px;
        border: 1px solid var(--borde);
        border-radius: 21px;
        background: linear-gradient(115deg, rgba(123,16,40,.22), rgba(21,25,34,.95) 48%), var(--panel);
        box-shadow: 0 18px 40px rgba(0,0,0,.18);
        margin-bottom: 18px;
    }

    .hero-kicker {
        color: #e6b7c3;
        font-size: .74rem;
        font-weight: 900;
        letter-spacing: .16em;
        text-transform: uppercase;
        margin-bottom: 7px;
    }

    .hero-title {
        color: white;
        font-size: clamp(1.9rem, 3vw, 3rem);
        line-height: 1.04;
        font-weight: 950;
        letter-spacing: -.04em;
        margin-bottom: 10px;
    }

    .hero-copy {
        color: #d0d4dc;
        max-width: 900px;
        font-size: 1rem;
        line-height: 1.55;
        margin: 0;
    }

    .hero-meta { display:flex; flex-wrap:wrap; gap:9px; margin-top:16px; }
    .meta-chip {
        display:inline-flex; align-items:center; gap:7px; padding:7px 11px;
        border:1px solid rgba(255,255,255,.14); border-radius:999px;
        background:rgba(5,7,11,.22); color:#edf0f4; font-size:.77rem; font-weight:750;
    }

    .section-head {
        padding: 18px 22px;
        border-left: 5px solid var(--guinda-500);
        border-radius: 0 15px 15px 0;
        background: linear-gradient(90deg, rgba(123,16,40,.22), rgba(21,25,34,.8));
        margin-bottom: 16px;
    }
    .section-head h1 { margin:0 0 4px 0; font-size:clamp(1.5rem,2.2vw,2.25rem); }
    .section-head p { margin:0; color:var(--texto-suave); line-height:1.48; }

    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--borde) !important;
        border-radius: 17px !important;
        background: rgba(20,24,33,.72) !important;
    }

    .semester-header {
        min-height:42px; display:flex; align-items:center; justify-content:center;
        color:#f7dce3; font-weight:950; font-size:.9rem; text-align:center;
        border:1px solid rgba(166,27,54,.45); border-bottom:3px solid var(--guinda-500);
        border-radius:10px 10px 4px 4px; background:rgba(123,16,40,.18); margin-bottom:10px;
    }

    .credit-box { padding:14px; border-radius:13px; text-align:center; font-weight:900; margin-top:10px; }
    .credit-ok { background:rgba(4,95,70,.30); color:var(--verde); border:1px solid var(--verde); }
    .credit-error { background:rgba(153,27,27,.27); color:#ff8c95; border:1px solid #ff6b76; }
    .selection-note { color:var(--texto-suave); font-size:.82rem; margin:4px 0 14px 0; }

    .stButton > button, [data-testid="stFormSubmitButton"] > button {
        min-height:46px; color:white !important;
        background:linear-gradient(135deg,var(--guinda-700),var(--guinda-500)) !important;
        border:1px solid rgba(255,255,255,.1) !important;
        font-weight:850 !important; border-radius:11px !important;
        box-shadow:0 9px 20px rgba(92,8,28,.21);
    }
    .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        background:linear-gradient(135deg,var(--guinda-600),#bf2444) !important;
        border-color:rgba(255,255,255,.2) !important; transform:translateY(-1px);
    }

    .group-card {
        border:1px solid var(--borde);
        border-left:4px solid var(--guinda-500);
        border-radius:14px;
        padding:13px 14px;
        background:linear-gradient(135deg,rgba(37,41,53,.9),rgba(18,21,29,.94));
        margin-bottom:10px;
    }
    .group-title { color:#fff; font-size:1rem; font-weight:900; margin-bottom:4px; }
    .group-meta { color:var(--texto-suave); font-size:.8rem; line-height:1.5; }
    .session-chip {
        display:inline-block; margin:3px 4px 3px 0; padding:5px 8px;
        border-radius:999px; border:1px solid rgba(255,255,255,.13);
        background:rgba(255,255,255,.05); color:#e9ebef; font-size:.72rem; font-weight:750;
    }
    .rating-row { display:flex; align-items:center; gap:12px; min-height:90px; }
    .rating-donut {
        width:76px; height:76px; border-radius:50%; position:relative; flex:0 0 76px;
        display:flex; align-items:center; justify-content:center;
    }
    .rating-donut::after {
        content:""; width:54px; height:54px; border-radius:50%; background:#171b24; position:absolute;
    }
    .rating-number { position:relative; z-index:2; color:#fff; font-size:1rem; font-weight:950; }
    .rating-copy { color:var(--texto-suave); font-size:.8rem; line-height:1.45; }
    .status-full { color:#ff9ea7; font-weight:850; }
    .status-open { color:#76e8b2; font-weight:850; }

    .subject-panel-title {
        display:flex; align-items:center; gap:8px; margin:0 0 10px 0;
        color:#fff; font-size:1.05rem; font-weight:950;
    }
    .professor-card-head {
        padding:8px 10px; margin-bottom:6px; border-left:3px solid var(--guinda-500);
        border-radius:8px; background:rgba(123,16,40,.13);
    }
    .professor-card-name { color:#fff; font-size:.92rem; font-weight:900; line-height:1.25; }
    .professor-card-sub { color:var(--texto-suave); font-size:.7rem; margin-top:2px; }
    .compact-rating { min-height:58px !important; gap:8px !important; margin:2px 0 6px; }
    .compact-donut { width:52px !important; height:52px !important; flex-basis:52px !important; }
    .compact-donut::after { width:36px !important; height:36px !important; }
    .compact-donut .rating-number { font-size:.82rem !important; }
    .group-warning {
        color:#ffd08a; font-size:.72rem; line-height:1.35; margin:-2px 0 6px 2px;
    }
    .compact-help { color:var(--texto-suave); font-size:.72rem; line-height:1.35; }

    .horario-grid {
        width:100%; border-collapse:separate; border-spacing:0; text-align:center;
        font-size:.8em; background:#fff; color:#151820; border-radius:12px; overflow:hidden;
        box-shadow:0 12px 28px rgba(0,0,0,.18);
    }
    .horario-grid th { background:var(--guinda-700); color:white; padding:9px; border:1px solid #5d0c20; }
    .horario-grid td { border:1px solid #e0e3e9; height:47px; vertical-align:middle; padding:2px; }
    .hora-col { background:#e8eaf0; font-weight:900; width:72px; }
    .clase-cell {
        border-radius:6px; padding:5px; color:#111; font-weight:800; font-size:.92em;
        height:100%; display:flex; flex-direction:column; justify-content:center;
    }

    .footer-note { text-align:center; color:#7f8794; font-size:.75rem; padding-top:25px; }

    @media (max-width: 1180px) {
        .brand-header { grid-template-columns:110px 1fr 110px; }
        .progress-step span { display:none; }
    }

    @media (max-width:760px) {
        .brand-header { grid-template-columns:1fr; gap:10px; }
        .institution-logo { display:none; }
        .project-logo img { max-height:92px; }
        .progress-step { font-size:.66rem; padding:7px 3px; }
        .hero-panel { padding:22px 18px; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# 2. RECURSOS VISUALES
# =============================================================================
def _first_existing_path(*candidates):
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def _data_uri(path):
    if path is None:
        return None
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _logo_html(path, fallback):
    uri = _data_uri(path)
    if uri:
        return f'<img src="{uri}" alt="{fallback}">'
    return f'<div class="institution-fallback">{fallback}</div>'


def render_brand_header(current_step):
    tecnm_path = _first_existing_path("assets/logo_tecnm.png", "assets/logo_tec.png", "logo_tec.png")
    its_path = _first_existing_path("assets/logo_its.png", "logo_its.png")
    project_path = _first_existing_path("assets/horario_its_logo.svg", "horario_its_logo.svg")

    project_uri = _data_uri(project_path)
    project_html = (
        f'<img src="{project_uri}" alt="{APP_NAME}">'
        if project_uri
        else '<div style="text-align:center"><div style="font-size:2.1rem;font-weight:950;color:#fff">HORARIO ITS 🫏</div><div style="color:#b9bec8;font-size:.8rem">GENERADOR DE HORARIOS</div></div>'
    )

    st.markdown(
        f"""
        <div class="brand-header">
            <div class="institution-logo">{_logo_html(tecnm_path, "TECNM")}</div>
            <div class="project-logo">{project_html}</div>
            <div class="institution-logo">{_logo_html(its_path, "ITS")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels = (
        (1, "Inicio", "Configura tu carga"),
        (2, "Materias", "Elige asignaturas"),
        (3, "Grupos", "Profesores y horas"),
        (4, "Horarios", "Compara opciones"),
    )
    items = []
    for number, title, subtitle in labels:
        if number < current_step:
            css_class, icon = "done", "✓"
        elif number == current_step:
            css_class, icon = "active", str(number)
        else:
            css_class, icon = "", str(number)
        items.append(
            f'<div class="progress-step {css_class}"><strong>{icon}. {title}</strong><span>· {subtitle}</span></div>'
        )
    st.markdown('<div class="progress-track">' + "".join(items) + "</div>", unsafe_allow_html=True)


def render_section_header(title, description):
    st.markdown(
        f'<div class="section-head"><h1>{title}</h1><p>{description}</p></div>',
        unsafe_allow_html=True,
    )




def render_subject_card_css():
    """Activa el estilo de tarjetas únicamente en la página de materias."""
    st.markdown(
        r"""
        <style>
        [data-testid="stCheckbox"] {
            min-height: 160px !important;
            height: 160px !important;
            max-height: 160px !important;
            margin-bottom: 10px !important;
        }
        [data-testid="stCheckbox"] > label {
            width: 100% !important;
            min-height: 152px !important;
            height: 152px !important;
            max-height: 152px !important;
            box-sizing: border-box !important;
            border: 1px solid rgba(180,186,198,.28) !important;
            border-radius: 14px !important;
            padding: 12px 8px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            overflow: visible !important;
            transition: transform .16s ease, border-color .16s ease, background .16s ease !important;
            cursor: pointer !important;
            background: linear-gradient(145deg, rgba(27,32,43,.98), rgba(16,19,27,.98));
        }
        [data-testid="stCheckbox"] > label:hover {
            border-color: var(--guinda-500) !important;
            background: linear-gradient(145deg, rgba(83,15,33,.72), rgba(24,27,37,.98)) !important;
            transform: translateY(-2px);
            box-shadow: 0 10px 22px rgba(0,0,0,.18);
        }
        [data-testid="stCheckbox"]:has(input:checked) > label {
            background: linear-gradient(145deg, var(--guinda-700), var(--guinda-500)) !important;
            border-color: #d74b68 !important;
            box-shadow: 0 10px 25px rgba(123,16,40,.32);
        }
        [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] {
            width: 100% !important;
            display:flex !important;
            align-items:center !important;
            justify-content:center !important;
        }
        [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p {
            width:100% !important;
            margin:0 !important;
            color:#f5f6f8 !important;
            font-size:clamp(.61rem,.69vw,.78rem) !important;
            line-height:1.2 !important;
            font-weight:780 !important;
            text-align:center !important;
            white-space:normal !important;
            word-break:normal !important;
            overflow-wrap:break-word !important;
            hyphens:none !important;
        }
        [data-testid="stCheckbox"]:has(input:checked) div[data-testid="stMarkdownContainer"] p {
            color:white !important;
            font-weight:900 !important;
        }
        @media (max-width:1180px) {
            [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p {
                font-size:.58rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_footer():
    st.markdown(
        f'<div class="footer-note">{APP_NAME} · Desarrollado por {AUTOR} · Instituto Tecnológico de Saltillo</div>',
        unsafe_allow_html=True,
    )

# =============================================================================
# 3. ICONOS, COLORES Y SERIACIONES
# =============================================================================
COLORS = [
    "#FFCDD2", "#F8BBD0", "#E1BEE7", "#D1C4E9", "#C5CAE9", "#BBDEFB",
    "#B3E5FC", "#B2EBF2", "#B2DFDB", "#C8E6C9", "#DCEDC8", "#F0F4C3",
]

ICONOS_MATERIAS = {
    "Química": "⚗️", "Cálculo Diferencial": "➗", "Taller De Ética": "⚖️",
    "Dibujo Asistido Por Computadora": "🖥️", "Metrología Y Normalización": "📏",
    "Fundamentos De Investigación": "🔎", "Estadística Y Control De Calidad": "📊",
    "Álgebra Lineal": "🔢", "Cálculo Integral": "∫", "Ciencia E Ingeniería De Materiales": "🧱",
    "Programación Básica": "💻", "Administración Y Contabilidad": "🧾",
    "Desarrollo Sustentable": "🌱", "Métodos Numéricos": "🧮", "Electromagnetismo": "🧲",
    "Procesos De Fabricación": "🏭", "Cálculo Vectorial": "🧭", "Estática": "🏗️",
    "Mecánica De Materiales": "🔩", "Dinámica": "🏎️", "Ecuaciones Diferenciales": "📈",
    "Taller De Investigación I": "📝", "Análisis De Circuitos Eléctricos": "🔌",
    "Fundamentos De Termodinámica": "🌡️", "Mecanismos": "⚙️", "Programación Avanzada": "🧑‍💻",
    "Taller De Investigación II": "📚", "Máquinas Eléctricas": "⚡", "Análisis De Fluidos": "💧",
    "Electrónica Analógica": "〰️", "Electrónica De Potencia Aplicada": "🔋",
    "Instrumentación": "🎛️", "Diseño De Elementos Mecánicos": "🛠️", "Electrónica Digital": "0️⃣",
    "Vibraciones Mecánicas": "📳", "Administración del Mantenimiento": "📋",
    "Dinámica De Sistemas": "🔄", "Manufactura Avanzada": "🏭",
    "Circuitos Hidráulicos Y Neumáticos": "💨", "Mantenimiento": "🔧",
    "Microcontroladores": "🧠", "Diseño Asistido por Computadora": "✏️", "Control": "🎚️",
    "Formulación Y Evaluación De Proyectos": "📑", "Controladores Lógicos Programables": "🧩",
    "Sistemas Avanzados De Manufactura": "🦾", "Redes Industriales": "🌐",
    "Tópicos Selectos de Automatización Industrial": "🤖", "Robótica": "🤖",
    "Residencia Profesional": "🎓",
}

SERIADAS_DIRECTAS = (
    ("Cálculo Diferencial", "Cálculo Integral"),
    ("Cálculo Integral", "Cálculo Vectorial"),
    ("Cálculo Vectorial", "Ecuaciones Diferenciales"),
    ("Cálculo Vectorial", "Dinámica"),
    ("Química", "Ciencia E Ingeniería De Materiales"),
    ("Ciencia E Ingeniería De Materiales", "Procesos De Fabricación"),
    ("Procesos De Fabricación", "Manufactura Avanzada"),
    ("Dinámica", "Mecanismos"),
    ("Mecanismos", "Vibraciones Mecánicas"),
    ("Vibraciones Mecánicas", "Dinámica De Sistemas"),
    ("Dinámica De Sistemas", "Control"),
    ("Estática", "Mecánica De Materiales"),
    ("Mecánica De Materiales", "Diseño De Elementos Mecánicos"),
    ("Electromagnetismo", "Análisis De Circuitos Eléctricos"),
    ("Análisis De Circuitos Eléctricos", "Electrónica Analógica"),
    ("Electrónica Analógica", "Electrónica Digital"),
    ("Electrónica Digital", "Microcontroladores"),
    ("Programación Básica", "Programación Avanzada"),
    ("Máquinas Eléctricas", "Electrónica De Potencia Aplicada"),
    ("Electrónica De Potencia Aplicada", "Controladores Lógicos Programables"),
    ("Circuitos Hidráulicos Y Neumáticos", "Controladores Lógicos Programables"),
    ("Controladores Lógicos Programables", "Tópicos Selectos de Automatización Industrial"),
    ("Redes Industriales", "Tópicos Selectos de Automatización Industrial"),
    ("Taller De Investigación I", "Taller De Investigación II"),
)

# =============================================================================
# 4. GOOGLE SHEETS: OPINIONES Y REPORTES
# =============================================================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# La hoja existente del usuario usa estas cuatro columnas y escala de 0 a 100.
RATING_HEADERS = ["Profesor", "Comentario", "Calificación", "Fecha"]

# Un reporte se registra por opción completa de grupo/horario, no bloquea la selección.
REPORT_HEADERS = [
    "Profesor",
    "Materia",
    "Grupo",
    "Horario",
    "Opcion_ID",
    "Estado",
    "Fecha",
    "Periodo",
    "Carrera",
]

# Respaldo del archivo opiniones_its. El valor no es una credencial privada.
DEFAULT_SPREADSHEET_ID = "1I2RS8vuH2Yr32k2vZG18n-YZF6h_9z4N7oVTNf2EmyQ"


def _normalize(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text).lower()
    return " ".join(text.split())


_NAME_STOPWORDS = {"de", "del", "la", "las", "los", "y", "ma", "maria"}


def _name_tokens(value):
    return [
        token
        for token in _normalize(value).split()
        if len(token) > 1 and token not in _NAME_STOPWORDS
    ]


def _professor_matches(saved_name, target_name):
    """Tolera acentos, orden distinto, nombres abreviados y apellidos compuestos."""
    saved = _normalize(saved_name)
    target = _normalize(target_name)
    if not saved or not target:
        return False
    if saved == target:
        return True

    saved_tokens = _name_tokens(saved)
    target_tokens = _name_tokens(target)
    saved_set = set(saved_tokens)
    target_set = set(target_tokens)

    if saved_set == target_set and saved_set:
        return True

    common = saved_set & target_set
    minimum_size = min(len(saved_set), len(target_set))
    if minimum_size >= 2 and len(common) / minimum_size >= 0.75:
        return True

    # Comparar también los nombres ordenados evita que "Gómez Muñoz Ana Gabriela"
    # falle contra "Ana Gabriela Gomez Muñoz".
    saved_sorted = " ".join(sorted(saved_tokens))
    target_sorted = " ".join(sorted(target_tokens))
    if SequenceMatcher(None, saved_sorted, target_sorted).ratio() >= 0.84:
        return True

    return SequenceMatcher(None, saved, target).ratio() >= 0.80


def display_professor_name(value):
    """Convierte 'Apellidos Nombres' a 'Nombres Apellidos' para mostrarlo."""
    original = " ".join(str(value or "POR ASIGNAR").split())
    if _normalize(original) == "por asignar":
        return "POR ASIGNAR"

    parts = original.split()
    if len(parts) < 3:
        return original

    # La oferta del ITS coloca normalmente dos apellidos al inicio.
    surnames = parts[:2]
    given_names = parts[2:]
    return " ".join(given_names + surnames)


@st.cache_resource
def get_db_connection():
    try:
        info = dict(st.secrets["gcp_service_account"])
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None


def _sheet_config():
    config = {}
    try:
        if "google_sheets" in st.secrets:
            config.update(dict(st.secrets["google_sheets"]))
    except Exception:
        pass
    for key in ("spreadsheet_id", "spreadsheet_url", "spreadsheet_name"):
        try:
            if key in st.secrets and key not in config:
                config[key] = st.secrets[key]
        except Exception:
            pass
    return config


@st.cache_resource
def get_spreadsheet():
    client = get_db_connection()
    if client is None:
        return None

    config = _sheet_config()

    # Cada intento se prueba por separado. Un ID mal escrito en Secrets ya no
    # impide que la app pruebe el ID correcto o el nombre del archivo.
    id_candidates = []
    configured_id = str(config.get("spreadsheet_id", "")).strip()
    if configured_id:
        id_candidates.append(configured_id)
    if DEFAULT_SPREADSHEET_ID not in id_candidates:
        id_candidates.append(DEFAULT_SPREADSHEET_ID)

    for spreadsheet_id in id_candidates:
        try:
            return client.open_by_key(spreadsheet_id)
        except Exception:
            continue

    configured_url = str(config.get("spreadsheet_url", "")).strip()
    if configured_url:
        try:
            return client.open_by_url(configured_url)
        except Exception:
            pass

    name_candidates = []
    configured_name = str(config.get("spreadsheet_name", "")).strip()
    if configured_name:
        name_candidates.append(configured_name)
    name_candidates.extend(
        [
            "opiniones_its",
            "Opiniones_its",
            "Opiniones ITS",
            "Horario ITS",
            "HorarioITS",
            "Waze Académico",
            "Waze Academico",
        ]
    )

    for name in dict.fromkeys(name_candidates):
        try:
            return client.open(name)
        except Exception:
            continue

    return None


def _ensure_headers(worksheet, required_headers):
    try:
        values = worksheet.get_all_values()
        if not values:
            worksheet.append_row(required_headers)
            return list(required_headers)

        headers = [str(value).strip() for value in values[0]]
        normalized = {_normalize(header) for header in headers if header}
        missing = [header for header in required_headers if _normalize(header) not in normalized]
        if missing:
            headers.extend(missing)
            worksheet.update(range_name="A1", values=[headers])
        return headers
    except Exception:
        return list(required_headers)


def _worksheet(candidates, headers):
    book = get_spreadsheet()
    if book is None:
        return None

    for name in candidates:
        try:
            worksheet = book.worksheet(name)
            _ensure_headers(worksheet, headers)
            return worksheet
        except gspread.WorksheetNotFound:
            continue
        except Exception:
            return None

    try:
        worksheet = book.add_worksheet(title=candidates[0], rows=1500, cols=max(12, len(headers)))
        worksheet.append_row(headers)
        return worksheet
    except Exception:
        return None


def _record_value(record, *aliases):
    normalized = {_normalize(key): value for key, value in record.items()}
    for alias in aliases:
        key = _normalize(alias)
        if key in normalized:
            return normalized[key]
    return ""


def _append_record(worksheet, values_by_header, required_headers):
    headers = _ensure_headers(worksheet, required_headers)
    normalized_values = {_normalize(key): value for key, value in values_by_header.items()}
    row = [normalized_values.get(_normalize(header), "") for header in headers]
    worksheet.append_row(row, value_input_option="USER_ENTERED")


@st.cache_data(ttl=30)
def read_ratings():
    """Lee Hoja 1 sin depender de get_all_records, que falla con columnas vacías."""
    worksheet = _worksheet(("Hoja 1", "Opiniones", "Calificaciones", "Profesores"), RATING_HEADERS)
    if worksheet is None:
        return []

    try:
        values = worksheet.get_all_values()
        if not values:
            return []

        headers = [_normalize(value) for value in values[0]]
        records = []
        for raw_row in values[1:]:
            if not any(str(value).strip() for value in raw_row):
                continue
            padded = list(raw_row) + [""] * max(0, len(headers) - len(raw_row))
            record = {
                headers[index]: padded[index]
                for index in range(len(headers))
                if headers[index]
            }
            records.append(record)
        return records
    except Exception:
        return []


@st.cache_data(ttl=30)
def read_reports():
    worksheet = _worksheet(("reportes_grupos", "Grupos_Llenos", "Grupos Llenos", "Reportes"), REPORT_HEADERS)
    if worksheet is None:
        return []
    try:
        return worksheet.get_all_records()
    except Exception:
        return []


def ratings_for_professor(professor):
    result = []
    for row in read_ratings():
        saved_name = _record_value(row, "Profesor", "Maestro", "Docente")
        if not _professor_matches(saved_name, professor):
            continue

        try:
            raw_score = str(
                _record_value(
                    row,
                    "Calificación",
                    "Calificacion",
                    "Rating",
                    "Puntuación",
                    "Puntuacion",
                )
            ).replace(",", ".").strip()
            score = float(raw_score)
        except (TypeError, ValueError):
            continue

        # Compatibilidad con opiniones antiguas en escala 1-5.
        if 0 <= score <= 5:
            score *= 20
        if not 0 <= score <= 100:
            continue

        result.append(
            {
                "calificacion": score,
                "comentario": str(
                    _record_value(row, "Comentario", "Opinión", "Opinion", "Reseña", "Resena")
                ).strip(),
                "fecha": str(_record_value(row, "Fecha", "Timestamp")).strip(),
            }
        )
    return result


def schedule_signature(group):
    return "|".join(
        f"{day}-{start}-{end}"
        for day, start, end in sorted(group.get("horario", []))
    )


def group_option_id(group):
    return f"{group.get('id', '')}|{schedule_signature(group)}"


def report_count(group):
    option_target = _normalize(group_option_id(group))
    group_target = _normalize(group.get("id", ""))
    schedule_target = _normalize(compact_schedule(group.get("horario", [])))
    count = 0

    for row in read_reports():
        state = _normalize(_record_value(row, "Estado", "Reporte", "Status"))
        if state not in ("", "lleno", "grupo lleno", "cerrado"):
            continue

        saved_option = _normalize(_record_value(row, "Opcion_ID", "Opción_ID", "Opcion", "Option_ID"))
        saved_group = _normalize(_record_value(row, "Grupo", "Grupo_ID", "ID"))
        saved_schedule = _normalize(_record_value(row, "Horario", "Hora"))

        if saved_option and saved_option == option_target:
            count += 1
        elif saved_group == group_target and (not saved_schedule or saved_schedule == schedule_target):
            count += 1

    return count


def submit_rating(professor, score, comment):
    worksheet = _worksheet(("Hoja 1", "Opiniones", "Calificaciones", "Profesores"), RATING_HEADERS)
    if worksheet is None:
        return False
    try:
        _append_record(
            worksheet,
            {
                "Profesor": professor,
                "Comentario": comment.strip(),
                "Calificación": int(score),
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            RATING_HEADERS,
        )
        read_ratings.clear()
        return True
    except Exception:
        return False


def submit_full_report(subject, group):
    worksheet = _worksheet(("reportes_grupos", "Grupos_Llenos", "Grupos Llenos", "Reportes"), REPORT_HEADERS)
    if worksheet is None:
        return False
    try:
        _append_record(
            worksheet,
            {
                "Profesor": group.get("profesor", "POR ASIGNAR"),
                "Materia": subject,
                "Grupo": group.get("id", ""),
                "Horario": compact_schedule(group.get("horario", [])),
                "Opcion_ID": group_option_id(group),
                "Estado": "LLENO",
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Periodo": PERIODO_CODIGO,
                "Carrera": st.session_state.get("carrera_nombre", ""),
            },
            REPORT_HEADERS,
        )
        read_reports.clear()
        return True
    except Exception:
        return False


# =============================================================================
# 5. CARGA Y NORMALIZACIÓN DE LA OFERTA
# =============================================================================
@st.cache_data
def _read_json(filepath, modified_ns):
    del modified_ns
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def load_oferta_json(periodo, carrera):
    filepath = f"data/{periodo}/{carrera}.json"
    if not os.path.exists(filepath):
        return None
    try:
        return _read_json(filepath, os.stat(filepath).st_mtime_ns)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"El archivo de la oferta tiene un error en la línea {error.lineno}, columna {error.colno}."
        ) from error


def format_json_to_oferta(json_data):
    if not isinstance(json_data, dict):
        raise ValueError("La oferta académica no tiene una estructura válida.")
    materias = json_data.get("materias", json_data)
    if not isinstance(materias, dict) or not materias:
        raise ValueError("No se encontraron materias en la oferta académica.")

    oferta = {}
    mat_sem = {semester: [] for semester in range(1, 10)}
    credits = {}

    for key, info in materias.items():
        if not isinstance(info, dict):
            raise ValueError(f"La materia {key} no tiene una estructura válida.")
        name = str(info.get("nombre", "")).strip()
        if not name:
            raise ValueError(f"La materia {key} no tiene nombre.")
        try:
            semester = int(info.get("semestre"))
            subject_credits = int(info.get("creditos", 0))
        except (TypeError, ValueError) as error:
            raise ValueError(f"La materia {name} tiene datos inválidos.") from error
        if semester not in range(1, 10):
            raise ValueError(f"La materia {name} tiene un semestre inválido.")
        if name in oferta:
            raise ValueError(f"Nombre de materia duplicado: {name}")

        mat_sem[semester].append(name)
        credits[name] = subject_credits
        oferta[name] = []

        for group in info.get("grupos", []):
            schedule = [
                (int(session["dia"]), int(session["inicio"]), int(session["fin"]))
                for session in group.get("horario", [])
            ]
            oferta[name].append(
                {
                    "profesor": group.get("profesor", "POR ASIGNAR"),
                    "salon": group.get("salon", "POR ASIGNAR"),
                    "horario": schedule,
                    "id": group.get("id", ""),
                    "materia": name,
                }
            )

    for semester in mat_sem:
        mat_sem[semester].sort()
    return oferta, mat_sem, credits

# =============================================================================
# 6. REGLAS ACADÉMICAS
# =============================================================================
def build_prerequisite_graph():
    graph = {}
    for previous, next_subject in SERIADAS_DIRECTAS:
        graph.setdefault(previous, set()).add(next_subject)
    return graph


GRAFO_SERIADAS = build_prerequisite_graph()


def later_subjects(subject):
    visited = set()
    pending = list(GRAFO_SERIADAS.get(subject, set()))
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(GRAFO_SERIADAS.get(current, set()))
    return visited


def serial_conflicts(selection):
    selected = set(selection)
    conflicts = []
    for previous in sorted(selected):
        for next_subject in sorted(later_subjects(previous)):
            if next_subject in selected:
                conflicts.append((previous, next_subject))
    return conflicts


def validate_selection(selection, desired_count, credits_by_subject):
    errors = []
    total_credits = sum(credits_by_subject.get(subject, 0) for subject in selection)
    if len(selection) != desired_count:
        errors.append(
            f"Debes seleccionar exactamente {desired_count} materias; seleccionaste {len(selection)}."
        )
    if total_credits > MAX_CREDITOS:
        errors.append(f"La carga suma {total_credits} créditos y el máximo permitido es {MAX_CREDITOS}.")
    for previous, next_subject in serial_conflicts(selection):
        errors.append(f"No puedes cursar {previous} y {next_subject} en el mismo periodo porque son seriadas.")
    if RESIDENCIA in selection and len(selection) - 1 > MAX_MATERIAS_ADICIONALES_RESIDENCIA:
        errors.append(
            f"Residencia Profesional puede acompañarse de máximo {MAX_MATERIAS_ADICIONALES_RESIDENCIA} materias adicionales."
        )
    return errors, total_credits

# =============================================================================
# 7. FILTRO DE GRUPOS Y MOTOR DE COMBINACIONES
# =============================================================================
def session_label(session):
    day, start, end = session
    day_name = DIAS[day] if 0 <= day < len(DIAS) else f"Día {day}"
    return f"{day_name} {start}:00-{end}:00"


def _day_ranges(days):
    days = sorted(set(days))
    if not days:
        return ""
    ranges = []
    start = previous = days[0]
    for day in days[1:]:
        if day == previous + 1:
            previous = day
            continue
        ranges.append((start, previous))
        start = previous = day
    ranges.append((start, previous))

    labels = []
    for first, last in ranges:
        first_name = DIAS[first] if 0 <= first < len(DIAS) else f"Día {first}"
        last_name = DIAS[last] if 0 <= last < len(DIAS) else f"Día {last}"
        labels.append(first_name if first == last else f"{first_name}-{last_name}")
    return ", ".join(labels)


def compact_schedule(schedule):
    """Comprime Lun 10-11, Mar 10-11... como Lun-Jue 10:00-11:00."""
    by_time = defaultdict(list)
    for day, start, end in sorted(schedule):
        by_time[(start, end)].append(day)
    parts = []
    for (start, end), days in sorted(by_time.items()):
        parts.append(f"{_day_ranges(days)} {start}:00-{end}:00")
    return " · ".join(parts) if parts else "Sin horario"


def short_group_id(group_id):
    value = str(group_id or "SIN ID")
    return value.split("-")[-1] if "-" in value else value


def group_fits(group, time_range, blocked_hours):
    blocked = {int(value.split(":")[0]) for value in blocked_hours}
    for _, start, end in group.get("horario", []):
        if start < time_range[0] or end > time_range[1]:
            return False
        if any(hour in blocked for hour in range(start, end)):
            return False
    return True


def schedules_overlap(schedule_1, schedule_2):
    for session_1 in schedule_1:
        for session_2 in schedule_2:
            if session_1[0] == session_2[0] and max(session_1[1], session_2[1]) < min(session_1[2], session_2[2]):
                return True
    return False


def _schedule_presence_metrics(schedule):
    """Menor valor = menos tiempo total dentro del Tec."""
    sessions_by_day = defaultdict(list)
    occupied_slots = set()

    for course in schedule:
        for day, start, end in course.get("horario", []):
            sessions_by_day[day].append((start, end))
            for hour in range(start, end):
                occupied_slots.add((day, hour))

    if not sessions_by_day:
        return (0, 0, 0, 0)

    total_presence = 0
    for sessions in sessions_by_day.values():
        total_presence += max(end for _, end in sessions) - min(start for start, _ in sessions)

    class_hours = len(occupied_slots)
    idle_hours = max(0, total_presence - class_hours)
    days_on_campus = len(sessions_by_day)
    latest_exit = max(end for sessions in sessions_by_day.values() for _, end in sessions)
    return (total_presence, idle_hours, days_on_campus, latest_exit)


def _schedule_preference_score(schedule):
    return sum(int(course.get("_preference", 0)) for course in schedule)


def _combination_sort_key(schedule):
    # Mayor preferencia primero; después menor permanencia en el Tec.
    return (-_schedule_preference_score(schedule), *_schedule_presence_metrics(schedule))


def generate_combinations(subjects, filtered_offer):
    if not subjects:
        return [[]], "OK"

    ordered_subjects = sorted(subjects, key=lambda subject: len(filtered_offer.get(subject, [])))
    pools = []
    for subject in ordered_subjects:
        options = filtered_offer.get(subject, [])
        if not options:
            return [], f"No quedó ningún horario habilitado para {subject}."
        pools.append(options)

    sequence = count()
    # (-preferencia, permanencia, huecos, secuencia, índice, combinación)
    heap = [(0, 0, 0, next(sequence), 0, [])]
    completed = []
    max_completed_to_compare = max(MAX_RESULTADOS * 15, 150)
    max_states = 75000
    explored = 0

    while heap and len(completed) < max_completed_to_compare and explored < max_states:
        _, _, _, _, index, combination = heapq.heappop(heap)
        explored += 1

        if index == len(pools):
            completed.append(list(combination))
            continue

        for group in pools[index]:
            if any(
                schedules_overlap(group.get("horario", []), previous.get("horario", []))
                for previous in combination
            ):
                continue

            new_combination = combination + [group]
            preference = _schedule_preference_score(new_combination)
            presence, idle, _, _ = _schedule_presence_metrics(new_combination)
            heapq.heappush(
                heap,
                (-preference, presence, idle, next(sequence), index + 1, new_combination),
            )

    completed.sort(key=_combination_sort_key)
    return completed[:MAX_RESULTADOS], "OK"


# =============================================================================
# 8. HORARIO HTML Y COMPONENTES DE PROFESORES
# =============================================================================
def create_timetable_html(schedule):
    if not schedule:
        return "<div style='padding:16px;color:#aeb4c0'>No hay bloques que mostrar.</div>"

    hours = [hour for course in schedule for session in course["horario"] for hour in (session[1], session[2])]
    if not hours:
        return ""

    min_hour, max_hour = min(hours), max(hours)
    has_saturday = any(session[0] == 5 for course in schedule for session in course["horario"])
    day_count = 6 if has_saturday else 5
    grid = {hour: [None] * day_count for hour in range(min_hour, max_hour)}
    colors = {course["materia"]: COLORS[index % len(COLORS)] for index, course in enumerate(schedule)}

    for course in schedule:
        for session in course["horario"]:
            for hour in range(session[1], session[2]):
                if session[0] < day_count:
                    grid[hour][session[0]] = (
                        f"<div class='clase-cell' style='background-color:{colors[course['materia']]}'><span>{course['materia']}</span>"
                        f"<small>{display_professor_name(course['profesor'])}</small></div>"
                    )

    headers = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"][:day_count]
    html = "<table class='horario-grid'><thead><tr><th class='hora-col'>Hora</th>" + "".join(
        f"<th>{day}</th>" for day in headers
    ) + "</tr></thead><tbody>"
    for hour in range(min_hour, max_hour):
        html += f"<tr><td class='hora-col'>{hour}:00-{hour+1}:00</td>" + "".join(
            f"<td>{grid[hour][day] or ''}</td>" for day in range(day_count)
        ) + "</tr>"
    return html + "</tbody></table>"


def rating_html(ratings):
    if not ratings:
        average, count_ratings = 0.0, 0
    else:
        average = sum(item["calificacion"] for item in ratings) / len(ratings)
        count_ratings = len(ratings)
    angle = max(0, min(360, average / 100 * 360))
    color = "#3ddc97" if average >= 80 else "#f7c66b" if average >= 60 else "#ff6b76"
    label = f"{average:.0f}" if count_ratings else "—"
    copy = (
        f"{count_ratings} opinión{'es' if count_ratings != 1 else ''}"
        if count_ratings
        else "Sin opiniones"
    )
    return (
        '<div class="rating-row compact-rating">'
        f'<div class="rating-donut compact-donut" style="background:conic-gradient({color} 0deg {angle}deg, #343946 {angle}deg 360deg)">'
        f'<span class="rating-number">{label}</span></div>'
        f'<div class="rating-copy"><strong style="color:#fff">{copy}</strong><br>Promedio / 100</div>'
        '</div>'
    )


def _pdf_safe(value):
    return str(value or "").replace("–", "-").replace("—", "-").encode("latin-1", "replace").decode("latin-1")


def _pdf_short(value, limit):
    text_value = _pdf_safe(value)
    return text_value if len(text_value) <= limit else text_value[: max(1, limit - 3)] + "..."


def _pdf_output_bytes(pdf):
    """Compatible con PyFPDF 1.x y fpdf2."""
    raw = pdf.output(dest="S")
    if isinstance(raw, str):
        return raw.encode("latin-1")
    return bytes(raw)


def create_schedule_pdf(schedule, option_number, student_data):
    pdf = FPDF(orientation="L", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    page_width = pdf.w
    margin = 10
    usable_width = page_width - (2 * margin)

    tecnm_path = _first_existing_path("assets/logo_tecnm.png", "assets/logo_tec.png", "logo_tec.png")
    its_path = _first_existing_path("assets/logo_its.png", "logo_its.png")

    # Encabezado institucional.
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, page_width, 34, style="F")
    pdf.set_fill_color(128, 0, 0)
    pdf.rect(0, 31, page_width, 3, style="F")

    if tecnm_path:
        try:
            pdf.image(str(tecnm_path), x=margin, y=6, w=34)
        except Exception:
            pass
    if its_path:
        try:
            pdf.image(str(its_path), x=page_width - margin - 24, y=5, w=24)
        except Exception:
            pass

    pdf.set_text_color(65, 65, 65)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(48, 5)
    pdf.cell(page_width - 96, 5, _pdf_safe("TECNOLÓGICO NACIONAL DE MÉXICO"), align="C")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(48, 11)
    pdf.cell(page_width - 96, 6, _pdf_safe("INSTITUTO TECNOLÓGICO DE SALTILLO"), align="C")
    pdf.set_text_color(128, 0, 0)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_xy(48, 19)
    pdf.cell(page_width - 96, 7, _pdf_safe("HORARIO ITS"), align="C")

    # Tabla visible con datos institucionales, académicos y del estudiante.
    y = 38
    carrera = str(st.session_state.get("carrera_nombre", "")).strip() or "No especificada"
    nombre = str(student_data.get("nombre", "")).strip() or "No especificado"
    matricula = str(student_data.get("matricula", "")).strip() or "No especificada"
    semestre = str(student_data.get("semestre", "")).strip() or "No especificado"

    title_height = 7
    row_height_info = 7
    label_width = 24
    value_width = (usable_width - (2 * label_width)) / 2

    pdf.set_xy(margin, y)
    pdf.set_fill_color(128, 0, 0)
    pdf.set_draw_color(128, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(
        usable_width,
        title_height,
        _pdf_safe("DATOS ACADÉMICOS Y DEL ESTUDIANTE"),
        border=1,
        align="C",
        fill=True,
    )
    y += title_height

    info_rows = [
        (
            "Sistema",
            "Tecnológico Nacional de México",
            "Plantel",
            "Instituto Tecnológico de Saltillo",
        ),
        (
            "Carrera",
            carrera,
            "Periodo",
            PERIODO_TEXTO,
        ),
        (
            "Nombre",
            nombre,
            "Matrícula",
            matricula,
        ),
        (
            "Semestre",
            semestre,
            "Horario",
            f"Opción {option_number}",
        ),
    ]

    for left_label, left_value, right_label, right_value in info_rows:
        pdf.set_xy(margin, y)

        pdf.set_fill_color(128, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(
            label_width,
            row_height_info,
            _pdf_safe(left_label),
            border=1,
            align="C",
            fill=True,
        )

        pdf.set_fill_color(250, 246, 247)
        pdf.set_text_color(35, 35, 35)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(
            value_width,
            row_height_info,
            _pdf_short(left_value, 52),
            border=1,
            align="C",
            fill=True,
        )

        pdf.set_fill_color(128, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(
            label_width,
            row_height_info,
            _pdf_safe(right_label),
            border=1,
            align="C",
            fill=True,
        )

        pdf.set_fill_color(250, 246, 247)
        pdf.set_text_color(35, 35, 35)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(
            value_width,
            row_height_info,
            _pdf_short(right_value, 52),
            border=1,
            align="C",
            fill=True,
        )
        y += row_height_info

    y += 4

    if not schedule:
        pdf.set_xy(margin, y + 10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(usable_width, 10, _pdf_safe("La carga no contiene materias con horario."), align="C")
        return _pdf_output_bytes(pdf)

    hours = [hour for course in schedule for session in course["horario"] for hour in (session[1], session[2])]
    min_hour, max_hour = min(hours), max(hours)
    has_saturday = any(session[0] == 5 for course in schedule for session in course["horario"])
    day_count = 6 if has_saturday else 5
    headers = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"][:day_count]

    grid = {hour: [None] * day_count for hour in range(min_hour, max_hour)}
    for course in schedule:
        for day, start, end in course.get("horario", []):
            if day >= day_count:
                continue
            for hour in range(start, end):
                grid[hour][day] = course

    time_width = 22
    day_width = (usable_width - time_width) / day_count
    available_height = pdf.h - y - 10
    row_count = max(1, max_hour - min_hour)
    row_height = min(12, max(7.2, (available_height - 9) / row_count))

    pdf.set_xy(margin, y)
    pdf.set_fill_color(128, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(time_width, 9, "Hora", border=1, align="C", fill=True)
    for header in headers:
        pdf.cell(day_width, 9, _pdf_safe(header), border=1, align="C", fill=True)
    pdf.ln(9)

    color_map = {
        course["materia"]: (
            255 - ((index * 13) % 35),
            219 + ((index * 7) % 25),
            224 + ((index * 5) % 22),
        )
        for index, course in enumerate(schedule)
    }

    for hour in range(min_hour, max_hour):
        x = margin
        row_y = pdf.get_y()
        pdf.set_fill_color(235, 237, 242)
        pdf.set_text_color(25, 25, 25)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(x, row_y)
        pdf.cell(time_width, row_height, f"{hour}:00-{hour + 1}:00", border=1, align="C", fill=True)
        x += time_width

        for day in range(day_count):
            course = grid[hour][day]
            pdf.set_xy(x, row_y)
            if course:
                r, g, b = color_map[course["materia"]]
                pdf.set_fill_color(r, g, b)
                pdf.rect(x, row_y, day_width, row_height, style="DF")
                pdf.set_text_color(20, 20, 20)
                pdf.set_font("Helvetica", "B", 6.5)
                pdf.set_xy(x + 1, row_y + 1.0)
                pdf.cell(day_width - 2, 3.2, _pdf_short(course["materia"], 34), align="C")
                pdf.set_font("Helvetica", "", 6)
                pdf.set_xy(x + 1, row_y + min(4.9, row_height - 3.4))
                pdf.cell(
                    day_width - 2,
                    3,
                    _pdf_short(display_professor_name(course["profesor"]), 32),
                    align="C",
                )
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.cell(day_width, row_height, "", border=1, fill=True)
            x += day_width

        pdf.set_y(row_y + row_height)

    return _pdf_output_bytes(pdf)


# =============================================================================
# 9. ESTADO DE NAVEGACIÓN
# =============================================================================
if "step" not in st.session_state:
    st.session_state.step = 1

render_brand_header(st.session_state.step)

# =============================================================================
# PÁGINA 1 — INICIO
# =============================================================================
if st.session_state.step == 1:
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-kicker">Planeación académica · Ago-Dic 2026</div>
            <div class="hero-title">Organiza tu carga y genera horarios sin choques.</div>
            <p class="hero-copy">Selecciona tu carrera, materias y grupos. Horario ITS compara las opciones disponibles y crea alternativas compatibles.</p>
            <div class="hero-meta">
                <span class="meta-chip">🎓 Máximo 36 créditos</span>
                <span class="meta-chip">🧩 Validación de seriaciones</span>
                <span class="meta-chip">👤 Autor: {AUTOR}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_col, form_col = st.columns([.85, 1.25], gap="large")
    with info_col:
        render_section_header("Bienvenido a Horario ITS", "Planea tu carga antes de realizar la inscripción oficial.")
        st.markdown(
            """
            **La página te permite:**

            - Elegir materias de los nueve semestres.
            - Revisar profesores, grupos y horarios disponibles.
            - Consultar opiniones de otros estudiantes.
            - Generar combinaciones sin traslapes.
            """
        )

    with form_col:
        render_section_header("Configura tu búsqueda", "Selecciona la carrera y la cantidad de materias que deseas cursar.")
        with st.form("configuracion_inicial", border=True):
            st.text_input("📌 Periodo académico", PERIODO_TEXTO, disabled=True)
            career = st.selectbox("🎓 Carrera", list(CARRERAS.keys()), index=0)
            amount = st.number_input("📚 Materias a cursar", min_value=1, max_value=9, value=6, step=1)
            submit = st.form_submit_button("Cargar oferta  ➜", use_container_width=True, type="primary")

        if submit:
            slug = CARRERAS[career]
            try:
                data = load_oferta_json(PERIODO_CODIGO, slug)
                if data is None:
                    st.info("La oferta de esta carrera todavía no está disponible para el periodo seleccionado.")
                else:
                    (
                        st.session_state.oferta,
                        st.session_state.mat_sem,
                        st.session_state.creditos,
                    ) = format_json_to_oferta(data)
                    st.session_state.seleccion = []
                    st.session_state.cant_deseada = int(amount)
                    st.session_state.carrera = slug
                    st.session_state.carrera_nombre = career
                    for key in list(st.session_state.keys()):
                        if key.startswith(("materia_", "grupo_", "sesion_")):
                            del st.session_state[key]
                    st.session_state.step = 2
                    st.rerun()
            except ValueError as error:
                st.error(f"❌ {error}")

# =============================================================================
# PÁGINA 2 — MATERIAS
# =============================================================================
elif st.session_state.step == 2:
    render_subject_card_css()
    render_section_header(
        "📚 Selección de materias",
        "Elige la cantidad indicada. El sistema validará créditos, seriaciones y reglas especiales.",
    )

    if "seleccion" not in st.session_state:
        st.session_state.seleccion = []

    total_subjects = sum(len(subjects) for subjects in st.session_state.mat_sem.values())
    st.markdown(
        f'<div class="selection-note">{st.session_state.get("carrera_nombre", "")} · {total_subjects} materias disponibles · selecciona {st.session_state.cant_deseada}.</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(9, gap="small")
    selection = []
    for semester in range(1, 10):
        with columns[semester - 1]:
            st.markdown(f'<div class="semester-header">{semester}° semestre</div>', unsafe_allow_html=True)
            semester_subjects = st.session_state.mat_sem.get(semester, [])
            if not semester_subjects:
                st.caption("Sin materias")
            for subject in semester_subjects:
                credits = st.session_state.creditos.get(subject, 0)
                icon = ICONOS_MATERIAS.get(subject, "📘")
                label = f"{icon}  \n**{subject}**  \n({credits} Cr)"
                selected = st.checkbox(
                    label,
                    value=(subject in st.session_state.seleccion),
                    key=f"materia_{semester}_{subject}",
                )
                if selected:
                    selection.append(subject)

    errors, total_credits = validate_selection(selection, st.session_state.cant_deseada, st.session_state.creditos)
    st.divider()
    state_class = "credit-ok" if not errors else "credit-error"
    st.markdown(
        f'<div class="credit-box {state_class}">Créditos: {total_credits}/{MAX_CREDITOS} &nbsp;·&nbsp; Materias: {len(selection)}/{st.session_state.cant_deseada}</div>',
        unsafe_allow_html=True,
    )
    for error in errors:
        st.warning(f"⚠️ {error}")

    back_col, next_col = st.columns(2)
    if back_col.button("← Volver", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
    if not errors and next_col.button("Continuar a grupos  ➜", type="primary", use_container_width=True):
        st.session_state.seleccion = selection
        st.session_state.step = 3
        st.rerun()

# =============================================================================
# PÁGINA 3 — GRUPOS, PROFESORES Y DISPONIBILIDAD
# =============================================================================
elif st.session_state.step == 3:
    render_section_header(
        "👨‍🏫 Profesores y horarios disponibles",
        "Marca tus preferencias y conserva únicamente los horarios que deseas considerar.",
    )

    selected_subjects = list(st.session_state.seleccion)
    schedulable_subjects = [subject for subject in selected_subjects if subject != RESIDENCIA]

    if RESIDENCIA in selected_subjects:
        st.info("Residencia Profesional cuenta en tu carga y créditos, pero no ocupa bloques en el horario.")

    if get_spreadsheet() is None:
        st.warning("Las opiniones y reportes no pudieron conectarse en este momento.")

    with st.container(border=True):
        range_col, blocked_col = st.columns(2, gap="large")
        with range_col:
            time_range = st.slider("Horario en el Tec", 7, 22, (7, 22))
        with blocked_col:
            blocked = st.multiselect(
                "Horas que no deseas cursar",
                [f"{hour}:00-{hour+1}:00" for hour in range(7, 22)],
                placeholder="Selecciona las horas que deseas dejar libres",
            )

    st.caption("Preferencia: ✅ preferido · ➖ neutral · ❌ descartado. Todos comienzan en neutral.")

    filtered_offer = {}
    missing_subjects = []

    if not schedulable_subjects:
        st.success("Tu selección únicamente incluye Residencia Profesional. Puedes continuar al resumen.")

    for subject in schedulable_subjects:
        icon = ICONOS_MATERIAS.get(subject, "📘")
        groups = [
            group
            for group in st.session_state.oferta.get(subject, [])
            if group_fits(group, time_range, blocked)
        ]

        with st.container(border=True):
            st.markdown(
                f'<div class="subject-panel-title"><span>{icon}</span><span>{subject}</span></div>',
                unsafe_allow_html=True,
            )

            if not groups:
                st.warning("No hay horarios de esta materia dentro de la disponibilidad seleccionada.")
                missing_subjects.append(subject)
                filtered_offer[subject] = []
                continue

            groups_by_professor = defaultdict(list)
            for group in groups:
                groups_by_professor[group.get("profesor", "POR ASIGNAR")].append(group)

            enabled_groups = []
            professor_items = sorted(
                groups_by_professor.items(),
                key=lambda item: _normalize(display_professor_name(item[0])),
            )

            for row_start in range(0, len(professor_items), 3):
                row_items = professor_items[row_start:row_start + 3]
                columns = st.columns(3, gap="medium")

                for column, (professor, professor_groups) in zip(columns, row_items):
                    with column:
                        with st.container(border=True):
                            professor_token = f"{_normalize(subject)}_{_normalize(professor)}"
                            display_name = display_professor_name(professor)
                            ratings = ratings_for_professor(professor)

                            st.markdown(
                                f'<div class="professor-card-head"><div class="professor-card-name">{display_name}</div>'
                                f'<div class="professor-card-sub">{len(professor_groups)} horario(s) disponible(s)</div></div>',
                                unsafe_allow_html=True,
                            )

                            preference_key = f"preference_{professor_token}"
                            previous_key = f"previous_{preference_key}"
                            preference = st.radio(
                                "Preferencia del profesor",
                                options=["✅", "➖", "❌"],
                                index=1,
                                horizontal=True,
                                key=preference_key,
                                help="✅ Preferido · ➖ Neutral · ❌ Descartar",
                            )

                            option_data = []
                            for group_index, group in enumerate(professor_groups):
                                option_id = group_option_id(group)
                                option_key = f"option_{professor_token}_{group_index}_{option_id}"
                                option_data.append((group_index, group, option_id, option_key))

                            previous_preference = st.session_state.get(previous_key, "➖")
                            if preference == "❌":
                                for _, _, _, option_key in option_data:
                                    st.session_state[option_key] = False
                            elif previous_preference == "❌":
                                for _, _, _, option_key in option_data:
                                    st.session_state[option_key] = True
                            st.session_state[previous_key] = preference

                            st.markdown(rating_html(ratings), unsafe_allow_html=True)

                            option_labels = {}
                            for group_index, group, option_id, option_key in option_data:
                                schedule_text = compact_schedule(group.get("horario", []))
                                reports = report_count(group)
                                option_labels[option_id] = (schedule_text, group)

                                selected = st.checkbox(
                                    schedule_text,
                                    value=(preference != "❌"),
                                    key=option_key,
                                    disabled=(preference == "❌"),
                                )
                                if reports:
                                    st.markdown(
                                        f'<div class="group-warning">⚠ Reportado como lleno {reports} vez/veces. '
                                        'Aun así puedes seleccionarlo.</div>',
                                        unsafe_allow_html=True,
                                    )

                                if selected and preference != "❌":
                                    selected_group = dict(group)
                                    selected_group["_preference"] = 1 if preference == "✅" else 0
                                    enabled_groups.append(selected_group)

                            comments = [item for item in ratings if item["comentario"].strip()]
                            with st.expander(f"Comentarios ({len(comments)})"):
                                if comments:
                                    for item in comments[-10:]:
                                        date_text = f" — {item['fecha']}" if item.get("fecha") else ""
                                        st.write(f"• {item['comentario']}{date_text}")
                                else:
                                    st.caption("Este profesor todavía no tiene comentarios.")

                            with st.expander("Agregar opinión"):
                                with st.form(f"rating_form_{professor_token}"):
                                    score = st.slider(
                                        "Calificación (0 a 100)",
                                        0,
                                        100,
                                        80,
                                        step=5,
                                        key=f"score_{professor_token}",
                                    )
                                    comment = st.text_area(
                                        "Tu comentario",
                                        max_chars=300,
                                        key=f"comment_{professor_token}",
                                    )
                                    send_rating = st.form_submit_button("Publicar opinión", use_container_width=True)
                                if send_rating:
                                    if submit_rating(display_name, score, comment):
                                        st.success("Opinión registrada.")
                                        st.rerun()
                                    else:
                                        st.warning("No se pudo conectar con la hoja de opiniones.")

                            toggle_key = f"show_report_{professor_token}"
                            if st.button(
                                "Reportar horario lleno",
                                key=f"toggle_report_{professor_token}",
                                use_container_width=True,
                            ):
                                st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
                                st.rerun()

                            if st.session_state.get(toggle_key, False) and option_labels:
                                selected_option = st.radio(
                                    "Selecciona el horario reportado",
                                    options=list(option_labels),
                                    format_func=lambda value, labels=option_labels: labels[value][0],
                                    key=f"report_select_{professor_token}",
                                )
                                if st.button(
                                    "Confirmar reporte",
                                    key=f"confirm_report_{professor_token}",
                                    use_container_width=True,
                                ):
                                    group_to_report = option_labels[selected_option][1]
                                    if submit_full_report(subject, group_to_report):
                                        st.session_state[toggle_key] = False
                                        st.success("Reporte registrado; el horario seguirá disponible con advertencia.")
                                        st.rerun()
                                    else:
                                        st.warning("No se pudo conectar con la hoja de reportes.")

            filtered_offer[subject] = enabled_groups
            if not enabled_groups:
                missing_subjects.append(subject)

    st.divider()
    if missing_subjects:
        st.warning("Debes conservar al menos un horario para: " + ", ".join(sorted(set(missing_subjects))))

    back_col, next_col = st.columns(2)
    if back_col.button("← Regresar a materias", use_container_width=True):
        st.session_state.step = 2
        st.rerun()

    can_continue = not missing_subjects
    if next_col.button(
        "Generar horarios  ➜",
        type="primary",
        use_container_width=True,
        disabled=not can_continue,
    ):
        st.session_state.oferta_filtrada = filtered_offer
        st.session_state.materias_horario = schedulable_subjects
        st.session_state.step = 4
        st.rerun()

# =============================================================================
# PÁGINA 4 — RESULTADOS
# =============================================================================
elif st.session_state.step == 4:
    render_section_header(
        "🗓️ Horarios compatibles",
        "Primero se respetan tus profesores preferidos y después se minimiza el tiempo total dentro del Tec.",
    )

    with st.expander("Datos para descarga de PDF (opcional)", expanded=False):
        pdf_col_1, pdf_col_2, pdf_col_3 = st.columns(3)
        with pdf_col_1:
            student_name = st.text_input("Nombre", key="pdf_student_name")
        with pdf_col_2:
            student_id = st.text_input("Matrícula", key="pdf_student_id")
        with pdf_col_3:
            student_semester = st.text_input("Semestre", key="pdf_student_semester")

    student_data = {
        "nombre": student_name,
        "matricula": student_id,
        "semestre": student_semester,
    }

    subjects = st.session_state.get("materias_horario", [])
    filtered_offer = st.session_state.get("oferta_filtrada", {})
    results, message = generate_combinations(subjects, filtered_offer)

    back_col, _ = st.columns(2)
    if back_col.button("← Regresar a horarios", use_container_width=True):
        st.session_state.step = 3
        st.rerun()

    if not results:
        st.error(message)
    else:
        st.success(f"Se encontraron {len(results)} opciones compatibles.")

        for index, schedule in enumerate(results):
            option_number = index + 1
            with st.expander(f"Opción {option_number}", expanded=(index == 0)):
                st.markdown(create_timetable_html(schedule), unsafe_allow_html=True)
                pdf_data = create_schedule_pdf(schedule, option_number, student_data)
                st.download_button(
                    f"Descargar PDF · Opción {option_number}",
                    data=pdf_data,
                    file_name=f"Horario_ITS_Opcion_{option_number}.pdf",
                    mime="application/pdf",
                    key=f"download_pdf_{option_number}",
                    use_container_width=True,
                )

render_footer()
