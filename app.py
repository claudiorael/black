import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
import random
import pytz
import pandas as pd
from datetime import datetime
from docx import Document
import io

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Portal Mokkita", page_icon="🦔", layout="wide")

URL_MOKKITA = "https://raw.githubusercontent.com/claudiorael/black/main/mokkita.png"

# --- 2. CSS PARA UI MODERNA Y MOKKITA FLOTANTE ---
st.markdown(f"""
<style>
    .stApp {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }}
    header {{ display: none !important; }}
    footer {{ display: none !important; }}
    
    .css-1r6slb0, .st-emotion-cache-1r6slb0, .st-emotion-cache-1v0mbdj {{
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.5);
        margin-bottom: 20px;
    }}

    h1, h2, h3, h4 {{ color: #1e293b !important; font-family: 'Segoe UI', sans-serif; font-weight: 800; }}

    .stButton>button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; border: none; border-radius: 12px; padding: 15px;
        font-size: 18px; font-weight: bold; box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
        transition: all 0.3s ease; width: 100%; height: 60px;
    }}
    .stButton>button:hover {{ transform: translateY(-3px); box-shadow: 0 8px 25px rgba(118, 75, 162, 0.6); }}

    @keyframes flotar {{ 0% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-12px); }} 100% {{ transform: translateY(0px); }} }}
    .bot-container {{ position: fixed; bottom: 30px; right: 30px; z-index: 999999; display: flex; flex-direction: column; align-items: flex-end; pointer-events: none; }}
    .bot-bubble {{ background: white; color: #1e293b; padding: 15px 20px; border-radius: 20px 20px 0px 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); margin-bottom: 15px; font-weight: 700; font-size: 15px; max-width: 250px; text-align: right; border: 2px solid #e2e8f0; animation: flotar 4s ease-in-out infinite; pointer-events: auto; }}
    .bot-img {{ width: 145px; height: 145px; background-color: white; background-image: url('{URL_MOKKITA}'); background-size: cover; background-position: center; border-radius: 50%; border: 4px solid white; box-shadow: 0 10px 25px rgba(0,0,0,0.2); animation: flotar 4s ease-in-out infinite; animation-delay: 0.2s; pointer-events: auto; cursor: pointer; transition: transform 0.3s; }}
    .bot-img:hover {{ transform: scale(1.1); }}
</style>
""", unsafe_allow_html=True)

# --- 3. ARCHIVOS Y LÓGICA DE DATOS ESTADÍSTICOS ---
STATS_FILE = "mokkita_stats.json"
PROMPT_FILE = "mokkita_prompt.json"
ZONA_HORARIA = pytz.timezone('America/Santiago')

