import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
import random
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Defensa de Grado - Mokkita", page_icon="🦔", layout="centered")

# --- IMAGEN DEL BOT (TEMPORAL) ---
URL_IMAGEN_MOKKITA = "https://img.freepik.com/vector-premium/lindo-erizo-gafas-ilustracion-vector-plano-dibujos-animados_1116146-5.jpg"

# --- ESTILOS CSS BASE (Eliminación de rigidez de Streamlit) ---
st.markdown("""
<style>
    /* Ocultar barra superior blanca vacía y pie de página */
    .stApp > header { display: none !important; }
    footer { display: none !important; }
    
    /* Centrar verticalmente el contenido */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Diseño moderno para la caja de Login */
    .login-container {
        background: #ffffff;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: auto;
        border: 1px solid #e2e8f0;
    }
    
    /* Botones primarios (Reducidos y flotantes) */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border-radius: 30px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 14px 0 rgba(99,102,241,0.39);
        transition: transform 0.2s;
    }
    .stButton>button[kind="primary"]:hover {
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- INYECCIÓN DEL WIDGET INTERACTIVO DE MOKKITA (HTML/JS) ---
def renderizar_mokkita(mensaje_personalizado=""):
    frases_animo = [
        "¡Vamos con esa defensa de grado! Tú puedes.",
        "Un buen marco teórico lo es todo. ¡Revisemos!",
        "La clínica requiere rigor. Ponme a prueba.",
        "Acomoda tus ideas, yo me ajusto los lentes.",
        "¡Respira profundo! Aquí estoy para ayudarte."
    ]
    mensaje_final = mensaje_personalizado if mensaje_personalizado else random.choice(frases_animo)
    
    html_code = f"""
    <style>
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-15px); }}
            100% {{ transform: translateY(0px); }}
        }}
        .mokkita-wrapper {{
            position: fixed;
            bottom: 40px;
            right: 40px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            z-index: 99999;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .chat-bubble {{
            background: #ffffff;
            color: #1e293b;
            padding: 15px 20px;
            border-radius: 18px 18px 0px 18px;
            box-shadow: 0px 8px 24px rgba(0,0,0,0.15);
            margin-bottom: 15px;
            font-weight: 600;
            font-size: 14px;
            max-width: 250px;
            text-align: right;
            border: 2px solid #e2e8f0;
            animation: float 4s ease-in-out infinite;
        }}
        .bot-avatar {{
            width: 100px;
            height: 100px;
            background-image: url('{URL_IMAGEN_MOKKITA}');
            background-size: cover;
            background-position: center;
            border-radius: 50%;
            border: 4px solid #ffffff;
            box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
            animation: float 4s ease-in-out infinite;
            animation-delay: 0.2s;
            cursor: pointer;
            transition: transform 0.3s;
        }}
        .bot-avatar:hover {{
            transform: scale(1.1);
        }}
    </style>
    <div class="mokkita-wrapper">
        <div class="chat-bubble">{mensaje_final}</div>
        <div class="bot-avatar"></div>
    </div>
    """
    components.html(html_code, height=300, width=350)

# --- ARCHIVOS ---
STATS_FILE = "mokkita_stats.json"
PROMPT_FILE = "mokkita_prompt.json"

def registrar_estadistica(usuario, accion):
    registro = {"usuario": usuario, "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "accion": accion}
    datos = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f: datos = json.load(f)
    datos.append(registro)
    with open(STATS_FILE, "w") as f: json.dump(datos, f)

PROMPT_POR_DEFECTO = """Eres Mokkita, un erizo intelectual con lentes. Eres un profesor clínico imparcial.
Debes identificar el paradigma del estudiante y evaluar la coherencia interna en base a ese mismo marco.
Estructura: 1. VEREDICTO | 2. PUNTOS FUERTES | 3. ÁREAS DE MEJORA | 4. RECOMENDACIÓN"""

def obtener_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r") as f: return json.load(f).get("prompt", PROMPT_POR_DEFECTO)
    return PROMPT_POR_DEFECTO

def guardar_prompt(nuevo_prompt):
    with open(PROMPT_FILE, "w") as f: json.dump({"prompt": nuevo_prompt}, f)

# --- SESIÓN ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state: st.session_state["usuario_actual"] = None

# --- LOGIN (DISEÑO COMPACTO) ---
def mostrar_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Creamos un contenedor HTML para forzar el diseño compacto
    st.markdown("""
        <div class="login-container">
            <h2 style='text-align: center; color: #1e293b; font-weight: 800; margin-bottom: 5px;'>🦔 Mokkita</h2>
            <p style='text-align: center; color: #64748b; font-size: 14px; margin-bottom: 20px;'>Revisión Académica</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Usamos columnas para achicar los campos de texto
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        usuario = st.text_input("Usuario", placeholder="Tu usuario...").strip().lower()
        clave = st.text_input("Contraseña", type="password", placeholder="Tu clave...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Ingresar", type="primary", use_container_width=True):
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

# --- APP PRINCIPAL (INTERACTIVA) ---
def mostrar_aplicacion():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    
    # Renderizamos a Mokkita con un mensaje de bienvenida personalizado
    renderizar_mokkita(f"¡Hola {st.session_state['usuario_actual'].capitalize()}! Sube tu trabajo y evaluemos ese paradigma.")

    # Cabecera compacta
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown(f"**Usuario:** {st.session_state['usuario_actual'].capitalize()}")
    with col2:
        if st.button("Cerrar Sesión"):
            registrar_estadistica(st.session_state["usuario_actual"], "Logout")
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = None
            st.rerun()
    
    st.markdown("---")

    if st.session_state["usuario_actual"] == "claudio":
        tab_revisor, tab_admin = st.tabs(["🎓 Revisión de Grado", "⚙️ Admin"])
    else:
        tab_revisor = st.container()

    with tab_revisor:
        st.markdown("### Configuración de Revisión")
        c1, c2 = st.columns(2)
        with c1: enfoque_feedback = st.selectbox("Personalidad", ["Académico e Imparcial", "Constructivo", "Directo"])
        with c2: nivel_teorico = st.slider("Exigencia (1 al 5)", 1, 5, 4)

        st.markdown("### Documentos")
        col_t, col_a = st.columns(2)
        with col_t: archivo_trabajo = st.file_uploader("📄 Trabajo de Grado", type=["pdf", "txt", "docx"])
        with col_a: archivo_autor = st.file_uploader("📚 Pauta/Autor (Opcional)", type=["pdf", "txt"])

        st.markdown("<br>", unsafe_allow_html=True)
        if archivo_trabajo:
            if st.button("✨ Generar Evaluación con Mokkita", type="primary"):
                registrar_estadistica(st.session_state["usuario_actual"], "Evaluación Generada")
                
                with st.spinner("Mokkita procesando..."):
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
                        instrucciones = f"{prompt_base}\n\nTono: {enfoque_feedback}.\nNivel (1-5): {nivel_teorico}."
                        modelo = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=instrucciones)
                        
                        contenido = [g_trabajo]
                        if g_autor:
                            contenido.insert(0, g_autor)
                            contenido.append("Analiza el trabajo comparándolo con el autor adjunto.")
                        else:
                            contenido.append("Analiza de manera imparcial este trabajo de grado.")
                        
                        respuesta = modelo.generate_content(contenido)
                        st.success("¡Análisis completado!")
                        
                        st.markdown("<div style='background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #6366f1;'>", unsafe_allow_html=True)
                        st.markdown(respuesta.text)
                        st.markdown("</div><br>", unsafe_allow_html=True)
                        
                        st.download_button("💾 Descargar Evaluación", respuesta.text, file_name=f"Evaluacion_{st.session_state['usuario_actual']}.md")
                            
                    except Exception as e: st.error(f"Error de API: {e}")
                    finally:
                        for f_g in archivos_gemini:
                            try: genai.delete_file(f_g.name)
                            except: pass
                        for f_tmp in archivos_temporales:
                            if os.path.exists(f_tmp): os.remove(f_tmp)

    if st.session_state["usuario_actual"] == "claudio":
        with tab_admin:
            st.markdown("### Modificar Cerebro")
            nuevo_prompt = st.text_area("System Prompt", value=obtener_prompt(), height=200)
            if st.button("Guardar", type="primary"):
                guardar_prompt(nuevo_prompt)
                st.success("Cerebro actualizado.")
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f: st.dataframe(json.load(f), use_container_width=True)

# --- INICIO ---
if not st.session_state["autenticado"]: mostrar_login()
else: mostrar_aplicacion()
