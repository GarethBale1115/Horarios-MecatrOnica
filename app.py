import streamlit as st
import pandas as pd
import itertools
from fpdf import FPDF
import os
import re

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN VISUAL
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Horario ITS", page_icon="🐴", layout="wide")

st.markdown("""
<style>
    :root { --guinda: #800000; --fondo-oscuro: #0e1117; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--guinda) !important; font-family: 'Arial', sans-serif; }
    
    /* TARJETAS SIN PALOMITA */
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

    /* ENCABEZADOS */
    .semestre-header { color: var(--guinda) !important; font-weight: 900; font-size: 1em; text-align: center; border-bottom: 3px solid var(--guinda); margin-bottom: 10px; text-transform: uppercase; }
    
    /* CREDIT BOXES */
    .credit-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 10px; }
    .credit-ok { background-color: rgba(4, 95, 70, 0.3); color: #34d399; border: 1px solid #34d399; }
    .credit-error { background-color: rgba(153, 27, 27, 0.3); color: #f87171; border: 1px solid #f87171; }

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

    /* RESTAURAR PALOMITA EN EXPANDERS */
    [data-testid="stExpander"] [data-testid="stCheckbox"] label span[role="checkbox"] { display: block !important; }
    [data-testid="stExpander"] [data-testid="stCheckbox"] label { min-height: 30px !important; border: none !important; justify-content: flex-start !important; text-align: left !important; }
    [data-testid="stExpander"] [data-testid="stCheckbox"]:has(input:checked) label { background-color: transparent !important; }
    [data-testid="stExpander"] [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p { color: inherit !important; font-weight: normal !important; text-align: left !important; }
    
    /* COMENTARIOS */
    .comment-bubble { background-color: rgba(128, 128, 128, 0.1); padding: 8px; border-radius: 5px; margin-bottom: 5px; font-size: 0.9em; border-left: 3px solid var(--guinda); }
</style>
""", unsafe_allow_html=True)

COLORS = ['#FFCDD2', '#F8BBD0', '#E1BEE7', '#D1C4E9', '#C5CAE9', '#BBDEFB', '#B3E5FC', '#B2EBF2', '#B2DFDB', '#C8E6C9', '#DCEDC8', '#F0F4C3', '#FFF9C4', '#FFECB3', '#FFE0B2', '#FFCCBC']

# -----------------------------------------------------------------------------
# 2. INICIALIZAR ESTADO
# -----------------------------------------------------------------------------
if 'step' not in st.session_state: st.session_state.step = 1
if 'num_materias_deseadas' not in st.session_state: st.session_state.num_materias_deseadas = 6
if 'materias_seleccionadas' not in st.session_state: st.session_state.materias_seleccionadas = []
if 'rango_hora' not in st.session_state: st.session_state.rango_hora = (7, 22)
if 'horas_libres' not in st.session_state: st.session_state.horas_libres = []
if 'prefs' not in st.session_state: st.session_state.prefs = {}
if 'resultados' not in st.session_state: st.session_state.resultados = None
if 'opiniones' not in st.session_state: st.session_state.opiniones = {"Ana Gabriela Gomez Muñoz": {"suma": 450, "votos": 5, "comentarios": ["Excelente maestra", "Estricta"]}, "Gerardo Jarquín Hernández": {"suma": 98, "votos": 1, "comentarios": ["El mejor para Robótica"]}}

# Variables del alumno
if 'alumno_nombre' not in st.session_state: st.session_state.alumno_nombre = ""
if 'alumno_nc' not in st.session_state: st.session_state.alumno_nc = ""
if 'alumno_sem' not in st.session_state: st.session_state.alumno_sem = 1
if 'alumno_per' not in st.session_state: st.session_state.alumno_per = "ENE-JUN 2026"

# -----------------------------------------------------------------------------
# 3. DATOS SINCRONIZADOS (TODO CON EMOJIS - CERO FALLAS)
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

