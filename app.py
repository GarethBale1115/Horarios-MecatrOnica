import streamlit as st
import pandas as pd
import itertools
from fpdf import FPDF
import os

# -----------------------------------------------------------------------------
# CONFIGURACIÓN VISUAL Y DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Carga Académica ITS", page_icon="🎓", layout="wide")

# Inyectar CSS para darle color y quitar el estilo "oscuro y triste"
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #f0f2f6; /* Fondo gris claro */
    }
    [data-testid="stHeader"] {
        background-color: #f0f2f6;
    }
    .st-emotion-cache-10trblm {
        color: #31333F; /* Texto oscuro */
    }
    h1, h2, h3 {
        color: #1E3A8A !important; /* Títulos azules */
    }
    .stExpander .streamlit-expanderHeader {
        background-color: #E0E7FF; /* Colorcito en los acordeones */
        color: #1E3A8A;
        font-weight: bold;
    }
    /* Estilo para las tablas de horario visuales */
    .horario-grid {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        font-family: sans-serif;
        font-size: 0.85em;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .horario-grid th {
        background-color: #1E3A8A;
        color: white;
        padding: 8px;
        border: 1px solid #ccc;
    }
    .horario-grid td {
        border: 1px solid #eee;
        height: 50px; /* Altura fija para que se vea uniforme */
        vertical-align: middle;
        padding: 2px;
    }
    .hora-col {
        background-color: #f9fafb;
        font-weight: bold;
        color: #555;
        width: 80px;
    }
    .clase-cell {
        border-radius: 4px;
        padding: 4px;
        color: #222;
        font-weight: 600;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .clase-prof {
        font-weight: normal;
        font-size: 0.8em;
        margin-top: 2px;
        color: #444;
    }
</style>
""", unsafe_allow_html=True)

# Paleta de colores pastel para las materias
COLORS = ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF', '#D7B3FF', '#FFC8DD', '#A2EDE2', '#F4A261', '#E76F51']

# Inicializar estado
if 'step' not in st.session_state: st.session_state.step = 1
if 'num_materias_deseadas' not in st.session_state: st.session_state.num_materias_deseadas = 6
if 'materias_seleccionadas' not in st.session_state: st.session_state.materias_seleccionadas = []
if 'rango_hora' not in st.session_state: st.session_state.rango_hora = (7, 22)
if 'horas_libres' not in st.session_state: st.session_state.horas_libres = []
if 'prefs_descarte' not in st.session_state: st.session_state.prefs_descarte = {} # Nuevo: Solo guarda descartes
if 'resultados' not in st.session_state: st.session_state.resultados = None

# Datos del alumno
if 'alumno_nombre' not in st.session_state: st.session_state.alumno_nombre = ""
if 'alumno_nc' not in st.session_state: st.session_state.alumno_nc = ""
if 'alumno_sem' not in st.session_state: st.session_state.alumno_sem = "1"
if 'alumno_per' not in st.session_state: st.session_state.alumno_per = "ENE-JUN 2026"

# -----------------------------------------------------------------------------
# BASE DE DATOS Y OFERTA (Igual que antes)
# -----------------------------------------------------------------------------
database = {
    "Ingeniería Mecatrónica": {
        "Semestre 1": ["Química", "Cálculo Diferencial", "Taller de Ética", "Dibujo Asistido por Computadora", "Metrología y Normalización", "Fundamentos de Investigación"],
        "Semestre 2": ["Cálculo Integral", "Álgebra Lineal", "Ciencia e Ingeniería de Materiales", "Programación Básica", "Estadística y Control de Calidad", "Administración y Contabilidad"],
        "Semestre 3": ["Cálculo Vectorial", "Procesos de Fabricación", "Electromagnetismo", "Estática", "Métodos Numéricos", "Desarrollo Sustentable"],
        "Semestre 4": ["Ecuaciones Diferenciales", "Fundamentos de Termodinámica", "Mecánica de Materiales", "Dinámica", "Análisis de Circuitos Eléctricos", "Taller de Investigación I"],
        "Semestre 5": ["Máquinas Eléctricas", "Electrónica Analógica", "Mecanismos", "Análisis de Fluidos", "Taller de Investigación II", "Programación Avanzada"],
        "Semestre 6": ["Electrónica de Potencia Aplicada", "Instrumentación", "Diseño de Elementos Mecánicos", "Electrónica Digital", "Vibraciones Mecánicas", "Administración del Mantenimiento"],
        "Semestre 7": ["Manufactura Avanzada", "Diseño Asistido por Computadora", "Dinámica de Sistemas", "Circuitos Hidráulicos y Neumáticos", "Mantenimiento", "Microcontroladores"],
        "Semestre 8": ["Formulación y Evaluación de Proyectos", "Controladores Lógicos Programables", "Control", "Sistemas Avanzados de Manufactura", "Redes Industriales"],
        "Semestre 9": ["Robótica", "Tópicos Selectos de Automatización Industrial"]
    }
}

oferta_academica = {
    # ... SEMESTRE 1 ...
    "Química": [{"profesor": "Norma Hernández Flores", "horario": [(d,7,8) for d in range(4)], "id":"Q1"}, {"profesor": "Norma Hernández Flores", "horario": [(d,8,9) for d in range(4)], "id":"Q2"}, {"profesor": "Norma Hernández Flores", "horario": [(d,11,12) for d in range(4)], "id":"Q3"}, {"profesor": "Norma Hernández Flores", "horario": [(d,12,13) for d in range(4)], "id":"Q4"}, {"profesor": "Hilda Araceli Torres Plata", "horario": [(d,8,9) for d in range(4)], "id":"Q5"}, {"profesor": "Hilda Araceli Torres Plata", "horario": [(d,9,10) for d in range(4)], "id":"Q6"}, {"profesor": "Alma Leticia Cázares Arreguin", "horario": [(d,13,14) for d in range(4)], "id":"Q7"}, {"profesor": "Alma Leticia Cázares Arreguin", "horario": [(d,14,15) for d in range(4)], "id":"Q8"}, {"profesor": "Alma Leticia Cázares Arreguin", "horario": [(d,16,17) for d in range(4)], "id":"Q9"}, {"profesor": "José Raymundo Garza Aldaco", "horario": [(d,15,16) for d in range(4)], "id":"Q10"}, {"profesor": "Alejandra Torres Ordaz", "horario": [(d,15,16) for d in range(4)], "id":"Q11"}, {"profesor": "Alejandra Torres Ordaz", "horario": [(d,16,17) for d in range(4)], "id":"Q12"}, {"profesor": "Alejandra Torres Ordaz", "horario": [(d,17,18) for d in range(4)], "id":"Q13"}, {"profesor": "Victor Martinez Rivera", "horario": [(d,15,16) for d in range(4)], "id":"Q14"}, {"profesor": "Victor Martinez Rivera", "horario": [(d,16,17) for d in range(4)], "id":"Q15"}, {"profesor": "Victor Martinez Rivera", "horario": [(d,17,18) for d in range(4)], "id":"Q16"}, {"profesor": "Silvia Susana Aguirre Sanchez", "horario": [(d,17,18) for d in range(4)], "id":"Q17"}, {"profesor": "Silvia Susana Aguirre Sanchez", "horario": [(d,18,19) for d in range(4)], "id":"Q18"}, {"profesor": "Karina Azucena Ayala Torres", "horario": [(d,17,18) for d in range(4)], "id":"Q19"}, {"profesor": "Karina Azucena Ayala Torres", "horario": [(d,18,19) for d in range(4)], "id":"Q20"}],
    "Cálculo Diferencial": [{"profesor": "Allen Epifanio Lopez", "horario": [(d,7,8) for d in range(5)], "id":"CD1"}, {"profesor": "Kevin Alberto Cordova Ventura", "horario": [(d,8,9) for d in range(5)], "id":"CD2"}, {"profesor": "Kevin Alberto Cordova Ventura", "horario": [(d,12,13) for d in range(5)], "id":"CD3"}, {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d,8,9) for d in range(5)], "id":"CD4"}, {"profesor": "Brenda Zavala Aguillon", "horario": [(d,9,10) for d in range(5)], "id":"CD5"}, {"profesor": "Brenda Zavala Aguillon", "horario": [(d,12,13) for d in range(5)], "id":"CD6"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,10,11) for d in range(5)], "id":"CD7"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,11,12) for d in range(5)], "id":"CD8"}, {"profesor": "Eliana Sarahi Sanchez Gonzalez", "horario": [(d,11,12) for d in range(5)], "id":"CD9"}, {"profesor": "Ana Victoria Ferniza Sandoval", "horario": [(d,11,12) for d in range(5)], "id":"CD10"}, {"profesor": "Ana Victoria Ferniza Sandoval", "horario": [(d,13,14) for d in range(5)], "id":"CD11"}, {"profesor": "Edna Marina Gonzalez Martinez", "horario": [(d,11,12) for d in range(5)], "id":"CD12"}, {"profesor": "Rodrigo Juarez Martinez", "horario": [(d,15,16) for d in range(5)], "id":"CD13"}, {"profesor": "Jose Jesus Israel Ruiz Benitez", "horario": [(d,16,17) for d in range(5)], "id":"CD14"}, {"profesor": "Javier Guadalupe Cuellar Villarreal", "horario": [(d,16,17) for d in range(5)], "id":"CD15"}, {"profesor": "Irma Karina Olmedo Landeros", "horario": [(d,17,18) for d in range(5)], "id":"CD16"}],
    "Taller de Ética": [{"profesor": "Emma Julia Velarde Sanchez", "horario": [(d,7,8) for d in range(4)], "id":"TE1"}, {"profesor": "Emma Julia Velarde Sanchez", "horario": [(d,8,9) for d in range(4)], "id":"TE2"}, {"profesor": "Maria Del Refugio Quijano Urbano", "horario": [(d,7,8) for d in range(4)], "id":"TE3"}, {"profesor": "Maria Del Refugio Quijano Urbano", "horario": [(d,9,10) for d in range(4)], "id":"TE4"}, {"profesor": "Claudia Enriqueta Cárdenas Aguirre", "horario": [(d,9,10) for d in range(4)], "id":"TE5"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,9,10) for d in range(4)], "id":"TE6"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,10,11) for d in range(4)], "id":"TE7"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,11,12) for d in range(4)], "id":"TE8"}, {"profesor": "Juana María Espinoza Rocha", "horario": [(d,13,14) for d in range(4)], "id":"TE9"}, {"profesor": "Ana Laura Peña Cruz", "horario": [(d,10,11) for d in range(4)], "id":"TE10"}, {"profesor": "Guadalupe Del Socorro Peña Cruz", "horario": [(d,10,11) for d in range(4)], "id":"TE11"}, {"profesor": "Guadalupe Del Socorro Peña Cruz", "horario": [(d,12,13) for d in range(4)], "id":"TE12"}, {"profesor": "Sara Griselda Reyes Patiño", "horario": [(d,11,12) for d in range(4)], "id":"TE13"}, {"profesor": "Martin Mireles Contreras", "horario": [(d,15,16) for d in range(4)], "id":"TE14"}, {"profesor": "Martin Mireles Contreras", "horario": [(d,16,17) for d in range(4)], "id":"TE15"}, {"profesor": "Verónica Arlaine Barajas Salazar", "horario": [(d,17,18) for d in range(4)], "id":"TE16"}, {"profesor": "Verónica Arlaine Barajas Salazar", "horario": [(d,18,19) for d in range(4)], "id":"TE17"}, {"profesor": "Marcela Perales Moreno", "horario": [(d,18,19) for d in range(4)], "id":"TE18"}, {"profesor": "Marcela Perales Moreno", "horario": [(d,20,21) for d in range(4)], "id":"TE19"}, {"profesor": "Jesus Esquivel Alonso", "horario": [(d,18,19) for d in range(4)], "id":"TE20"}, {"profesor": "Carlos Benito Arriaga Aguilar", "horario": [(d,20,21) for d in range(4)], "id":"TE21"}],
    "Dibujo Asistido por Computadora": [{"profesor": "Cynthia Maricela Calzoncit Carranza", "horario": [(d,10,11) for d in range(4)], "id":"D1"}, {"profesor": "Laura Villegas Leza", "horario": [(d,12,13) for d in range(4)], "id":"D2"}, {"profesor": "Laura Villegas Leza", "horario": [(d,13,14) for d in range(4)], "id":"D3"}, {"profesor": "Alejandro Ayala Ramos", "horario": [(d,14,15) for d in range(4)], "id":"D4"}, {"profesor": "Alejandro Ayala Ramos", "horario": [(d,15,16) for d in range(4)], "id":"D5"}],
    "Metrología y Normalización": [{"profesor": "Juan Francisco Tovar Epifanio", "horario": [(d,7,8) for d in range(4)], "id":"M1"}, {"profesor": "Juan Francisco Tovar Epifanio", "horario": [(d,12,13) for d in range(4)], "id":"M2"}, {"profesor": "Pedro Lopez Martinez", "horario": [(d,10,11) for d in range(4)], "id":"M3"}, {"profesor": "Eustaquio Silva Torres", "horario": [(d,12,13) for d in range(4)], "id":"M4"}, {"profesor": "Eustaquio Silva Torres", "horario": [(d,14,15) for d in range(4)], "id":"M5"}, {"profesor": "Carlos Eduardo Resendiz Galindo", "horario": [(d,16,17) for d in range(4)], "id":"M6"}, {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d,18,19) for d in range(4)], "id":"M7"}],
    "Fundamentos de Investigación": [{"profesor": "Cristobal Enrique Yeverino Martinez", "horario": [(d,10,11) for d in range(4)], "id":"F1"}, {"profesor": "Cristobal Enrique Yeverino Martinez", "horario": [(d,11,12) for d in range(4)], "id":"F2"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,12,13) for d in range(4)], "id":"F3"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,13,14) for d in range(4)], "id":"F4"}],
    # --- SEMESTRE 2 ---
    "Cálculo Integral": [{"profesor": "Víctor Arturo Ferniza Pérez", "horario": [(d,7,8) for d in range(5)], "id":"CI1"}, {"profesor": "Víctor Arturo Ferniza Pérez", "horario": [(d,8,9) for d in range(5)], "id":"CI2"}, {"profesor": "Víctor Arturo Ferniza Pérez", "horario": [(d,9,10) for d in range(5)], "id":"CI3"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,7,8) for d in range(5)], "id":"CI4"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,8,9) for d in range(5)], "id":"CI5"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,9,10) for d in range(5)], "id":"CI6"}, {"profesor": "Felipe De Jesus Mendoza Morales", "horario": [(d,10,11) for d in range(5)], "id":"CI7"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,7,8) for d in range(5)], "id":"CI8"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,8,9) for d in range(5)], "id":"CI9"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,9,10) for d in range(5)], "id":"CI10"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,10,11) for d in range(5)], "id":"CI11"}, {"profesor": "Silvia Polendo Luis", "horario": [(d,11,12) for d in range(5)], "id":"CI12"}, {"profesor": "Narda Lucely Reyes Acosta", "horario": [(d,8,9) for d in range(5)], "id":"CI13"}, {"profesor": "Narda Lucely Reyes Acosta", "horario": [(d,11,12) for d in range(5)], "id":"CI14"}, {"profesor": "Narda Lucely Reyes Acosta", "horario": [(d,12,13) for d in range(5)], "id":"CI15"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,8,9) for d in range(5)], "id":"CI16"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,9,10) for d in range(5)], "id":"CI17"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,10,11) for d in range(5)], "id":"CI18"}, {"profesor": "J. Santos Valdez Perez", "horario": [(d,11,12) for d in range(5)], "id":"CI19"}, {"profesor": "Fabio López Campos", "horario": [(d,10,11) for d in range(5)], "id":"CI20"}, {"profesor": "Fabio López Campos", "horario": [(d,11,12) for d in range(5)], "id":"CI21"}, {"profesor": "Fabio López Campos", "horario": [(d,12,13) for d in range(5)], "id":"CI22"}, {"profesor": "Fabio López Campos", "horario": [(d,13,14) for d in range(5)], "id":"CI23"}, {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d,12,13) for d in range(5)], "id":"CI24"}, {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d,17,18) for d in range(5)], "id":"CI25"}, {"profesor": "Luis Manuel Ferniza Pérez", "horario": [(d,12,13) for d in range(5)], "id":"CI26"}, {"profesor": "Luis Manuel Ferniza Pérez", "horario": [(d,13,14) for d in range(5)], "id":"CI27"}, {"profesor": "Ignacio Dávila Ríos", "horario": [(d,16,17) for d in range(5)], "id":"CI28"}, {"profesor": "Ignacio Dávila Ríos", "horario": [(d,19,20) for d in range(5)], "id":"CI29"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,16,17) for d in range(5)], "id":"CI30"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,18,19) for d in range(5)], "id":"CI31"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,21,22) for d in range(5)], "id":"CI32"}],
    "Álgebra Lineal": [{"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,7,8) for d in range(5)], "id":"AL1"}, {"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,8,9) for d in range(5)], "id":"AL2"}, {"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,9,10) for d in range(5)], "id":"AL3"}, {"profesor": "Juan Angel Sánchez Espinoza", "horario": [(d,10,11) for d in range(5)], "id":"AL4"}, {"profesor": "Juan Francisco Benavides Ramos", "horario": [(d,7,8) for d in range(5)], "id":"AL5"}, {"profesor": "Juan Francisco Benavides Ramos", "horario": [(d,8,9) for d in range(5)], "id":"AL6"}, {"profesor": "Juan Francisco Benavides Ramos", "horario": [(d,9,10) for d in range(5)], "id":"AL7"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,7,8) for d in range(5)], "id":"AL8"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,9,10) for d in range(5)], "id":"AL9"}, {"profesor": "Juan Antonio Ruiz Muñiz", "horario": [(d,9,10) for d in range(5)], "id":"AL10"}, {"profesor": "Juan Antonio Ruiz Muñiz", "horario": [(d,12,13) for d in range(5)], "id":"AL11"}, {"profesor": "Jorge Alberto Ruiz Muñiz", "horario": [(d,11,12) for d in range(5)], "id":"AL12"}, {"profesor": "Celina Gaytan Tanguma", "horario": [(d,12,13) for d in range(5)], "id":"AL13"}, {"profesor": "Celina Gaytan Tanguma", "horario": [(d,13,14) for d in range(5)], "id":"AL14"}, {"profesor": "Celina Gaytan Tanguma", "horario": [(d,14,15) for d in range(5)], "id":"AL15"}, {"profesor": "Ignacio Dávila Ríos", "horario": [(d,18,19) for d in range(5)], "id":"AL16"}, {"profesor": "Veronica Martinez Villafuerte", "horario": [(d,16,17) for d in range(5)], "id":"AL17"}, {"profesor": "Justino Barrales Montes", "horario": [(d,16,17) for d in range(5)], "id":"AL18"}, {"profesor": "Justino Barrales Montes", "horario": [(d,17,18) for d in range(5)], "id":"AL19"}, {"profesor": "Justino Barrales Montes", "horario": [(d,18,19) for d in range(5)], "id":"AL20"}],
    "Ciencia e Ingeniería de Materiales": [{"profesor": "Dolores García De León", "horario": [(d,10,11) for d in range(5)], "id":"CIM1"}, {"profesor": "Dolores García De León", "horario": [(d,12,13) for d in range(5)], "id":"CIM2"}, {"profesor": "Luis Alberto Terrazas Ramos", "horario": [(d,10,11) for d in range(5)], "id":"CIM3"}, {"profesor": "Luis Alberto Terrazas Ramos", "horario": [(d,11,12) for d in range(5)], "id":"CIM4"}, {"profesor": "Luis Alberto Terrazas Ramos", "horario": [(d,14,15) for d in range(5)], "id":"CIM5"}, {"profesor": "Raquel Guadalupe Ruiz Moreno", "horario": [(d,10,11) for d in range(5)], "id":"CIM6"}, {"profesor": "Andrea Sanchez Arroyo", "horario": [(d,15,16) for d in range(5)], "id":"CIM7"}, {"profesor": "Socorro Del Carmen Espinoza Cardona", "horario": [(d,16,17) for d in range(5)], "id":"CIM8"}, {"profesor": "Socorro Del Carmen Espinoza Cardona", "horario": [(d,18,19) for d in range(5)], "id":"CIM9"}],
    "Programación Básica": [{"profesor": "Francisco Javier De Leon Macias", "horario": [(d,7,8) for d in range(5)], "id":"PB1"}, {"profesor": "Francisco Javier De Leon Macias", "horario": [(d,8,9) for d in range(5)], "id":"PB2"}, {"profesor": "Leticia Castillo Hernández", "horario": [(d,9,10) for d in range(5)], "id":"PB3"}, {"profesor": "Leticia Castillo Hernández", "horario": [(d,13,14) for d in range(5)], "id":"PB4"}, {"profesor": "Leticia Castillo Hernández", "horario": [(d,14,15) for d in range(5)], "id":"PB5"}, {"profesor": "Arturo Alejandro Domínguez Martínez", "horario": [(d,11,12) for d in range(5)], "id":"PB6"}, {"profesor": "Hector Garcia Hernandez", "horario": [(d,15,16) for d in range(5)], "id":"PB7"}, {"profesor": "Garcia Hernandez Hector", "horario": [(d,16,17) for d in range(5)], "id":"PB8"}, {"profesor": "Mario Alberto Jáuregui Sánchez", "horario": [(d,17,18) for d in range(5)], "id":"PB9"}, {"profesor": "Mario Alberto Jáuregui Sánchez", "horario": [(d,18,19) for d in range(5)], "id":"PB10"}],
    "Estadística y Control de Calidad": [{"profesor": "Georgina Solis Rodriguez", "horario": [(d,8,9) for d in range(4)], "id":"ECC1"}, {"profesor": "Georgina Solis Rodriguez", "horario": [(d,9,10) for d in range(4)], "id":"ECC2"}, {"profesor": "Federico Zertuche Luis", "horario": [(d,10,11) for d in range(4)], "id":"ECC3"}, {"profesor": "Jose Sirahuen Velez Name", "horario": [(d,11,12) for d in range(4)], "id":"ECC4"}, {"profesor": "Jose Sirahuen Velez Name", "horario": [(d,13,14) for d in range(4)], "id":"ECC5"}, {"profesor": "Jose Sirahuen Velez Name", "horario": [(d,14,15) for d in range(4)], "id":"ECC6"}, {"profesor": "Irma Violeta García Pimentel", "horario": [(d,11,12) for d in range(4)], "id":"ECC7"}, {"profesor": "Irma Violeta García Pimentel", "horario": [(d,12,13) for d in range(4)], "id":"ECC8"}, {"profesor": "Alma Patricia Lopez De Leon", "horario": [(d,16,17) for d in range(4)], "id":"ECC9"}, {"profesor": "Alma Patricia Lopez De Leon", "horario": [(d,18,19) for d in range(4)], "id":"ECC10"}],
    "Administración y Contabilidad": [{"profesor": "Dalia Veronica Aguillon Padilla", "horario": [(d,10,11) for d in range(4)], "id":"AC1"}, {"profesor": "Patricia Alejandra Fernandez Rangel", "horario": [(d,11,12) for d in range(4)], "id":"AC2"}, {"profesor": "Patricia Alejandra Fernandez Rangel", "horario": [(d,12,13) for d in range(4)], "id":"AC3"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,13,14) for d in range(4)], "id":"AC4"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,14,15) for d in range(4)], "id":"AC5"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,15,16) for d in range(4)], "id":"AC6"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,16,17) for d in range(4)], "id":"AC7"}, {"profesor": "Martin Rodriguez Contreras", "horario": [(d,17,18) for d in range(4)], "id":"AC8"}, {"profesor": "Francisco Alberto Galindo González", "horario": [(d,17,18) for d in range(4)], "id":"AC9"}, {"profesor": "Edgar Felipe Vazquez Siller", "horario": [(d,19,20) for d in range(4)], "id":"AC10"}],
    # --- SEMESTRE 3 ---
    "Cálculo Vectorial": [{"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,8,9) for d in range(5)], "id":"CV1"}, {"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,9,10) for d in range(5)], "id":"CV2"}, {"profesor": "Silvia Deyanira Rodriguez Luna", "horario": [(d,9,10) for d in range(5)], "id":"CV3"}, {"profesor": "Silvia Deyanira Rodriguez Luna", "horario": [(d,10,11) for d in range(5)], "id":"CV4"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,13,14) for d in range(5)], "id":"CV5"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,14,15) for d in range(5)], "id":"CV6"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,15,16) for d in range(5)], "id":"CV7"}, {"profesor": "Jose Ignacio Garcia Alvarez", "horario": [(d,16,17) for d in range(5)], "id":"CV8"}, {"profesor": "Rene Sanchez Ramos", "horario": [(d,13,14) for d in range(5)], "id":"CV9"}, {"profesor": "Rene Sanchez Ramos", "horario": [(d,14,15) for d in range(5)], "id":"CV10"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,14,15) for d in range(5)], "id":"CV11"}, {"profesor": "Gloria Estela Martinez Montemayor", "horario": [(d,16,17) for d in range(5)], "id":"CV12"}, {"profesor": "Miguel Angel Flores Villa", "horario": [(d,19,20) for d in range(5)], "id":"CV13"}],
    "Procesos de Fabricación": [{"profesor": "Efrain Almanza Casas", "horario": [(d,8,9) for d in range(4)], "id":"PF1"}, {"profesor": "Efrain Almanza Casas", "horario": [(d,9,10) for d in range(4)], "id":"PF2"}, {"profesor": "Efrain Almanza Casas", "horario": [(d,13,14) for d in range(4)], "id":"PF3"}, {"profesor": "Anabel Azucena Hernandez Cortes", "horario": [(d,13,14) for d in range(4)], "id":"PF4"}, {"profesor": "Arnoldo Solis Covarrubias", "horario": [(d,16,17) for d in range(4)], "id":"PF5"}, {"profesor": "Arnoldo Solis Covarrubias", "horario": [(d,19,20) for d in range(4)], "id":"PF6"}],
    "Electromagnetismo": [{"profesor": "Christian Aldaco González", "horario": [(d,9,10) for d in range(5)], "id":"E1"}, {"profesor": "Christian Aldaco González", "horario": [(d,10,11) for d in range(5)], "id":"E2"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,14,15) for d in range(5)], "id":"E3"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,15,16) for d in range(5)], "id":"E4"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,16,17) for d in range(5)], "id":"E5"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,17,18) for d in range(5)], "id":"E6"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,18,19) for d in range(5)], "id":"E7"}, {"profesor": "Benjamin Arellano Orozco", "horario": [(d,19,20) for d in range(5)], "id":"E8"}],
    "Estática": [{"profesor": "Jorge Oyervides Valdez", "horario": [(d,8,9) for d in range(4)], "id":"ES1"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,9,10) for d in range(4)], "id":"ES2"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,12,13) for d in range(4)], "id":"ES3"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,17,18) for d in range(4)], "id":"ES4"}, {"profesor": "Jorge Oyervides Valdez", "horario": [(d,18,19) for d in range(4)], "id":"ES5"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,10,11) for d in range(4)], "id":"ES6"}, {"profesor": "Leticia Urbina Valdes", "horario": [(d,11,12) for d in range(4)], "id":"ES7"}],
    "Métodos Numéricos": [{"profesor": "Gustavo Lopez Guarin", "horario": [(d,15,16) for d in range(4)], "id":"MN1"}, {"profesor": "Justino Barrales Montes", "horario": [(d,15,16) for d in range(4)], "id":"MN2"}, {"profesor": "Justino Barrales Montes", "horario": [(d,19,20) for d in range(4)], "id":"MN3"}, {"profesor": "Justino Barrales Montes", "horario": [(d,20,21) for d in range(4)], "id":"MN4"}, {"profesor": "Justino Barrales Montes", "horario": [(d,21,22) for d in range(4)], "id":"MN5"}],
    "Desarrollo Sustentable": [{"profesor": "Fernando Miguel Viesca Farias", "horario": [(d,7,8) for d in range(5)], "id":"DS1"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,8,9) for d in range(5)], "id":"DS2"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,9,10) for d in range(5)], "id":"DS3"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,11,12) for d in range(5)], "id":"DS4"}, {"profesor": "Virginia Flores Gaytan", "horario": [(d,12,13) for d in range(5)], "id":"DS5"}, {"profesor": "Aida Isolda Fernández De La Cerda", "horario": [(d,8,9) for d in range(5)], "id":"DS6"}, {"profesor": "Aida Isolda Fernández De La Cerda", "horario": [(d,9,10) for d in range(5)], "id":"DS7"}, {"profesor": "Marcela Guadalupe Moreno Padilla", "horario": [(d,9,10) for d in range(5)], "id":"DS8"}, {"profesor": "Marcela Guadalupe Moreno Padilla", "horario": [(d,10,11) for d in range(5)], "id":"DS9"}, {"profesor": "Marcela Guadalupe Moreno Padilla", "horario": [(d,13,14) for d in range(5)], "id":"DS10"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,11,12) for d in range(5)], "id":"DS11"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,12,13) for d in range(5)], "id":"DS12"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,15,16) for d in range(5)], "id":"DS13"}, {"profesor": "Alicia Orta Mendoza", "horario": [(d,16,17) for d in range(5)], "id":"DS14"}, {"profesor": "Pedro Angel Gonzalez Barrera", "horario": [(d,11,12) for d in range(5)], "id":"DS15"}, {"profesor": "Pedro Angel Gonzalez Barrera", "horario": [(d,12,13) for d in range(5)], "id":"DS16"}, {"profesor": "Pedro Angel Gonzalez Barrera", "horario": [(d,13,14) for d in range(5)], "id":"DS17"}, {"profesor": "Alexeyevich Flores Sanchez", "horario": [(d,11,12) for d in range(5)], "id":"DS18"}, {"profesor": "Alexeyevich Flores Sanchez", "horario": [(d,12,13) for d in range(5)], "id":"DS19"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,13,14) for d in range(5)], "id":"DS20"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,14,15) for d in range(5)], "id":"DS21"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,17,18) for d in range(5)], "id":"DS22"}, {"profesor": "Manuel Rodarte Carrillo", "horario": [(d,18,19) for d in range(5)], "id":"DS23"}, {"profesor": "Juan Carlos Loyola Licea", "horario": [(d,15,16) for d in range(5)], "id":"DS24"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,15,16) for d in range(5)], "id":"DS25"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,16,17) for d in range(5)], "id":"DS26"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,17,18) for d in range(5)], "id":"DS27"}, {"profesor": "Mario Alberto De La Rosa Cepeda", "horario": [(d,18,19) for d in range(5)], "id":"DS28"}, {"profesor": "Ramon Andres Durón Ibarra", "horario": [(d,16,17) for d in range(5)], "id":"DS29"}, {"profesor": "Veronica Amaro Hernandez", "horario": [(d,17,18) for d in range(5)], "id":"DS30"}, {"profesor": "Veronica Amaro Hernandez", "horario": [(d,18,19) for d in range(5)], "id":"DS31"}, {"profesor": "Rene Martinez Perez", "horario": [(d,18,19) for d in range(5)], "id":"DS32"}, {"profesor": "Rene Martinez Perez", "horario": [(d,19,20) for d in range(5)], "id":"DS33"}],
    # --- SEMESTRE 4 ---
    "Ecuaciones Diferenciales": [{"profesor": "Ismael Luevano Martinez", "horario": [(d,8,9) for d in range(5)], "id":"ED1"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,8,9) for d in range(5)], "id":"ED2"}, {"profesor": "Romina Denisse Sanchez", "horario": [(d,10,11) for d in range(5)], "id":"ED3"}, {"profesor": "César Iván Cantú", "horario": [(d,9,10) for d in range(5)], "id":"ED4"}, {"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,10,11) for d in range(5)], "id":"ED5"}, {"profesor": "Lucia Marisol Valdes Gonzalez", "horario": [(d,11,12) for d in range(5)], "id":"ED6"}, {"profesor": "Olivia García Calvillo", "horario": [(d,10,11) for d in range(5)], "id":"ED7"}, {"profesor": "Olivia García Calvillo", "horario": [(d,11,12) for d in range(5)], "id":"ED8"}, {"profesor": "Olivia García Calvillo", "horario": [(d,13,14) for d in range(5)], "id":"ED9"}, {"profesor": "Olivia García Calvillo", "horario": [(d,14,15) for d in range(5)], "id":"ED10"}, {"profesor": "Jesus Cantú Perez", "horario": [(d,11,12) for d in range(5)], "id":"ED11"}, {"profesor": "Jesus Cantú Perez", "horario": [(d,13,14) for d in range(5)], "id":"ED12"}, {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,13,14) for d in range(5)], "id":"ED13"}, {"profesor": "Jorge Alberto Ramos Oliveira", "horario": [(d,17,18) for d in range(5)], "id":"ED14"}],
    "Fundamentos de Termodinámica": [{"profesor": "Luis Miguel Veloz Pachicano", "horario": [(d,7,8) for d in range(4)], "id":"FT1"}, {"profesor": "Luis Miguel Veloz Pachicano", "horario": [(d,11,12) for d in range(4)], "id":"FT2"}, {"profesor": "Elena Guadalupe Luques Lopez", "horario": [(d,8,9) for d in range(4)], "id":"FT3"}, {"profesor": "Elena Guadalupe Luques Lopez", "horario": [(d,13,14) for d in range(4)], "id":"FT4"}, {"profesor": "Erendira Del Rocio Gamon Perales", "horario": [(d,10,11) for d in range(4)], "id":"FT5"}, {"profesor": "Erendira Del Rocio Gamon Perales", "horario": [(d,12,13) for d in range(4)], "id":"FT6"}, {"profesor": "Edgar Omar Resendiz Flores", "horario": [(d,12,13) for d in range(4)], "id":"FT7"}, {"profesor": "Massiel Cristina Cisneros Morales", "horario": [(d,15,16) for d in range(4)], "id":"FT8"}, {"profesor": "Massiel Cristina Cisneros Morales", "horario": [(d,18,19) for d in range(4)], "id":"FT9"}],
    "Mecánica de Materiales": [{"profesor": "Juan Carlos Cardenas Contreras", "horario": [(0,7,8),(1,7,8),(2,7,8),(3,7,8),(4,7,9)], "id":"MM1"}, {"profesor": "Juan Carlos Cardenas Contreras", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"MM2"}, {"profesor": "Juan Carlos Cardenas Contreras", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,11,13)], "id":"MM3"}, {"profesor": "Juan Francisco Tovar Epifanio", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,12,14)], "id":"MM4"}, {"profesor": "Adolfo Galvan Avalos", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,17,19)], "id":"MM5"}],
    "Dinámica": [{"profesor": "Claudia Yvonne Franco Martinez", "horario": [(d,8,9) for d in range(4)], "id":"DIN1"}, {"profesor": "Cipriano Alvarado González", "horario": [(d,10,11) for d in range(4)], "id":"DIN2"}, {"profesor": "Cipriano Alvarado González", "horario": [(d,11,12) for d in range(4)], "id":"DIN3"}, {"profesor": "Cipriano Alvarado González", "horario": [(d,12,13) for d in range(4)], "id":"DIN4"}, {"profesor": "Juan Arredondo Valdez", "horario": [(d,17,18) for d in range(4)], "id":"DIN5"}, {"profesor": "Ismene Guadalupe De La Peña Alcala", "horario": [(d,19,20) for d in range(4)], "id":"DIN6"}, {"profesor": "Ismene Guadalupe De La Peña Alcala", "horario": [(d,20,21) for d in range(4)], "id":"DIN7"}],
    "Análisis de Circuitos Eléctricos": [{"profesor": "Iván De Jesús Epifanio López", "horario": [(0,8,9),(1,8,9),(2,8,9),(3,8,9),(4,7,9)], "id":"ACE1"}, {"profesor": "Iván De Jesús Epifanio López", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,10,12)], "id":"ACE2"}, {"profesor": "Fernando Aguilar Gaona", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"ACE3"}, {"profesor": "Alejandro Martínez Hernández", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"ACE4"}, {"profesor": "Horacio Tolentino Quilantan", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"ACE5"}, {"profesor": "Josue Isrrael Najera Diaz", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"ACE6"}, {"profesor": "Josue Isrrael Najera Diaz", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,18,20)], "id":"ACE7"}, {"profesor": "Josue Isrrael Najera Diaz", "horario": [(0,20,21),(1,20,21),(2,20,21),(3,20,21),(4,20,22)], "id":"ACE8"}, {"profesor": "Obed Ramírez Gómez", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"ACE9"}],
    "Taller de Investigación I": [{"profesor": "Juana Maria Dueñaz Reyes", "horario": [(d,7,8) for d in range(4)], "id":"TI1"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,7,8) for d in range(4)], "id":"TI2"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,8,9) for d in range(4)], "id":"TI3"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,9,10) for d in range(4)], "id":"TI4"}, {"profesor": "Fernando Alfonso Ruiz Moreno", "horario": [(d,10,11) for d in range(4)], "id":"TI5"}, {"profesor": "Luis Manuel Navarro Huitron", "horario": [(d,13,14) for d in range(4)], "id":"TI6"}],
    # --- SEMESTRE 5 ---
    "Máquinas Eléctricas": [{"profesor": "Gabriel Allende Sancho", "horario": [(d,8,9) for d in range(5)], "id":"ME1"}, {"profesor": "Mario Alberto Ponce Llamas", "horario": [(d,9,10) for d in range(5)], "id":"ME2"}, {"profesor": "Mario Alberto Ponce Llamas", "horario": [(d,11,12) for d in range(5)], "id":"ME3"}, {"profesor": "Alejandra Hernandez Rodriguez", "horario": [(d,15,16) for d in range(5)], "id":"ME4"}, {"profesor": "Daniel Ruiz Calderon", "horario": [(d,17,18) for d in range(5)], "id":"ME5"}],
    "Electrónica Analógica": [{"profesor": "Fernando Aguilar Gaona", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"EA1"}, {"profesor": "Fernando Aguilar Gaona", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,11,13)], "id":"EA2"}, {"profesor": "Rolando Rodriguez Pimentel", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"EA3"}, {"profesor": "Joaquin Antonio Alvarado Bustos", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,9,11)], "id":"EA4"}, {"profesor": "Joaquin Antonio Alvarado Bustos", "horario": [(0,11,12),(1,11,12),(2,11,12),(3,11,12),(4,11,13)], "id":"EA5"}],
    "Mecanismos": [{"profesor": "Cipriano Alvarado González", "horario": [(d,9,10) for d in range(5)], "id":"MEC1"}, {"profesor": "Julian Javier Hernandez De La Rosa", "horario": [(d,11,12) for d in range(5)], "id":"MEC2"}, {"profesor": "Julian Javier Hernandez De La Rosa", "horario": [(d,12,13) for d in range(5)], "id":"MEC3"}, {"profesor": "Julian Javier Hernandez De La Rosa", "horario": [(d,15,16) for d in range(5)], "id":"MEC4"}],
    "Análisis de Fluidos": [{"profesor": "Edgar Benito Martinez Mercado", "horario": [(d,7,8) for d in range(4)], "id":"AF1"}, {"profesor": "Edgar Benito Martinez Mercado", "horario": [(d,11,12) for d in range(4)], "id":"AF2"}, {"profesor": "Edgar Benito Martinez Mercado", "horario": [(d,13,14) for d in range(4)], "id":"AF3"}, {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d,16,17) for d in range(4)], "id":"AF4"}, {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d,19,20) for d in range(4)], "id":"AF5"}, {"profesor": "Ignacio Javier González Ordaz", "horario": [(d,18,19) for d in range(4)], "id":"AF6"}, {"profesor": "Ignacio Javier González Ordaz", "horario": [(d,19,20) for d in range(4)], "id":"AF7"}],
    "Taller de Investigación II": [{"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,7,8) for d in range(4)], "id":"TI2_1"}, {"profesor": "Juana Maria Dueñaz Reyes", "horario": [(d,8,9) for d in range(4)], "id":"TI2_2"}, {"profesor": "Ma. Elida Zavala Torres", "horario": [(d,17,18) for d in range(4)], "id":"TI2_3"}, {"profesor": "Ma. Elida Zavala Torres", "horario": [(d,18,19) for d in range(4)], "id":"TI2_4"}],
    "Programación Avanzada": [{"profesor": "Juan Gilberto Navarro Rodriguez", "horario": [(0,7,8),(1,7,8),(2,7,8),(3,7,8),(4,7,9)], "id":"PA1"}, {"profesor": "Juan Gilberto Navarro Rodriguez", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,12,14)], "id":"PA2"}, {"profesor": "Olga Lidia Vidal Vazquez", "horario": [(0,8,9),(1,8,9),(2,8,9),(3,8,9),(4,8,10)], "id":"PA3"}, {"profesor": "Olga Lidia Vidal Vazquez", "horario": [(0,14,15),(1,14,15),(2,14,15),(3,14,15),(4,13,15)], "id":"PA4"}, {"profesor": "Yolanda Mexicano Reyes", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,8,10)], "id":"PA5"}, {"profesor": "Yolanda Mexicano Reyes", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,10,12)], "id":"PA6"}, {"profesor": "Yolanda Mexicano Reyes", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"PA7"}, {"profesor": "Martha Patricia Piña Villanueva", "horario": [(0,11,12),(1,11,12),(2,11,12),(3,11,12),(4,10,12)], "id":"PA8"}, {"profesor": "Martha Patricia Piña Villanueva", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"PA9"}, {"profesor": "Alfredo Salazar Garcia", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,16,18)], "id":"PA10"}],
    # --- SEMESTRE 6 ---
    "Electrónica de Potencia Aplicada": [{"profesor": "Iván De Jesús Epifanio López", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"EPA1"}, {"profesor": "Alejandro Martínez Hernández", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"EPA2"}],
    "Instrumentación": [{"profesor": "Francisco Agustin Vazquez Esquivel", "horario": [(d,8,9) for d in range(5)], "id":"INS1"}, {"profesor": "Francisco Agustin Vazquez Esquivel", "horario": [(d,16,17) for d in range(5)], "id":"INS2"}, {"profesor": "Cecilia Mendoza Rivas", "horario": [(d,11,12) for d in range(5)], "id":"INS3"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,15,16) for d in range(5)], "id":"INS4"}],
    "Diseño de Elementos Mecánicos": [{"profesor": "Nestor Roberto Saavedra Camacho", "horario": [(d,7,8) for d in range(5)], "id":"DEM1"}, {"profesor": "Lourdes Guadalupe Adame Oviedo", "horario": [(d,10,11) for d in range(5)], "id":"DEM2"}, {"profesor": "Juan Antonio Guerrero Hernández", "horario": [(d,16,17) for d in range(5)], "id":"DEM3"}, {"profesor": "Juan Antonio Guerrero Hernández", "horario": [(d,18,19) for d in range(5)], "id":"DEM4"}],
    "Electrónica Digital": [{"profesor": "Karina Diaz Rosas", "horario": [(d,10,11) for d in range(5)], "id":"EDG1"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,12,13) for d in range(5)], "id":"EDG2"}, {"profesor": "Ewald Fritsche Ramírez", "horario": [(d,16,17) for d in range(5)], "id":"EDG3"}, {"profesor": "Miguel Maldonado Leza", "horario": [(d,20,22) for d in range(5)], "id":"EDG4"}],
    "Vibraciones Mecánicas": [{"profesor": "Ruben Flores Campos", "horario": [(d,7,8) for d in range(5)], "id":"VM1"}, {"profesor": "Ruben Flores Campos", "horario": [(d,10,11) for d in range(5)], "id":"VM2"}, {"profesor": "Ruben Flores Campos", "horario": [(d,11,12) for d in range(5)], "id":"VM3"}, {"profesor": "Ruben Flores Campos", "horario": [(d,12,13) for d in range(5)], "id":"VM4"}, {"profesor": "Juan Carlos Anaya Zavaleta", "horario": [(d,15,16) for d in range(5)], "id":"VM5"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,15,16) for d in range(5)], "id":"VM6"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,18,19) for d in range(5)], "id":"VM7"}, {"profesor": "Erendira Guadalupe Reyna Valdes", "horario": [(d,19,20) for d in range(5)], "id":"VM8"}],
    "Administración del Mantenimiento": [{"profesor": "Juan Manuel Saucedo Alonso", "horario": [(d,8,9) for d in range(4)], "id":"ADM1"}, {"profesor": "Iván De Jesús Contreras Silva", "horario": [(d,10,11) for d in range(4)], "id":"ADM2"}, {"profesor": "Orquidea Esmeralda Velarde Sánchez", "horario": [(d,11,12) for d in range(4)], "id":"ADM3"}, {"profesor": "Orquidea Esmeralda Velarde Sánchez", "horario": [(d,12,13) for d in range(4)], "id":"ADM4"}, {"profesor": "Cesar Humberto Avendaño Malacara", "horario": [(d,19,20) for d in range(4)], "id":"ADM5"}, {"profesor": "Cesar Humberto Avendaño Malacara", "horario": [(d,20,21) for d in range(4)], "id":"ADM6"}],
    # --- SEMESTRE 7 ---
    "Manufactura Avanzada": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,9,10) for d in range(5)], "id":"MA1"}, {"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,10,11) for d in range(5)], "id":"MA2"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,12,13) for d in range(5)], "id":"MA3"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,15,16) for d in range(5)], "id":"MA4"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,16,17) for d in range(5)], "id":"MA5"}],
    "Diseño Asistido por Computadora": [{"profesor": "José Santos Avendaño Méndez", "horario": [(d,9,10) for d in range(5)], "id":"DAC1"}, {"profesor": "Ana Laura Saucedo Jimenez", "horario": [(d,10,11) for d in range(5)], "id":"DAC2"}, {"profesor": "Juan Carlos Anaya Zavaleta", "horario": [(d,16,17) for d in range(5)], "id":"DAC3"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,19,20) for d in range(5)], "id":"DAC4"}, {"profesor": "Luis Uriel García Bustos", "horario": [(d,20,21) for d in range(5)], "id":"DAC5"}],
    "Dinámica de Sistemas": [{"profesor": "Karla Ivonne Fernandez Ramirez", "horario": [(d,11,12) for d in range(5)], "id":"DSYS1"}, {"profesor": "Gerardo Jarquín Hernández", "horario": [(d,13,14) for d in range(5)], "id":"DSYS2"}],
    "Circuitos Hidráulicos y Neumáticos": [{"profesor": "Luis Rey Santos Saucedo", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"CHN1"}, {"profesor": "Luis Rey Santos Saucedo", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,16,18)], "id":"CHN2"}, {"profesor": "Cecilia Mendoza Rivas", "horario": [(0,14,15),(1,14,15),(2,14,15),(3,14,15),(4,14,16)], "id":"CHN3"}, {"profesor": "Manuel Enrique Sandoval Lopez", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,17,19)], "id":"CHN4"}],
    "Mantenimiento": [{"profesor": "Jose Maria Resendiz Vielma", "horario": [(d,15,16) for d in range(5)], "id":"MANT1"}, {"profesor": "Jose Maria Resendiz Vielma", "horario": [(d,16,17) for d in range(5)], "id":"MANT2"}, {"profesor": "Luis Gerardo Sanchez Chavez", "horario": [(d,16,17) for d in range(5)], "id":"MANT3"}, {"profesor": "Luis Gerardo Sanchez Chavez", "horario": [(d,18,19) for d in range(5)], "id":"MANT4"}, {"profesor": "Luis Gerardo Sanchez Chavez", "horario": [(d,19,20) for d in range(5)], "id":"MANT5"}, {"profesor": "Francisco Jesus Ramos Garcia", "horario": [(d,17,18) for d in range(5)], "id":"MANT6"}, {"profesor": "Pedro Celedonio Lopez Lara", "horario": [(d,20,21) for d in range(5)], "id":"MANT7"}],
    "Microcontroladores": [{"profesor": "Pedro Quintanilla Contreras", "horario": [(d,11,12) for d in range(5)], "id":"MICRO1"}, {"profesor": "Jozef Jesus Reyes Reyna", "horario": [(d,17,18) for d in range(5)], "id":"MICRO2"}],
    # --- SEMESTRE 8 ---
    "Formulación y Evaluación de Proyectos": [{"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,7,8),(1,7,8),(2,7,8)], "id":"FEP1"}, {"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,10,11),(1,10,11),(2,10,11)], "id":"FEP2"}, {"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,19,20),(1,19,20),(2,19,20)], "id":"FEP3"}, {"profesor": "Nadia Patricia Ramirez Santillan", "horario": [(0,8,9),(1,8,9),(2,8,9)], "id":"FEP4"}, {"profesor": "Perla Magdalena Garcia Her", "horario": [(0,11,12),(1,11,12),(2,11,12)], "id":"FEP5"}, {"profesor": "Jackeline Elizabeth Fernandez Flores", "horario": [(0,18,19),(1,18,19),(2,18,19)], "id":"FEP6"}],
    "Controladores Lógicos Programables": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,8,9) for d in range(5)], "id":"PLC1"}, {"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,11,12) for d in range(5)], "id":"PLC2"}],
    "Control": [{"profesor": "Cesar Gerardo Martinez Sanchez", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"CTRL1"}, {"profesor": "Jesus Guerrero Contreras", "horario": [(0,15,16),(1,15,16),(2,15,16),(3,15,16),(4,15,17)], "id":"CTRL2"}, {"profesor": "Ricardo Martínez Alvarado", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,17,19)], "id":"CTRL3"}, {"profesor": "Isaac Ruiz Ramos", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"CTRL4"}],
    "Sistemas Avanzados de Manufactura": [{"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,9,10) for d in range(5)], "id":"SAM1"}, {"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,10,11) for d in range(5)], "id":"SAM2"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,17,18) for d in range(5)], "id":"SAM3"}],
    "Redes Industriales": [{"profesor": "Francisco Flores Sanmiguel", "horario": [(d,15,16) for d in range(5)], "id":"RI1"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,16,17) for d in range(5)], "id":"RI2"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,17,18) for d in range(5)], "id":"RI3"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,18,19) for d in range(5)], "id":"RI4"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,19,20) for d in range(5)], "id":"RI5"}],
    # --- SEMESTRE 9 ---
    "Robótica": [{"profesor": "Gerardo Jarquín Hernández", "horario": [(d,7,8) for d in range(5)], "id":"ROB1"}, {"profesor": "Gerardo Jarquín Hernández", "horario": [(d,14,15) for d in range(5)], "id":"ROB2"}],
    "Tópicos Selectos de Automatización Industrial": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"TS1"}, {"profesor": "Victor Manuel Retana Castillo", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,17,19)], "id":"TS2"}, {"profesor": "Victor Manuel Retana Castillo", "horario": [(0,20,21),(1,20,21),(2,20,21),(3,20,21),(4,20,22)], "id":"TS3"}, {"profesor": "Luis Rey Santos Saucedo", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"TS4"}]
}

# -----------------------------------------------------------------------------
# FUNCIONES LÓGICAS Y PDF
# -----------------------------------------------------------------------------
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo_tec.png"): self.image('logo_tec.png', 10, 8, 33)
        if os.path.exists("logo_its.png"): self.image('logo_its.png', 240, 8, 33)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'TECNOLÓGICO NACIONAL DE MÉXICO', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INSTITUTO TECNOLÓGICO DE SALTILLO', 0, 1, 'C')
        self.ln(15)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_pro_pdf(horario, alumno_data):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Datos Alumno
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Carga Académica", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=10)
    pdf.set_fill_color(240, 240, 240)
    
    # Fila 1
    pdf.cell(30, 8, "No. Control:", 1, 0, 'L', 1)
    pdf.cell(40, 8, alumno_data.get("nc", ""), 1, 0, 'L')
    pdf.cell(30, 8, "Nombre:", 1, 0, 'L', 1)
    pdf.cell(100, 8, alumno_data.get("nombre", "").upper(), 1, 0, 'L')
    pdf.cell(30, 8, "Semestre:", 1, 0, 'L', 1)
    pdf.cell(30, 8, alumno_data.get("semestre", ""), 1, 1, 'L')
    
    # Fila 2
    pdf.cell(30, 8, "Carrera:", 1, 0, 'L', 1)
    pdf.cell(100, 8, "INGENIERÍA MECATRÓNICA", 1, 0, 'L')
    pdf.cell(30, 8, "Periodo:", 1, 0, 'L', 1)
    pdf.cell(100, 8, alumno_data.get("periodo", "ENE-JUN 2026"), 1, 1, 'L')
    pdf.ln(10)

    # Tabla PDF
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    w_mat, w_prof, w_dia = 70, 60, 25
    pdf.cell(w_mat, 10, "Materia", 1, 0, 'C', 1)
    pdf.cell(w_prof, 10, "Profesor", 1, 0, 'C', 1)
    for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]:
        pdf.cell(w_dia, 10, dia, 1, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=8)
    def get_start_hour(clase):
        if not clase['horario']: return 24
        return min([h[1] for h in clase['horario']])
    horario_ordenado = sorted(horario, key=get_start_hour)
    
    for clase in horario_ordenado:
        h = 10
        materia_nome = clase['materia'][:38]
        profesor_nome = clase['profesor'].split('(')[0][:30]
        pdf.cell(w_mat, h, materia_nome, 1)
        pdf.cell(w_prof, h, profesor_nome, 1)
        for d in range(5):
            txt_hora = ""
            for sesion in clase['horario']:
                if sesion[0] == d: txt_hora = f"{sesion[1]}:00-{sesion[2]}:00"
            pdf.cell(w_dia, h, txt_hora, 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

def traslape(horario1, horario2):
    for h1 in horario1:
        for h2 in horario2:
            if h1[0] == h2[0]:
                if h1[1] < h2[2] and h1[2] > h2[1]: return True
    return False

def generar_combinaciones(materias, rango, descartados, horas_libres):
    bloqueos = []
    for hl in horas_libres:
        inicio = int(hl.split(":")[0])
        bloqueos.append(inicio)

    pool = []
    for mat in materias:
        if mat not in oferta_academica: continue
        opciones = []
        for sec in oferta_academica[mat]:
            key = f"{mat}_{sec['profesor']}"
            
            # FILTRO 1: Descartes (❌)
            if key in descartados and descartados[key]: continue 
            
            dentro = True
            for h in sec['horario']:
                # FILTRO 2: Rango Global
                if h[1] < rango[0] or h[2] > rango[1]: 
                    dentro = False; break
                
                # FILTRO 3: Horas Libres (Huecos)
                for b in bloqueos:
                    if max(h[1], b) < min(h[2], b+1):
                        dentro = False; break
                if not dentro: break
            
            if dentro:
                s = sec.copy(); s['materia'] = mat
                opciones.append(s)
        
        if not opciones:
            return [], f"❌ **{mat}**: No tiene horarios disponibles con tus filtros (Hora libre, Rango o Profesor Descartado)."
        pool.append(opciones)
    
    # Generar combinaciones (Sin puntaje)
    combos = list(itertools.product(*pool))
    validos = []
    
    for c in combos:
        ok = True
        for i in range(len(c)):
            for j in range(i+1, len(c)):
                if traslape(c[i]['horario'], c[j]['horario']): ok=False; break
            if not ok: break
        if ok: validos.append(c)
    
    return validos, "OK"

# NUEVA FUNCIÓN: Generar tabla HTML visual
def create_timetable_html(horario):
    # 1. Asignar colores únicos a cada materia del horario actual
    subject_colors = {}
    for i, clase in enumerate(horario):
        subject_colors[clase['materia']] = COLORS[i % len(COLORS)]

    # 2. Construir la rejilla (7am a 10pm, Lun-Vie)
    grid = {h: [None]*5 for h in range(7, 23)} 
    
    # 3. Llenar la rejilla con los datos
    for clase in horario:
        # Acortar nombres para que quepan
        materia_short = clase['materia'] if len(clase['materia']) < 20 else clase['materia'][:17] + "..."
        prof_parts = clase['profesor'].split(' ')
        prof_short = f"{prof_parts[0]} {prof_parts[1] if len(prof_parts)>1 else ''}"
        color = subject_colors[clase['materia']]
        
        for sesion in clase['horario']:
            dia = sesion[0]
            hora_ini = sesion[1]
            # Si la clase es de 2 horas (ej. 7-9), la BD tiene (7,8) y (8,9). Se llena cada celda.
            if hora_ini in grid:
                grid[hora_ini][dia] = {
                    'text': f"<div class='clase-cell' style='background-color: {color};'><span>{materia_short}</span><span class='clase-prof'>{prof_short}</span></div>"
                }

    # 4. Generar el HTML de la tabla
    html = """<table class="horario-grid">"""
    html += "<thead><tr><th class='hora-col'>Hora</th><th>Lunes</th><th>Martes</th><th>Miércoles</th><th>Jueves</th><th>Viernes</th></tr></thead><tbody>"
    
    for h in range(7, 23):
        hora_str = f"{h}:00 - {h+1}:00"
        html += f"<tr><td class='hora-col'>{hora_str}</td>"
        for d in range(5):
            cell = grid[h][d]
            if cell:
                html += f"<td>{cell['text']}</td>"
            else:
                html += f"<td></td>" # Celda vacía
        html += "</tr>"
    html += "</tbody></table>"
    return html

# -----------------------------------------------------------------------------
# INTERFAZ WIZARD (PASO A PASO)
# -----------------------------------------------------------------------------

# --- PASO 1: BIENVENIDA ---
if st.session_state.step == 1:
    st.title("🐯 Generador de Horarios ITS")
    st.markdown("### ¡Bienvenido Ingeniero!")
    st.write("Esta herramienta te ayudará a encontrar la combinación perfecta de materias y maestros para tu siguiente semestre.")
    st.write("---")
    
    cant = st.number_input("¿Cuántas materias piensas meter?", min_value=1, max_value=9, value=6)
    
    if st.button("Comenzar ➡️"):
        st.session_state.num_materias_deseadas = cant
        st.session_state.step = 2
        st.rerun()

# --- PASO 2: SELECCIÓN DE MATERIAS (Ahora desplegadas por defecto) ---
elif st.session_state.step == 2:
    st.title("📚 Selección de Materias")
    st.info(f"Debes seleccionar exactamente **{st.session_state.num_materias_deseadas}** materias.")
    
    todas_materias = []
    seleccion_previa = st.session_state.materias_seleccionadas
    
    # Mostrar acordeón por semestres, ABIERTOS por defecto
    for sem, lista in database["Ingeniería Mecatrónica"].items():
        with st.expander(f"📌 {sem}", expanded=True): # expanded=True los abre
            default_val = [m for m in seleccion_previa if m in lista]
            sel = st.multiselect(f"Selecciona materias de {sem}:", lista, default=default_val, label_visibility="collapsed")
            todas_materias.extend(sel)
    
    st.write("---")
    st.write(f"**Seleccionadas:** {len(todas_materias)} de {st.session_state.num_materias_deseadas}")
    
    col1, col2 = st.columns([1,1])
    if col1.button("⬅️ Atrás"):
        st.session_state.step = 1
        st.rerun()
        
    if col2.button("Siguiente ➡️", type="primary"):
        if len(todas_materias) != st.session_state.num_materias_deseadas:
            st.error(f"⚠️ Error: Debes seleccionar exactamente {st.session_state.num_materias_deseadas} materias.")
        else:
            st.session_state.materias_seleccionadas = todas_materias
            st.session_state.step = 3
            st.rerun()

# --- PASO 3: DISPONIBILIDAD ---
elif st.session_state.step == 3:
    st.title("⏰ Tu Disponibilidad")
    st.write("Define tu horario ideal y tus horas libres.")
    
    col_rang, col_free = st.columns(2)
    
    with col_rang:
        st.subheader("Rango General")
        rango = st.slider("¿A qué hora puedes estar en la escuela?", 7, 22, (7, 22))
        st.session_state.rango_hora = rango
        
    with col_free:
        st.subheader("Horas Libres (Huecos)")
        st.info("Selecciona las horas donde NO quieres clase.")
        horas_posibles = [f"{h}:00-{h+1}:00" for h in range(7, 22)]
        libres = st.multiselect("Quiero estas horas libres:", horas_posibles)
        st.session_state.horas_libres = libres
    
    col1, col2 = st.columns([1,1])
    if col1.button("⬅️ Atrás"):
        st.session_state.step = 2
        st.rerun()
    if col2.button("Siguiente ➡️", type="primary"):
        st.session_state.step = 4
        st.rerun()

# --- PASO 4: PROFESORES (Sin puntos, solo descarte) ---
elif st.session_state.step == 4:
    st.title("👨‍🏫 Filtrado de Profesores")
    st.write("Marca las casillas de los profesores que **NO** deseas bajo ninguna circunstancia.")
    
    prefs_temp = {}
    for mat in st.session_state.materias_seleccionadas:
        if mat in oferta_academica:
            with st.container(border=True):
                st.subheader(mat)
                profes = sorted(list(set([p['profesor'] for p in oferta_academica[mat]])))
                cols = st.columns(3) # Mostrar en 3 columnas para ahorrar espacio
                for i, p in enumerate(profes):
                    key = f"{mat}_{p}"
                    # Checkbox simple: Marcado = Descartar
                    descartar = cols[i % 3].checkbox(f"❌ {p}", key=key, value=st.session_state.prefs_descarte.get(key, False))
                    prefs_temp[key] = descartar

    col1, col2 = st.columns([1,1])
    if col1.button("⬅️ Atrás"):
        st.session_state.step = 3
        st.rerun()
    if col2.button("🚀 GENERAR HORARIOS", type="primary"):
        st.session_state.prefs_descarte = prefs_temp
        st.session_state.step = 5
        st.session_state.resultados = None # Forzar recálculo
        st.rerun()

# --- PASO 5: RESULTADOS VISUALES ---
elif st.session_state.step == 5:
    st.title("✅ Resultados Finales")
    
    col_back, col_space = st.columns([1, 4])
    if col_back.button("⬅️ Ajustar Filtros"):
        st.session_state.step = 4
        st.rerun()

    with st.expander("📝 Configurar Datos del Alumno para PDF (Opcional)", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        st.session_state.alumno_nombre = c1.text_input("Nombre", st.session_state.alumno_nombre)
        st.session_state.alumno_nc = c2.text_input("No. Control", st.session_state.alumno_nc)
        st.session_state.alumno_sem = c3.text_input("Semestre", st.session_state.alumno_sem)
        st.session_state.alumno_per = c4.text_input("Periodo", st.session_state.alumno_per)

    # Ejecutar cálculo
    if st.session_state.resultados is None:
        res, msg = generar_combinaciones(st.session_state.materias_seleccionadas, st.session_state.rango_hora, st.session_state.prefs_descarte, st.session_state.horas_libres)
        if not res and msg != "OK":
            st.error(msg)
            st.session_state.resultados = []
        else:
            st.session_state.resultados = res

    # Mostrar Resultados
    if st.session_state.resultados:
        res = st.session_state.resultados
        num_res = len(res)
        st.success(f"¡Se encontraron {num_res} combinaciones posibles!")
        
        alumno_data = {
            "nombre": st.session_state.alumno_nombre,
            "nc": st.session_state.alumno_nc,
            "semestre": st.session_state.alumno_sem,
            "periodo": st.session_state.alumno_per
        }

        # MOSTRAR TODAS LAS OPCIONES (Sin límite)
        for i, horario in enumerate(res):
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                col_info.subheader(f"Opción {i+1}")
                
                pdf_bytes = create_pro_pdf(horario, alumno_data)
                col_btn.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"Carga_{st.session_state.alumno_nc}_Op{i+1}.pdf",
                    mime="application/pdf",
                    key=f"btn_dl_{i}"
                )
                
                # --- HORARIO VISUAL HTML ---
                timetable_html = create_timetable_html(horario)
                st.markdown(timetable_html, unsafe_allow_html=True)
                st.write("") # Espacio extra

    elif st.session_state.resultados is not None and len(st.session_state.resultados) == 0:
        st.warning("⚠️ **No se encontraron horarios compatibles.**")
        st.markdown("Revisa los filtros de horas libres, el rango de hora o los profesores descartados.")

    if st.button("🔄 Volver al Inicio (Reiniciar Todo)"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
