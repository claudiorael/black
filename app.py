import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Defensa de Grado - Mokkita", page_icon="🦔", layout="wide")

# --- ESTILOS CSS AVANZADOS (UI MÁS LIMPIA Y MOKKITA ANIMADO) ---
st.markdown("""
<style>
    /* Fondo con gradiente moderno y oscuro */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #ffffff;
    }
    
    /* Contenedores translúcidos */
    .st-emotion-cache-1r6slb0, .st-emotion-cache-1v0mbdj {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
    }

    /* Ocultar barra superior y pie de página de Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Botones más grandes, redondeados e interactivos */
    .stButton>button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        border: none;
        border-radius: 30px;
        color: #1a1a1a !important;
        font-weight: 800;
        transition: all 0.3s ease;
        height: 60px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0, 201, 255, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 201, 255, 0.6);
    }

    /* Modificar los cuadros de subida de archivos (menos formulario, más botón) */
    .stFileUploader>div>div {
        background: rgba(0,0,0,0.2) !important;
        border-radius: 15px !important;
        border: 2px dashed rgba(255,255,255,0.3) !important;
    }

    /* ANIMACIÓN DE MOKKITA FLOTANTE EN LA ESQUINA */
    @keyframes flotar {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }
    .mokkita-bot {
        position: fixed;
        bottom: 30px;
        right: 30px;
        font-size: 70px;
        animation: flotar 3s ease-in-out infinite;
        z-index: 9999;
        cursor: pointer;
        text-shadow: 0px 10px 20px rgba(0,0,0,0.5);
    }
    .mokkita-dialogo {
        position: fixed;
        bottom: 120px;
        right: 40px;
        background: rgba(255,255,255,0.9);
        color: #000;
        padding: 10px 15px;
        border-radius: 15px;
        font-weight: bold;
        z-index: 9998;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
    }
    .mokkita-bot:hover + .mokkita-dialogo {
        opacity: 1;
    }
</style>

<!-- Widget HTML inyectado de Mokkita -->
<div class="mokkita-bot">🦔</div>
<div class="mokkita-dialogo">¡Hola! Soy Mokkita.<br>Sube tu trabajo aquí.</div>
""", unsafe_allow_html=True)

# --- ARCHIVOS DE CONFIGURACIÓN LOCAL ---
STATS_FILE = "mokkita_stats.json"
PROMPT_FILE = "mokkita_prompt.json"