SERIACION = {
    "∫ Cálculo Integral": ["📐 Cálculo Diferencial"], "🧱 Ciencia e Ingeniería de Materiales": ["🧪 Química"], "↗️ Cálculo Vectorial": ["∫ Cálculo Integral"],
    "🔨 Procesos de Fabricación": ["🧱 Ciencia e Ingeniería de Materiales"], "💻 Programación Avanzada": ["💾 Programación Básica"], "🏎️ Dinámica": ["↗️ Cálculo Vectorial"],
    "📉 Ecuaciones Diferenciales": ["↗️ Cálculo Vectorial"], "🏭 Manufactura Avanzada": ["🔨 Procesos de Fabricación"], "🔌 Análisis de Circuitos Eléctricos": ["⚡ Electromagnetismo"],
    "🦾 Mecánica de Materiales": ["🏗️ Estática"], "📑 Taller de Investigación II": ["📝 Taller de Investigación I"], "🔗 Mecanismos": ["🏎️ Dinámica"],
    "📟 Electrónica Analógica": ["🔌 Análisis de Circuitos Eléctricos"], "🔩 Diseño de Elementos Mecánicos": ["🦾 Mecánica de Materiales"], "⚡ Electrónica de Potencia Aplicada": ["⚙️ Máquinas Eléctricas"],
    "〰️ Vibraciones Mecánicas": ["🔗 Mecanismos"], "👾 Electrónica Digital": ["📟 Electrónica Analógica"], "🎛️ Controladores Lógicos Programables": ["⚡ Electrónica de Potencia Aplicada", "🌬️ Circuitos Hidráulicos y Neumáticos"],
    "💾 Microcontroladores": ["👾 Electrónica Digital"], "🎮 Control": ["🔄 Dinámica de Sistemas"], "🏭 Tópicos Selectos de Automatización Industrial": ["🎛️ Controladores Lógicos Programables"]
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

oferta_academica = {
    "🧪 Química": [{"profesor": "Norma Hernández Flores", "horario": [(d,7,8) for d in range(4)], "id":"Q1"}, {"profesor": "Norma Hernández Flores", "horario": [(d,8,9) for d in range(4)], "id":"Q2"}, {"profesor": "Norma Hernández Flores", "horario": [(d,11,12) for d in range(4)], "id":"Q3"}, {"profesor": "Norma Hernández Flores", "horario": [(d,12,13) for d in range(4)], "id":"Q4"}, {"profesor": "Hilda Araceli Torres Plata", "horario": [(d,8,9) for d in range(4)], "id":"Q5"}, {"profesor": "Hilda Araceli Torres Plata", "horario": [(d,9,10) for d in range(4)], "id":"Q6"}, {"profesor": "Alma Leticia Cázares Arreguin", "horario": [(d,13,14) for d in range(4)], "id":"Q7"}, {"profesor": "Alma Leticia Cázares Arreguin", "horario": [(d,14,15) for d in range(4)], "id":"Q8"}, {"profesor": "Alma Leticia Cázares Arreguin", "horario": [(d,16,17) for d in range(4)], "id":"Q9"}, {"profesor": "José Raymundo Garza Aldaco", "horario": [(d,15,16) for d in range(4)], "id":"Q10"}, {"profesor": "Alejandra Torres Ordaz", "horario": [(d,15,16) for d in range(4)], "id":"Q11"}, {"profesor": "Alejandra Torres Ordaz", "horario": [(d,16,17) for d in range(4)], "id":"Q12"}, {"profesor": "Alejandra Torres Ordaz", "horario": [(d,17,18) for d in range(4)], "id":"Q13"}, {"profesor": "Victor Martinez Rivera", "horario": [(d,15,16) for d in range(4)], "id":"Q14"}, {"profesor": "Victor Martinez Rivera", "horario": [(d,16,17) for d in range(4)], "id":"Q15"}, {"profesor": "Victor Martinez Rivera", "horario": [(d,17,18) for d in range(4)], "id":"Q16"}, {"profesor": "Silvia Susana Aguirre Sanchez", "horario": [(d,17,18) for d in range(4)], "id":"Q17"}, {"profesor": "Silvia Susana Aguirre Sanchez", "horario": [(d,18,19) for d in range(4)], "id":"Q18"}, {"profesor": "Karina Azucena Ayala Torres", "horario": [(d,17,18) for d in range(4)], "id":"Q19"}, {"profesor": "Karina Azucena Ayala Torres", "horario": [(d,18,19) for d in range(4)], "id":"Q20"}],
    "📐 Cálculo Diferencial": [{"profesor": "Allen Epifanio Lopez", "horario": [(d,7,8) for d in range(5)], "id":"CD1"}, {"profesor": "Kevin Alberto Cordova Ventura", "horario": [(d,8,9) for d in range(5)], "id":"CD2"}, {"profesor": "Kevin Alberto Cordova Ventura", "horario": [(d,12,13) for d in range(5)], "id":"CD3"}, {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d,8,9) for d in range(5)], "id":"CD4"}, {"profesor": "Brenda Zavala Aguillon", "horario": [(d,9,10) for d in range(5)], "id":"CD5"}, {"profesor": "Brenda Zavala Aguillon", "horario": [(d,12,13) for d in range(5)], "id":"CD6"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,10,11) for d in range(5)], "id":"CD7"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,11,12) for d in range(5)], "id":"CD8"}, {"profesor": "Eliana Sarahi Sanchez Gonzalez", "horario": [(d,11,12) for d in range(5)], "id":"CD9"}, {"profesor": "Ana Victoria Ferniza Sandoval", "horario": [(d,11,12) for d in range(5)], "id":"CD10"}, {"profesor": "Ana Victoria Ferniza Sandoval", "horario": [(d,13,14) for d in range(5)], "id":"CD11"}, {"profesor": "Edna Marina Gonzalez Martinez", "horario": [(d,11,12) for d in range(5)], "id":"CD12"}, {"profesor": "Rodrigo Juarez Martinez", "horario": [(d,15,16) for d in range(5)], "id":"CD13"}, {"profesor": "Jose Jesus Israel Ruiz Benitez", "horario": [(d,16,17) for d in range(5)], "id":"CD14"}, {"profesor": "Javier Guadalupe Cuellar Villarreal", "horario": [(d,16,17) for d in range(5)], "id":"CD15"}, {"profesor": "Irma Karina Olmedo Landeros", "horario": [(d,17,18) for d in range(5)], "id":"CD16"}],
    "⚖️ Taller de Ética": [{"profesor": "Emma Julia Velarde Sanchez", "horario": [(d,7,8) for d in range(4)], "id":"TE1"}, {"profesor": "Emma Julia Velarde Sanchez", "horario": [(d,8,9) for d in range(4)], "id":"TE2"}, {"profesor": "Maria Del Refugio Quijano Urbano", "horario": [(d,7,8) for d in range(4)], "id":"TE3"}, {"profesor": "Maria Del Refugio Quijano Urbano", "horario": [(d,9,10) for d in range(4)], "id":"TE4"}, {"profesor": "Claudia Enriqueta Cárdenas Aguirre", "horario": [(d,9,10) for d in range(4)], "id":"TE5"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,9,10) for d in range(4)], "id":"TE6"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,10,11) for d in range(4)], "id":"TE7"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,11,12) for d in range(4)], "id":"TE8"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,13,14) for d in range(4)], "id":"TE9"}, {"profesor": "Ana Laura Peña Cruz", "horario": [(d,10,11) for d in range(4)], "id":"TE10"}, {"profesor": "Guadalupe Del Socorro Peña Cruz", "horario": [(d,10,11) for d in range(4)], "id":"TE11"}, {"profesor": "Guadalupe Del Socorro Peña Cruz", "horario": [(d,12,13) for d in range(4)], "id":"TE12"}, {"profesor": "Sara Griselda Reyes Patiño", "horario": [(d,11,12) for d in range(4)], "id":"TE13"}, {"profesor": "Martin Mireles Contreras", "horario": [(d,15,16) for d in range(4)], "id":"TE14"}, {"profesor": "Martin Mireles Contreras", "horario": [(d,16,17) for d in range(4)], "id":"TE15"}, {"profesor": "Verónica Arlaine Barajas Salazar", "horario": [(d,17,18) for d in range(4)], "id":"TE16"}, {"profesor": "Verónica Arlaine Barajas Salazar", "horario": [(d,18,19) for d in range(4)], "id":"TE17"}, {"profesor": "Marcela Perales Moreno", "horario": [(d,18,19) for d in range(4)], "id":"TE18"}, {"profesor": "Marcela Perales Moreno", "horario": [(d,20,21) for d in range(4)], "id":"TE19"}, {"profesor": "Jesus Esquivel Alonso", "horario": [(d,18,19) for d in range(4)], "id":"TE20"}, {"profesor": "Carlos Benito Arriaga Aguilar", "horario": [(d,20,21) for d in range(4)], "id":"TE21"}],
    "💻 Dibujo Asistido por Computadora": [{"profesor": "Cynthia Maricela Calzoncit Carranza", "horario": [(d,10,11) for d in range(4)], "id":"D1"}, {"profesor": "Laura Villegas Leza", "horario": [(d,12,13) for d in range(4)], "id":"D2"}, {"profesor": "Laura Villegas Leza", "horario": [(d,13,14) for d in range(4)], "id":"D3"}, {"profesor": "Alejandro Ayala Ramos", "horario": [(d,14,15) for d in range(4)], "id":"D4"}, {"profesor": "Alejandro Ayala Ramos", "horario": [(d,15,16) for d in range(4)], "id":"D5"}],
    "📏 Metrología y Normalización": [{"profesor": "Juan Francisco Tovar Epifanio", "horario": [(d,7,8) for d in range(4)], "id":"M1"}, {"profesor": "Juan Francisco Tovar Epifanio", "horario": [(d,12,13) for d in range(4)], "id":"M2"}, {"profesor": "Pedro Lopez Martinez", "horario": [(d,10,11) for d in range(4)], "id":"M3"}, {"profesor": "Eustaquio Silva Torres", "horario": [(d,12,13) for d in range(4)], "id":"M4"}, {"profesor": "Eustaquio Silva Torres", "horario": [(d,14,15) for d in range(4)], "id":"M5"}, {"profesor": "Carlos Eduardo Resendiz Galindo", "horario": [(d,16,17) for d in range(4)], "id":"M6"}, {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d,18,19) for d in range(4)], "id":"M7"}],
    "🔎 Fundamentos de Investigación": [{"profesor": "Cristobal Enrique Yeverino Martinez", "horario": [(d,10,11) for d in range(4)], "id":"F1"}, {"profesor": "Cristobal Enrique Yeverino Martinez", "horario": [(d,11,12) for d in range(4)], "id":"F2"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,12,13) for d in range(4)], "id":"F3"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,13,14) for d in range(4)], "id":"F4"}],
    "∫ Cálculo Integral": [{"profesor": "Víctor Arturo Ferniza Pérez", "horario": [(d,7,8) for d in range(5)], "id":"CI1"}, {"profesor": "Víctor Arturo Ferniza Pérez", "horario": [(d,8,9) for d in range(5)], "id":"CI2"}, {"profesor": "Víctor Arturo Ferniza Pérez", "horario": [(d,9,10) for d in range(5)], "id":"CI3"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,7,8) for d in range(5)], "id":"CI4"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,8,9) for d in range(5)], "id":"CI5"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,9,10) for d in range(5)], "id":"CI6"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,10,11) for d in range(5)], "id":"CI7"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,7,8) for d in range(5)], "id":"CI8"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,8,9) for d in range(5)], "id":"CI9"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,9,10) for d in range(5)], "id":"CI10"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,10,11) for d in range(5)], "id":"CI11"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,11,12) for d in range(5)], "id":"CI12"}, {"profesor": "Narda Lucely Reyes Acosta", "horario": [(d,8,9) for d in range(5)], "id":"CI13"}, {"profesor": "Narda Lucely Reyes Acosta", "horario": [(d,11,12) for d in range(5)], "id":"CI14"}, {"profesor": "Narda Lucely Reyes Acosta", "horario": [(d,12,13) for d in range(5)], "id":"CI15"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,8,9) for d in range(5)], "id":"CI16"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,9,10) for d in range(5)], "id":"CI17"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,10,11) for d in range(5)], "id":"CI18"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,11,12) for d in range(5)], "id":"CI19"}, {"profesor": "Fabio López Campos", "horario": [(d,10,11) for d in range(5)], "id":"CI20"}, {"profesor": "Fabio López Campos", "horario": [(d,11,12) for d in range(5)], "id":"CI21"}, {"profesor": "Fabio López Campos", "horario": [(d,12,13) for d in range(5)], "id":"CI22"}, {"profesor": "Fabio López Campos", "horario": [(d,13,14) for d in range(5)], "id":"CI23"}, {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d,12,13) for d in range(5)], "id":"CI24"}, {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d,17,18) for d in range(5)], "id":"CI25"}, {"profesor": "Luis Manuel Ferniza Pérez", "horario": [(d,12,13) for d in range(5)], "id":"CI26"}, {"profesor": "Luis Manuel Ferniza Pérez", "horario": [(d,13,14) for d in range(5)], "id":"CI27"}, {"profesor": "Ignacio Dávila Ríos", "horario": [(d,16,17) for d in range(5)], "id":"CI28"}, {"profesor": "Ignacio Dávila Ríos", "horario": [(d,19,20) for d in range(5)], "id":"CI29"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,16,17) for d in range(5)], "id":"CI30"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,18,19) for d in range(5)], "id":"CI31"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,21,22) for d in range(5)], "id":"CI32"}],
    "🧮 Álgebra Lineal": [{"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,7,8) for d in range(5)], "id":"AL1"}, {"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,8,9) for d in range(5)], "id":"AL2"}, {"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,9,10) for d in range(5)], "id":"AL3"}, {"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,10,11) for d in range(5)], "id":"AL4"}, {"profesor": "Juan Francisco Benavides Ramos", "horario": [(d,7,8) for d in range(5)], "id":"AL5"}, {"profesor": "Juan Francisco Benavides Ramos", "horario": [(d,8,9) for d in range(5)], "id":"AL6"}, {"profesor": "Juan Francisco Benavides Ramos", "horario": [(d,9,10) for d in range(5)], "id":"AL7"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,7,8) for d in range(5)], "id":"AL8"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,9,10) for d in range(5)], "id":"AL9"}, {"profesor": "Juan Antonio Ruiz Muñiz", "horario": [(d,9,10) for d in range(5)], "id":"AL10"}, {"profesor": "Juan Antonio Ruiz Muñiz", "horario": [(d,12,13) for d in range(5)], "id":"AL11"}, {"profesor": "Jorge Alberto Ruiz Muñiz", "horario": [(d,11,12) for d in range(5)], "id":"AL12"}, {"profesor": "Celina Gaytan Tanguma", "horario": [(d,12,13) for d in range(5)], "id":"AL13"}, {"profesor": "Celina Gaytan Tanguma", "horario": [(d,13,14) for d in range(5)], "id":"AL14"}, {"profesor": "Celina Gaytan Tanguma", "horario": [(d,14,15) for d in range(5)], "id":"AL15"}, {"profesor": "Ignacio Dávila Ríos", "horario": [(d,18,19) for d in range(5)], "id":"AL16"}, {"profesor": "Veronica Martinez Villafuerte", "horario": [(d,16,17) for d in range(5)], "id":"AL17"}, {"profesor": "Justino Barrales Montes", "horario": [(d,16,17) for d in range(5)], "id":"AL18"}, {"profesor": "Justino Barrales Montes", "horario": [(d,17,18) for d in range(5)], "id":"AL19"}, {"profesor": "Justino Barrales Montes", "horario": [(d,18,19) for d in range(5)], "id":"AL20"}],
    "🧱 Ciencia e Ingeniería de Materiales": [{"profesor": "Dolores García De León", "horario": [(d,10,11) for d in range(5)], "id":"CIM1"}, {"profesor": "Dolores García De León", "horario": [(d,12,13) for d in range(5)], "id":"CIM2"}, {"profesor": "Luis Alberto Terrazas Ramos", "horario": [(d,10,11) for d in range(5)], "id":"CIM3"}, {"profesor": "Luis Alberto Terrazas Ramos", "horario": [(d,11,12) for d in range(5)], "id":"CIM4"}, {"profesor": "Luis Alberto Terrazas Ramos", "horario": [(d,14,15) for d in range(5)], "id":"CIM5"}, {"profesor": "Raquel Guadalupe Ruiz Moreno", "horario": [(d,10,11) for d in range(5)], "id":"CIM6"}, {"profesor": "Andrea Sanchez Arroyo", "horario": [(d,15,16) for d in range(5)], "id":"CIM7"}, {"profesor": "Socorro Del Carmen Espinoza Cardona", "horario": [(d,16,17) for d in range(5)], "id":"CIM8"}, {"profesor": "Socorro Del Carmen Espinoza Cardona", "horario": [(d,18,19) for d in range(5)], "id":"CIM9"}],
    "💾 Programación Básica": [{"profesor": "Francisco Javier De Leon Macias", "horario": [(d,7,8) for d in range(5)], "id":"PB1"}, {"profesor": "Francisco Javier De Leon Macias", "horario": [(d,8,9) for d in range(5)], "id":"PB2"}, {"profesor": "Leticia Castillo Hernández", "horario": [(d,9,10) for d in range(5)], "id":"PB3"}, {"profesor": "Leticia Castillo Hernández", "horario": [(d,13,14) for d in range(5)], "id":"PB4"}, {"profesor": "Leticia Castillo Hernández", "horario": [(d,14,15) for d in range(5)], "id":"PB5"}, {"profesor": "Arturo Alejandro Domínguez Martínez", "horario": [(d,11,12) for d in range(5)], "id":"PB6"}, {"profesor": "Hector Garcia Hernandez", "horario": [(d,15,16) for d in range(5)], "id":"PB7"}, {"profesor": "Garcia Hernandez Hector", "horario": [(d,16,17) for d in range(5)], "id":"PB8"}, {"profesor": "Mario Alberto Jáuregui Sánchez", "horario": [(d,17,18) for d in range(5)], "id":"PB9"}, {"profesor": "Mario Alberto Jáuregui Sánchez", "horario": [(d,18,19) for d in range(5)], "id":"PB10"}],
    "📊 Estadística y Control de Calidad": [{"profesor": "Georgina Solis Rodriguez", "horario": [(d,8,9) for d in range(4)], "id":"ECC1"}, {"profesor": "Georgina Solis Rodriguez", "horario": [(d,9,10) for d in range(4)], "id":"ECC2"}, {"profesor": "Federico Zertuche Luis", "horario": [(d,10,11) for d in range(4)], "id":"ECC3"}, {"profesor": "Jose Sirahuen Velez Name", "horario": [(d,11,12) for d in range(4)], "id":"ECC4"}, {"profesor": "Jose Sirahuen Velez Name", "horario": [(d,13,14) for d in range(4)], "id":"ECC5"}, {"profesor": "Jose Sirahuen Velez Name", "horario": [(d,14,15) for d in range(4)], "id":"ECC6"}, {"profesor": "Irma Violeta García Pimentel", "horario": [(d,11,12) for d in range(4)], "id":"ECC7"}, {"profesor": "Irma Violeta García Pimentel", "horario": [(d,12,13) for d in range(4)], "id":"ECC8"}, {"profesor": "Alma Patricia Lopez De Leon", "horario": [(d,16,17) for d in range(4)], "id":"ECC9"}, {"profesor": "Alma Patricia Lopez De Leon", "horario": [(d,18,19) for d in range(4)], "id":"ECC10"}],
    "💰 Administración y Contabilidad": [{"profesor": "Dalia Veronica Aguillon Padilla", "horario": [(d,10,11) for d in range(4)], "id":"AC1"}, {"profesor": "Patricia Alejandra Fernandez Rangel", "horario": [(d,11,12) for d in range(4)], "id":"AC2"}, {"profesor": "Patricia Alejandra Fernandez Rangel", "horario": [(d,12,13) for d in range(4)], "id":"AC3"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,13,14) for d in range(4)], "id":"AC4"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,14,15) for d in range(4)], "id":"AC5"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,15,16) for d in range(4)], "id":"AC6"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,16,17) for d in range(4)], "id":"AC7"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,17,18) for d in range(4)], "id":"AC8"}, {"profesor": "Francisco Alberto Galindo González", "horario": [(d,17,18) for d in range(4)], "id":"AC9"}, {"profesor": "Edgar Felipe Vazquez Siller", "horario": [(d,19,20) for d in range(4)], "id":"AC10"}],
    # SEMESTRE 3
    "↗️ Cálculo Vectorial": [{"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,8,9) for d in range(5)], "id":"CV1"}, {"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,9,10) for d in range(5)], "id":"CV2"}, {"profesor": "Silvia Deyanira Rodriguez Luna", "horario": [(d,9,10) for d in range(5)], "id":"CV3"}, {"profesor": "Silvia Deyanira Rodriguez Luna", "horario": [(d,10,11) for d in range(5)], "id":"CV4"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,13,14) for d in range(5)], "id":"CV5"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,14,15) for d in range(5)], "id":"CV6"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,15,16) for d in range(5)], "id":"CV7"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,16,17) for d in range(5)], "id":"CV8"}, {"profesor": "Rene Sanchez Ramos", "horario": [(d,13,14) for d in range(5)], "id":"CV9"}, {"profesor": "Rene Sanchez Ramos", "horario": [(d,14,15) for d in range(5)], "id":"CV10"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,14,15) for d in range(5)], "id":"CV11"}, {"profesor": "Gloria Estela Martinez Montemayor", "horario": [(d,16,17) for d in range(5)], "id":"CV12"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,19,20) for d in range(5)], "id":"CV13"}],
    "🔨 Procesos de Fabricación": [{"profesor": "Efrain Almanza Casas", "horario": [(d,8,9) for d in range(4)], "id":"PF1"}, {"profesor": "Efrain Almanza Casas", "horario": [(d,9,10) for d in range(4)], "id":"PF2"}, {"profesor": "Efrain Almanza Casas", "horario": [(d,13,14) for d in range(4)], "id":"PF3"}, {"profesor": "Anabel Azucena Hernandez Cortes", "horario": [(d,13,14) for d in range(4)], "id":"PF4"}, {"profesor": "Arnoldo Solis Covarrubias", "horario": [(d,16,17) for d in range(4)], "id":"PF5"}, {"profesor": "Arnoldo Solis Covarrubias", "horario": [(d,19,20) for d in range(4)], "id":"PF6"}],
    "⚡ Electromagnetismo": [{"profesor": "Christian Aldaco González", "horario": [(d,9,10) for d in range(5)], "id":"E1"}, {"profesor": "Christian Aldaco González", "horario": [(d,10,11) for d in range(5)], "id":"E2"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,14,15) for d in range(5)], "id":"E3"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,15,16) for d in range(5)], "id":"E4"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,16,17) for d in range(5)], "id":"E5"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,17,18) for d in range(5)], "id":"E6"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,18,19) for d in range(5)], "id":"E7"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,19,20) for d in range(5)], "id":"E8"}],
    "🏗️ Estática": [{"profesor": "Jorge Oyervides Valdez", "horario": [(d,8,9) for d in range(4)], "id":"ES1"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,9,10) for d in range(4)], "id":"ES2"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,12,13) for d in range(4)], "id":"ES3"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,17,18) for d in range(4)], "id":"ES4"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,18,19) for d in range(4)], "id":"ES5"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,10,11) for d in range(4)], "id":"ES6"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,11,12) for d in range(4)], "id":"ES7"}],
    "🔢 Métodos Numéricos": [{"profesor": "Gustavo Lopez Guarin", "horario": [(d,15,16) for d in range(4)], "id":"MN1"}, {"profesor": "Justino Barrales Montes", "horario": [(d,15,16) for d in range(4)], "id":"MN2"}, {"profesor": "Justino Barrales Montes", "horario": [(d,19,20) for d in range(4)], "id":"MN3"}, {"profesor": "Justino Barrales Montes", "horario": [(d,20,21) for d in range(4)], "id":"MN4"}, {"profesor": "Justino Barrales Montes", "horario": [(d,21,22) for d in range(4)], "id":"MN5"}],
    "🌱 Desarrollo Sustentable": [{"profesor": "Fernando Miguel Viesca Farias", "horario": [(d,7,8) for d in range(5)], "id":"DS1"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,8,9) for d in range(5)], "id":"DS2"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,9,10) for d in range(5)], "id":"DS3"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,11,12) for d in range(5)], "id":"DS4"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,12,13) for d in range(5)], "id":"DS5"}, {"profesor": "Aida Isolda Fernández De La Cerda", "horario": [(d,8,9) for d in range(5)], "id":"DS6"}, {"profesor": "Aida Isolda Fernández De La Cerda", "horario": [(d,9,10) for d in range(5)], "id":"DS7"}, {"profesor": "Marcela Guadalupe Moreno Padilla", "horario": [(d,9,10) for d in range(5)], "id":"DS8"}, {"profesor": "Marcela Guadalupe Moreno Padilla", "horario": [(d,10,11) for d in range(5)], "id":"DS9"}, {"profesor": "Marcela Guadalupe Moreno Padilla", "horario": [(d,13,14) for d in range(5)], "id":"DS10"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,11,12) for d in range(5)], "id":"DS11"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,12,13) for d in range(5)], "id":"DS12"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,15,16) for d in range(5)], "id":"DS13"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,16,17) for d in range(5)], "id":"DS14"}, {"profesor": "Pedro Angel Gonzalez Barrera", "horario": [(d,11,12) for d in range(5)], "id":"DS15"}, {"profesor": "Pedro Angel Gonzalez Barrera", "horario": [(d,12,13) for d in range(5)], "id":"DS16"}, {"profesor": "Pedro Angel Gonzalez Barrera", "horario": [(d,13,14) for d in range(5)], "id":"DS17"}, {"profesor": "Alexeyevich Flores Sanchez", "horario": [(d,11,12) for d in range(5)], "id":"DS18"}, {"profesor": "Alexeyevich Flores Sanchez", "horario": [(d,12,13) for d in range(5)], "id":"DS19"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,13,14) for d in range(5)], "id":"DS20"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,14,15) for d in range(5)], "id":"DS21"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,17,18) for d in range(5)], "id":"DS22"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,18,19) for d in range(5)], "id":"DS23"}, {"profesor": "Juan Carlos Loyola Licea", "horario": [(d,15,16) for d in range(5)], "id":"DS24"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,15,16) for d in range(5)], "id":"DS25"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,16,17) for d in range(5)], "id":"DS26"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,17,18) for d in range(5)], "id":"DS27"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,18,19) for d in range(5)], "id":"DS28"}, {"profesor": "Ramon Andres Durón Ibarra", "horario": [(d,16,17) for d in range(5)], "id":"DS29"}, {"profesor": "Veronica Amaro Hernandez", "horario": [(d,17,18) for d in range(5)], "id":"DS30"}, {"profesor": "Veronica Amaro Hernandez", "horario": [(d,18,19) for d in range(5)], "id":"DS31"}, {"profesor": "Rene Martinez Perez", "horario": [(d,18,19) for d in range(5)], "id":"DS32"}, {"profesor": "Rene Martinez Perez", "horario": [(d,19,20) for d in range(5)], "id":"DS33"}],
    # SEMESTRE 4
    "📉 Ecuaciones Diferenciales": [{"profesor": "Ismael Luevano Martinez", "horario": [(d,8,9) for d in range(5)], "id":"ED1"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,8,9) for d in range(5)], "id":"ED2"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,10,11) for d in range(5)], "id":"ED3"}, {"profesor": "César Iván Cantú", "horario": [(d,9,10) for d in range(5)], "id":"ED4"}, {"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,10,11) for d in range(5)], "id":"ED5"}, {"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,11,12) for d in range(5)], "id":"ED6"}, {"profesor": "Olivia García Calvillo", "horario": [(d,10,11) for d in range(5)], "id":"ED7"}, {"profesor": "Olivia García Calvillo", "horario": [(d,11,12) for d in range(5)], "id":"ED8"}, {"profesor": "Olivia García Calvillo", "horario": [(d,13,14) for d in range(5)], "id":"ED9"}, {"profesor": "Olivia García Calvillo", "horario": [(d,14,15) for d in range(5)], "id":"ED10"}, {"profesor": "Jesus Cantú Perez", "horario": [(d,11,12) for d in range(5)], "id":"ED11"}, {"profesor": "Jesus Cantú Perez", "horario": [(d,13,14) for d in range(5)], "id":"ED12"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,13,14) for d in range(5)], "id":"ED13"}, {"profesor": "Jorge Alberto Ramos Oliveira", "horario": [(d,17,18) for d in range(5)], "id":"ED14"}],
    "🔥 Fundamentos de Termodinámica": [{"profesor": "Luis Miguel Veloz Pachicano", "horario": [(d,7,8) for d in range(4)], "id":"FT1"}, {"profesor": "Luis Miguel Veloz Pachicano", "horario": [(d,11,12) for d in range(4)], "id":"FT2"}, {"profesor": "Elena Guadalupe Luques Lopez", "horario": [(d,8,9) for d in range(4)], "id":"FT3"}, {"profesor": "Elena Guadalupe Luques Lopez", "horario": [(d,13,14) for d in range(4)], "id":"FT4"}, {"profesor": "Erendira Del Rocio Gamon Perales", "horario": [(d,10,11) for d in range(4)], "id":"FT5"}, {"profesor": "Erendira Del Rocio Gamon Perales", "horario": [(d,12,13) for d in range(4)], "id":"FT6"}, {"profesor": "Edgar Omar Resendiz Flores", "horario": [(d,12,13) for d in range(4)], "id":"FT7"}, {"profesor": "Massiel Cristina Cisneros Morales", "horario": [(d,15,16) for d in range(4)], "id":"FT8"}, {"profesor": "Massiel Cristina Cisneros Morales", "horario": [(d,18,19) for d in range(4)], "id":"FT9"}],
    "🦾 Mecánica de Materiales": [{"profesor": "Juan Carlos Cardenas Contreras", "horario": [(0,7,8),(1,7,8),(2,7,8),(3,7,8),(4,7,9)], "id":"MM1"}, {"profesor": "Juan Carlos Cardenas Contreras", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"MM2"}, {"profesor": "Juan Carlos Cardenas Contreras", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,11,13)], "id":"MM3"}, {"profesor": "Juan Francisco Tovar Epifanio", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,12,14)], "id":"MM4"}, {"profesor": "Adolfo Galvan Avalos", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,17,19)], "id":"MM5"}],
    "🏎️ Dinámica": [{"profesor": "Claudia Yvonne Franco Martinez", "horario": [(d,8,9) for d in range(4)], "id":"DIN1"}, {"profesor": "Cipriano Alvarado González", "horario": [(d,10,11) for d in range(4)], "id":"DIN2"}, {"profesor": "Cipriano Alvarado González", "horario": [(d,11,12) for d in range(4)], "id":"DIN3"}, {"profesor": "Cipriano Alvarado González", "horario": [(d,12,13) for d in range(4)], "id":"DIN4"}, {"profesor": "Juan Arredondo Valdez", "horario": [(d,17,18) for d in range(4)], "id":"DIN5"}, {"profesor": "Ismene Guadalupe De La Peña Alcala", "horario": [(d,19,20) for d in range(4)], "id":"DIN6"}, {"profesor": "Ismene Guadalupe De La Peña Alcala", "horario": [(d,20,21) for d in range(4)], "id":"DIN7"}],
    "🔌 Análisis de Circuitos Eléctricos": [{"profesor": "Iván De Jesús Epifanio López", "horario": [(0,8,9),(1,8,9),(2,8,9),(3,8,9),(4,7,9)], "id":"ACE1"}, {"profesor": "Iván De Jesús Epifanio López", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,10,12)], "id":"ACE2"}, {"profesor": "Fernando Aguilar Gaona", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"ACE3"}, {"profesor": "Alejandro Martínez Hernández", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"ACE4"}, {"profesor": "Horacio Tolentino Quilantan", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"ACE5"}, {"profesor": "Josue Isrrael Najera Diaz", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"ACE6"}, {"profesor": "Josue Isrrael Najera Diaz", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,18,20)], "id":"ACE7"}, {"profesor": "Josue Isrrael Najera Diaz", "horario": [(0,20,21),(1,20,21),(2,20,21),(3,20,21),(4,20,22)], "id":"ACE8"}, {"profesor": "Obed Ramírez Gómez", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"ACE9"}],
    "📝 Taller de Investigación I": [{"profesor": "Juana Maria Dueñaz Reyes", "horario": [(d,7,8) for d in range(4)], "id":"TI1"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,7,8) for d in range(4)], "id":"TI2"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,8,9) for d in range(4)], "id":"TI3"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,9,10) for d in range(4)], "id":"TI4"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,10,11) for d in range(4)], "id":"TI5"}, {"profesor": "Luis Manuel Navarro Huitron", "horario": [(d,13,14) for d in range(4)], "id":"TI6"}],
    # SEMESTRE 5
    "⚙️ Máquinas Eléctricas": [{"profesor": "Gabriel Allende Sancho", "horario": [(d,8,9) for d in range(5)], "id":"ME1"}, {"profesor": "Mario Alberto Ponce Llamas", "horario": [(d,9,10) for d in range(5)], "id":"ME2"}, {"profesor": "Mario Alberto Ponce Llamas", "horario": [(d,11,12) for d in range(5)], "id":"ME3"}, {"profesor": "Alejandra Hernandez Rodriguez", "horario": [(d,15,16) for d in range(5)], "id":"ME4"}, {"profesor": "Daniel Ruiz Calderon", "horario": [(d,17,18) for d in range(5)], "id":"ME5"}],
    "📟 Electrónica Analógica": [{"profesor": "Fernando Aguilar Gaona", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"EA1"}, {"profesor": "Fernando Aguilar Gaona", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,11,13)], "id":"EA2"}, {"profesor": "Rolando Rodriguez Pimentel", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"EA3"}, {"profesor": "Joaquin Antonio Alvarado Bustos", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,9,11)], "id":"EA4"}, {"profesor": "Joaquin Antonio Alvarado Bustos", "horario": [(0,11,12),(1,11,12),(2,11,12),(3,11,12),(4,11,13)], "id":"EA5"}],
    "🔗 Mecanismos": [{"profesor": "Cipriano Alvarado González", "horario": [(d,9,10) for d in range(5)], "id":"MEC1"}, {"profesor": "Julian Javier Hernandez De La Rosa", "horario": [(d,11,12) for d in range(5)], "id":"MEC2"}, {"profesor": "Julian Javier Hernandez De La Rosa", "horario": [(d,12,13) for d in range(5)], "id":"MEC3"}, {"profesor": "Julian Javier Hernandez De La Rosa", "horario": [(d,15,16) for d in range(5)], "id":"MEC4"}],
    "💧 Análisis de Fluidos": [{"profesor": "Edgar Benito Martinez Mercado", "horario": [(d,7,8) for d in range(4)], "id":"AF1"}, {"profesor": "Edgar Benito Martinez Mercado", "horario": [(d,11,12) for d in range(4)], "id":"AF2"}, {"profesor": "Edgar Benito Martinez Mercado", "horario": [(d,13,14) for d in range(4)], "id":"AF3"}, {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d,16,17) for d in range(4)], "id":"AF4"}, {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d,19,20) for d in range(4)], "id":"AF5"}, {"profesor": "Ignacio Javier González Ordaz", "horario": [(d,18,19) for d in range(4)], "id":"AF6"}, {"profesor": "Ignacio Javier González Ordaz", "horario": [(d,19,20) for d in range(4)], "id":"AF7"}],
    "📑 Taller de Investigación II": [{"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,7,8) for d in range(4)], "id":"TI2_1"}, {"profesor": "Juana Maria Dueñaz Reyes", "horario": [(d,8,9) for d in range(4)], "id":"TI2_2"}, {"profesor": "Ma. Elida Zavala Torres", "horario": [(d,17,18) for d in range(4)], "id":"TI2_3"}, {"profesor": "Ma. Elida Zavala Torres", "horario": [(d,18,19) for d in range(4)], "id":"TI2_4"}],
    "💻 Programación Avanzada": [{"profesor": "Juan Gilberto Navarro Rodriguez", "horario": [(0,7,8),(1,7,8),(2,7,8),(3,7,8),(4,7,9)], "id":"PA1"}, {"profesor": "Juan Gilberto Navarro Rodriguez", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,12,14)], "id":"PA2"}, {"profesor": "Olga Lidia Vidal Vazquez", "horario": [(0,8,9),(1,8,9),(2,8,9),(3,8,9),(4,8,10)], "id":"PA3"}, {"profesor": "Olga Lidia Vidal Vazquez", "horario": [(0,14,15),(1,14,15),(2,14,15),(3,14,15),(4,13,15)], "id":"PA4"}, {"profesor": "Yolanda Mexicano Reyes", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,8,10)], "id":"PA5"}, {"profesor": "Yolanda Mexicano Reyes", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,10,12)], "id":"PA6"}, {"profesor": "Yolanda Mexicano Reyes", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"PA7"}, {"profesor": "Martha Patricia Piña Villanueva", "horario": [(0,11,12),(1,11,12),(2,11,12),(3,11,12),(4,10,12)], "id":"PA8"}, {"profesor": "Martha Patricia Piña Villanueva", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"PA9"}, {"profesor": "Alfredo Salazar Garcia", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,16,18)], "id":"PA10"}],
    # SEMESTRE 6
    "⚡ Electrónica de Potencia Aplicada": [{"profesor": "Iván De Jesús Epifanio López", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"EPA1"}, {"profesor": "Alejandro Martínez Hernández", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"EPA2"}],
    "🌡️ Instrumentación": [{"profesor": "Francisco Agustin Vazquez Esquivel", "horario": [(d,8,9) for d in range(5)], "id":"INS1"}, {"profesor": "Francisco Agustin Vazquez Esquivel", "horario": [(d,16,17) for d in range(5)], "id":"INS2"}, {"profesor": "Cecilia Mendoza Rivas", "horario": [(d,11,12) for d in range(5)], "id":"INS3"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,15,16) for d in range(5)], "id":"INS4"}],
    "🔩 Diseño de Elementos Mecánicos": [{"profesor": "Nestor Roberto Saavedra Camacho", "horario": [(d,7,8) for d in range(5)], "id":"DEM1"}, {"profesor": "Lourdes Guadalupe Adame Oviedo", "horario": [(d,10,11) for d in range(5)], "id":"DEM2"}, {"profesor": "Juan Antonio Guerrero Hernández", "horario": [(d,16,17) for d in range(5)], "id":"DEM3"}, {"profesor": "Juan Antonio Guerrero Hernández", "horario": [(d,18,19) for d in range(5)], "id":"DEM4"}],
    "👾 Electrónica Digital": [{"profesor": "Karina Diaz Rosas", "horario": [(d,10,11) for d in range(5)], "id":"EDG1"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,12,13) for d in range(5)], "id":"EDG2"}, {"profesor": "Ewald Fritsche Ramírez", "horario": [(d,16,17) for d in range(5)], "id":"EDG3"}, {"profesor": "Miguel Maldonado Leza", "horario": [(d,20,22) for d in range(5)], "id":"EDG4"}],
    "〰️ Vibraciones Mecánicas": [{"profesor": "Ruben Flores Campos", "horario": [(d,7,8) for d in range(5)], "id":"VM1"}, {"profesor": "Ruben Flores Campos", "horario": [(d,10,11) for d in range(5)], "id":"VM2"}, {"profesor": "Ruben Flores Campos", "horario": [(d,11,12) for d in range(5)], "id":"VM3"}, {"profesor": "Ruben Flores Campos", "horario": [(d,12,13) for d in range(5)], "id":"VM4"}, {"profesor": "Juan Carlos Anaya Zavaleta", "horario": [(d,15,16) for d in range(5)], "id":"VM5"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,15,16) for d in range(5)], "id":"VM6"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,18,19) for d in range(5)], "id":"VM7"}, {"profesor": "Erendira Guadalupe Reyna Valdes", "horario": [(d,19,20) for d in range(5)], "id":"VM8"}],
    "🛠️ Administración del Mantenimiento": [{"profesor": "Juan Manuel Saucedo Alonso", "horario": [(d,8,9) for d in range(4)], "id":"ADM1"}, {"profesor": "Iván De Jesús Contreras Silva", "horario": [(d,10,11) for d in range(4)], "id":"ADM2"}, {"profesor": "Orquidea Esmeralda Velarde Sánchez", "horario": [(d,11,12) for d in range(4)], "id":"ADM3"}, {"profesor": "Orquidea Esmeralda Velarde Sánchez", "horario": [(d,12,13) for d in range(4)], "id":"ADM4"}, {"profesor": "Cesar Humberto Avendaño Malacara", "horario": [(d,19,20) for d in range(4)], "id":"ADM5"}, {"profesor": "Cesar Humberto Avendaño Malacara", "horario": [(d,20,21) for d in range(4)], "id":"ADM6"}],
    # SEMESTRE 7
    "🏭 Manufactura Avanzada": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,9,10) for d in range(5)], "id":"MA1"}, {"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,10,11) for d in range(5)], "id":"MA2"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,12,13) for d in range(5)], "id":"MA3"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,15,16) for d in range(5)], "id":"MA4"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,16,17) for d in range(5)], "id":"MA5"}],
    "🖥️ Diseño Asistido por Computadora": [{"profesor": "José Santos Avendaño Méndez", "horario": [(d,9,10) for d in range(5)], "id":"DAC1"}, {"profesor": "Ana Laura Saucedo Jimenez", "horario": [(d,10,11) for d in range(5)], "id":"DAC2"}, {"profesor": "Juan Carlos Anaya Zavaleta", "horario": [(d,16,17) for d in range(5)], "id":"DAC3"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,19,20) for d in range(5)], "id":"DAC4"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,20,21) for d in range(5)], "id":"DAC5"}],
    "🔄 Dinámica de Sistemas": [{"profesor": "Karla Ivonne Fernandez Ramirez", "horario": [(d,11,12) for d in range(5)], "id":"DSYS1"}, {"profesor": "Gerardo Jarquín Hernández", "horario": [(d,13,14) for d in range(5)], "id":"DSYS2"}],
    "🌬️ Circuitos Hidráulicos y Neumáticos": [{"profesor": "Luis Rey Santos Saucedo", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"CHN1"}, {"profesor": "Luis Rey Santos Saucedo", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,16,18)], "id":"CHN2"}, {"profesor": "Cecilia Mendoza Rivas", "horario": [(0,14,15),(1,14,15),(2,14,15),(3,14,15),(4,14,16)], "id":"CHN3"}, {"profesor": "Manuel Enrique Sandoval Lopez", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,17,19)], "id":"CHN4"}],
    "🔧 Mantenimiento": [{"profesor": "Jose Maria Resendiz Vielma", "horario": [(d,15,16) for d in range(5)], "id":"MANT1"}, {"profesor": "Jose Maria Resendiz Vielma", "horario": [(d,16,17) for d in range(5)], "id":"MANT2"}, {"profesor": "Luis Gerardo Sanchez Chavez", "horario": [(d,16,17) for d in range(5)], "id":"MANT3"}, {"profesor": "Luis Gerardo Sanchez Chavez", "horario": [(d,18,19) for d in range(5)], "id":"MANT4"}, {"profesor": "Luis Gerardo Sanchez Chavez", "horario": [(d,19,20) for d in range(5)], "id":"MANT5"}, {"profesor": "Francisco Jesus Ramos Garcia", "horario": [(d,17,18) for d in range(5)], "id":"MANT6"}, {"profesor": "Pedro Celedonio Lopez Lara", "horario": [(d,20,21) for d in range(5)], "id":"MANT7"}],
    "💾 Microcontroladores": [{"profesor": "Pedro Quintanilla Contreras", "horario": [(d,11,12) for d in range(5)], "id":"MICRO1"}, {"profesor": "Jozef Jesus Reyes Reyna", "horario": [(d,17,18) for d in range(5)], "id":"MICRO2"}],
    # SEMESTRE 8
    "📈 Formulación y Evaluación de Proyectos": [{"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,7,8),(1,7,8),(2,7,8)], "id":"FEP1"}, {"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,10,11),(1,10,11),(2,10,11)], "id":"FEP2"}, {"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,19,20),(1,19,20),(2,19,20)], "id":"FEP3"}, {"profesor": "Nadia Patricia Ramirez Santillan", "horario": [(0,8,9),(1,8,9),(2,8,9)], "id":"FEP4"}, {"profesor": "Perla Magdalena Garcia Her", "horario": [(0,11,12),(1,11,12),(2,11,12)], "id":"FEP5"}, {"profesor": "Jackeline Elizabeth Fernandez Flores", "horario": [(0,18,19),(1,18,19),(2,18,19)], "id":"FEP6"}],
    "🎛️ Controladores Lógicos Programables": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,8,9) for d in range(5)], "id":"PLC1"}, {"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,11,12) for d in range(5)], "id":"PLC2"}],
    "🎮 Control": [{"profesor": "Cesar Gerardo Martinez Sanchez", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"CTRL1"}, {"profesor": "Jesus Guerrero Contreras", "horario": [(0,15,16),(1,15,16),(2,15,16),(3,15,16),(4,15,17)], "id":"CTRL2"}, {"profesor": "Ricardo Martínez Alvarado", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,17,19)], "id":"CTRL3"}, {"profesor": "Isaac Ruiz Ramos", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"CTRL4"}],
    "🤖 Sistemas Avanzados de Manufactura": [{"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,9,10) for d in range(5)], "id":"SAM1"}, {"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,10,11) for d in range(5)], "id":"SAM2"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,17,18) for d in range(5)], "id":"SAM3"}],
    "🌐 Redes Industriales": [{"profesor": "Francisco Flores Sanmiguel", "horario": [(d,15,16) for d in range(5)], "id":"RI1"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,16,17) for d in range(5)], "id":"RI2"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,17,18) for d in range(5)], "id":"RI3"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,18,19) for d in range(5)], "id":"RI4"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,19,20) for d in range(5)], "id":"RI5"}],
    # SEMESTRE 9
    "🦾 Robótica": [{"profesor": "Gerardo Jarquín Hernández", "horario": [(d,7,8) for d in range(5)], "id":"ROB1"}, {"profesor": "Gerardo Jarquín Hernández", "horario": [(d,14,15) for d in range(5)], "id":"ROB2"}],
    "🏭 Tópicos Selectos de Automatización Industrial": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"TS1"}, {"profesor": "Victor Manuel Retana Castillo", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,17,19)], "id":"TS2"}, {"profesor": "Victor Manuel Retana Castillo", "horario": [(0,20,21),(1,20,21),(2,20,21),(3,20,21),(4,20,22)], "id":"TS3"}, {"profesor": "Luis Rey Santos Saucedo", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"TS4"}]
}

