import base64
import json
import mimetypes
import os
from pathlib import Path

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# =============================================================================
# 1. IDENTIDAD, CONFIGURACIÓN E INTERFAZ
# =============================================================================
APP_NAME = "Horario ITS"
APP_SUBTITLE = "Generador inteligente de horarios académicos"
AUTOR = "Luis Miguel Jiménez Espinoza"
PERIODO_CODIGO = "2026_AGO_DIC"
PERIODO_TEXTO = "AGOSTO - DICIEMBRE 2026"

# Catálogo centralizado. Solo Mecatrónica tiene oferta JSON por ahora.
# Cuando agregues otra carrera, basta con crear su JSON con el nombre indicado.
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
        --guinda-suave: rgba(166, 27, 54, 0.13);
        --oro: #c49a56;
        --fondo: #0e1117;
        --panel: #151922;
        --panel-2: #1c212c;
        --borde: rgba(225, 229, 238, 0.16);
        --texto: #f4f5f7;
        --texto-suave: #aeb4c0;
        --verde: #3ddc97;
        --rojo: #ff6b76;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 16% -10%, rgba(123, 16, 40, 0.22), transparent 32rem),
            radial-gradient(circle at 96% 2%, rgba(196, 154, 86, 0.07), transparent 24rem),
            var(--fondo);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1780px;
        padding-top: 1.1rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: var(--texto) !important;
        font-family: Arial, Helvetica, sans-serif;
        letter-spacing: -0.02em;
    }

    .brand-header {
        display: grid;
        grid-template-columns: minmax(130px, 0.8fr) minmax(420px, 2.4fr) minmax(130px, 0.8fr);
        gap: 26px;
        align-items: center;
        padding: 19px 24px;
        border: 1px solid var(--borde);
        border-top: 4px solid var(--guinda-600);
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(29, 33, 44, 0.97), rgba(17, 20, 28, 0.98));
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.23);
        margin-bottom: 12px;
    }

    .institution-logo {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 78px;
    }

    .institution-logo img {
        width: 100%;
        max-width: 176px;
        max-height: 82px;
        object-fit: contain;
        filter: drop-shadow(0 5px 12px rgba(0, 0, 0, 0.24));
    }

    .institution-fallback {
        width: 100%;
        min-height: 72px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px dashed rgba(255, 255, 255, 0.24);
        border-radius: 13px;
        color: var(--texto-suave);
        font-size: 0.78rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: 0.08em;
    }

    .project-logo {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .project-logo img {
        width: min(100%, 670px);
        max-height: 126px;
        object-fit: contain;
    }

    .progress-track {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin: 0 0 24px 0;
    }

    .progress-step {
        min-height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 9px 14px;
        border-radius: 12px;
        border: 1px solid var(--borde);
        background: rgba(22, 26, 35, 0.92);
        color: var(--texto-suave);
        font-size: 0.82rem;
        font-weight: 800;
        text-align: center;
    }

    .progress-step.done {
        color: #ffdce4;
        border-color: rgba(166, 27, 54, 0.55);
        background: rgba(123, 16, 40, 0.26);
    }

    .progress-step.active {
        color: white;
        border-color: var(--guinda-500);
        background: linear-gradient(135deg, var(--guinda-700), var(--guinda-500));
        box-shadow: 0 8px 20px rgba(123, 16, 40, 0.27);
    }

    .hero-panel {
        padding: 30px 32px;
        border: 1px solid var(--borde);
        border-radius: 22px;
        background:
            linear-gradient(115deg, rgba(123, 16, 40, 0.22), rgba(21, 25, 34, 0.95) 48%),
            var(--panel);
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
        margin-bottom: 18px;
    }

    .hero-kicker {
        color: #e6b7c3;
        font-size: 0.75rem;
        font-weight: 900;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero-title {
        color: white;
        font-size: clamp(1.9rem, 3.4vw, 3.35rem);
        line-height: 1.03;
        font-weight: 950;
        letter-spacing: -0.045em;
        margin-bottom: 12px;
    }

    .hero-copy {
        color: #d0d4dc;
        max-width: 880px;
        font-size: 1rem;
        line-height: 1.65;
        margin: 0;
    }

    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 9px;
        margin-top: 19px;
    }

    .meta-chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 8px 12px;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 999px;
        background: rgba(5, 7, 11, 0.22);
        color: #edf0f4;
        font-size: 0.78rem;
        font-weight: 750;
    }

    .section-head {
        padding: 20px 24px;
        border-left: 5px solid var(--guinda-500);
        border-radius: 0 16px 16px 0;
        background: linear-gradient(90deg, rgba(123, 16, 40, 0.22), rgba(21, 25, 34, 0.8));
        margin-bottom: 18px;
    }

    .section-head h1 {
        margin: 0 0 5px 0;
        font-size: clamp(1.55rem, 2.3vw, 2.35rem);
    }

    .section-head p {
        margin: 0;
        color: var(--texto-suave);
        line-height: 1.55;
    }

    .form-note {
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(166, 27, 54, 0.10);
        border: 1px solid rgba(166, 27, 54, 0.30);
        color: #e1c4cb;
        font-size: 0.83rem;
        margin-top: 10px;
    }

    [data-testid="stForm"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--borde) !important;
        border-radius: 18px !important;
        background: rgba(20, 24, 33, 0.72) !important;
    }

    /* Tarjetas de materias: indicador y tooltip ocultos para ganar ancho. */
    [data-testid="stCheckbox"] {
        height: 132px !important;
        min-height: 132px !important;
        max-height: 132px !important;
        margin-bottom: 10px !important;
    }

    [data-testid="stCheckbox"] [role="checkbox"] {
        display: none !important;
    }

    [data-testid="stCheckbox"] > label {
        width: 100% !important;
        height: 124px !important;
        min-height: 124px !important;
        max-height: 124px !important;
        box-sizing: border-box !important;
        border: 1px solid rgba(180, 186, 198, 0.28) !important;
        border-radius: 14px !important;
        padding: 10px 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        overflow: hidden !important;
        transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease !important;
        cursor: pointer !important;
        background: linear-gradient(145deg, rgba(27, 32, 43, 0.98), rgba(16, 19, 27, 0.98));
    }

    [data-testid="stCheckbox"] > label:hover {
        border-color: var(--guinda-500) !important;
        background: linear-gradient(145deg, rgba(83, 15, 33, 0.72), rgba(24, 27, 37, 0.98)) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.18);
    }

    [data-testid="stCheckbox"]:has(input:checked) > label {
        background: linear-gradient(145deg, var(--guinda-700), var(--guinda-500)) !important;
        border-color: #d74b68 !important;
        box-shadow: 0 10px 25px rgba(123, 16, 40, 0.32);
    }

    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p {
        width: 100% !important;
        margin: 0 !important;
        color: #f5f6f8 !important;
        font-size: clamp(0.67rem, 0.73vw, 0.82rem) !important;
        line-height: 1.22 !important;
        font-weight: 760 !important;
        text-align: center !important;
        white-space: normal !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        hyphens: none !important;
        text-wrap: balance;
    }

    [data-testid="stCheckbox"]:has(input:checked)
    div[data-testid="stMarkdownContainer"] p {
        color: white !important;
        font-weight: 900 !important;
    }

    .semester-header {
        min-height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #f7dce3;
        font-weight: 950;
        font-size: 0.92rem;
        text-align: center;
        border: 1px solid rgba(166, 27, 54, 0.45);
        border-bottom: 3px solid var(--guinda-500);
        border-radius: 10px 10px 4px 4px;
        background: rgba(123, 16, 40, 0.18);
        margin-bottom: 10px;
    }

    .credit-box {
        padding: 15px;
        border-radius: 13px;
        text-align: center;
        font-weight: 900;
        margin-top: 10px;
        letter-spacing: 0.01em;
    }

    .credit-ok {
        background: rgba(4, 95, 70, 0.30);
        color: var(--verde);
        border: 1px solid var(--verde);
    }

    .credit-error {
        background: rgba(153, 27, 27, 0.27);
        color: #ff8c95;
        border: 1px solid #ff6b76;
    }

    .selection-note {
        color: var(--texto-suave);
        font-size: 0.82rem;
        margin: 4px 0 14px 0;
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        min-height: 47px;
        color: white !important;
        background: linear-gradient(135deg, var(--guinda-700), var(--guinda-500)) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        font-weight: 850 !important;
        border-radius: 11px !important;
        box-shadow: 0 9px 20px rgba(92, 8, 28, 0.21);
    }

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, var(--guinda-600), #bf2444) !important;
        border-color: rgba(255, 255, 255, 0.20) !important;
        transform: translateY(-1px);
    }

    .horario-grid {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        text-align: center;
        font-size: 0.8em;
        background: #ffffff;
        color: #151820;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
    }

    .horario-grid th {
        background: var(--guinda-700);
        color: white;
        padding: 9px;
        border: 1px solid #5d0c20;
    }

    .horario-grid td {
        border: 1px solid #e0e3e9;
        height: 47px;
        vertical-align: middle;
        padding: 2px;
    }

    .hora-col {
        background: #e8eaf0;
        font-weight: 900;
        width: 72px;
    }

    .clase-cell {
        border-radius: 6px;
        padding: 5px;
        color: #111;
        font-weight: 800;
        font-size: 0.92em;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .footer-note {
        text-align: center;
        color: #7f8794;
        font-size: 0.76rem;
        padding-top: 26px;
    }

    @media (max-width: 1180px) {
        [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p {
            font-size: 0.63rem !important;
        }
        .brand-header {
            grid-template-columns: 120px 1fr 120px;
        }
    }

    @media (max-width: 760px) {
        .brand-header {
            grid-template-columns: 1fr;
            gap: 12px;
        }
        .institution-logo {
            display: none;
        }
        .project-logo img {
            max-height: 96px;
        }
        .progress-step {
            font-size: 0.68rem;
            padding: 7px 4px;
        }
        .hero-panel {
            padding: 24px 20px;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


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
    tecnm_path = _first_existing_path(
        "assets/logo_tecnm.png",
        "assets/logo_tec.png",
        "logo_tec.png",
    )
    its_path = _first_existing_path(
        "assets/logo_its.png",
        "logo_its.png",
    )
    project_path = _first_existing_path(
        "assets/horario_its_logo.svg",
        "horario_its_logo.svg",
    )

    project_uri = _data_uri(project_path)
    if project_uri:
        project_html = f'<img src="{project_uri}" alt="{APP_NAME}">'
    else:
        project_html = (
            '<div style="text-align:center">'
            '<div style="font-size:2.15rem;font-weight:950;color:#fff">'
            'HORARIO ITS 🫏</div>'
            '<div style="color:#b9bec8;font-size:.82rem">'
            'GENERADOR INTELIGENTE DE HORARIOS</div></div>'
        )

    st.markdown(
        f"""
        <div class="brand-header">
            <div class="institution-logo">
                {_logo_html(tecnm_path, "TECNM")}
            </div>
            <div class="project-logo">{project_html}</div>
            <div class="institution-logo">
                {_logo_html(its_path, "ITS")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels = (
        (1, "Inicio", "Configura tu carga"),
        (2, "Materias", "Elige tu retícula"),
        (3, "Horarios", "Genera opciones"),
    )
    items = []
    for step_number, title, subtitle in labels:
        if step_number < current_step:
            css_class = "done"
            icon = "✓"
        elif step_number == current_step:
            css_class = "active"
            icon = str(step_number)
        else:
            css_class = ""
            icon = str(step_number)
        items.append(
            f'<div class="progress-step {css_class}">'
            f'<strong>{icon}. {title}</strong><span>· {subtitle}</span></div>'
        )

    st.markdown(
        '<div class="progress-track">' + ''.join(items) + '</div>',
        unsafe_allow_html=True,
    )


def render_section_header(title, description):
    st.markdown(
        f"""
        <div class="section-head">
            <h1>{title}</h1>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        f"""
        <div class="footer-note">
            {APP_NAME} · Desarrollado por {AUTOR}. Proyecto académico independiente;
            verifica tu carga final en los canales oficiales del ITS.
        </div>
        """,
        unsafe_allow_html=True,
    )

COLORS = [
    "#FFCDD2", "#F8BBD0", "#E1BEE7", "#D1C4E9",
    "#C5CAE9", "#BBDEFB", "#B3E5FC", "#B2EBF2",
    "#B2DFDB", "#C8E6C9", "#DCEDC8", "#F0F4C3",
]

MAX_CREDITOS = 36
RESIDENCIA = "Residencia Profesional"
MAX_MATERIAS_ADICIONALES_RESIDENCIA = 2

# Iconos ligeros: no requieren archivos PNG ni vuelven lenta la aplicación.
ICONOS_MATERIAS = {
    "Química": "⚗️",
    "Cálculo Diferencial": "➗",
    "Taller De Ética": "⚖️",
    "Dibujo Asistido Por Computadora": "🖥️",
    "Metrología Y Normalización": "📏",
    "Fundamentos De Investigación": "🔎",
    "Estadística Y Control De Calidad": "📊",
    "Álgebra Lineal": "🔢",
    "Cálculo Integral": "∫",
    "Ciencia E Ingeniería De Materiales": "🧱",
    "Programación Básica": "💻",
    "Administración Y Contabilidad": "🧾",
    "Desarrollo Sustentable": "🌱",
    "Métodos Numéricos": "🧮",
    "Electromagnetismo": "🧲",
    "Procesos De Fabricación": "🏭",
    "Cálculo Vectorial": "🧭",
    "Estática": "🏗️",
    "Mecánica De Materiales": "🔩",
    "Dinámica": "🏎️",
    "Ecuaciones Diferenciales": "📈",
    "Taller De Investigación I": "📝",
    "Análisis De Circuitos Eléctricos": "🔌",
    "Fundamentos De Termodinámica": "🌡️",
    "Mecanismos": "⚙️",
    "Programación Avanzada": "🧑‍💻",
    "Taller De Investigación II": "📚",
    "Máquinas Eléctricas": "⚡",
    "Análisis De Fluidos": "💧",
    "Electrónica Analógica": "〰️",
    "Electrónica De Potencia Aplicada": "🔋",
    "Instrumentación": "🎛️",
    "Diseño De Elementos Mecánicos": "🛠️",
    "Electrónica Digital": "0️⃣",
    "Vibraciones Mecánicas": "📳",
    "Administración del Mantenimiento": "📋",
    "Dinámica De Sistemas": "🔄",
    "Manufactura Avanzada": "🏭",
    "Circuitos Hidráulicos Y Neumáticos": "💨",
    "Mantenimiento": "🔧",
    "Microcontroladores": "🧠",
    "Diseño Asistido por Computadora": "✏️",
    "Control": "🎚️",
    "Formulación Y Evaluación De Proyectos": "📑",
    "Controladores Lógicos Programables": "🧩",
    "Sistemas Avanzados De Manufactura": "🦾",
    "Redes Industriales": "🌐",
    "Tópicos Selectos de Automatización Industrial": "🤖",
    "Robótica": "🤖",
    "Residencia Profesional": "🎓",
}

# Relaciones visibles en la retícula. Si A es antecedente de B, no se permite
# escoger A y B en el mismo periodo. También se calcula la relación transitiva:
# por ejemplo, Diferencial e Integral, pero también Diferencial y Vectorial.
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
# 2. CONEXIÓN A GOOGLE SHEETS
# =============================================================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_db_connection():
    if "gcp_service_account" not in st.secrets:
        return None

    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace(
                "\\n", "\n"
            )
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=SCOPES,
        )
        return gspread.authorize(creds)
    except Exception:
        return None


db_client = get_db_connection()

# =============================================================================
# 3. CARGA Y NORMALIZACIÓN DE LA OFERTA
# =============================================================================
@st.cache_data
def _read_json(filepath, modified_ns):
    """Renueva la caché cuando cambia la fecha de modificación del JSON."""
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
            f"JSON inválido en {filepath}: línea {error.lineno}, "
            f"columna {error.colno}. {error.msg}"
        ) from error


def format_json_to_oferta(json_data):
    """Convierte el JSON al formato interno usado por el generador."""
    if not isinstance(json_data, dict):
        raise ValueError("La raíz del JSON debe ser un objeto.")

    materias = json_data.get("materias", json_data)

    if not isinstance(materias, dict) or not materias:
        raise ValueError("No se encontraron materias dentro del JSON.")

    oferta = {}
    mat_sem = {semestre: [] for semestre in range(1, 10)}
    creditos = {}

    for clave, info in materias.items():
        if not isinstance(info, dict):
            raise ValueError(f"La materia {clave} no tiene estructura válida.")

        nombre = str(info.get("nombre", "")).strip()
        if not nombre:
            raise ValueError(f"La materia {clave} no tiene nombre.")

        try:
            semestre = int(info.get("semestre"))
            creditos_materia = int(info.get("creditos", 0))
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"La materia {clave} tiene semestre o créditos inválidos."
            ) from error

        if semestre not in range(1, 10):
            raise ValueError(
                f"La materia {nombre} tiene semestre {semestre}; debe ser 1 a 9."
            )

        if nombre in oferta:
            raise ValueError(f"Nombre de materia duplicado: {nombre}")

        mat_sem[semestre].append(nombre)
        creditos[nombre] = creditos_materia
        oferta[nombre] = []

        for grupo in info.get("grupos", []):
            horario = [
                (
                    int(sesion["dia"]),
                    int(sesion["inicio"]),
                    int(sesion["fin"]),
                )
                for sesion in grupo.get("horario", [])
            ]

            oferta[nombre].append(
                {
                    "profesor": grupo.get("profesor", "POR ASIGNAR"),
                    "salon": grupo.get("salon", "POR ASIGNAR"),
                    "horario": horario,
                    "id": grupo.get("id", ""),
                    "materia": nombre,
                }
            )

    for semestre in mat_sem:
        mat_sem[semestre].sort()

    return oferta, mat_sem, creditos

# =============================================================================
# 4. REGLAS DE SELECCIÓN
# =============================================================================
def construir_grafo_seriadas():
    grafo = {}
    for antecedente, consecuente in SERIADAS_DIRECTAS:
        grafo.setdefault(antecedente, set()).add(consecuente)
    return grafo


GRAFO_SERIADAS = construir_grafo_seriadas()


def materias_posteriores(materia):
    """Obtiene todas las materias posteriores por cierre transitivo."""
    visitadas = set()
    pendientes = list(GRAFO_SERIADAS.get(materia, set()))

    while pendientes:
        actual = pendientes.pop()
        if actual in visitadas:
            continue
        visitadas.add(actual)
        pendientes.extend(GRAFO_SERIADAS.get(actual, set()))

    return visitadas


def detectar_conflictos_seriados(seleccion):
    seleccionadas = set(seleccion)
    conflictos = []

    for antecedente in sorted(seleccionadas):
        for consecuente in sorted(materias_posteriores(antecedente)):
            if consecuente in seleccionadas:
                conflictos.append((antecedente, consecuente))

    return conflictos


def validar_seleccion(seleccion, cantidad_deseada, creditos_por_materia):
    errores = []
    total_creditos = sum(
        creditos_por_materia.get(materia, 0)
        for materia in seleccion
    )

    if len(seleccion) != cantidad_deseada:
        errores.append(
            f"Debes seleccionar exactamente {cantidad_deseada} materias; "
            f"actualmente seleccionaste {len(seleccion)}."
        )

    if total_creditos > MAX_CREDITOS:
        errores.append(
            f"La carga suma {total_creditos} créditos y el máximo permitido "
            f"es {MAX_CREDITOS}."
        )

    conflictos = detectar_conflictos_seriados(seleccion)
    for antecedente, consecuente in conflictos:
        errores.append(
            f"No puedes cursar simultáneamente {antecedente} y {consecuente}; "
            "son materias seriadas en la retícula."
        )

    if RESIDENCIA in seleccion:
        materias_adicionales = len(seleccion) - 1
        if materias_adicionales > MAX_MATERIAS_ADICIONALES_RESIDENCIA:
            errores.append(
                "Residencia Profesional puede acompañarse de máximo "
                f"{MAX_MATERIAS_ADICIONALES_RESIDENCIA} materias adicionales."
            )

    return errores, total_creditos

# =============================================================================
# 5. MOTOR DE COMBINACIONES
# =============================================================================
def traslape(horario_1, horario_2):
    for sesion_1 in horario_1:
        for sesion_2 in horario_2:
            mismo_dia = sesion_1[0] == sesion_2[0]
            se_cruzan = max(sesion_1[1], sesion_2[1]) < min(
                sesion_1[2], sesion_2[2]
            )
            if mismo_dia and se_cruzan:
                return True
    return False


def generar_combinaciones(materias, rango, hrs_libres, oferta):
    bloqueos = [int(hora.split(":")[0]) for hora in hrs_libres]
    pools = []

    # Primero procesa las materias con menos grupos para podar antes el árbol.
    materias_ordenadas = sorted(
        materias,
        key=lambda materia: len(oferta.get(materia, [])),
    )

    for materia in materias_ordenadas:
        if materia not in oferta:
            return [], f"❌ No se encontró {materia} en la oferta."

        opciones = []
        for seccion in oferta[materia]:
            dentro = True

            for sesion in seccion["horario"]:
                if sesion[1] < rango[0] or sesion[2] > rango[1]:
                    dentro = False
                    break

                if any(
                    hora_bloqueada in range(sesion[1], sesion[2])
                    for hora_bloqueada in bloqueos
                ):
                    dentro = False
                    break

            if dentro:
                opciones.append(seccion)

        if not opciones:
            return [], f"❌ {materia} no cuadra con tus bloqueos de tiempo."

        pools.append(opciones)

    validos = []

    def backtrack(indice, combinacion):
        if len(validos) >= 15:
            return

        if indice == len(pools):
            validos.append(list(combinacion))
            return

        for seccion in pools[indice]:
            if not any(
                traslape(seccion["horario"], previa["horario"])
                for previa in combinacion
            ):
                combinacion.append(seccion)
                backtrack(indice + 1, combinacion)
                combinacion.pop()

    backtrack(0, [])
    return validos, "OK"

# =============================================================================
# 6. GENERACIÓN DEL HORARIO HTML
# =============================================================================
def create_timetable_html(horario):
    if not horario:
        return ""

    horas = [
        hora
        for clase in horario
        for sesion in clase["horario"]
        for hora in (sesion[1], sesion[2])
    ]

    if not horas:
        return ""

    min_hora, max_hora = min(horas), max(horas)
    tiene_sabado = any(
        sesion[0] == 5
        for clase in horario
        for sesion in clase["horario"]
    )
    cantidad_dias = 6 if tiene_sabado else 5
    grid = {
        hora: [None] * cantidad_dias
        for hora in range(min_hora, max_hora)
    }

    colores = {
        clase["materia"]: COLORS[indice % len(COLORS)]
        for indice, clase in enumerate(horario)
    }

    for clase in horario:
        for sesion in clase["horario"]:
            for hora in range(sesion[1], sesion[2]):
                if sesion[0] < cantidad_dias:
                    grid[hora][sesion[0]] = (
                        "<div class='clase-cell' "
                        f"style='background-color:{colores[clase['materia']]}' >"
                        f"<span>{clase['materia']}</span><br>"
                        f"<small>{clase['profesor']}</small>"
                        "</div>"
                    )

    encabezados = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"][:cantidad_dias]
    html = (
        "<table class='horario-grid'><thead><tr>"
        "<th class='hora-col'>Hora</th>"
        + "".join(f"<th>{dia}</th>" for dia in encabezados)
        + "</tr></thead><tbody>"
    )

    for hora in range(min_hora, max_hora):
        html += (
            f"<tr><td class='hora-col'>{hora}-{hora + 1}</td>"
            + "".join(
                f"<td>{grid[hora][dia] or ''}</td>"
                for dia in range(cantidad_dias)
            )
            + "</tr>"
        )

    return html + "</tbody></table>"

# =============================================================================
# 7. FLUJO DE NAVEGACIÓN
# =============================================================================
if "step" not in st.session_state:
    st.session_state.step = 1

render_brand_header(st.session_state.step)

if st.session_state.step == 1:
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-kicker">Planeación académica · Ago-Dic 2026</div>
            <div class="hero-title">Arma tu horario sin choques y con reglas de carga claras.</div>
            <p class="hero-copy">
                Selecciona tu carrera y el número de materias que deseas cursar. Después podrás
                elegir asignaturas de los nueve semestres, validar créditos y seriaciones, definir
                tus horas no disponibles y comparar combinaciones de grupos compatibles.
            </p>
            <div class="hero-meta">
                <span class="meta-chip">🧠 Motor de combinaciones</span>
                <span class="meta-chip">🧩 Validación de seriaciones</span>
                <span class="meta-chip">🎓 Máximo 36 créditos</span>
                <span class="meta-chip">👤 Autor: {AUTOR}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    columna_info, columna_formulario = st.columns([1.05, 1.25], gap="large")

    with columna_info:
        render_section_header(
            "Bienvenido a Horario ITS",
            "Una herramienta para explorar cargas académicas antes de realizar tu inscripción oficial.",
        )
        st.markdown(
            """
            **¿Qué hace la página?**

            1. Carga la oferta académica publicada para el periodo.
            2. Organiza las materias por semestre y controla el total de créditos.
            3. Evita combinaciones de materias seriadas en el mismo periodo.
            4. Genera alternativas de horario sin traslapes entre grupos.

            **Importante:** esta herramienta sirve para planeación. La disponibilidad real,
            prerrequisitos y autorización final dependen del Instituto Tecnológico de Saltillo.
            """
        )

    with columna_formulario:
        render_section_header(
            "Configura tu búsqueda",
            "El periodo es fijo. Las carreras sin archivo JSON aparecerán como próximas a integrarse.",
        )

        with st.form("configuracion_inicial", border=True):
            st.text_input(
                "📌 Periodo académico",
                PERIODO_TEXTO,
                disabled=True,
            )

            opciones_carrera = list(CARRERAS.keys())

            def formato_carrera(nombre):
                slug = CARRERAS[nombre]
                disponible = os.path.exists(
                    f"data/{PERIODO_CODIGO}/{slug}.json"
                )
                estado = "Disponible" if disponible else "Próximamente"
                simbolo = "●" if disponible else "○"
                return f"{nombre}  {simbolo} {estado}"

            carrera = st.selectbox(
                "🎓 Carrera",
                opciones_carrera,
                index=0,
                format_func=formato_carrera,
            )

            cantidad = st.number_input(
                "📚 Materias a cursar",
                min_value=1,
                max_value=9,
                value=6,
                step=1,
            )

            st.markdown(
                "<div class='form-note'>La selección deberá coincidir exactamente "
                "con esta cantidad y no podrá superar 36 créditos.</div>",
                unsafe_allow_html=True,
            )

            enviar = st.form_submit_button(
                "Cargar oferta  ➜",
                use_container_width=True,
                type="primary",
            )

        if enviar:
            carrera_clean = CARRERAS[carrera]

            try:
                data = load_oferta_json(PERIODO_CODIGO, carrera_clean)

                if data is None:
                    st.info(
                        "Esta carrera ya está incluida en el catálogo, pero su oferta "
                        f"{PERIODO_TEXTO} todavía no se ha cargado. "
                        f"Agrega `data/{PERIODO_CODIGO}/{carrera_clean}.json` para habilitarla."
                    )
                else:
                    (
                        st.session_state.oferta,
                        st.session_state.mat_sem,
                        st.session_state.creditos,
                    ) = format_json_to_oferta(data)

                    st.session_state.seleccion = []

                    for key in list(st.session_state.keys()):
                        if key.startswith("materia_"):
                            del st.session_state[key]

                    st.session_state.cant_deseada = int(cantidad)
                    st.session_state.carrera = carrera_clean
                    st.session_state.carrera_nombre = carrera
                    st.session_state.step = 2
                    st.rerun()

            except ValueError as error:
                st.error(f"❌ {error}")

elif st.session_state.step == 2:
    render_section_header(
        "📚 Selección de materias",
        "Elige exactamente la cantidad indicada. El sistema valida créditos, seriaciones y reglas especiales antes de permitirte continuar.",
    )

    if "seleccion" not in st.session_state:
        st.session_state.seleccion = []

    total_materias = sum(
        len(materias)
        for materias in st.session_state.mat_sem.values()
    )
    carrera_nombre = st.session_state.get("carrera_nombre", "MECATRÓNICA")
    st.markdown(
        f"<div class='selection-note'>"
        f"{carrera_nombre} · {total_materias} materias disponibles · "
        f"selecciona {st.session_state.cant_deseada}."
        f"</div>",
        unsafe_allow_html=True,
    )

    columnas = st.columns(9, gap="small")
    seleccion = []

    for semestre in range(1, 10):
        with columnas[semestre - 1]:
            st.markdown(
                f"<div class='semester-header'>{semestre}° semestre</div>",
                unsafe_allow_html=True,
            )

            materias_semestre = st.session_state.mat_sem.get(semestre, [])

            if not materias_semestre:
                st.caption("Sin materias")

            for materia in materias_semestre:
                creditos_materia = st.session_state.creditos.get(materia, 0)
                icono = ICONOS_MATERIAS.get(materia, "📘")
                etiqueta = (
                    f"{icono}  \n"
                    f"**{materia}**  \n"
                    f"{creditos_materia} Cr"
                )

                seleccionada = st.checkbox(
                    etiqueta,
                    value=(materia in st.session_state.seleccion),
                    key=f"materia_{semestre}_{materia}",
                )

                if seleccionada:
                    seleccion.append(materia)

    errores, creditos_totales = validar_seleccion(
        seleccion,
        st.session_state.cant_deseada,
        st.session_state.creditos,
    )

    st.divider()

    clase_estado = "credit-ok" if not errores else "credit-error"
    st.markdown(
        f"<div class='credit-box {clase_estado}'>"
        f"Créditos: {creditos_totales}/{MAX_CREDITOS} &nbsp;·&nbsp; "
        f"Materias: {len(seleccion)}/{st.session_state.cant_deseada}"
        "</div>",
        unsafe_allow_html=True,
    )

    for error in errores:
        st.warning(f"⚠️ {error}")

    columna_volver, columna_siguiente = st.columns(2)

    if columna_volver.button("← Volver", use_container_width=True):
        st.session_state.step = 1
        st.rerun()

    if not errores:
        if columna_siguiente.button(
            "Continuar a disponibilidad  ➜",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.seleccion = seleccion
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    render_section_header(
        "⏰ Disponibilidad y resultados",
        "Define tu rango permitido y bloquea las horas en las que no puedes asistir. El motor buscará grupos sin traslapes.",
    )

    materias_resumen = " · ".join(st.session_state.seleccion)
    st.caption(f"Materias seleccionadas: {materias_resumen}")

    with st.container(border=True):
        columna_rango, columna_libres = st.columns(2, gap="large")
        with columna_rango:
            rango = st.slider("Horario global", 7, 22, (7, 22))
        with columna_libres:
            libres = st.multiselect(
                "Bloquear horas",
                [f"{hora}:00-{hora + 1}:00" for hora in range(7, 22)],
                placeholder="Selecciona las horas que deseas dejar libres",
            )

    columna_atras, _ = st.columns(2)
    if columna_atras.button(
        "← Regresar a materias",
        use_container_width=True,
    ):
        st.session_state.step = 2
        st.rerun()

    resultados, mensaje = generar_combinaciones(
        st.session_state.seleccion,
        rango,
        libres,
        st.session_state.oferta,
    )

    if not resultados:
        st.error(mensaje)
    else:
        st.success(f"Se encontraron {len(resultados)} opciones compatibles.")
        for indice, horario in enumerate(resultados):
            with st.expander(
                f"Opción {indice + 1}",
                expanded=(indice == 0),
            ):
                st.markdown(
                    create_timetable_html(horario),
                    unsafe_allow_html=True,
                )

render_footer()
