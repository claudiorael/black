import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
import random
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA (WIDE = ANCHO COMPLETO) ---
st.set_page_config(page_title="Portal Mokkita", page_icon="🦔", layout="wide")

# La URL directa a tu imagen en GitHub
URL_MOKKITA = "https://raw.githubusercontent.com/claudiorael/black/main/mokkita.png"

# --- 2. SÚPER CSS PARA UI MODERNA Y MOKKITA FLOTANTE ---
st.markdown(f"""
<style>
    /* Fondo de la aplicación con un gradiente suave y profesional */
    .stApp {{
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }}
    
    /* Ocultar elementos nativos de Streamlit */
    header {{ display: none !important; }}
    footer {{ display: none !important; }}
    
    /* Crear el efecto de Tarjetas (Cards) para los bloques de contenido */
    .css-1r6slb0, .st-emotion-cache-1r6slb0, .st-emotion-cache-1v0mbdj {{
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.5);
        margin-bottom: 20px;
    }}

    /* Estilizar Títulos */
    h1, h2, h3, h4 {{
        color: #1e293b !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
    }}

    /* Botones de Acción Atractivos */
    .stButton>button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 15px;
        font-size: 18px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
        transition: all 0.3s ease;
        width: 100%;
        height: 60px;
    }}
    .stButton>button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(118, 75, 162, 0.6);
    }}

    /* --- MOKKITA FLOTANTE --- */
    @keyframes flotar {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-12px); }}
        100% {{ transform: translateY(0px); }}
    }}
    .bot-container {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        pointer-events: none;
    }}
    .bot-bubble {{
        background: white;
        color: #1e293b;
        padding: 15px 20px;
        border-radius: 20px 20px 0px 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 15px;
        font-weight: 700;
        font-size: 15px;
        max-width: 250px;
        text-align: right;
        border: 2px solid #e2e8f0;
        animation: flotar 4s ease-in-out infinite;
        pointer-events: auto;
    }}
    .bot-img {{
        width: 110px;
        height: 110px;
        background-color: white;
        background-image: url('{URL_MOKKITA}');
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        border: 4px solid white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        animation: flotar 4s ease-in-out infinite;
        animation-delay: 0.2s;
        pointer-events: auto;
        cursor: pointer;
        transition: transform 0.3s;
    }}
    .bot-img:hover {{ transform: scale(1.1); }}
</style>
""", unsafe_allow_html=True)

# --- 3. ARCHIVOS Y LÓGICA DE DATOS ---
STATS_FILE = "mokkita_stats.json"
PROMPT_FILE = "mokkita_prompt.json"