# -----------------------------------------------------------------------------
# 4. FUNCIONES LÓGICAS
# -----------------------------------------------------------------------------
def clean_text(text):
    return text.encode('latin-1', 'ignore').decode('latin-1')

def traslape(horario1, horario2):
    for h1 in horario1:
        for h2 in horario2:
            if h1[0] == h2[0]:
                if max(h1[1], h2[1]) < min(h1[2], h2[2]): return True
    return False

def generar_combinaciones(materias, rango, prefs, horas_libres):
    bloqueos = []
    for hl in horas_libres: inicio = int(hl.split(":")[0]); bloqueos.append(inicio)
    pool = []
    for mat in materias:
        if mat not in oferta_academica: continue
        opciones = []
        for sec in oferta_academica[mat]:
            prof_name = sec['profesor']
            key = f"{mat}_{prof_name}"
            puntos = prefs.get(key, 50)
            if puntos == 0: continue 
            dentro = True
            for h in sec['horario']:
                if h[1] < rango[0] or h[2] > rango[1]: dentro = False; break
                for b in bloqueos:
                    if max(h[1], b) < min(h[2], b+1): dentro = False; break
                time_key = f"time_{mat}_{prof_name}_{h[1]}"
                if not st.session_state.get(time_key, True): dentro = False; break
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
                if traslape(c[i]['horario'], c[j]['horario']): ok=False; break
            if not ok: break
        if ok: validos.append((score, c))
    
    def sort_key(item):
        puntos, horario = item
        horas = []
        for clase in horario:
            for s in clase['horario']: horas.append(s[1])
        if not horas: return (puntos, 0)
        span = max(horas) - min(horas)
        return (puntos, -span)
    validos.sort(key=sort_key, reverse=True)
    return validos, "OK"

