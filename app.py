import streamlit as st
import pandas as pd
import itertools
from fpdf import FPDF
import base64

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Horarios Mecatrónica", page_icon="⚙️", layout="wide")

# -----------------------------------------------------------------------------
# BASE DE DATOS (NOMBRES DE MATERIAS)
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

# -----------------------------------------------------------------------------
# OFERTA ACADÉMICA COMPLETA (SEM 1 - 9)
# -----------------------------------------------------------------------------
# Días: 0=Lun, 1=Mar, 2=Mie, 3=Jue, 4=Vie
oferta_academica = {
    # --- SEMESTRE 1 ---
    "Química": [
        {"profesor": "Norma Hernández Flores (7-8am)", "horario": [(d, 7, 8) for d in range(4)], "id": "Q1"},
        {"profesor": "Norma Hernández Flores (8-9am)", "horario": [(d, 8, 9) for d in range(4)], "id": "Q2"},
        {"profesor": "Norma Hernández Flores (11-12pm)", "horario": [(d, 11, 12) for d in range(4)], "id": "Q3"},
        {"profesor": "Norma Hernández Flores (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "Q4"},
        {"profesor": "Hilda Araceli Torres Plata (8-9am)", "horario": [(d, 8, 9) for d in range(4)], "id": "Q5"},
        {"profesor": "Hilda Araceli Torres Plata (9-10am)", "horario": [(d, 9, 10) for d in range(4)], "id": "Q6"},
        {"profesor": "Alma Leticia Cázares Arreguin (1-2pm)", "horario": [(d, 13, 14) for d in range(4)], "id": "Q7"},
        {"profesor": "Alma Leticia Cázares Arreguin (2-3pm)", "horario": [(d, 14, 15) for d in range(4)], "id": "Q8"},
        {"profesor": "Alma Leticia Cázares Arreguin (4-5pm)", "horario": [(d, 16, 17) for d in range(4)], "id": "Q9"},
        {"profesor": "José Raymundo Garza Aldaco (3-4pm)", "horario": [(d, 15, 16) for d in range(4)], "id": "Q10"},
        {"profesor": "Alejandra Torres Ordaz (3-4pm)", "horario": [(d, 15, 16) for d in range(4)], "id": "Q11"},
        {"profesor": "Alejandra Torres Ordaz (4-5pm)", "horario": [(d, 16, 17) for d in range(4)], "id": "Q12"},
        {"profesor": "Alejandra Torres Ordaz (5-6pm)", "horario": [(d, 17, 18) for d in range(4)], "id": "Q13"},
        {"profesor": "Victor Martinez Rivera (3-4pm)", "horario": [(d, 15, 16) for d in range(4)], "id": "Q14"},
        {"profesor": "Victor Martinez Rivera (4-5pm)", "horario": [(d, 16, 17) for d in range(4)], "id": "Q15"},
        {"profesor": "Victor Martinez Rivera (5-6pm)", "horario": [(d, 17, 18) for d in range(4)], "id": "Q16"},
        {"profesor": "Silvia Susana Aguirre Sanchez (5-6pm)", "horario": [(d, 17, 18) for d in range(4)], "id": "Q17"},
        {"profesor": "Silvia Susana Aguirre Sanchez (6-7pm)", "horario": [(d, 18, 19) for d in range(4)], "id": "Q18"},
        {"profesor": "Karina Azucena Ayala Torres (5-6pm)", "horario": [(d, 17, 18) for d in range(4)], "id": "Q19"},
        {"profesor": "Karina Azucena Ayala Torres (6-7pm)", "horario": [(d, 18, 19) for d in range(4)], "id": "Q20"},
    ],
    "Cálculo Diferencial": [
        {"profesor": "Allen Epifanio Lopez", "horario": [(d, 7, 8) for d in range(5)], "id": "CD1"},
        {"profesor": "Kevin Alberto Cordova Ventura (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "CD2"},
        {"profesor": "Kevin Alberto Cordova Ventura (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CD3"},
        {"profesor": "Erwin Rommel Cerda Leon", "horario": [(d, 8, 9) for d in range(5)], "id": "CD4"},
        {"profesor": "Brenda Zavala Aguillon (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "CD5"},
        {"profesor": "Brenda Zavala Aguillon (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CD6"},
        {"profesor": "Alicia Guadalupe Del Bosque Martínez (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CD7"},
        {"profesor": "Alicia Guadalupe Del Bosque Martínez (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CD8"},
        {"profesor": "Eliana Sarahi Sanchez Gonzalez", "horario": [(d, 11, 12) for d in range(5)], "id": "CD9"},
        {"profesor": "Ana Victoria Ferniza Sandoval (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CD10"},
        {"profesor": "Ana Victoria Ferniza Sandoval (1-2pm)", "horario": [(d, 13, 14) for d in range(5)], "id": "CD11"},
        {"profesor": "Edna Marina Gonzalez Martinez", "horario": [(d, 11, 12) for d in range(5)], "id": "CD12"},
        {"profesor": "Rodrigo Juarez Martinez", "horario": [(d, 15, 16) for d in range(5)], "id": "CD13"},
        {"profesor": "Jose Jesus Israel Ruiz Benitez", "horario": [(d, 16, 17) for d in range(5)], "id": "CD14"},
        {"profesor": "Javier Guadalupe Cuellar Villarreal", "horario": [(d, 16, 17) for d in range(5)], "id": "CD15"},
        {"profesor": "Irma Karina Olmedo Landeros", "horario": [(d, 17, 18) for d in range(5)], "id": "CD16"},
    ],
    "Taller de Ética": [
        {"profesor": "Emma Julia Velarde Sanchez (7-8am)", "horario": [(d, 7, 8) for d in range(4)], "id": "TE1"},
        {"profesor": "Emma Julia Velarde Sanchez (8-9am)", "horario": [(d, 8, 9) for d in range(4)], "id": "TE2"},
        {"profesor": "Maria Del Refugio Quijano Urbano (7-8am)", "horario": [(d, 7, 8) for d in range(4)], "id": "TE3"},
        {"profesor": "Maria Del Refugio Quijano Urbano (9-10am)", "horario": [(d, 9, 10) for d in range(4)], "id": "TE4"},
        {"profesor": "Claudia Enriqueta Cárdenas Aguirre", "horario": [(d, 9, 10) for d in range(4)], "id": "TE5"},
        {"profesor": "Juana María Espinoza Rocha (9-10am)", "horario": [(d, 9, 10) for d in range(4)], "id": "TE6"},
        {"profesor": "Juana María Espinoza Rocha (10-11am)", "horario": [(d, 10, 11) for d in range(4)], "id": "TE7"},
        {"profesor": "Juana María Espinoza Rocha (11-12pm)", "horario": [(d, 11, 12) for d in range(4)], "id": "TE8"},
        {"profesor": "Juana María Espinoza Rocha (1-2pm)", "horario": [(d, 13, 14) for d in range(4)], "id": "TE9"},
        {"profesor": "Ana Laura Peña Cruz", "horario": [(d, 10, 11) for d in range(4)], "id": "TE10"},
        {"profesor": "Guadalupe Del Socorro Peña Cruz (10-11am)", "horario": [(d, 10, 11) for d in range(4)], "id": "TE11"},
        {"profesor": "Guadalupe Del Socorro Peña Cruz (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "TE12"},
        {"profesor": "Sara Griselda Reyes Patiño", "horario": [(d, 11, 12) for d in range(4)], "id": "TE13"},
        {"profesor": "Martin Mireles Contreras (3-4pm)", "horario": [(d, 15, 16) for d in range(4)], "id": "TE14"},
        {"profesor": "Martin Mireles Contreras (4-5pm)", "horario": [(d, 16, 17) for d in range(4)], "id": "TE15"},
        {"profesor": "Verónica Arlaine Barajas Salazar (5-6pm)", "horario": [(d, 17, 18) for d in range(4)], "id": "TE16"},
        {"profesor": "Verónica Arlaine Barajas Salazar (6-7pm)", "horario": [(d, 18, 19) for d in range(4)], "id": "TE17"},
        {"profesor": "Marcela Perales Moreno (6-7pm)", "horario": [(d, 18, 19) for d in range(4)], "id": "TE18"},
        {"profesor": "Marcela Perales Moreno (8-9pm)", "horario": [(d, 20, 21) for d in range(4)], "id": "TE19"},
        {"profesor": "Jesus Esquivel Alonso", "horario": [(d, 18, 19) for d in range(4)], "id": "TE20"},
        {"profesor": "Carlos Benito Arriaga Aguilar", "horario": [(d, 20, 21) for d in range(4)], "id": "TE21"},
    ],
    "Dibujo Asistido por Computadora": [
        {"profesor": "Cynthia Maricela Calzoncit Carranza", "horario": [(d, 10, 11) for d in range(4)], "id": "D1"},
        {"profesor": "Laura Villegas Leza (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "D2"},
        {"profesor": "Laura Villegas Leza (1-2pm)", "horario": [(d, 13, 14) for d in range(4)], "id": "D3"},
        {"profesor": "Alejandro Ayala Ramos (2-3pm)", "horario": [(d, 14, 15) for d in range(4)], "id": "D4"},
        {"profesor": "Alejandro Ayala Ramos (3-4pm)", "horario": [(d, 15, 16) for d in range(4)], "id": "D5"},
    ],
    "Metrología y Normalización": [
        {"profesor": "Juan Francisco Tovar Epifanio (7-8am)", "horario": [(d, 7, 8) for d in range(4)], "id": "M1"},
        {"profesor": "Juan Francisco Tovar Epifanio (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "M2"},
        {"profesor": "Pedro Lopez Martinez", "horario": [(d, 10, 11) for d in range(4)], "id": "M3"},
        {"profesor": "Eustaquio Silva Torres (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "M4"},
        {"profesor": "Eustaquio Silva Torres (2-3pm)", "horario": [(d, 14, 15) for d in range(4)], "id": "M5"},
        {"profesor": "Carlos Eduardo Resendiz Galindo", "horario": [(d, 16, 17) for d in range(4)], "id": "M6"},
        {"profesor": "Luis Alejandro Gonzalez Valdez", "horario": [(d, 18, 19) for d in range(4)], "id": "M7"},
    ],
    "Fundamentos de Investigación": [
        {"profesor": "Cristobal Enrique Yeverino Martinez (10-11am)", "horario": [(d, 10, 11) for d in range(4)], "id": "F1"},
        {"profesor": "Cristobal Enrique Yeverino Martinez (11-12pm)", "horario": [(d, 11, 12) for d in range(4)], "id": "F2"},
        {"profesor": "Leticia Urbina Valdes (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "F3"},
        {"profesor": "Leticia Urbina Valdes (1-2pm)", "horario": [(d, 13, 14) for d in range(4)], "id": "F4"},
    ],
    # --- SEMESTRE 2 ---
    "Cálculo Integral": [
        {"profesor": "Víctor Arturo Ferniza Pérez (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "CI1"},
        {"profesor": "Víctor Arturo Ferniza Pérez (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "CI2"},
        {"profesor": "Víctor Arturo Ferniza Pérez (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "CI3"},
        {"profesor": "Felipe De Jesus Mendoza Morales (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "CI4"},
        {"profesor": "Felipe De Jesus Mendoza Morales (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "CI5"},
        {"profesor": "Felipe De Jesus Mendoza Morales (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "CI6"},
        {"profesor": "Felipe De Jesus Mendoza Morales (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CI7"},
        {"profesor": "Silvia Polendo Luis (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "CI8"},
        {"profesor": "Silvia Polendo Luis (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "CI9"},
        {"profesor": "Silvia Polendo Luis (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "CI10"},
        {"profesor": "Silvia Polendo Luis (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CI11"},
        {"profesor": "Silvia Polendo Luis (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CI12"},
        {"profesor": "Narda Lucely Reyes Acosta (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "CI13"},
        {"profesor": "Narda Lucely Reyes Acosta (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CI14"},
        {"profesor": "Narda Lucely Reyes Acosta (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CI15"},
        {"profesor": "J. Santos Valdez Perez (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "CI16"},
        {"profesor": "J. Santos Valdez Perez (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "CI17"},
        {"profesor": "J. Santos Valdez Perez (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CI18"},
        {"profesor": "J. Santos Valdez Perez (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CI19"},
        {"profesor": "Fabio López Campos (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CI20"},
        {"profesor": "Fabio López Campos (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CI21"},
        {"profesor": "Fabio López Campos (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CI22"},
        {"profesor": "Fabio López Campos (1-2pm)", "horario": [(d, 13, 14) for d in range(5)], "id": "CI23"},
        {"profesor": "Erwin Rommel Cerda Leon (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CI24"},
        {"profesor": "Erwin Rommel Cerda Leon (5-6pm)", "horario": [(d, 17, 18) for d in range(5)], "id": "CI25"},
        {"profesor": "Luis Manuel Ferniza Pérez (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CI26"},
        {"profesor": "Luis Manuel Ferniza Pérez (1-2pm)", "horario": [(d, 13, 14) for d in range(5)], "id": "CI27"},
        {"profesor": "Ignacio Dávila Ríos (4-5pm)", "horario": [(d, 16, 17) for d in range(5)], "id": "CI28"},
        {"profesor": "Ignacio Dávila Ríos (7-8pm)", "horario": [(d, 19, 20) for d in range(5)], "id": "CI29"},
        {"profesor": "Miguel Angel Flores Villa (4-5pm)", "horario": [(d, 16, 17) for d in range(5)], "id": "CI30"},
        {"profesor": "Miguel Angel Flores Villa (6-7pm)", "horario": [(d, 18, 19) for d in range(5)], "id": "CI31"},
        {"profesor": "Miguel Angel Flores Villa (9-10pm)", "horario": [(d, 21, 22) for d in range(5)], "id": "CI32"},
    ],
    "Álgebra Lineal": [
        {"profesor": "Juan Angel Sánchez Espinoza (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "AL1"},
        {"profesor": "Juan Angel Sánchez Espinoza (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "AL2"},
        {"profesor": "Juan Angel Sánchez Espinoza (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "AL3"},
        {"profesor": "Juan Angel Sánchez Espinoza (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "AL4"},
        {"profesor": "Juan Francisco Benavides Ramos (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "AL5"},
        {"profesor": "Juan Francisco Benavides Ramos (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "AL6"},
        {"profesor": "Juan Francisco Benavides Ramos (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "AL7"},
        {"profesor": "Romina Denisse Sanchez (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "AL8"},
        {"profesor": "Romina Denisse Sanchez (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "AL9"},
        {"profesor": "Juan Antonio Ruiz Muñiz (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "AL10"},
        {"profesor": "Juan Antonio Ruiz Muñiz (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "AL11"},
        {"profesor": "Jorge Alberto Ruiz Muñiz", "horario": [(d, 11, 12) for d in range(5)], "id": "AL12"},
        {"profesor": "Celina Gaytan Tanguma (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "AL13"},
        {"profesor": "Celina Gaytan Tanguma (1-2pm)", "horario": [(d, 13, 14) for d in range(5)], "id": "AL14"},
        {"profesor": "Celina Gaytan Tanguma (2-3pm)", "horario": [(d, 14, 15) for d in range(5)], "id": "AL15"},
        {"profesor": "Ignacio Dávila Ríos (6-7pm)", "horario": [(d, 18, 19) for d in range(5)], "id": "AL16"},
        {"profesor": "Veronica Martinez Villafuerte", "horario": [(d, 16, 17) for d in range(5)], "id": "AL17"},
        {"profesor": "Justino Barrales Montes (4-5pm)", "horario": [(d, 16, 17) for d in range(5)], "id": "AL18"},
        {"profesor": "Justino Barrales Montes (5-6pm)", "horario": [(d, 17, 18) for d in range(5)], "id": "AL19"},
        {"profesor": "Justino Barrales Montes (6-7pm)", "horario": [(d, 18, 19) for d in range(5)], "id": "AL20"},
    ],
    "Ciencia e Ingeniería de Materiales": [
        {"profesor": "Dolores García De León (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CIM1"},
        {"profesor": "Dolores García De León (12-1pm)", "horario": [(d, 12, 13) for d in range(5)], "id": "CIM2"},
        {"profesor": "Luis Alberto Terrazas Ramos (10-11am)", "horario": [(d, 10, 11) for d in range(5)], "id": "CIM3"},
        {"profesor": "Luis Alberto Terrazas Ramos (11-12pm)", "horario": [(d, 11, 12) for d in range(5)], "id": "CIM4"},
        {"profesor": "Luis Alberto Terrazas Ramos (2-3pm)", "horario": [(d, 14, 15) for d in range(5)], "id": "CIM5"},
        {"profesor": "Raquel Guadalupe Ruiz Moreno", "horario": [(d, 10, 11) for d in range(5)], "id": "CIM6"},
        {"profesor": "Andrea Sanchez Arroyo", "horario": [(d, 15, 16) for d in range(5)], "id": "CIM7"},
        {"profesor": "Socorro Del Carmen Espinoza Cardona (4-5pm)", "horario": [(d, 16, 17) for d in range(5)], "id": "CIM8"},
        {"profesor": "Socorro Del Carmen Espinoza Cardona (6-7pm)", "horario": [(d, 18, 19) for d in range(5)], "id": "CIM9"},
    ],
    "Programación Básica": [
        {"profesor": "Francisco Javier De Leon Macias (7-8am)", "horario": [(d, 7, 8) for d in range(5)], "id": "PB1"},
        {"profesor": "Francisco Javier De Leon Macias (8-9am)", "horario": [(d, 8, 9) for d in range(5)], "id": "PB2"},
        {"profesor": "Leticia Castillo Hernández (9-10am)", "horario": [(d, 9, 10) for d in range(5)], "id": "PB3"},
        {"profesor": "Leticia Castillo Hernández (1-2pm)", "horario": [(d, 13, 14) for d in range(5)], "id": "PB4"},
        {"profesor": "Leticia Castillo Hernández (2-3pm)", "horario": [(d, 14, 15) for d in range(5)], "id": "PB5"},
        {"profesor": "Arturo Alejandro Domínguez Martínez", "horario": [(d, 11, 12) for d in range(5)], "id": "PB6"},
        {"profesor": "Hector Garcia Hernandez (3-4pm)", "horario": [(d, 15, 16) for d in range(5)], "id": "PB7"},
        {"profesor": "Garcia Hernandez Hector (4-5pm)", "horario": [(d, 16, 17) for d in range(5)], "id": "PB8"},
        {"profesor": "Mario Alberto Jáuregui Sánchez (5-6pm)", "horario": [(d, 17, 18) for d in range(5)], "id": "PB9"},
        {"profesor": "Mario Alberto Jáuregui Sánchez (6-7pm)", "horario": [(d, 18, 19) for d in range(5)], "id": "PB10"},
    ],
    "Estadística y Control de Calidad": [
        {"profesor": "Georgina Solis Rodriguez (8-9am)", "horario": [(d, 8, 9) for d in range(4)], "id": "ECC1"},
        {"profesor": "Georgina Solis Rodriguez (9-10am)", "horario": [(d, 9, 10) for d in range(4)], "id": "ECC2"},
        {"profesor": "Federico Zertuche Luis", "horario": [(d, 10, 11) for d in range(4)], "id": "ECC3"},
        {"profesor": "Jose Sirahuen Velez Name (11-12pm)", "horario": [(d, 11, 12) for d in range(4)], "id": "ECC4"},
        {"profesor": "Jose Sirahuen Velez Name (1-2pm)", "horario": [(d, 13, 14) for d in range(4)], "id": "ECC5"},
        {"profesor": "Jose Sirahuen Velez Name (2-3pm)", "horario": [(d, 14, 15) for d in range(4)], "id": "ECC6"},
        {"profesor": "Irma Violeta García Pimentel (11-12pm)", "horario": [(d, 11, 12) for d in range(4)], "id": "ECC7"},
        {"profesor": "Irma Violeta García Pimentel (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "ECC8"},
        {"profesor": "Alma Patricia Lopez De Leon (4-5pm)", "horario": [(d, 16, 17) for d in range(4)], "id": "ECC9"},
        {"profesor": "Alma Patricia Lopez De Leon (6-7pm)", "horario": [(d, 18, 19) for d in range(4)], "id": "ECC10"},
    ],
    "Administración y Contabilidad": [
        {"profesor": "Dalia Veronica Aguillon Padilla", "horario": [(d, 10, 11) for d in range(4)], "id": "AC1"},
        {"profesor": "Patricia Alejandra Fernandez Rangel (11-12pm)", "horario": [(d, 11, 12) for d in range(4)], "id": "AC2"},
        {"profesor": "Patricia Alejandra Fernandez Rangel (12-1pm)", "horario": [(d, 12, 13) for d in range(4)], "id": "AC3"},
        {"profesor": "Martin Rodriguez Contreras (1-2pm)", "horario": [(d, 13, 14) for d in range(4)], "id": "AC4"},
        {"profesor": "Martin Rodriguez Contreras (2-3pm)", "horario": [(d, 14, 15) for d in range(4)], "id": "AC5"},
        {"profesor": "Martin Rodriguez Contreras (3-4pm)", "horario": [(d, 15, 16) for d in range(4)], "id": "AC6"},
        {"profesor": "Martin Rodriguez Contreras (4-5pm)", "horario": [(d, 16, 17) for d in range(4)], "id": "AC7"},
        {"profesor": "Martin Rodriguez Contreras (5-6pm)", "horario": [(d, 17, 18) for d in range(4)], "id": "AC8"},
        {"profesor": "Francisco Alberto Galindo González", "horario": [(d, 17, 18) for d in range(4)], "id": "AC9"},
        {"profesor": "Edgar Felipe Vazquez Siller", "horario": [(d, 19, 20) for d in range(4)], "id": "AC10"},
    ],
    # --- SEMESTRE 3 ---
    "Cálculo Vectorial": [
        {"profesor": "Lucia Marisol Valdes Gonzalez (8-9am)", "horario": [(d,8,9) for d in range(5)], "id":"CV1"},
        {"profesor": "Lucia Marisol Valdes Gonzalez (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"CV2"},
        {"profesor": "Silvia Deyanira Rodriguez Luna (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"CV3"},
        {"profesor": "Silvia Deyanira Rodriguez Luna (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"CV4"},
        {"profesor": "Jose Ignacio Garcia Alvarez (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"CV5"},
        {"profesor": "Jose Ignacio Garcia Alvarez (2-3pm)", "horario": [(d,14,15) for d in range(5)], "id":"CV6"},
        {"profesor": "Jose Ignacio Garcia Alvarez (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"CV7"},
        {"profesor": "Jose Ignacio Garcia Alvarez (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"CV8"},
        {"profesor": "Rene Sanchez Ramos (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"CV9"},
        {"profesor": "Rene Sanchez Ramos (2-3pm)", "horario": [(d,14,15) for d in range(5)], "id":"CV10"},
        {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,14,15) for d in range(5)], "id":"CV11"},
        {"profesor": "Gloria Estela Martinez Montemayor", "horario": [(d,16,17) for d in range(5)], "id":"CV12"},
        {"profesor": "Miguel Angel Flores Villa", "horario": [(d,19,20) for d in range(5)], "id":"CV13"}
    ],
    "Procesos de Fabricación": [
        {"profesor": "Efrain Almanza Casas (8-9am)", "horario": [(d,8,9) for d in range(4)], "id":"PF1"},
        {"profesor": "Efrain Almanza Casas (9-10am)", "horario": [(d,9,10) for d in range(4)], "id":"PF2"},
        {"profesor": "Efrain Almanza Casas (1-2pm)", "horario": [(d,13,14) for d in range(4)], "id":"PF3"},
        {"profesor": "Anabel Azucena Hernandez Cortes", "horario": [(d,13,14) for d in range(4)], "id":"PF4"},
        {"profesor": "Arnoldo Solis Covarrubias (4-5pm)", "horario": [(d,16,17) for d in range(4)], "id":"PF5"},
        {"profesor": "Arnoldo Solis Covarrubias (7-8pm)", "horario": [(d,19,20) for d in range(4)], "id":"PF6"}
    ],
    "Electromagnetismo": [
        {"profesor": "Christian Aldaco González (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"E1"},
        {"profesor": "Christian Aldaco González (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"E2"},
        {"profesor": "Benjamin Arellano Orozco (2-3pm)", "horario": [(d,14,15) for d in range(5)], "id":"E3"},
        {"profesor": "Benjamin Arellano Orozco (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"E4"},
        {"profesor": "Benjamin Arellano Orozco (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"E5"},
        {"profesor": "Benjamin Arellano Orozco (5-6pm)", "horario": [(d,17,18) for d in range(5)], "id":"E6"},
        {"profesor": "Benjamin Arellano Orozco (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"E7"},
        {"profesor": "Benjamin Arellano Orozco (7-8pm)", "horario": [(d,19,20) for d in range(5)], "id":"E8"}
    ],
    "Estática": [
        {"profesor": "Jorge Oyervides Valdez (8-9am)", "horario": [(d,8,9) for d in range(4)], "id":"ES1"},
        {"profesor": "Jorge Oyervides Valdez (9-10am)", "horario": [(d,9,10) for d in range(4)], "id":"ES2"},
        {"profesor": "Jorge Oyervides Valdez (12-1pm)", "horario": [(d,12,13) for d in range(4)], "id":"ES3"},
        {"profesor": "Jorge Oyervides Valdez (5-6pm)", "horario": [(d,17,18) for d in range(4)], "id":"ES4"},
        {"profesor": "Jorge Oyervides Valdez (6-7pm)", "horario": [(d,18,19) for d in range(4)], "id":"ES5"},
        {"profesor": "Leticia Urbina Valdes (10-11am)", "horario": [(d,10,11) for d in range(4)], "id":"ES6"},
        {"profesor": "Leticia Urbina Valdes (11-12pm)", "horario": [(d,11,12) for d in range(4)], "id":"ES7"}
    ],
    "Métodos Numéricos": [
        {"profesor": "Gustavo Lopez Guarin", "horario": [(d,15,16) for d in range(4)], "id":"MN1"},
        {"profesor": "Justino Barrales Montes (3-4pm)", "horario": [(d,15,16) for d in range(4)], "id":"MN2"},
        {"profesor": "Justino Barrales Montes (7-8pm)", "horario": [(d,19,20) for d in range(4)], "id":"MN3"},
        {"profesor": "Justino Barrales Montes (8-9pm)", "horario": [(d,20,21) for d in range(4)], "id":"MN4"},
        {"profesor": "Justino Barrales Montes (9-10pm)", "horario": [(d,21,22) for d in range(4)], "id":"MN5"}
    ],
    "Desarrollo Sustentable": [
        {"profesor": "Fernando Miguel Viesca Farias", "horario": [(d,7,8) for d in range(5)], "id":"DS1"},
        {"profesor": "Virginia Flores Gaytan (8-9am)", "horario": [(d,8,9) for d in range(5)], "id":"DS2"},
        {"profesor": "Virginia Flores Gaytan (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"DS3"},
        {"profesor": "Virginia Flores Gaytan (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"DS4"},
        {"profesor": "Virginia Flores Gaytan (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"DS5"},
        {"profesor": "Aida Isolda Fernández De La Cerda (8-9am)", "horario": [(d,8,9) for d in range(5)], "id":"DS6"},
        {"profesor": "Aida Isolda Fernández De La Cerda (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"DS7"},
        {"profesor": "Marcela Guadalupe Moreno Padilla (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"DS8"},
        {"profesor": "Marcela Guadalupe Moreno Padilla (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"DS9"},
        {"profesor": "Marcela Guadalupe Moreno Padilla (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"DS10"},
        {"profesor": "Alicia Orta Mendoza (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"DS11"},
        {"profesor": "Alicia Orta Mendoza (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"DS12"},
        {"profesor": "Alicia Orta Mendoza (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"DS13"},
        {"profesor": "Alicia Orta Mendoza (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"DS14"},
        {"profesor": "Pedro Angel Gonzalez Barrera (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"DS15"},
        {"profesor": "Pedro Angel Gonzalez Barrera (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"DS16"},
        {"profesor": "Pedro Angel Gonzalez Barrera (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"DS17"},
        {"profesor": "Alexeyevich Flores Sanchez (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"DS18"},
        {"profesor": "Alexeyevich Flores Sanchez (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"DS19"},
        {"profesor": "Manuel Rodarte Carrillo (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"DS20"},
        {"profesor": "Manuel Rodarte Carrillo (2-3pm)", "horario": [(d,14,15) for d in range(5)], "id":"DS21"},
        {"profesor": "Manuel Rodarte Carrillo (5-6pm)", "horario": [(d,17,18) for d in range(5)], "id":"DS22"},
        {"profesor": "Manuel Rodarte Carrillo (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"DS23"},
        {"profesor": "Juan Carlos Loyola Licea", "horario": [(d,15,16) for d in range(5)], "id":"DS24"},
        {"profesor": "Mario Alberto De La Rosa Cepeda (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"DS25"},
        {"profesor": "Mario Alberto De La Rosa Cepeda (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"DS26"},
        {"profesor": "Mario Alberto De La Rosa Cepeda (5-6pm)", "horario": [(d,17,18) for d in range(5)], "id":"DS27"},
        {"profesor": "Mario Alberto De La Rosa Cepeda (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"DS28"},
        {"profesor": "Ramon Andres Durón Ibarra", "horario": [(d,16,17) for d in range(5)], "id":"DS29"},
        {"profesor": "Veronica Amaro Hernandez (5-6pm)", "horario": [(d,17,18) for d in range(5)], "id":"DS30"},
        {"profesor": "Veronica Amaro Hernandez (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"DS31"},
        {"profesor": "Rene Martinez Perez (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"DS32"},
        {"profesor": "Rene Martinez Perez (7-8pm)", "horario": [(d,19,20) for d in range(5)], "id":"DS33"}
    ],
    # --- SEMESTRE 4 ---
    "Ecuaciones Diferenciales": [
        {"profesor": "Ismael Luevano Martinez", "horario": [(d,8,9) for d in range(5)], "id":"ED1"},
        {"profesor": "Romina Denisse Sanchez (8-9am)", "horario": [(d,8,9) for d in range(5)], "id":"ED2"},
        {"profesor": "Romina Denisse Sanchez (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"ED3"},
        {"profesor": "César Iván Cantú", "horario": [(d,9,10) for d in range(5)], "id":"ED4"},
        {"profesor": "Lucia Marisol Valdes Gonzalez (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"ED5"},
        {"profesor": "Lucia Marisol Valdes Gonzalez (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"ED6"},
        {"profesor": "Olivia García Calvillo (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"ED7"},
        {"profesor": "Olivia García Calvillo (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"ED8"},
        {"profesor": "Olivia García Calvillo (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"ED9"},
        {"profesor": "Olivia García Calvillo (2-3pm)", "horario": [(d,14,15) for d in range(5)], "id":"ED10"},
        {"profesor": "Jesus Cantú Perez (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"ED11"},
        {"profesor": "Jesus Cantú Perez (1-2pm)", "horario": [(d,13,14) for d in range(5)], "id":"ED12"},
        {"profesor": "Alicia Guadalupe Del Bosque Martínez", "horario": [(d,13,14) for d in range(5)], "id":"ED13"},
        {"profesor": "Jorge Alberto Ramos Oliveira", "horario": [(d,17,18) for d in range(5)], "id":"ED14"}
    ],
    "Fundamentos de Termodinámica": [
        {"profesor": "Luis Miguel Veloz Pachicano (7-8am)", "horario": [(d,7,8) for d in range(4)], "id":"FT1"},
        {"profesor": "Luis Miguel Veloz Pachicano (11-12pm)", "horario": [(d,11,12) for d in range(4)], "id":"FT2"},
        {"profesor": "Elena Guadalupe Luques Lopez (8-9am)", "horario": [(d,8,9) for d in range(4)], "id":"FT3"},
        {"profesor": "Elena Guadalupe Luques Lopez (1-2pm)", "horario": [(d,13,14) for d in range(4)], "id":"FT4"},
        {"profesor": "Erendira Del Rocio Gamon Perales (10-11am)", "horario": [(d,10,11) for d in range(4)], "id":"FT5"},
        {"profesor": "Erendira Del Rocio Gamon Perales (12-1pm)", "horario": [(d,12,13) for d in range(4)], "id":"FT6"},
        {"profesor": "Edgar Omar Resendiz Flores", "horario": [(d,12,13) for d in range(4)], "id":"FT7"},
        {"profesor": "Massiel Cristina Cisneros Morales (3-4pm)", "horario": [(d,15,16) for d in range(4)], "id":"FT8"},
        {"profesor": "Massiel Cristina Cisneros Morales (6-7pm)", "horario": [(d,18,19) for d in range(4)], "id":"FT9"}
    ],
    "Mecánica de Materiales": [
        {"profesor": "Juan Carlos Cardenas Contreras (7-8am)", "horario": [(0,7,8),(1,7,8),(2,7,8),(3,7,8),(4,7,9)], "id":"MM1"},
        {"profesor": "Juan Carlos Cardenas Contreras (9-10am)", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"MM2"},
        {"profesor": "Juan Carlos Cardenas Contreras (12-1pm)", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,11,13)], "id":"MM3"},
        {"profesor": "Juan Francisco Tovar Epifanio", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,12,14)], "id":"MM4"},
        {"profesor": "Adolfo Galvan Avalos", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,17,19)], "id":"MM5"}
    ],
    "Dinámica": [
        {"profesor": "Claudia Yvonne Franco Martinez", "horario": [(d,8,9) for d in range(4)], "id":"DIN1"},
        {"profesor": "Cipriano Alvarado González (10-11am)", "horario": [(d,10,11) for d in range(4)], "id":"DIN2"},
        {"profesor": "Cipriano Alvarado González (11-12pm)", "horario": [(d,11,12) for d in range(4)], "id":"DIN3"},
        {"profesor": "Cipriano Alvarado González (12-1pm)", "horario": [(d,12,13) for d in range(4)], "id":"DIN4"},
        {"profesor": "Juan Arredondo Valdez", "horario": [(d,17,18) for d in range(4)], "id":"DIN5"},
        {"profesor": "Ismene Guadalupe De La Peña Alcala (7-8pm)", "horario": [(d,19,20) for d in range(4)], "id":"DIN6"},
        {"profesor": "Ismene Guadalupe De La Peña Alcala (8-9pm)", "horario": [(d,20,21) for d in range(4)], "id":"DIN7"}
    ],
    "Análisis de Circuitos Eléctricos": [
        {"profesor": "Iván De Jesús Epifanio López (8-9am)", "horario": [(0,8,9),(1,8,9),(2,8,9),(3,8,9),(4,7,9)], "id":"ACE1"},
        {"profesor": "Iván De Jesús Epifanio López (10-11am)", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,10,12)], "id":"ACE2"},
        {"profesor": "Fernando Aguilar Gaona", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"ACE3"},
        {"profesor": "Alejandro Martínez Hernández", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"ACE4"},
        {"profesor": "Horacio Tolentino Quilantan", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"ACE5"},
        {"profesor": "Josue Isrrael Najera Diaz (4-5pm)", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"ACE6"},
        {"profesor": "Josue Isrrael Najera Diaz (6-7pm)", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,18,20)], "id":"ACE7"},
        {"profesor": "Josue Isrrael Najera Diaz (8-9pm)", "horario": [(0,20,21),(1,20,21),(2,20,21),(3,20,21),(4,20,22)], "id":"ACE8"},
        {"profesor": "Obed Ramírez Gómez", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"ACE9"}
    ],
    "Taller de Investigación I": [
        {"profesor": "Juana Maria Dueñaz Reyes", "horario": [(d,7,8) for d in range(4)], "id":"TI1"},
        {"profesor": "Fernando Alfonso Ruiz Moreno (7-8am)", "horario": [(d,7,8) for d in range(4)], "id":"TI2"},
        {"profesor": "Fernando Alfonso Ruiz Moreno (8-9am)", "horario": [(d,8,9) for d in range(4)], "id":"TI3"},
        {"profesor": "Fernando Alfonso Ruiz Moreno (9-10am)", "horario": [(d,9,10) for d in range(4)], "id":"TI4"},
        {"profesor": "Fernando Alfonso Ruiz Moreno (10-11am)", "horario": [(d,10,11) for d in range(4)], "id":"TI5"},
        {"profesor": "Luis Manuel Navarro Huitron", "horario": [(d,13,14) for d in range(4)], "id":"TI6"}
    ],
    # --- SEMESTRE 5 ---
    "Máquinas Eléctricas": [
        {"profesor": "Gabriel Allende Sancho", "horario": [(d,8,9) for d in range(5)], "id":"ME1"},
        {"profesor": "Mario Alberto Ponce Llamas (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"ME2"},
        {"profesor": "Mario Alberto Ponce Llamas (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"ME3"},
        {"profesor": "Alejandra Hernandez Rodriguez", "horario": [(d,15,16) for d in range(5)], "id":"ME4"},
        {"profesor": "Daniel Ruiz Calderon", "horario": [(d,17,18) for d in range(5)], "id":"ME5"}
    ],
    "Electrónica Analógica": [
        {"profesor": "Fernando Aguilar Gaona (9-10am)", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"EA1"},
        {"profesor": "Fernando Aguilar Gaona (12-1pm)", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,11,13)], "id":"EA2"},
        {"profesor": "Rolando Rodriguez Pimentel", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"EA3"},
        {"profesor": "Joaquin Antonio Alvarado Bustos (10-11am)", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,9,11)], "id":"EA4"},
        {"profesor": "Joaquin Antonio Alvarado Bustos (11-12pm)", "horario": [(0,11,12),(1,11,12),(2,11,12),(3,11,12),(4,11,13)], "id":"EA5"}
    ],
    "Mecanismos": [
        {"profesor": "Cipriano Alvarado González", "horario": [(d,9,10) for d in range(5)], "id":"MEC1"},
        {"profesor": "Julian Javier Hernandez De La Rosa (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"MEC2"},
        {"profesor": "Julian Javier Hernandez De La Rosa (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"MEC3"},
        {"profesor": "Julian Javier Hernandez De La Rosa (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"MEC4"}
    ],
    "Análisis de Fluidos": [
        {"profesor": "Edgar Benito Martinez Mercado (7-8am)", "horario": [(d,7,8) for d in range(4)], "id":"AF1"},
        {"profesor": "Edgar Benito Martinez Mercado (11-12pm)", "horario": [(d,11,12) for d in range(4)], "id":"AF2"},
        {"profesor": "Edgar Benito Martinez Mercado (1-2pm)", "horario": [(d,13,14) for d in range(4)], "id":"AF3"},
        {"profesor": "Luis Alejandro Gonzalez Valdez (4-5pm)", "horario": [(d,16,17) for d in range(4)], "id":"AF4"},
        {"profesor": "Luis Alejandro Gonzalez Valdez (7-8pm)", "horario": [(d,19,20) for d in range(4)], "id":"AF5"},
        {"profesor": "Ignacio Javier González Ordaz (6-7pm)", "horario": [(d,18,19) for d in range(4)], "id":"AF6"},
        {"profesor": "Ignacio Javier González Ordaz (7-8pm)", "horario": [(d,19,20) for d in range(4)], "id":"AF7"}
    ],
    "Taller de Investigación II": [
        {"profesor": "Ada Karina Velarde Sanchez", "horario": [(d,7,8) for d in range(4)], "id":"TI2_1"},
        {"profesor": "Juana Maria Dueñaz Reyes", "horario": [(d,8,9) for d in range(4)], "id":"TI2_2"},
        {"profesor": "Ma. Elida Zavala Torres (5-6pm)", "horario": [(d,17,18) for d in range(4)], "id":"TI2_3"},
        {"profesor": "Ma. Elida Zavala Torres (6-7pm)", "horario": [(d,18,19) for d in range(4)], "id":"TI2_4"}
    ],
    "Programación Avanzada": [
        {"profesor": "Juan Gilberto Navarro Rodriguez (7-8am)", "horario": [(0,7,8),(1,7,8),(2,7,8),(3,7,8),(4,7,9)], "id":"PA1"},
        {"profesor": "Juan Gilberto Navarro Rodriguez (1-2pm)", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,12,14)], "id":"PA2"},
        {"profesor": "Olga Lidia Vidal Vazquez (8-9am)", "horario": [(0,8,9),(1,8,9),(2,8,9),(3,8,9),(4,8,10)], "id":"PA3"},
        {"profesor": "Olga Lidia Vidal Vazquez (2-3pm)", "horario": [(0,14,15),(1,14,15),(2,14,15),(3,14,15),(4,13,15)], "id":"PA4"},
        {"profesor": "Yolanda Mexicano Reyes (9-10am)", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,8,10)], "id":"PA5"},
        {"profesor": "Yolanda Mexicano Reyes (10-11am)", "horario": [(0,10,11),(1,10,11),(2,10,11),(3,10,11),(4,10,12)], "id":"PA6"},
        {"profesor": "Yolanda Mexicano Reyes (12-1pm)", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"PA7"},
        {"profesor": "Martha Patricia Piña Villanueva (11-12pm)", "horario": [(0,11,12),(1,11,12),(2,11,12),(3,11,12),(4,10,12)], "id":"PA8"},
        {"profesor": "Martha Patricia Piña Villanueva (12-1pm)", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"PA9"},
        {"profesor": "Alfredo Salazar Garcia", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,16,18)], "id":"PA10"}
    ],
    # --- SEMESTRE 6 ---
    "Electrónica de Potencia Aplicada": [
        {"profesor": "Iván De Jesús Epifanio López", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"EPA1"},
        {"profesor": "Alejandro Martínez Hernández", "horario": [(0,16,17),(1,16,17),(2,16,17),(3,16,17),(4,16,18)], "id":"EPA2"}
    ],
    "Instrumentación": [
        {"profesor": "Francisco Agustin Vazquez Esquivel (8-9am)", "horario": [(d,8,9) for d in range(5)], "id":"INS1"},
        {"profesor": "Francisco Agustin Vazquez Esquivel (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"INS2"},
        {"profesor": "Cecilia Mendoza Rivas", "horario": [(d,11,12) for d in range(5)], "id":"INS3"},
        {"profesor": "Neider Gonzalez Roblero", "horario": [(d,15,16) for d in range(5)], "id":"INS4"}
    ],
    "Diseño de Elementos Mecánicos": [
        {"profesor": "Nestor Roberto Saavedra Camacho", "horario": [(d,7,8) for d in range(5)], "id":"DEM1"},
        {"profesor": "Lourdes Guadalupe Adame Oviedo", "horario": [(d,10,11) for d in range(5)], "id":"DEM2"},
        {"profesor": "Juan Antonio Guerrero Hernández (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"DEM3"},
        {"profesor": "Juan Antonio Guerrero Hernández (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"DEM4"}
    ],
    "Electrónica Digital": [
        {"profesor": "Karina Diaz Rosas", "horario": [(d,10,11) for d in range(5)], "id":"EDG1"},
        {"profesor": "Francisco Flores Sanmiguel", "horario": [(d,12,13) for d in range(5)], "id":"EDG2"},
        {"profesor": "Ewald Fritsche Ramírez", "horario": [(d,16,17) for d in range(5)], "id":"EDG3"},
        {"profesor": "Miguel Maldonado Leza", "horario": [(d,20,22) for d in range(5)], "id":"EDG4"} # 8-10pm asumiendo 2 horas diarias o es error? Puse 2hrs
    ],
    "Vibraciones Mecánicas": [
        {"profesor": "Ruben Flores Campos (7-8am)", "horario": [(d,7,8) for d in range(5)], "id":"VM1"},
        {"profesor": "Ruben Flores Campos (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"VM2"},
        {"profesor": "Ruben Flores Campos (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"VM3"},
        {"profesor": "Ruben Flores Campos (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"VM4"},
        {"profesor": "Juan Carlos Anaya Zavaleta", "horario": [(d,15,16) for d in range(5)], "id":"VM5"},
        {"profesor": "Luis Uriel García Bustos (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"VM6"},
        {"profesor": "Luis Uriel García Bustos (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"VM7"},
        {"profesor": "Erendira Guadalupe Reyna Valdes", "horario": [(d,19,20) for d in range(5)], "id":"VM8"}
    ],
    "Administración del Mantenimiento": [
        {"profesor": "Juan Manuel Saucedo Alonso", "horario": [(d,8,9) for d in range(4)], "id":"ADM1"},
        {"profesor": "Iván De Jesús Contreras Silva", "horario": [(d,10,11) for d in range(4)], "id":"ADM2"},
        {"profesor": "Orquidea Esmeralda Velarde Sánchez (11-12pm)", "horario": [(d,11,12) for d in range(4)], "id":"ADM3"},
        {"profesor": "Orquidea Esmeralda Velarde Sánchez (12-1pm)", "horario": [(d,12,13) for d in range(4)], "id":"ADM4"},
        {"profesor": "Cesar Humberto Avendaño Malacara (7-8pm)", "horario": [(d,19,20) for d in range(4)], "id":"ADM5"},
        {"profesor": "Cesar Humberto Avendaño Malacara (8-9pm)", "horario": [(d,20,21) for d in range(4)], "id":"ADM6"}
    ],
    # --- SEMESTRE 7 ---
    "Manufactura Avanzada": [
        {"profesor": "Ana Gabriela Gomez Muñoz (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"MA1"},
        {"profesor": "Ana Gabriela Gomez Muñoz (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"MA2"},
        {"profesor": "Maria Del Socorro Marines Leal (12-1pm)", "horario": [(d,12,13) for d in range(5)], "id":"MA3"},
        {"profesor": "Maria Del Socorro Marines Leal (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"MA4"},
        {"profesor": "Maria Del Socorro Marines Leal (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"MA5"}
    ],
    "Diseño Asistido por Computadora": [
        {"profesor": "José Santos Avendaño Méndez", "horario": [(d,9,10) for d in range(5)], "id":"DAC1"},
        {"profesor": "Ana Laura Saucedo Jimenez", "horario": [(d,10,11) for d in range(5)], "id":"DAC2"},
        {"profesor": "Juan Carlos Anaya Zavaleta", "horario": [(d,16,17) for d in range(5)], "id":"DAC3"},
        {"profesor": "Luis Uriel García Bustos (7-8pm)", "horario": [(d,19,20) for d in range(5)], "id":"DAC4"},
        {"profesor": "Luis Uriel García Bustos (8-9pm)", "horario": [(d,20,21) for d in range(5)], "id":"DAC5"}
    ],
    "Dinámica de Sistemas": [
        {"profesor": "Karla Ivonne Fernandez Ramirez", "horario": [(d,11,12) for d in range(5)], "id":"DSYS1"},
        {"profesor": "Gerardo Jarquín Hernández", "horario": [(d,13,14) for d in range(5)], "id":"DSYS2"}
    ],
    "Circuitos Hidráulicos y Neumáticos": [
        {"profesor": "Luis Rey Santos Saucedo (1-2pm)", "horario": [(0,13,14),(1,13,14),(2,13,14),(3,13,14),(4,13,15)], "id":"CHN1"},
        {"profesor": "Luis Rey Santos Saucedo (5-6pm)", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,16,18)], "id":"CHN2"},
        {"profesor": "Cecilia Mendoza Rivas", "horario": [(0,14,15),(1,14,15),(2,14,15),(3,14,15),(4,14,16)], "id":"CHN3"},
        {"profesor": "Manuel Enrique Sandoval Lopez", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,17,19)], "id":"CHN4"}
    ],
    "Mantenimiento": [
        {"profesor": "Jose Maria Resendiz Vielma (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"MANT1"},
        {"profesor": "Jose Maria Resendiz Vielma (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"MANT2"},
        {"profesor": "Luis Gerardo Sanchez Chavez (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"MANT3"},
        {"profesor": "Luis Gerardo Sanchez Chavez (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"MANT4"},
        {"profesor": "Luis Gerardo Sanchez Chavez (7-8pm)", "horario": [(d,19,20) for d in range(5)], "id":"MANT5"},
        {"profesor": "Francisco Jesus Ramos Garcia", "horario": [(d,17,18) for d in range(5)], "id":"MANT6"},
        {"profesor": "Pedro Celedonio Lopez Lara", "horario": [(d,20,21) for d in range(5)], "id":"MANT7"}
    ],
    "Microcontroladores": [
        {"profesor": "Pedro Quintanilla Contreras", "horario": [(d,11,12) for d in range(5)], "id":"MICRO1"},
        {"profesor": "Jozef Jesus Reyes Reyna", "horario": [(d,17,18) for d in range(5)], "id":"MICRO2"}
    ],
    # --- SEMESTRE 8 ---
    "Formulación y Evaluación de Proyectos": [
        {"profesor": "Jose Ignacio Gonzalez Delgado (7-8am)", "horario": [(0,7,8),(1,7,8),(2,7,8)], "id":"FEP1"},
        {"profesor": "Jose Ignacio Gonzalez Delgado (10-11am)", "horario": [(0,10,11),(1,10,11),(2,10,11)], "id":"FEP2"},
        {"profesor": "Jose Ignacio Gonzalez Delgado (7-8pm)", "horario": [(0,19,20),(1,19,20),(2,19,20)], "id":"FEP3"},
        {"profesor": "Nadia Patricia Ramirez Santillan", "horario": [(0,8,9),(1,8,9),(2,8,9)], "id":"FEP4"},
        {"profesor": "Perla Magdalena Garcia Her", "horario": [(0,11,12),(1,11,12),(2,11,12)], "id":"FEP5"},
        {"profesor": "Jackeline Elizabeth Fernandez Flores", "horario": [(0,18,19),(1,18,19),(2,18,19)], "id":"FEP6"}
    ],
    "Controladores Lógicos Programables": [
        {"profesor": "Ana Gabriela Gomez Muñoz (8-9am)", "horario": [(d,8,9) for d in range(5)], "id":"PLC1"},
        {"profesor": "Ana Gabriela Gomez Muñoz (11-12pm)", "horario": [(d,11,12) for d in range(5)], "id":"PLC2"}
    ],
    "Control": [
        {"profesor": "Cesar Gerardo Martinez Sanchez", "horario": [(0,9,10),(1,9,10),(2,9,10),(3,9,10),(4,9,11)], "id":"CTRL1"},
        {"profesor": "Jesus Guerrero Contreras", "horario": [(0,15,16),(1,15,16),(2,15,16),(3,15,16),(4,15,17)], "id":"CTRL2"},
        {"profesor": "Ricardo Martínez Alvarado", "horario": [(0,17,18),(1,17,18),(2,17,18),(3,17,18),(4,17,19)], "id":"CTRL3"},
        {"profesor": "Isaac Ruiz Ramos", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"CTRL4"}
    ],
    "Sistemas Avanzados de Manufactura": [
        {"profesor": "Ada Karina Velarde Sanchez (9-10am)", "horario": [(d,9,10) for d in range(5)], "id":"SAM1"},
        {"profesor": "Ada Karina Velarde Sanchez (10-11am)", "horario": [(d,10,11) for d in range(5)], "id":"SAM2"},
        {"profesor": "Maria Del Socorro Marines Leal", "horario": [(d,17,18) for d in range(5)], "id":"SAM3"}
    ],
    "Redes Industriales": [
        {"profesor": "Francisco Flores Sanmiguel (3-4pm)", "horario": [(d,15,16) for d in range(5)], "id":"RI1"},
        {"profesor": "Francisco Flores Sanmiguel (4-5pm)", "horario": [(d,16,17) for d in range(5)], "id":"RI2"},
        {"profesor": "Francisco Flores Sanmiguel (5-6pm)", "horario": [(d,17,18) for d in range(5)], "id":"RI3"},
        {"profesor": "Neider Gonzalez Roblero (6-7pm)", "horario": [(d,18,19) for d in range(5)], "id":"RI4"},
        {"profesor": "Neider Gonzalez Roblero (7-8pm)", "horario": [(d,19,20) for d in range(5)], "id":"RI5"}
    ],
    # --- SEMESTRE 9 ---
    "Robótica": [
        {"profesor": "Gerardo Jarquín Hernández (7-8am)", "horario": [(d,7,8) for d in range(5)], "id":"ROB1"},
        {"profesor": "Gerardo Jarquín Hernández (2-3pm)", "horario": [(d,14,15) for d in range(5)], "id":"ROB2"}
    ],
    "Tópicos Selectos de Automatización Industrial": [
        {"profesor": "Ana Gabriela Gomez Muñoz", "horario": [(0,12,13),(1,12,13),(2,12,13),(3,12,13),(4,12,14)], "id":"TS1"},
        {"profesor": "Victor Manuel Retana Castillo (6-7pm)", "horario": [(0,18,19),(1,18,19),(2,18,19),(3,18,19),(4,17,19)], "id":"TS2"},
        {"profesor": "Victor Manuel Retana Castillo (8-9pm)", "horario": [(0,20,21),(1,20,21),(2,20,21),(3,20,21),(4,20,22)], "id":"TS3"},
        {"profesor": "Luis Rey Santos Saucedo", "horario": [(0,19,20),(1,19,20),(2,19,20),(3,19,20),(4,19,21)], "id":"TS4"}
    ]
}

# -----------------------------------------------------------------------------
# ESTADO DE LA APLICACIÓN (SESSION STATE)
# -----------------------------------------------------------------------------
if 'materias_seleccionadas' not in st.session_state:
    st.session_state.materias_seleccionadas = []
if 'rango_hora' not in st.session_state:
    st.session_state.rango_hora = (7, 22)
if 'prefs' not in st.session_state:
    st.session_state.prefs = {}
if 'step' not in st.session_state:
    st.session_state.step = 1

# -----------------------------------------------------------------------------
# FUNCIONES LÓGICAS
# -----------------------------------------------------------------------------
def traslape(horario1, horario2):
    for h1 in horario1:
        for h2 in horario2:
            if h1[0] == h2[0]: # Mismo día
                # h1 inicia antes de que h2 termine Y h1 termina despues de que h2 inicie
                if h1[1] < h2[2] and h1[2] > h2[1]:
                    return True
    return False

def generar_combinaciones(materias, rango, prefs):
    pool = []
    for mat in materias:
        if mat not in oferta_academica: continue
        opciones = []
        for sec in oferta_academica[mat]:
            # Filtro Preferencia
            key = f"{mat}_{sec['profesor']}"
            puntos = prefs.get(key, 50)
            if puntos == 0: continue
            
            # Filtro Horario
            dentro = True
            for h in sec['horario']:
                if h[1] < rango[0] or h[2] > rango[1]:
                    dentro = False; break
            if dentro:
                s = sec.copy()
                s['materia'] = mat
                s['score'] = puntos
                opciones.append(s)
        if opciones: pool.append(opciones)
        else: return [], f"No hay horarios válidos para {mat}"
    
    if not pool: return [], "Selecciona materias."
    
    combos = list(itertools.product(*pool))
    validos = []
    
    for c in combos:
        ok = True
        score = 0
        for i in range(len(c)):
            score += c[i]['score']
            for j in range(i+1, len(c)):
                if traslape(c[i]['horario'], c[j]['horario']):
                    ok = False; break
            if not ok: break
        if ok: validos.append((score, c))
    
    validos.sort(key=lambda x: x[0], reverse=True)
    return validos, "OK"

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TecNM - Instituto Tecnológico de Saltillo', 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Horario Generado - Enero Junio 2026', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pag {self.page_no()}', 0, 0, 'C')

def create_pdf(horario):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    dias = {0:"Lunes", 1:"Martes", 2:"Miercoles", 3:"Jueves", 4:"Viernes"}
    
    # Encabezados
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(70, 10, "Materia", 1, 0, 'C', 1)
    pdf.cell(60, 10, "Profesor", 1, 0, 'C', 1)
    pdf.cell(60, 10, "Horario", 1, 1, 'C', 1)
    
    for clase in horario:
        # Formatear horario
        h_str = ""
        # Agrupar dias
        for d in range(5):
            horas = [x for x in clase['horario'] if x[0]==d]
            if horas:
                h_str += f"{dias[d][:3]}:{horas[0][1]}-{horas[0][2]} "
        
        pdf.cell(70, 10, clase['materia'][:35], 1)
        pdf.cell(60, 10, clase['profesor'].split('(')[0][:30], 1)
        pdf.cell(60, 10, h_str, 1, 1)
        
    return pdf.output(dest='S').encode('latin-1')

# -----------------------------------------------------------------------------
# INTERFAZ DE USUARIO
# -----------------------------------------------------------------------------
st.title("🐯 Generador de Horarios ITS")
st.markdown("### Ingeniería Mecatrónica")

# --- PASO 1: SELECCIÓN DE MATERIAS ---
st.sidebar.header("1. Selecciona Materias")
todas_materias = []
for sem, lista in database["Ingeniería Mecatrónica"].items():
    with st.sidebar.expander(sem, expanded=False):
        sel = st.multiselect(f"Materias {sem}", lista)
        todas_materias.extend(sel)

st.session_state.materias_seleccionadas = todas_materias

# --- PASO 2: FILTROS ---
if st.session_state.materias_seleccionadas:
    st.header("2. Preferencias")
    
    col1, col2 = st.columns(2)
    with col1:
        rango = st.slider("Rango de Hora", 7, 22, (7, 15))
    
    st.subheader("Califica a los Maestros")
    for mat in st.session_state.materias_seleccionadas:
        if mat in oferta_academica:
            with st.expander(f"Profesor para {mat}", expanded=True):
                profes = sorted(list(set([p['profesor'] for p in oferta_academica[mat]])))
                for p in profes:
                    k = f"{mat}_{p}"
                    val = st.radio(p, ["✅", "➖", "❌"], index=1, key=k, horizontal=True)
                    if val == "✅": st.session_state.prefs[k] = 100
                    elif val == "❌": st.session_state.prefs[k] = 0
                    else: st.session_state.prefs[k] = 50

    if st.button("GENERAR HORARIOS", type="primary"):
        res, msg = generar_combinaciones(st.session_state.materias_seleccionadas, rango, st.session_state.prefs)
        
        if not res and msg != "OK":
            st.error(msg)
        else:
            st.success(f"Se encontraron {len(res)} opciones.")
            
            for i, (score, horario) in enumerate(res[:10]):
                with st.container():
                    st.markdown(f"**Opción {i+1}** (Puntaje: {score})")
                    df = []
                    dias_map = {0:"Lun", 1:"Mar", 2:"Mie", 3:"Jue", 4:"Vie"}
                    for clase in horario:
                        h_txt = ""
                        for h in clase['horario']:
                            h_txt += f"{dias_map[h[0]]} {h[1]}-{h[2]} "
                        df.append({"Materia": clase['materia'], "Profesor": clase['profesor'], "Horario": h_txt})
                    
                    st.table(pd.DataFrame(df))
                    
                    # PDF
                    pdf_bytes = create_pdf(horario)
                    st.download_button(f"📥 Descargar PDF Opción {i+1}", data=pdf_bytes, file_name=f"Horario_{i+1}.pdf", mime='application/pdf')
                    st.divider()

else:
    st.info("👈 Selecciona materias en el menú de la izquierda para comenzar.")