def registrar_estadistica(usuario, accion):
    registro = {"usuario": usuario, "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "accion": accion}
    datos = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f: datos = json.load(f)
    datos.append(registro)
    with open(STATS_FILE, "w") as f: json.dump(datos, f)

# Prompt por defecto muy afinado a tu contexto
PROMPT_POR_DEFECTO = """Eres Mokkita, un erizo intelectual con lentes que actúa como profesor supervisor clínico. 
Tu tarea es evaluar el trabajo de defensa de grado del estudiante.
Evalúa la articulación teórica (especialmente si usa constructivismo intersubjetivo o dinámica relacional) y la coherencia del análisis del caso.
Estructura:
1. 🎯 VEREDICTO DE MOKKITA
2. ✅ PUNTOS FUERTES
3. 🛠️ ÁREAS DE MEJORA
4. 💡 RECOMENDACIÓN CLÍNICA"""

def obtener_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r") as f: return json.load(f).get("prompt", PROMPT_POR_DEFECTO)
    return PROMPT_POR_DEFECTO

def guardar_prompt(nuevo_prompt):
    with open(PROMPT_FILE, "w") as f: json.dump({"prompt": nuevo_prompt}, f)

# --- LOGIN ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state: st.session_state["usuario_actual"] = None

def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Plataforma Mokkita</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #a8b2d1;'>Defensa de Grado & Análisis Clínico</p><br>", unsafe_allow_html=True)
        
        usuario = st.text_input("👤 Usuario").strip().lower()
        clave = st.text_input("🔑 Contraseña", type="password")
        if st.button("Ingresar al Portal"):
            try:
                usuarios_permitidos = st.secrets["usuarios"]
                if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == clave:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = usuario
                    registrar_estadistica(usuario, "Login")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")
            except KeyError:
                st.error("Error en secrets.")

# --- APLICACIÓN PRINCIPAL ---
def mostrar_aplicacion():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario_actual'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        registrar_estadistica(st.session_state["usuario_actual"], "Logout")
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = None
        st.rerun()

    if st.session_state["usuario_actual"] == "claudio":
        tab1, tab2 = st.tabs(["📝 Análisis Trabajo Final Defensa de Grado", "⚙️ Dashboard Admin (Oculto)"])
    else:
        tab1, = st.tabs(["📝 Análisis Trabajo Final Defensa de Grado"])

    # --- PESTAÑA 1: REVISIÓN ---
    with tab1:
        st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Análisis Trabajo Final Defensa de Grado</h2>", unsafe_allow_html=True)
        
        col_opciones, col_archivos = st.columns([1, 2])
        
        with col_opciones:
            st.markdown("### 🎛️ Parámetros")
            nivel_teorico = st.slider("Exigencia Teórica", 1, 5, 4)
            enfoque_feedback = st.selectbox("Personalidad de Mokkita", ["Académico y Estricto", "Constructivo", "Directo e Irónico"])
            
        with col_archivos:
            st.markdown("### 📄 Documentos")
            archivo_trabajo = st.file_uploader("Sube el Trabajo del Estudiante (Requerido)", type=["pdf", "txt", "docx"])
            with st.expander("Opcional: Subir Pauta o Autor de referencia"):
                archivo_autor = st.file_uploader("Material Base", type=["pdf", "txt"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        if archivo_trabajo:
            if st.button("Iniciar Evaluación con Mokkita"):
                registrar_estadistica(st.session_state["usuario_actual"], "Evaluación Generada")
                
                with st.spinner("Mokkita está leyendo meticulosamente tu trabajo..."):
                    archivos_temporales = []
                    archivos_gemini = []
                    try:
                        def procesar_archivo(archivo):
                            if not archivo: return None
                            ext = archivo.name.split('.')[-1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                                tmp.write(archivo.read())
                                rutatmp = tmp.name
                                archivos_temporales.append(rutatmp)
                            file_g = genai.upload_file(rutatmp)
                            archivos_gemini.append(file_g)
                            while file_g.state.name == 'PROCESSING':
                                time.sleep(2)
                                file_g = genai.get_file(file_g.name)
                            return file_g

                        g_trabajo = procesar_archivo(archivo_trabajo)
                        g_autor = procesar_archivo(archivo_autor)

                        # Armamos las instrucciones dinámicas
                        prompt_base = obtener_prompt()
                        instrucciones = f"{prompt_base}\n\nTono solicitado: {enfoque_feedback}.\nNivel de exigencia (1-5): {nivel_teorico}."
                        
                        modelo = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=instrucciones)
                        
                        contenido_a_enviar = [g_trabajo]
                        texto_solicitud = "Analiza este trabajo de grado."
                        if g_autor:
                            contenido_a_enviar.insert(0, g_autor)
                            texto_solicitud = "Analiza el trabajo del estudiante comparándolo con el material del autor adjunto."
                        
                        contenido_a_enviar.append(texto_solicitud)
                        
                        respuesta = modelo.generate_content(contenido_a_enviar)
                        
                        st.success("✨ ¡Análisis completado!")
                        with st.chat_message("Mokkita", avatar="🦔"):
                            st.markdown(respuesta.text)
                            st.download_button("💾 Descargar Evaluación Completa", respuesta.text, file_name=f"Evaluacion_Grado_{st.session_state['usuario_actual']}.md")
                            
                    except Exception as e:
                        st.error(f"Error de procesamiento: {e}")
                    finally:
                        for f_g in archivos_gemini:
                            try: genai.delete_file(f_g.name)
                            except: pass
                        for f_tmp in archivos_temporales:
                            if os.path.exists(f_tmp): os.remove(f_tmp)

    # --- PESTAÑA 2: ADMIN ---
    if st.session_state["usuario_actual"] == "claudio":
        with tab2:
            st.header("Centro de Mando Administrativo")
            
            st.subheader("🧠 Modificar el Cerebro de Mokkita")
            st.info("Aquí puedes reescribir las instrucciones base que Gemini usa para actuar como Mokkita. Los cambios aplican inmediatamente para todos.")
            prompt_actual = obtener_prompt()
            nuevo_prompt = st.text_area("Instrucciones del Sistema (System Prompt)", value=prompt_actual, height=200)
            
            if st.button("Guardar Nueva Personalidad"):
                guardar_prompt(nuevo_prompt)
                st.success("¡El cerebro de Mokkita ha sido actualizado con éxito!")

            st.markdown("---")
            st.subheader("📊 Estadísticas de Uso")
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    st.dataframe(json.load(f), use_container_width=True)
            else:
                st.write("Aún no hay datos.")

# --- INICIO ---
if not st.session_state["autenticado"]: mostrar_login()
else: mostrar_aplicacion()