class PDF(FPDF):
    def header(self):
        if os.path.exists("logo_tec.png"): self.image('logo_tec.png', 10, 5, 55)
        if os.path.exists("logo_its.png"): self.image('logo_its.png', 250, 5, 25)
        if os.path.exists("horarioits.png"): self.image('horarioits.png', 120, 5, 60)
        self.set_y(65)
        self.set_font('Arial', 'B', 16); self.set_text_color(128, 0, 0)
        self.cell(0, 10, 'TECNOLÓGICO NACIONAL DE MÉXICO', 0, 1, 'C')
        self.set_font('Arial', 'B', 12); self.set_text_color(0, 0, 0)
        self.cell(0, 8, 'INSTITUTO TECNOLÓGICO DE SALTILLO', 0, 1, 'C'); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, clean_text('Desarrollado por: Néstor Alexis Piña Rodríguez | Página ') + str(self.page_no()), 0, 0, 'C')

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
        materia_clean = clase['materia']
        materia_nome = clean_text(materia_clean)
        if len(materia_nome) > 38: materia_nome = materia_nome[:35] + "..."
        profesor_nome = clean_text(clase['profesor'].split('(')[0][:30])
        creditos = str(CREDITOS.get(materia_clean, 0))
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
            dia = sesion[0]; h_inicio = sesion[1]; h_fin = sesion[2]
            # BUCLE PARA LLENAR TODOS LOS BLOQUES DE LA CLASE
            for h in range(h_inicio, h_fin):
                if h in grid:
                    grid[h][dia] = {'text': f"<div class='clase-cell' style='background-color: {color};'><span>{mat_name}</span><span class='clase-prof'>{prof_name}</span></div>"}
    html = """<table class="horario-grid"><thead><tr><th class='hora-col'>Hora</th><th>Lun</th><th>Mar</th><th>Mié</th><th>Jue</th><th>Vie</th></tr></thead><tbody>"""
    for h in range(min_h, max_h):
        html += f"<tr><td class='hora-col'>{h}-{h+1}</td>"
        for d in range(5):
            cell = grid[h][d]
            html += f"<td>{cell['text']}</td>" if cell else "<td></td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