def registrar_estadistica(usuario, accion):
    registro = {"usuario": usuario, "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "accion": accion}
    datos = []
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f: datos = json.load(f)
    datos.append(registro)
    with open(STATS_FILE, "w") as f: json.dump(datos, f)

PROMPT_POR_DEFECTO = """Eres Mokkita, un erizo intelectual con lentes. Eres un profesor clínico imparcial y brillante.
Identifica el paradigma del estudiante y evalúa críticamente su coherencia interna.
Estructura:
1. 🎯 VEREDICTO DE MOKKITA
2. ✅ PUNTOS FUERTES (Aciertos en su propio paradigma)
3. 🛠️ ÁREAS DE MEJORA (Incoherencias)
4. 💡 RECOMENDACIÓN PARA LA DEFENSA"""

def obtener_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r") as f: return json.load(f).get("prompt", PROMPT_POR_DEFECTO)
    return PROMPT_POR_DEFECTO

def guardar_prompt(nuevo_prompt):
    with open(PROMPT_FILE, "w") as f: json.dump({"prompt": nuevo_prompt}, f)

def renderizar_globo(usuario):
    frases = [
        f"¡Vamos {usuario.capitalize()}! Sube ese trabajo.",
        "Un buen marco teórico lo es todo. ¡Revisemos!",
        "La clínica requiere rigor. Ponme a prueba.",
        "Acomoda tus ideas, yo me ajusto los lentes."
    ]
    mensaje = random.choice(frases)
    st.markdown(f"""
        <div class="bot-container">
            <div class="bot-bubble">{mensaje}</div>
            <div class="bot-img" title="Mokkita está listo para evaluar"></div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. SESIÓN Y ESTADO ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state: st.session_state["usuario_actual"] = None

# --- 5. LOGIN (DISEÑO CENTRADO) ---
def mostrar_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_centro, _ = st.columns([1, 1, 1]) 
    
    with col_centro:
        st.markdown("<h1 style='text-align: center;'>🦔 Portal Mokkita</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Acceso a la plataforma de revisión académica</p><br>", unsafe_allow_html=True)
        
        usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario...").strip().lower()
        clave = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Iniciar Sesión"):
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
                st.error("Falta configurar los secretos de usuarios.")

# --- 6. APP PRINCIPAL ---
def mostrar_aplicacion():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    
    # Inyectar Mokkita flotante
    renderizar_globo(st.session_state["usuario_actual"])

    # Header de sesión
    col_user, col_btn = st.columns([8, 2])
    with col_user:
        st.markdown(f"### 👤 Bienvenido(a), {st.session_state['usuario_actual'].capitalize()}")
    with col_btn:
        if st.button("Cerrar Sesión"):
            registrar_estadistica(st.session_state["usuario_actual"], "Logout")
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = None
            st.rerun()
    st.markdown("---")

    # Pestañas
    if st.session_state["usuario_actual"] == "claudio":
        tab_revisor, tab_admin = st.tabs(["🎓 Workspace Académico", "⚙️ Administración (Mokkita)"])
    else:
        tab_revisor, = st.tabs(["🎓 Workspace Académico"])

    with tab_revisor:
        st.markdown("## Análisis de Defensa de Grado")
        
        # Bloque de Configuración
        st.markdown("#### 1. Configuración de Mokkita")
        col_tono, col_nivel = st.columns(2)
        with col_tono:
            enfoque_feedback = st.selectbox("Personalidad del Revisor", ["Académico e Imparcial", "Constructivo", "Estricto e Irónico"])
        with col_nivel:
            nivel_teorico = st.slider("Nivel de Exigencia (1 al 5)", 1, 5, 4)
            
        st.markdown("<br>", unsafe_allow_html=True)

        # Bloque de Documentos
        st.markdown("#### 2. Carga de Documentos")
        col_trabajo, col_autor = st.columns(2)
        with col_trabajo:
            archivo_trabajo = st.file_uploader("📄 Sube el Trabajo (Requerido)", type=["pdf", "txt"])
        with col_autor:
            archivo_autor = st.file_uploader("📚 Material del Autor (Opcional)", type=["pdf", "txt"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón de Acción
        if archivo_trabajo:
            if st.button("✨ Generar Evaluación con Mokkita"):
                registrar_estadistica(st.session_state["usuario_actual"], "Evaluación Generada")
                
                with st.spinner("Mokkita está leyendo el documento con detención..."):
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
                        
                        # --- BÚSQUEDA DINÁMICA INFALIBLE ---
                        modelos_permitidos = [
                            m.name.replace("models/", "") 
                            for m in genai.list_models() 
                            if 'generateContent' in m.supported_generation_methods
                        ]
                        
                        if not modelos_permitidos:
                            st.error("Tu API Key no tiene modelos habilitados. Por favor, revisa tu clave en Google AI Studio.")
                            st.stop()
                            
                        # Elegir el mejor modelo disponible
                        modelo_elegido = modelos_permitidos[0]
                        for m in modelos_permitidos:
                            if "1.5-pro" in m:
                                modelo_elegido = m
                                break
                            elif "1.5-flash" in m:
                                modelo_elegido = m
                        
                        modelo = genai.GenerativeModel(model_name=modelo_elegido, system_instruction=instrucciones)
                        
                        # --- PREPARAR CONTENIDO ---
                        contenido = [g_trabajo]
                        if g_autor:
                            contenido.insert(0, g_autor)
                            contenido.append("Analiza el trabajo comparándolo con el material del autor.")
                        else:
                            contenido.append("Analiza de manera imparcial este trabajo de grado.")
                        
                        respuesta = modelo.generate_content(contenido)
                        st.success(f"¡Análisis completado exitosamente con el motor {modelo_elegido}!")
                        
                        st.markdown("<div style='background: white; padding: 30px; border-radius: 15px; border-left: 6px solid #764ba2;'>", unsafe_allow_html=True)
                        st.markdown(respuesta.text)
                        st.markdown("</div><br>", unsafe_allow_html=True)
                        
                        st.download_button("💾 Descargar Evaluación Completa", respuesta.text, file_name=f"Evaluacion_{st.session_state['usuario_actual']}.md")
                            
                    except Exception as e:
                        st.error(f"Error de conexión con Google Gemini: {e}")
                    finally:
                        for f_g in archivos_gemini:
                            try: genai.delete_file(f_g.name)
                            except: pass
                        for f_tmp in archivos_temporales:
                            if os.path.exists(f_tmp): os.remove(f_tmp)
        else:
            st.info("👆 Sube un trabajo de grado en el paso 2 para habilitar el motor de análisis.")

    # --- PESTAÑA ADMIN ---
    if st.session_state["usuario_actual"] == "claudio":
        with tab_admin:
            st.markdown("### 🧠 Centro de Mando Mokkita")
            nuevo_prompt = st.text_area("Instrucciones del Sistema (System Prompt)", value=obtener_prompt(), height=200)
            if st.button("Guardar Nueva Personalidad"):
                guardar_prompt(nuevo_prompt)
                st.success("¡Cerebro actualizado para todos los usuarios!")
            
            st.markdown("---")
            st.markdown("### 📊 Registro de Uso")
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    st.dataframe(json.load(f), use_container_width=True)

# --- INICIO ---
if not st.session_state["autenticado"]: 
    mostrar_login()
else: 
    mostrar_aplicacion()
