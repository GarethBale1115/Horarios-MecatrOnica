import streamlit as st
import pandas as pd
import itertools
from fpdf import FPDF
import os

# -----------------------------------------------------------------------------
# CONFIGURACIÓN VISUAL (MODO OSCURO NATIVO + TEMA ITS + CSS AVANZADO)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Horario ITS", page_icon="🐴", layout="wide")

st.markdown("""
<style>
    /* VARIABLES DE COLOR */
    :root {
        --guinda: #800000;
        --fondo-oscuro: #0e1117;
    }

    /* TÍTULOS EN GUINDA */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--guinda) !important;
        font-family: 'Arial', sans-serif;
    }

    /* --- TARJETAS DE MATERIAS (GRID PERFECTO) --- */
    
    /* Ocultar el input nativo (la palomita) */
    [data-testid="stCheckbox"] input {
        position: absolute; opacity: 0; cursor: pointer; z-index: 2; width: 100%; height: 100%;
    }
    
    /* Ocultar el div que dibuja la palomita en Streamlit */
    [data-testid="stCheckbox"] div[role="checkbox"] { display: none; }
    
    /* Contenedor principal del checkbox (La Tarjeta) */
    [data-testid="stCheckbox"] {
        position: relative;
        background-color: transparent;
        border: 1px solid rgba(128,128,128,0.4);
        border-radius: 8px;
        padding: 5px;
        margin-bottom: 8px;
        transition: all 0.2s;
        height: 90px; /* Altura FIJA para simetría */
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
    }

    /* Efecto Hover */
    [data-testid="stCheckbox"]:hover {
        border-color: var(--guinda);
        background-color: rgba(128, 0, 0, 0.15); 
    }

    /* ESTADO SELECCIONADO (Detectado por :has) */
    [data-testid="stCheckbox"]:has(input:checked) {
        background-color: var(--guinda) !important;
        border-color: var(--guinda) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* TEXTO DE LA MATERIA */
    [data-testid="stCheckbox"] p {
        font-size: 0.8em;
        line-height: 1.2;
        margin: 0;
        width: 100%;
        color: #e0e0e0; /* Texto claro por defecto */
        word-wrap: break-word;
        font-weight: 500;
        pointer-events: none; /* Dejar pasar el click al input */
    }

    /* TEXTO CUANDO ESTÁ SELECCIONADO */
    [data-testid="stCheckbox"]:has(input:checked) p {
        color: #ffffff !important;
        font-weight: bold !important;
    }

    /* ENCABEZADOS DE SEMESTRE (COLUMNAS) */
    .semestre-header {
        color: var(--guinda) !important;
        font-weight: 900;
        font-size: 1em;
        text-align: center;
        border-bottom: 3px solid var(--guinda);
        margin-bottom: 10px;
        padding-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* CREDIT BOXES */
    .credit-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-top: 10px; }
    .credit-ok { background-color: rgba(4, 95, 70, 0.3); color: #34d399; border: 1px solid #34d399; }
    .credit-error { background-color: rgba(153, 27, 27, 0.3); color: #f87171; border: 1px solid #f87171; }

    /* BOTONES */
    .stButton>button {
        color: white !important;
        background-color: var(--guinda) !important;
        border: none;
        font-weight: bold;
        border-radius: 6px;
    }
    .stButton>button:hover { background-color: #a00000 !important; }

    /* TABLA VISUAL DE RESULTADOS */
    .horario-grid { width: 100%; border-collapse: collapse; text-align: center; font-family: 'Arial', sans-serif; font-size: 0.8em; background-color: #ffffff; color: black; border-radius: 8px; overflow: hidden; }
    .horario-grid th { background-color: var(--guinda); color: white; padding: 8px; border: 1px solid #444; }
    .horario-grid td { border: 1px solid #ddd; height: 45px; vertical-align: middle; padding: 2px; color: #333; }
    .hora-col { background-color: #e0e0e0; font-weight: bold; color: #000; width: 70px; }
    
    .clase-cell { 
        border-radius: 4px; padding: 4px; color: #111; 
        font-weight: 700; font-size: 0.95em; height: 100%; 
        display: flex; flex-direction: column; justify-content: center; 
        line-height: 1.1; box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .clase-prof { font-weight: 500; font-size: 0.75em; color: #444; margin-top: 2px; }

    /* RESEÑAS */
    .comment-bubble {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 8px; border-radius: 5px; margin-bottom: 5px;
        font-size: 0.9em; border-left: 3px solid var(--guinda);
    }
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

if 'opiniones' not in st.session_state: 
    st.session_state.opiniones = {
        "Ana Gabriela Gomez Muñoz": {"suma": 450, "votos": 5, "comentarios": ["Excelente maestra, muy clara.", "Estricta pero justa."]},
        "Gerardo Jarquín Hernández": {"suma": 98, "votos": 1, "comentarios": ["El mejor para Robótica, 100% recomendado."]}
    }

# Datos alumno
if 'alumno_nombre' not in st.session_state: st.session_state.alumno_nombre = ""
if 'alumno_nc' not in st.session_state: st.session_state.alumno_nc = ""
if 'alumno_sem' not in st.session_state: st.session_state.alumno_sem = 1
if 'alumno_per' not in st.session_state: st.session_state.alumno_per = "ENE-JUN 2026"

# -----------------------------------------------------------------------------
# CRÉDITOS Y REGLAS
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
    "Vibraciones Mecánicas": ["Mecanismos"], "Electrónica Digital": ["Electrónica Analógica"], "Controladores Lógicos Programables": ["Electrónica de Potencia Aplicada"],
    "Microcontroladores": ["Electrónica Digital"], "Control": ["Dinámica de Sistemas"], "Tópicos Selectos de Automatización Industrial": ["Controladores Lógicos Programables"]
}

# -----------------------------------------------------------------------------
# BASE DE DATOS Y OFERTA (Se mantiene tu DB)
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

# (Pega aquí la OFERTA ACADÉMICA COMPLETA para que no falten profes)
oferta_academica = {
    # ... PEGAR TU DICCIONARIO COMPLETO AQUI ...
    # Por espacio, pongo solo ejemplos clave para que veas que funciona la lógica
    # Tienes que reemplazar esto con tu bloque gigante
    "Robótica": [{"profesor": "Gerardo Jarquín Hernández", "horario": [(d,7,8) for d in range(5)], "id":"ROB1"}, {"profesor": "Gerardo Jarquín Hernández", "horario": [(d,14,15) for d in range(5)], "id":"ROB2"}],
    "Controladores Lógicos Programables": [{"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,8,9) for d in range(5)], "id":"PLC1"}, {"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(d,11,12) for d in range(5)], "id":"PLC2"}],
    "Sistemas Avanzados de Manufactura": [{"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,9,10) for d in range(5)], "id":"SAM1"}, {"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,10,11) for d in range(5)], "id":"SAM2"}, {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,17,18) for d in range(5)], "id":"SAM3"}],
    "Microcontroladores": [{"profesor": "Pedro Quintanilla Contreras", "horario": [(d,11,12) for d in range(5)], "id":"MICRO1"}, {"profesor": "Jozef Jesus Reyes Reyna", "horario": [(d,17,18) for d in range(5)], "id":"MICRO2"}],
    "Redes Industriales": [{"profesor": "Francisco Flores Sanmiguel", "horario": [(d,15,16) for d in range(5)], "id":"RI1"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,16,17) for d in range(5)], "id":"RI2"}, {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,17,18) for d in range(5)], "id":"RI3"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,18,19) for d in range(5)], "id":"RI4"}, {"profesor": "Neider Gonzalez Roblero", "horario": [(d,19,20) for d in range(5)], "id":"RI5"}],
    "Formulación y Evaluación de Proyectos": [{"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,7,8),(1,7,8),(2,7,8)], "id":"FEP1"}, {"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,10,11),(1,10,11),(2,10,11)], "id":"FEP2"}, {"profesor": "Jose Ignacio Gonzalez Delgado", "horario": [(0,19,20),(1,19,20),(2,19,20)], "id":"FEP3"}, {"profesor": "Nadia Patricia Ramirez Santillan", "horario": [(0,8,9),(1,8,9),(2,8,9)], "id":"FEP4"}, {"profesor": "Perla Magdalena Garcia Her", "horario": [(0,11,12),(1,11,12),(2,11,12)], "id":"FEP5"}, {"profesor": "Jackeline Elizabeth Fernandez Flores", "horario": [(0,18,19),(1,18,19),(2,18,19)], "id":"FEP6"}],
    # ... AÑADE EL RESTO DE TUS MATERIAS AQUÍ ...
}

# -----------------------------------------------------------------------------
# FUNCIONES LÓGICAS (DEFINIDAS AL INICIO PARA EVITAR NAME ERROR)
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
    # Convertir horas libres a lista de inicios
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
            puntos = prefs.get(key, 50)
            
            # 1. Filtro: Profesor Descartado (❌ = 0 puntos)
            if puntos == 0: continue 
            
            dentro = True
            for h in sec['horario']:
                # 2. Filtro: Rango de Hora General
                if h[1] < rango[0] or h[2] > rango[1]: 
                    dentro = False; break
                
                # 3. Filtro: Horas Libres Especificas
                for b in bloqueos:
                    # Si la clase choca con la hora bloqueada
                    if max(h[1], b) < min(h[2], b+1):
                        dentro = False; break
                if not dentro: break
            
            if dentro:
                s = sec.copy(); s['materia'] = mat; s['score'] = puntos
                opciones.append(s)
        
        if not opciones:
            return [], f"❌ **{mat}**: No tiene horarios disponibles con tus filtros (Hora, Rango o Profe)."
        pool.append(opciones)
    
    # Generar combinaciones
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
    
    # ALGORITMO DE ORDENAMIENTO INTELIGENTE
    # Prioridad 1: Preferencia de Maestros (Score alto)
    # Prioridad 2: MENOR tiempo en el Tec (Eficiencia)
    def sort_key(item):
        puntos, horario = item
        horas_ocupadas = []
        for clase in horario:
            for s in clase['horario']: horas_ocupadas.append(s[1])
        
        if not horas_ocupadas: return (puntos, 0)
        
        # Calcular "Span" (Hora salida - Hora entrada)
        span = max(horas_ocupadas) - min(horas_ocupadas)
        
        # Retornar tupla: (Mayor Puntos, Menor Span)
        # Usamos negativo en span porque sort es reverse=True (Descendente)
        # Queremos MENOR span, asi que -Span mas cercano a 0 es "Mayor" en sort descendente
        return (puntos, -span)

    validos.sort(key=sort_key, reverse=True)
    return validos, "OK"

class PDF(FPDF):
    def header(self):
        # LOGOS EN PDF
        if os.path.exists("logo_tec.png"): self.image('logo_tec.png', 10, 5, 55)
        if os.path.exists("logo_its.png"): self.image('logo_its.png', 250, 5, 25)
        if os.path.exists("horarioits.png"): self.image('horarioits.png', 120, 5, 60) # Logo nuestro centrado
        
        self.set_y(25)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(128, 0, 0)
        self.cell(0, 10, 'TECNOLÓGICO NACIONAL DE MÉXICO', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, 'INSTITUTO TECNOLÓGICO DE SALTILLO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
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
    
    pdf.cell(30, h_row, "Carrera:", 1, 0, 'L', 1); pdf.cell(100, h_row, clean_text("INGENIERÍA MECATRÓNICA"), 1, 0, 'L')
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

# -----------------------------------------------------------------------------
# MENÚ LATERAL
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

    # --- PASO 2: MATERIAS (TABLERO 9 COLUMNAS) ---
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
                        if st.checkbox(f"{m} ({CREDITOS.get(m, 0)} Cr)", value=(m in st.session_state.materias_seleccionadas), key=f"chk_{m}"): selected_in_this_step.append(m)
        
        total_creditos = sum([CREDITOS.get(m, 0) for m in selected_in_this_step])
        num_sel = len(selected_in_this_step)
        
        st.write("---")
        c_info = st.container()
        if total_creditos <= 36: c_info.markdown(f"<div class='credit-box credit-ok'>✅ Créditos Acumulados: {total_creditos} / 36 | Materias: {num_sel}</div>", unsafe_allow_html=True); st.progress(total_creditos / 36)
        else: c_info.markdown(f"<div class='credit-box credit-error'>⛔ ¡EXCESO DE CRÉDITOS! ({total_creditos} / 36)</div>", unsafe_allow_html=True); st.progress(1.0)
        
        col1, col2 = st.columns([1,1])
        if col1.button("⬅️ Atrás"): st.session_state.step = 1; st.rerun()
        
        # VALIDACIONES
        bloqueo = False
        if total_creditos > 36: bloqueo = True
        if num_sel != st.session_state.num_materias_deseadas:
            bloqueo = True
            st.error(f"⚠️ Debes seleccionar EXACTAMENTE {st.session_state.num_materias_deseadas} materias. Tienes {num_sel}.")
            
        # Seriación
        for m in selected_in_this_step:
            if m in SERIACION:
                for req in SERIACION[m]:
                    if req in selected_in_this_step:
                        st.error(f"⛔ ERROR ACADÉMICO: No puedes llevar '{m}' y '{req}' al mismo tiempo (Seriación).")
                        bloqueo = True
        
        if bloqueo:
            if col2.button("🔄 Corregir Selección (Borrar Todo)"):
                st.session_state.materias_seleccionadas = []
                st.rerun()
        else:
            if col2.button("Siguiente ➡️", type="primary"):
                st.session_state.materias_seleccionadas = selected_in_this_step; st.session_state.step = 3; st.rerun()

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
        
        # AQUÍ ESTÁ LA CORRECCIÓN DEL NAME ERROR: generar_combinaciones YA ESTÁ DEFINIDA ARRIBA
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
            promedio = int(data["suma"] / data["votos"])
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
