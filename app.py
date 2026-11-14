import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Defensa de Grado - Mokkita", page_icon="🦔", layout="wide")

# --- IMAGEN DEL BOT (TEMPORAL) ---
# Cambia este enlace por el de tu GitHub cuando subas tu foto de Mokkita.
URL_IMAGEN_MOKKITA = "https://img.freepik.com/vector-premium/lindo-erizo-gafas-ilustracion-vector-plano-dibujos-animados_1116146-5.jpg"

# --- ESTILOS CSS (UI TIPO WEB APP) ---
st.markdown(f"""
<style>
    /* Fondo general */
    .stApp {{ background-color: #f4f7f6; }}
    
    /* Tarjetas de pasos (Contenedores) */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {{
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #eef2f5;
    }}
    
    /* Títulos personalizados */
    .web-title {{
        font-size: 2.8rem;
        font-weight: 800;
        color: #1E293B;
        text-align: center;
        margin-bottom: 0px;
    }}
    .web-subtitle {{
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 40px;
    }}
    
    /* Botón de Acción Principal */
    .stButton>button[kind="primary"] {{
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border-radius: 50px;
        padding: 15px 30px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        width: 100%;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
    }}
    .stButton>button[kind="primary"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.6);
    }}
    
    /* Animación del Bot Flotante */
    @keyframes flotar {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-12px); }}
        100% {{ transform: translateY(0px); }}
    }}
    .mokkita-bot {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 110px;
        height: 110px;
        background-image: url('{URL_IMAGEN_MOKKITA}');
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.2);
        animation: flotar 3s ease-in-out infinite;
        z-index: 9999;
        border: 4px solid #ffffff;
    }}
    .mokkita-dialogo {{
        position: fixed;
        bottom: 150px;
        right: 50px;
        background: #1E293B;
        color: white;
        padding: 15px 20px;
        border-radius: 15px;
        font-weight: 500;
        z-index: 9998;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
    }}
    .mokkita-bot:hover + .mokkita-dialogo {{ opacity: 1; }}
</style>
<div class="mokkita-bot"></div>
<div class="mokkita-dialogo">¡Hola! Ajusta mis parámetros y sube<br>tu trabajo para que lo analicemos.</div>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN Y ARCHIVOS ---
STATS_FILE = "mokkita_stats.json"
PROMPT_FILE = "mokkita_prompt.json"

def registrar_estadistica(usuario, accion):
    registro = {"usuario": usuario, "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "accion": accion}
    datos = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f: datos = json.load(f)
    datos.append(registro)
    with open(STATS_FILE, "w") as f: json.dump(datos, f)

PROMPT_POR_DEFECTO = """Eres Mokkita, un erizo intelectual que usa lentes y un chaleco. Eres un profesor supervisor clínico estricto e imparcial.
Debes identificar el paradigma que el estudiante presenta y evaluar críticamente la coherencia interna y articulación clínica en base a ese mismo marco.
Estructura tu respuesta así:
1. 🎯 VEREDICTO DE MOKKITA
2. ✅ PUNTOS FUERTES (Aciertos teóricos)
3. 🛠️ ÁREAS DE MEJORA (Incoherencias en su paradigma)
4. 💡 RECOMENDACIÓN PARA LA DEFENSA"""

def obtener_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r") as f: return json.load(f).get("prompt", PROMPT_POR_DEFECTO)
    return PROMPT_POR_DEFECTO

def guardar_prompt(nuevo_prompt):
    with open(PROMPT_FILE, "w") as f: json.dump({"prompt": nuevo_prompt}, f)

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state: st.session_state["usuario_actual"] = None

def mostrar_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #1E293B;'>🦔 Portal Mokkita</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B;'>Acceso a la plataforma de revisión académica</p><hr>", unsafe_allow_html=True)
        
        usuario = st.text_input("Usuario").strip().lower()
        clave = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary"):
            try:
                usuarios_permitidos = st.secrets["usuarios"]
                if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == clave:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = usuario
                    registrar_estadistica(usuario, "Login")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
            except KeyError:
                st.error("Falta configurar los secretos de usuarios.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- APP PRINCIPAL (INTERFAZ WEB) ---
def mostrar_aplicacion():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    
    # 1. HEADER CON BOTÓN DE CERRAR SESIÓN (Sin barra lateral)
    head_col1, head_col2 = st.columns([8, 2])
    with head_col1:
        st.markdown(f"**👤 Sesión activa:** {st.session_state['usuario_actual'].capitalize()}")
    with head_col2:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            registrar_estadistica(st.session_state["usuario_actual"], "Logout")
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = None
            st.rerun()
    
    st.markdown("---")

    # Si es admin, mostrar pestañas; si no, mostrar directo el revisor
    if st.session_state["usuario_actual"] == "claudio":
        tab_revisor, tab_admin = st.tabs(["🎓 Workspace Académico", "⚙️ Administración (Mokkita)"])
    else:
        tab_revisor = st.container()

    with tab_revisor:
        st.markdown("<p class='web-title'>Análisis de Defensa de Grado</p>", unsafe_allow_html=True)
        st.markdown("<p class='web-subtitle'>Sube tu documento y Mokkita evaluará la coherencia de tu marco teórico.</p>", unsafe_allow_html=True)
        
        # DISEÑO POR PASOS (Tipo Wizard)
        with st.container():
            st.markdown("### Paso 1: Configurar a Mokkita")
            c1, c2 = st.columns(2)
            with c1:
                enfoque_feedback = st.selectbox("Personalidad del Revisor", ["Académico e Imparcial", "Constructivo y Amable", "Irónico y Estricto"])
            with c2:
                nivel_teorico = st.slider("Nivel de Exigencia (1 al 5)", 1, 5, 4)

        with st.container():
            st.markdown("### Paso 2: Subir Documentos")
            col_trabajo, col_autor = st.columns(2)
            with col_trabajo:
                archivo_trabajo = st.file_uploader("📄 Tu Trabajo (Requerido)", type=["pdf", "txt", "docx"])
            with col_autor:
                archivo_autor = st.file_uploader("📚 Material del Autor (Opcional)", type=["pdf", "txt"])

        with st.container():
            st.markdown("### Paso 3: Generar Revisión")
            if not archivo_trabajo:
                st.info("💡 Sube tu trabajo en el Paso 2 para habilitar el motor de análisis.")
            else:
                if st.button("✨ Iniciar Evaluación con Mokkita", type="primary"):
                    registrar_estadistica(st.session_state["usuario_actual"], "Evaluación Generada")
                    
                    with st.spinner("Mokkita está analizando la coherencia de tu paradigma..."):
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
                            
                            contenido = [g_trabajo]
                            if g_autor:
                                contenido.insert(0, g_autor)
                                contenido.append("Analiza el trabajo del estudiante comparándolo con el material del autor.")
                            else:
                                contenido.append("Analiza de manera crítica e imparcial este trabajo de grado.")
                            
                            respuesta = modelo.generate_content(contenido)
                            
                            st.success("¡Análisis completado!")
                            
                            # Mostrar resultado en una tarjeta visual
                            st.markdown("<div style='background: white; padding: 30px; border-radius: 15px; border-left: 5px solid #4F46E5;'>", unsafe_allow_html=True)
                            st.markdown(respuesta.text)
                            st.markdown("</div><br>", unsafe_allow_html=True)
                            
                            st.download_button("💾 Descargar Evaluación en Texto", respuesta.text, file_name=f"Evaluacion_Mokkita_{st.session_state['usuario_actual']}.md")
                                
                        except Exception as e:
                            st.error(f"Error de procesamiento de API: {e}")
                        finally:
                            for f_g in archivos_gemini:
                                try: genai.delete_file(f_g.name)
                                except: pass
                            for f_tmp in archivos_temporales:
                                if os.path.exists(f_tmp): os.remove(f_tmp)

    # --- PESTAÑA DE ADMINISTRADOR (SOLO CLAUDIO) ---
    if st.session_state["usuario_actual"] == "claudio":
        with tab_admin:
            st.markdown("### 🧠 Centro de Mando")
            st.info("Edita las instrucciones internas de Mokkita.")
            nuevo_prompt = st.text_area("Instrucciones del Sistema", value=obtener_prompt(), height=250)
            if st.button("Guardar Nueva Personalidad", type="primary"):
                guardar_prompt(nuevo_prompt)
                st.success("Cerebro actualizado.")
            
            st.markdown("---")
            st.markdown("### 📊 Registro de Actividad")
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    st.dataframe(json.load(f), use_container_width=True)

# --- INICIO DE LA APP ---
if not st.session_state["autenticado"]: mostrar_login()
else: mostrar_aplicacion()
