import json
import os

import gspread
import pandas as pd
import streamlit as st
from fpdf import FPDF
from google.oauth2.service_account import Credentials

# =============================================================================
# 1. CONFIGURACIÓN E INTERFAZ
# =============================================================================
st.set_page_config(
    page_title="Horario ITS | Ago-Dic 2026",
    page_icon="🦅",
    layout="wide",
)

st.markdown(
    """
<style>
    :root {
        --guinda: #800000;
        --guinda-activo: #a90000;
        --fondo-oscuro: #0e1117;
    }

    h1, h2, h3 {
        color: var(--guinda) !important;
        font-family: Arial, sans-serif;
    }

    /* Cada checkbox ocupa exactamente el mismo alto. */
    [data-testid="stCheckbox"] {
        height: 122px !important;
        min-height: 122px !important;
        max-height: 122px !important;
        margin-bottom: 10px !important;
    }

    [data-testid="stCheckbox"] > label {
        width: 100% !important;
        height: 112px !important;
        min-height: 112px !important;
        max-height: 112px !important;
        box-sizing: border-box !important;
        border: 1px solid rgba(128, 128, 128, 0.45) !important;
        border-radius: 8px !important;
        padding: 8px 7px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        gap: 5px !important;
        overflow: hidden !important;
        transition: all 0.18s ease-in-out !important;
        cursor: pointer !important;
    }

    [data-testid="stCheckbox"] > label:hover {
        border-color: var(--guinda) !important;
        background-color: rgba(128, 0, 0, 0.15) !important;
        transform: translateY(-1px);
    }

    [data-testid="stCheckbox"]:has(input:checked) > label {
        background-color: var(--guinda-activo) !important;
        border-color: #ff4b4b !important;
    }

    [data-testid="stCheckbox"]:has(input:checked)
    div[data-testid="stMarkdownContainer"] p {
        color: white !important;
        font-weight: 800 !important;
    }

    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
    }

    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        font-size: 0.79rem !important;
        line-height: 1.25 !important;
        text-align: center !important;
        overflow-wrap: anywhere !important;
    }

    .stButton > button {
        color: white !important;
        background-color: var(--guinda) !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }

    .stButton > button:hover {
        background-color: var(--guinda-activo) !important;
    }

    .credit-box {
        padding: 14px;
        border-radius: 6px;
        text-align: center;
        font-weight: 800;
        margin-top: 10px;
    }

    .credit-ok {
        background-color: rgba(4, 95, 70, 0.30);
        color: #34d399;
        border: 1px solid #34d399;
    }

    .credit-error {
        background-color: rgba(153, 27, 27, 0.30);
        color: #f87171;
        border: 1px solid #f87171;
    }

    .semestre-header {
        color: var(--guinda) !important;
        font-weight: 900;
        font-size: 1em;
        text-align: center;
        border-bottom: 3px solid var(--guinda);
        margin-bottom: 10px;
    }

    .horario-grid {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        font-size: 0.8em;
        background-color: #ffffff;
        color: black;
        border-radius: 8px;
        overflow: hidden;
    }

    .horario-grid th {
        background-color: var(--guinda);
        color: white;
        padding: 8px;
        border: 1px solid #444;
    }

    .horario-grid td {
        border: 1px solid #ddd;
        height: 45px;
        vertical-align: middle;
        padding: 2px;
    }

    .hora-col {
        background-color: #e0e0e0;
        font-weight: bold;
        width: 70px;
    }

    .clase-cell {
        border-radius: 4px;
        padding: 4px;
        color: #111;
        font-weight: 700;
        font-size: 0.95em;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
</style>
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

if st.session_state.step == 1:
    st.markdown(
        "<h1 style='text-align:center;'>Horario ITS 🦅</h1>",
        unsafe_allow_html=True,
    )

    _, columna_central, _ = st.columns([1, 2, 1])
    with columna_central:
        with st.container(border=True):
            st.text_input(
                "📌 Periodo Académico",
                "AGOSTO - DICIEMBRE 2026",
                disabled=True,
            )
            carrera = st.selectbox(
                "🎓 Carrera",
                ["MECATRÓNICA", "INDUSTRIAL", "SISTEMAS"],
            )
            cantidad = st.number_input(
                "📚 Materias a cursar:",
                min_value=1,
                max_value=9,
                value=6,
            )

            if st.button(
                "Cargar Oferta ➡️",
                use_container_width=True,
                type="primary",
            ):
                carrera_clean = (
                    carrera.split(" ")[0]
                    .lower()
                    .replace("ó", "o")
                )

                try:
                    data = load_oferta_json("2026_AGO_DIC", carrera_clean)

                    if data is None:
                        st.error(
                            "❌ Falta el archivo "
                            f"/data/2026_AGO_DIC/{carrera_clean}.json"
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
                        st.session_state.step = 2
                        st.rerun()

                except ValueError as error:
                    st.error(f"❌ {error}")

elif st.session_state.step == 2:
    st.title("📚 Selección de Materias")

    if "seleccion" not in st.session_state:
        st.session_state.seleccion = []

    columnas = st.columns(9, gap="small")
    seleccion = []

    total_materias = sum(
        len(materias)
        for materias in st.session_state.mat_sem.values()
    )
    st.caption(f"Oferta cargada correctamente: {total_materias} materias.")

    for semestre in range(1, 10):
        with columnas[semestre - 1]:
            st.markdown(
                f"<div class='semestre-header'>{semestre}°</div>",
                unsafe_allow_html=True,
            )

            materias_semestre = st.session_state.mat_sem.get(semestre, [])

            if not materias_semestre:
                st.caption("Sin materias")

            for materia in materias_semestre:
                creditos_materia = st.session_state.creditos.get(materia, 0)
                icono = ICONOS_MATERIAS.get(materia, "📘")

                seleccionada = st.checkbox(
                    f"{icono} {materia} ({creditos_materia} Cr)",
                    value=(materia in st.session_state.seleccion),
                    key=f"materia_{semestre}_{materia}",
                    help=(
                        f"Semestre {semestre} · "
                        f"{creditos_materia} créditos"
                    ),
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
        f"Créditos: {creditos_totales}/{MAX_CREDITOS} | "
        f"Materias: {len(seleccion)}/{st.session_state.cant_deseada}"
        "</div>",
        unsafe_allow_html=True,
    )

    for error in errores:
        st.warning(f"⚠️ {error}")

    columna_volver, columna_siguiente = st.columns(2)

    if columna_volver.button("⬅️ Volver"):
        st.session_state.step = 1
        st.rerun()

    if not errores:
        if columna_siguiente.button("Siguiente ➡️", type="primary"):
            st.session_state.seleccion = seleccion
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    st.title("⏰ Disponibilidad y Resultados")

    columna_rango, columna_libres = st.columns(2)
    with columna_rango:
        rango = st.slider("Horario Global:", 7, 22, (7, 22))
    with columna_libres:
        libres = st.multiselect(
            "Bloquear horas:",
            [f"{hora}:00-{hora + 1}:00" for hora in range(7, 22)],
        )

    columna_atras, _ = st.columns(2)
    if columna_atras.button("⬅️ Atrás"):
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
        st.success(f"¡Se encontraron {len(resultados)} opciones!")
        for indice, horario in enumerate(resultados):
            with st.expander(
                f"Opción {indice + 1}",
                expanded=(indice == 0),
            ):
                st.markdown(
                    create_timetable_html(horario),
                    unsafe_allow_html=True,
                )