def registrar_estadistica(usuario, accion, nombres_archivos="", cantidad_archivos=0, tiempo_sesion=0):
    registro = {
        "usuario": usuario, 
        "fecha_hora": datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S"), 
        "accion": accion,
        "nombres_archivos": nombres_archivos,
        "cantidad_archivos": cantidad_archivos if cantidad_archivos > 0 else "",
        "minutos_en_sesion": round(tiempo_sesion, 2) if tiempo_sesion > 0 else ""
    }
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
        "La clínica requiere rigor. Ponme a prueba.",
        "Acomoda tus ideas, yo me ajusto los lentes.",
        "¡Respira profundo! Aquí estoy para ayudarte.",
        "El saber clínico se pule revisando y reescribiendo.",
        "Estructura, coherencia y rigor. ¡A trabajar!",
        "Tu marco teórico es tu brújula. Veamos hacia dónde apunta."
    ]
    st.markdown(f"""
        <div class="bot-container">
            <div class="bot-bubble">{random.choice(frases)}</div>
            <div class="bot-img" title="Mokkita está listo para evaluar"></div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. SESIÓN Y ESTADO ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state: st.session_state["usuario_actual"] = None
if "login_time" not in st.session_state: st.session_state["login_time"] = None

# --- 5. LOGIN ---
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
                    st.session_state["login_time"] = time.time()
                    registrar_estadistica(usuario, "Login")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")
            except KeyError:
                st.error("Falta configurar los secretos de usuarios.")

# --- 6. APP PRINCIPAL ---
def mostrar_aplicacion():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    renderizar_globo(st.session_state["usuario_actual"])

    # Header de sesión y Cierre
    col_user, col_btn = st.columns([8, 2])
    with col_user:
        st.markdown(f"### 👤 Bienvenido(a), {st.session_state['usuario_actual'].capitalize()}")
    with col_btn:
        if st.button("Cerrar Sesión"):
            tiempo_total = (time.time() - st.session_state["login_time"]) / 60
            registrar_estadistica(st.session_state["usuario_actual"], "Logout", tiempo_sesion=tiempo_total)
            st.session_state["autenticado"] = False
            st.session_state["usuario_actual"] = None
            st.session_state["login_time"] = None
            st.rerun()
    st.markdown("---")

    if st.session_state["usuario_actual"] == "claudio":
        tab_revisor, tab_admin = st.tabs(["🎓 Workspace Académico", "⚙️ Administración (Mokkita)"])
    else:
        tab_revisor, = st.tabs(["🎓 Workspace Académico"])

    with tab_revisor:
        st.markdown("## Análisis de Defensa de Grado")
        
        st.markdown("#### 1. Configuración de Mokkita")
        col_tono, col_nivel = st.columns(2)
        with col_tono:
            enfoque_feedback = st.selectbox("Personalidad del Revisor", ["Académico e Imparcial", "Constructivo", "Estricto e Irónico"])
        with col_nivel:
            nivel_teorico = st.slider("Nivel de Exigencia (1 al 5)", 1, 5, 4)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 2. Carga de Documentos")
        col_trabajo, col_autor = st.columns(2)
        with col_trabajo:
            archivo_trabajo = st.file_uploader("📄 Sube el Trabajo (Requerido - PDF/TXT)", type=["pdf", "txt"])
        with col_autor:
            archivo_autor = st.file_uploader("📚 Material del Autor (Opcional - PDF/TXT)", type=["pdf", "txt"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        if archivo_trabajo:
            if st.button("✨ Generar Evaluación con Mokkita"):
                
                # --- REGISTRO DE ARCHIVOS SUBIDOS ---
                lista_nombres = [archivo_trabajo.name]
                if archivo_autor: lista_nombres.append(archivo_autor.name)
                
                registrar_estadistica(
                    st.session_state["usuario_actual"], 
                    "Evaluación Generada", 
                    nombres_archivos=", ".join(lista_nombres), 
                    cantidad_archivos=len(lista_nombres)
                )
                
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
                        
                        modelos_permitidos = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        if not modelos_permitidos:
                            st.error("Tu API Key no tiene modelos habilitados.")
                            st.stop()
                            
                        modelo_elegido = modelos_permitidos[0]
                        for m in modelos_permitidos:
                            if "1.5-pro" in m:
                                modelo_elegido = m
                                break
                            elif "1.5-flash" in m:
                                modelo_elegido = m
                        
                        modelo = genai.GenerativeModel(model_name=modelo_elegido, system_instruction=instrucciones)
                        
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
                        
                        def crear_word(texto_respuesta):
                            doc = Document()
                            doc.add_heading('Análisis de Defensa de Grado - Mokkita', 0)
                            texto_limpio = texto_respuesta.replace('**', '') 
                            for linea in texto_limpio.split('\n'):
                                if linea.strip(): doc.add_paragraph(linea)
                            buffer = io.BytesIO()
                            doc.save(buffer)
                            buffer.seek(0)
                            return buffer

                        archivo_word = crear_word(respuesta.text)
                        st.download_button(
                            label="💾 Descargar Evaluación en Word",
                            data=archivo_word,
                            file_name=f"Evaluacion_{st.session_state['usuario_actual']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                            
                    except Exception as e:
                        st.error(f"Error de conexión con Google Gemini: {e}")
                    finally:
                        for f_g in archivos_gemini:
                            try: genai.delete_file(f_g.name)
                            except: pass
                        for f_tmp in archivos_temporales:
                            if os.path.exists(f_tmp): os.remove(f_tmp)
        else:
            st.info("👆 Sube un trabajo de grado (formato PDF o TXT) en el paso 2 para habilitar el motor de análisis.")

    # --- PESTAÑA ADMIN Y BASE DE DATOS EDITABLE ---
    if st.session_state["usuario_actual"] == "claudio":
        with tab_admin:
            st.markdown("### 🧠 Centro de Mando Mokkita")
            nuevo_prompt = st.text_area("Instrucciones del Sistema (System Prompt)", value=obtener_prompt(), height=150)
            if st.button("Guardar Nueva Personalidad"):
                guardar_prompt(nuevo_prompt)
                st.success("¡Cerebro actualizado para todos los usuarios!")
            
            st.markdown("---")
            st.markdown("### 📊 Base de Datos de Uso (Editable)")
            st.info("💡 Haz clic en la casilla izquierda de cualquier fila y presiona **Suprimir** en tu teclado para borrar registros, o edita directamente. Guarda los cambios abajo.")
            
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    datos_estadisticas = json.load(f)
                
                if datos_estadisticas:
                    df = pd.DataFrame(datos_estadisticas)
                    # Data_editor permite eliminar filas y modificar datos como en Excel
                    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                    
                    if st.button("💾 Guardar Cambios en la Base de Datos"):
                        with open(STATS_FILE, "w") as f:
                            json.dump(edited_df.to_dict(orient="records"), f)
                        st.success("¡Base de datos actualizada!")
                else:
                    st.write("Aún no hay registros guardados.")
            else:
                st.write("Aún no hay registros guardados.")

# --- INICIO ---
if not st.session_state["autenticado"]: mostrar_login()
else: mostrar_aplicacion()
