import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Revisor Académico Mokkita", page_icon="🦔", layout="wide")

# --- ESTILOS CSS (DISEÑO VISUAL TIPO "GLASSMORPHISM") ---
# Recreamos el fondo oscuro y los paneles translúcidos de la imagen de referencia.
st.markdown("""
<style>
    /* Fondo principal: Puedes cambiar la URL por cualquier imagen de psicología o educación */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1557683316-973673baf926?q=80&w=2000&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Panel translúcido central */
    .css-1r6slb0, .st-emotion-cache-1r6slb0, .st-emotion-cache-1v0mbdj {
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        color: white;
    }
    
    /* Textos en blanco para contrastar */
    h1, h2, h3, p, .stMarkdown, .stText {
        color: #ffffff !important;
    }
    
    /* Estilo de botones interactivos */
    .stButton>button {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        color: white;
        transition: all 0.3s ease;
        width: 100%;
        height: 60px;
    }
    .stButton>button:hover {
        background-color: rgba(255, 255, 255, 0.3);
        border-color: #ffffff;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- ARCHIVO DE ESTADÍSTICAS LOCAL ---
# Usamos un archivo JSON temporal para guardar los registros. 
# En producción avanzada esto iría a Google Sheets o Supabase.
STATS_FILE = "mokkita_stats.json"

def registrar_estadistica(usuario, accion):
    registro = {
        "usuario": usuario,
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accion": accion
    }
    datos = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            datos = json.load(f)
    datos.append(registro)
    with open(STATS_FILE, "w") as f:
        json.dump(datos, f)

def leer_estadisticas():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return []

# --- GESTIÓN DE SESIÓN (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None
if "hora_inicio" not in st.session_state:
    st.session_state["hora_inicio"] = None

def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>Plataforma Mokkita</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>INGRESA TUS CREDENCIALES</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            usuario = st.text_input("Usuario").strip().lower()
            clave = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar")
            
            if submit:
                try:
                    usuarios_permitidos = st.secrets["usuarios"]
                    if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == clave:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_actual"] = usuario
                        st.session_state["hora_inicio"] = time.time()
                        registrar_estadistica(usuario, "Login")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos.")
                except KeyError:
                    st.error("Error: Configura st.secrets['usuarios'].")

# --- APLICACIÓN PRINCIPAL ---
def mostrar_aplicacion():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    
    # Barra lateral
    st.sidebar.title(f"👤 {st.session_state['usuario_actual'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        tiempo_sesion = round((time.time() - st.session_state["hora_inicio"]) / 60, 2)
        registrar_estadistica(st.session_state["usuario_actual"], f"Logout (Minutos: {tiempo_sesion})")
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = None
        st.rerun()

    # Pestañas de navegación. La pestaña Admin solo se crea si el usuario es 'claudio'.
    if st.session_state["usuario_actual"] == "claudio":
        tab1, tab2 = st.tabs(["📝 Revisión de Trabajos", "📊 Dashboard Admin (Oculto)"])
    else:
        tab1, = st.tabs(["📝 Revisión de Trabajos"])

    # --- PESTAÑA 1: REVISIÓN ---
    with tab1:
        st.markdown("<h2 style='text-align: center;'>Análisis Crítico Constructivista</h2>", unsafe_allow_html=True)
        
        with st.chat_message("Mokkita", avatar="🦔"):
            st.write(f"Hola {st.session_state['usuario_actual'].capitalize()}. Soy Mokkita. Sube la pauta del autor y el trabajo del alumno. Mis niveles de crítica están listos.")

        col_a, col_b = st.columns(2)
        with col_a:
            nivel_teorico = st.slider("Rigor Teórico y Conceptual", 1, 5, 5)
        with col_b:
            enfoque_feedback = st.selectbox("Tono de Mokkita", ["Constructivo", "Estricto", "Crítico e Irónico"])

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            archivo_autor = st.file_uploader("📥 Subir Autor / Pauta (PDF/TXT)", type=["pdf", "txt"], key="autor")
        with col2:
            archivo_trabajo = st.file_uploader("📥 Subir Trabajo Estudiante (PDF/TXT)", type=["pdf", "txt"], key="trabajo")

        if archivo_autor and archivo_trabajo:
            if st.button("Generar Análisis Crítico", type="primary"):
                registrar_estadistica(st.session_state["usuario_actual"], "Generó Análisis")
                
                with st.spinner("Mokkita está analizando la articulación teórica..."):
                    archivos_temporales = []
                    archivos_gemini = []
                    try:
                        def subir_a_gemini(archivo_streamlit):
                            ext = archivo_streamlit.name.split('.')[-1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                                tmp.write(archivo_streamlit.read())
                                rutatmp = tmp.name
                                archivos_temporales.append(rutatmp)
                            
                            file_g = genai.upload_file(rutatmp)
                            archivos_gemini.append(file_g)
                            
                            while file_g.state.name == 'PROCESSING':
                                time.sleep(2)
                                file_g = genai.get_file(file_g.name)
                            return file_g

                        g_autor = subir_a_gemini(archivo_autor)
                        g_trabajo = subir_a_gemini(archivo_trabajo)

                        instrucciones = f"""
                        Eres Mokkita 🦔. Profesor universitario. Tono: {enfoque_feedback}.
                        Compara el trabajo del estudiante con el material del autor.
                        Rigor exigido: {nivel_teorico}/5.
                        
                        Estructura:
                        1. 🎯 VEREDICTO DE MOKKITA
                        2. ✅ PUNTOS FUERTES (Articulación)
                        3. 🛠️ ÁREAS DE MEJORA
                        """
                        modelo = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=instrucciones)
                        respuesta = modelo.generate_content([g_autor, g_trabajo, "Analiza estos documentos."])
                        
                        st.success("Análisis completado")
                        with st.chat_message("Mokkita", avatar="🦔"):
                            st.markdown(respuesta.text)
                            st.download_button(
                                label="💾 Descargar Reporte de Mokkita",
                                data=respuesta.text,
                                file_name=f"Reporte_{st.session_state['usuario_actual']}.md",
                                mime="text/markdown"
                            )
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        for f_g in archivos_gemini:
                            try: genai.delete_file(f_g.name)
                            except: pass
                        for f_tmp in archivos_temporales:
                            if os.path.exists(f_tmp):
                                os.remove(f_tmp)

    # --- PESTAÑA 2: DASHBOARD ADMIN (SOLO PARA CLAUDIO) ---
    if st.session_state["usuario_actual"] == "claudio":
        with tab2:
            st.subheader("Estadísticas de Uso de la Plataforma")
            datos = leer_estadisticas()
            if datos:
                st.dataframe(datos, use_container_width=True)
                
                # Métricas rápidas
                total_logins = len([d for d in datos if "Login" in d["accion"]])
                total_analisis = len([d for d in datos if "Generó Análisis" in d["accion"]])
                
                col1, col2 = st.columns(2)
                col1.metric("Ingresos Totales", total_logins)
                col2.metric("Trabajos Revisados", total_analisis)
            else:
                st.info("Aún no hay registros de actividad.")

# --- CONTROLADOR ---
if not st.session_state["autenticado"]:
    mostrar_login()
else:
    mostrar_aplicacion()
