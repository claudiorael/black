import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
# Forzamos que la barra lateral empiece abierta (expanded)
st.set_page_config(
    page_title="Defensa de Grado - Mokkita", 
    page_icon="🦔", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LA IMAGEN DE TU MOKKITA ---
URL_IMAGEN_MOKKITA = "https://raw.githubusercontent.com/claudiorael/black/main/mokkita.png"

# --- ESTILOS CSS (TEMA CLARO Y LIMPIO) ---
st.markdown(f"""
<style>
    /* Fondo claro y limpio */
    .stApp {{
        background-color: #F8F9FA;
        color: #2C3E50;
    }}
    
    /* Forzar que todos los textos sean oscuros */
    h1, h2, h3, p, span, .stMarkdown, .stText, label {{
        color: #2C3E50 !important;
    }}
    
    /* Contenedores blancos con sombra suave */
    .st-emotion-cache-1r6slb0, .st-emotion-cache-1v0mbdj {{
        background: #FFFFFF !important;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid #E9ECEF;
        padding: 2rem;
    }}

    /* Ocultar barra superior y pie de página de Streamlit */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Botones principales */
    .stButton>button {{
        background-color: #007BFF;
        border: none;
        border-radius: 8px;
        color: #FFFFFF !important;
        font-weight: 600;
        transition: all 0.3s ease;
        height: 50px;
        width: 100%;
    }}
    .stButton>button:hover {{
        background-color: #0056b3;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 123, 255, 0.3);
    }}

    /* ANIMACIÓN DE MOKKITA REAL FLOTANTE */
    @keyframes flotar {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
        100% {{ transform: translateY(0px); }}
    }}
    .mokkita-bot {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 100px;
        height: 100px;
        background-image: url('{URL_IMAGEN_MOKKITA}');
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.2);
        animation: flotar 3.5s ease-in-out infinite;
        z-index: 9999;
        cursor: pointer;
        border: 3px solid #FFFFFF;
    }}
    .mokkita-dialogo {{
        position: fixed;
        bottom: 140px;
        right: 40px;
        background: #FFFFFF;
        color: #2C3E50;
        padding: 12px 18px;
        border-radius: 12px;
        font-weight: bold;
        z-index: 9998;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.1);
        border: 1px solid #E9ECEF;
        pointer-events: none;
    }}
    .mokkita-dialogo::after {{
        content: '';
        position: absolute;
        bottom: -10px;
        right: 40px;
        border-width: 10px 10px 0;
        border-style: solid;
        border-color: #FFFFFF transparent transparent transparent;
        display: block;
        width: 0;
    }}
    .mokkita-bot:hover + .mokkita-dialogo {{
        opacity: 1;
    }}
</style>

<div class="mokkita-bot"></div>
<div class="mokkita-dialogo">¡Hola! Sube tu trabajo aquí<br>para que lo revisemos.</div>
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

# Prompt imparcial, evaluando la coherencia interna del paradigma del estudiante
PROMPT_POR_DEFECTO = """Eres Mokkita, un erizo intelectual que usa lentes y un chaleco. Eres un profesor supervisor clínico estricto, riguroso e imparcial.
Tu tarea es evaluar trabajos de defensa de grado de estudiantes de psicología, sin importar su corriente teórica.
Debes identificar el paradigma o marco teórico que el estudiante presenta en su texto y evaluar críticamente la coherencia interna, la articulación clínica del caso y la solidez argumentativa en base a ese mismo marco elegido por el alumno.
Estructura tu respuesta así:
1. 🎯 VEREDICTO CLÍNICO DE MOKKITA
2. ✅ PUNTOS FUERTES (Aciertos teóricos y metodológicos)
3. 🛠️ ÁREAS DE MEJORA (Incoherencias o fallos en la articulación de su propio paradigma)
4. 💡 RECOMENDACIÓN PARA LA DEFENSA"""

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
        st.markdown("<h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 5px;'>Plataforma Mokkita</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6c757d; margin-bottom: 30px;'>Defensa de Grado & Análisis Clínico</p>", unsafe_allow_html=True)
        
        with st.container():
            usuario = st.text_input("👤 Usuario").strip().lower()
            clave = st.text_input("🔑 Contraseña", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
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
        tab1, tab2 = st.tabs(["📝 Análisis Trabajo Final", "⚙️ Dashboard Admin (Oculto)"])
    else:
        tab1, = st.tabs(["📝 Análisis Trabajo Final"])

    # --- PESTAÑA 1: REVISIÓN ---
    with tab1:
        st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Análisis de Defensa de Grado</h2>", unsafe_allow_html=True)
        
        col_opciones, col_archivos = st.columns([1, 2])
        
        with col_opciones:
            st.markdown("#### 🎛️ Parámetros")
            nivel_teorico = st.slider("Exigencia Teórica", 1, 5, 4)
            enfoque_feedback = st.selectbox("Tono de Mokkita", ["Académico y Directo", "Constructivo", "Irónico y Agudo"])
            
        with col_archivos:
            st.markdown("#### 📄 Documentos")
            archivo_trabajo = st.file_uploader("Sube el Trabajo del Estudiante (Requerido)", type=["pdf", "txt", "docx"])
            with st.expander("Opcional: Subir Pauta o Autor de referencia"):
                archivo_autor = st.file_uploader("Material Base", type=["pdf", "txt"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        if archivo_trabajo:
            if st.button("Iniciar Evaluación con Mokkita"):
                registrar_estadistica(st.session_state["usuario_actual"], "Evaluación Generada")
                
                with st.spinner("Mokkita está ajustándose los lentes y leyendo el trabajo..."):
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

                        prompt_base = obtener_prompt()
                        instrucciones = f"{prompt_base}\n\nTono solicitado: {enfoque_feedback}.\nNivel de exigencia (1-5): {nivel_teorico}."
                        
                        modelo = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=instrucciones)
                        
                        contenido_a_enviar = [g_trabajo]
                        texto_solicitud = "Analiza de manera crítica e imparcial este trabajo de grado."
                        if g_autor:
                            contenido_a_enviar.insert(0, g_autor)
                            texto_solicitud = "Analiza el trabajo del estudiante comparándolo con el material del autor adjunto."
                        
                        contenido_a_enviar.append(texto_solicitud)
                        
                        respuesta = modelo.generate_content(contenido_a_enviar)
                        
                        st.success("✨ ¡Análisis completado!")
                        with st.chat_message("Mokkita", avatar=URL_IMAGEN_MOKKITA):
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
            st.info("Aquí puedes reescribir las instrucciones base. Se aplicarán para todos los usuarios.")
            prompt_actual = obtener_prompt()
            nuevo_prompt = st.text_area("Instrucciones del Sistema", value=prompt_actual, height=250)
            
            if st.button("Guardar Nueva Personalidad"):
                guardar_prompt(nuevo_prompt)
                st.success("¡El cerebro de Mokkita ha sido actualizado!")

            st.markdown("---")
            st.subheader("📊 Estadísticas de Uso")
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    st.dataframe(json.load(f), use_container_width=True)
            else:
                st.write("Aún no hay datos.")

if not st.session_state["autenticado"]: mostrar_login()
else: mostrar_aplicacion()