# -----------------------------------------------------------------------------
# 5. MENÚ LATERAL
# -----------------------------------------------------------------------------
menu = st.sidebar.radio("Menú", ["📅 Generador de Horarios", "⭐ Evaluación Docente"])

if os.path.exists("burro.png"):
    st.sidebar.image("burro.png", use_container_width=True)
    
if os.path.exists("reticula.pdf"):
    with open("reticula.pdf", "rb") as pdf_file:
        st.sidebar.download_button(label="📄 Descargar Retícula", data=pdf_file, file_name="Reticula_Mecatronica.pdf", mime="application/pdf")

# =============================================================================
# VISTA 1: GENERADOR
# =============================================================================
if menu == "📅 Generador de Horarios":
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
                    <p>Esta herramienta ha sido diseñada PARA la comunidad estudiantil de Ingeniería Mecatrónica 
                    del Instituto Tecnológico de Saltillo. Su objetivo principal es ayudarte a 
                    visualizar todas las posibles opciones de horario disponibles, facilitando la 
                    toma de decisiones para tu próxima carga académica.</p>
                    <p>Encuentra la combinación perfecta de materias y maestros que se ajuste a tus necesidades sin complicaciones.</p>
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

    elif st.session_state.step == 2:
        st.title("📚 Selección de Materias")
        cols = st.columns(9); selected_in_this_step = []
        all_semesters = list(database["Ingeniería Mecatrónica"].items())
        for i in range(9):
            if i < len(all_semesters):
                sem_name, materias = all_semesters[i]
                with cols[i]:
                    st.markdown(f"<div class='semestre-header'>{i+1}°</div>", unsafe_allow_html=True)
                    for m in materias:
                        cr = CREDITOS.get(m, 0)
                        if st.checkbox(f"{m} ({cr} Cr)", value=(m in st.session_state.materias_seleccionadas), key=f"chk_{m}"):
                            selected_in_this_step.append(m)
        total_creditos = sum([CREDITOS.get(m, 0) for m in selected_in_this_step])
        num_selected = len(selected_in_this_step)
        st.write("---")
        c_info = st.container()
        msg_cred = f"✅ Créditos: {total_creditos} / 36" if total_creditos <= 36 else f"⛔ Exceso: {total_creditos} / 36"
        style_cred = "credit-ok" if total_creditos <= 36 else "credit-error"
        msg_cant = f"Materias: {num_selected} / {st.session_state.num_materias_deseadas}"
        if num_selected != st.session_state.num_materias_deseadas: style_cred = "credit-error"; msg_cant = f"⚠️ Debes elegir exactamente {st.session_state.num_materias_deseadas} materias."
        c_info.markdown(f"<div class='credit-box {style_cred}'>{msg_cred} | {msg_cant}</div>", unsafe_allow_html=True)
        if total_creditos > 36: st.progress(1.0)
        else: st.progress(total_creditos / 36)
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 1; st.rerun()
        bloqueo = False
        if total_creditos > 36: bloqueo = True
        if num_selected != st.session_state.num_materias_deseadas: bloqueo = True
        conflicto_seriacion = []
        for materia in selected_in_this_step:
            if materia in SERIACION:
                for req in SERIACION[materia]:
                    for sel in selected_in_this_step:
                        if sel == req:
                            conflicto_seriacion.append(f"❌ {materia} requiere haber aprobado {sel}. No puedes llevar ambas."); bloqueo = True
        if conflicto_seriacion:
            for conf in conflicto_seriacion: st.error(conf)
        if bloqueo:
            if col2.button("🔄 Corregir Selección (Borrar Todo)"):
                st.session_state.materias_seleccionadas = []; st.rerun()
        else:
            if col2.button("Siguiente ➡️", type="primary"):
                st.session_state.materias_seleccionadas = selected_in_this_step; st.session_state.step = 3; st.rerun()

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

    elif st.session_state.step == 4:
        st.title("👨‍🏫 Filtrado de Profesores")
        st.info("✅ Preferencia Alta | ➖ Normal | ❌ Descartar")
        for mat in st.session_state.materias_seleccionadas:
            if mat in oferta_academica:
                with st.container(border=True):
                    st.subheader(f"{mat}")
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
                        key = f"{mat}_{p}"; 
                        with cols[i % 3]:
                            st.write(f"**{p}**")
                            val = st.radio("P", ["✅", "➖", "❌"], index=1, key=key, horizontal=True, label_visibility="collapsed")
                            if val == "✅": st.session_state.prefs[key] = 100
                            elif val == "❌": st.session_state.prefs[key] = 0
                            else: st.session_state.prefs[key] = 50
                            
                            with st.expander("🕒 Horas Disponibles"):
                                teacher_sections = [s for s in oferta_academica[mat] if s['profesor'] == p]
                                start_times = sorted(list(set([s['horario'][0][1] for s in teacher_sections])))
                                for t in start_times:
                                    t_key = f"time_{mat}_{p}_{t}"
                                    st.checkbox(f"{t}:00 - {t+1}:00", value=True, key=t_key)

                            with st.expander("⭐ Ver Opiniones"):
                                if p not in st.session_state.opiniones: st.session_state.opiniones[p] = {"suma": 0, "votos": 0, "comentarios": []}
                                data = st.session_state.opiniones[p]
                                prom = int(data["suma"]/data["votos"]) if data["votos"]>0 else 0
                                color = "#e74c3c" if prom<60 else "#f1c40f" if prom<90 else "#2ecc71"
                                st.markdown(f"<div style='text-align:center; font-weight:bold; color:{color}; font-size:1.2em;'>{prom}/100</div>", unsafe_allow_html=True)
                                if data["comentarios"]:
                                    for c in data["comentarios"][:2]: st.markdown(f"<div class='comment-bubble'>{c}</div>", unsafe_allow_html=True)
                                else: st.caption("Sin comentarios.")
                                new_c = st.text_input("Comentario:", key=f"t_{key}"); new_s = st.slider("Calif:",0,100,80,key=f"s_{key}")
                                if st.button("Enviar", key=f"b_{key}"):
                                    data["suma"]+=new_s; data["votos"]+=1; data["comentarios"].insert(0,new_c); st.success("¡Enviado!"); st.rerun()

        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 3; st.rerun()
        if col2.button("🚀 GENERAR HORARIOS", type="primary"): st.session_state.step = 5; st.session_state.resultados = None; st.rerun()

    elif st.session_state.step == 5:
        st.title("✅ Resultados Finales")
        col_back, _ = st.columns([1, 4])
        if col_back.button("⬅️ Ajustar Filtros"): st.session_state.step = 4; st.rerun()
        with st.expander("📝 Datos del Alumno (Para el PDF)", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            # Validación: Nombre solo letras
            raw_name = c1.text_input("Nombre", st.session_state.alumno_nombre)
            clean_name = re.sub(r'[^a-zA-Z\s]', '', raw_name)
            if raw_name != clean_name: st.warning("Solo se permiten letras en el nombre.")
            st.session_state.alumno_nombre = clean_name
            # Validación: No Control solo números
            raw_nc = c2.text_input("No. Control", st.session_state.alumno_nc)
            clean_nc = re.sub(r'\D', '', raw_nc)
            if raw_nc != clean_nc: st.warning("Solo se permiten números en el No. Control.")
            st.session_state.alumno_nc = clean_nc
            
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
# VISTA 2: EVALUACIÓN DOCENTE
# =============================================================================
elif menu == "⭐ Evaluación Docente":
    st.title("⭐ Califica a tu Maestro")
    st.markdown("Comparte tu opinión con la comunidad.")
    all_profs = set()
    for lista in oferta_academica.values():
        for grupo in lista: all_profs.add(grupo['profesor'])
    all_profs = sorted(list(all_profs))
    prof_selected = st.selectbox("Selecciona al profesor:", all_profs)
    st.write("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(f"Opina sobre: {prof_selected}")
        nuevo_comentario = st.text_area("Comentario (Anónimo):")
        nueva_calif = st.slider("Calificación (0-100):", 0, 100, 80)
        if st.button("Enviar Opinión"):
            if prof_selected not in st.session_state.opiniones: st.session_state.opiniones[prof_selected] = {"suma": 0, "votos": 0, "comentarios": []}
            db = st.session_state.opiniones[prof_selected]
            db["suma"] += nueva_calif; db["votos"] += 1; db["comentarios"].insert(0, nuevo_comentario)
            st.success("¡Opinión registrada!"); st.rerun()
    with c2:
        if prof_selected in st.session_state.opiniones:
            data = st.session_state.opiniones[prof_selected]
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
    if prof_selected in st.session_state.opiniones and st.session_state.opiniones[prof_selected]["comentarios"]:
        for com in st.session_state.opiniones[prof_selected]["comentarios"]: st.markdown(f"<div class='comment-bubble'>{com}</div>", unsafe_allow_html=True)
    else: st.write("No hay comentarios.")
