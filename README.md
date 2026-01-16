# 🦅 Horario ITS - Plataforma de Planeación Académica

**Horario ITS** es una aplicación web interactiva desarrollada en Python diseñada para optimizar el proceso de selección de carga académica para estudiantes de Ingeniería Mecatrónica. La herramienta soluciona la complejidad de coordinar horarios, detectar traslapes y evaluar la calidad docente mediante inteligencia colectiva.

## 🚀 Características Principales

* **Generador de Horarios Inteligente:** Algoritmo combinatorio que detecta automáticamente traslapes de horas y genera todas las opciones viables.
* **Base de Datos en Tiempo Real:** Integración con Google Sheets API para persistencia de datos.
* **Sistema "Waze Académico":** Los usuarios pueden reportar en tiempo real grupos cerrados para alertar a otros estudiantes.
* **Evaluación Docente (Crowdsourcing):** Sistema de reseñas y calificaciones anónimas para profesores.
* **Exportación PDF:** Generación automática de la propuesta de horario en formato oficial.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.9+
* **Frontend/Framework:** Streamlit
* **Backend/Data:** Pandas, NumPy
* **Base de Datos:** Google Sheets API (gspread + Google Cloud Platform)
* **Reportes:** FPDF para generación de documentos
* **Despliegue:** Streamlit Community Cloud

## 🔧 Instalación Local

Si deseas correr este proyecto en tu máquina local:

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/tu-usuario/horarios-mecatronica.git](https://github.com/tu-usuario/horarios-mecatronica.git)
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configura los secretos de Google Cloud en `.streamlit/secrets.toml`.
4.  Ejecuta la aplicación:
    ```bash
    streamlit run app.py
    ```

## 📈 Impacto
Actualmente utilizada por la comunidad estudiantil del ITS para el periodo Ene-Jun 2026, facilitando la toma de decisiones basada en datos reales.

---
*Desarrollado por Néstor Alexis Piña Rodríguez - Ing. Mecatrónica*
