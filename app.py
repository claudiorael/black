import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Revisor Académico Mokkita", page_icon="🦔", layout="wide")

# --- 2. GESTIÓN DE SESIÓN (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None

def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🦔 Portal de Revisión Mokkita")
        st.write("Ingresa tus credenciales para acceder al análisis crítico.")
        
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
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos.")
                except KeyError:
                    st.error("Error: No se encontró la lista de usuarios en los secretos del servidor.")

# --- 3. APLICACIÓN PRINCIPAL ---
def mostrar_aplicacion():
    # Configurar API
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    
    # Barra lateral
    st.sidebar.title(f"👤 Bienvenido, {st.session_state['usuario_actual'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = None
        st.rerun()

    st.title("Revisor de Trabajos y Autores")
    
    # Bienvenida de Mokkita
    with st.chat_message("Mokkita", avatar="🦔"):
        st.write(f"¡Hola {st.session_state['usuario_actual'].capitalize()}! Soy Mokkita 🦔, tu erizo intelectual de cabecera. Sube el texto del autor base y el trabajo que quieres que revise. Ajusta mis niveles de exigencia y me pondré los lentes para hacerte una crítica aguda.")

    # --- CONFIGURACIÓN DE NIVELES DE ANÁLISIS ---
    st.subheader("⚙️ Configuración del Análisis de Mokkita")
    with st.expander("Modificar niveles de evaluación (Clic para abrir)", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nivel_teorico = st.slider("Rigor Teórico y Conceptual", 1, 5, 5, help="Nivel de exigencia al evaluar el uso de conceptos del autor.")
            nivel_estructura = st.slider("Estructura y Coherencia", 1, 5, 4)
        with col_b:
            nivel_critica = st.slider("Profundidad Crítica", 1, 5, 4, help="Qué tanto se exige que el alumno cuestione o reflexione.")
            enfoque_feedback = st.selectbox("Tono de Mokkita", ["Constructivo y Motivador", "Estrictamente Académico", "Crítico, Irónico y Directo"])

    # --- SUBIDA DE ARCHIVOS ---
    st.subheader("📄 Carga de Documentos")
    col1, col2 = st.columns(2)
    
    with col1:
        archivo_autor = st.file_uploader("1. Sube el texto del Autor / Material Base (PDF o TXT)", type=["pdf", "txt"], key="autor")
    with col2:
        archivo_trabajo = st.file_uploader("2. Sube el Trabajo del Estudiante (PDF o TXT)", type=["pdf", "txt"], key="trabajo")

    # --- PROCESAMIENTO ---
    if archivo_autor and archivo_trabajo:
        if st.button("Generar Análisis Crítico", type="primary"):
            with st.spinner("Mokkita está leyendo los documentos... esto puede tomar un par de minutos."):
                archivos_temporales = []
                archivos_gemini = []
                
                try:
                    def subir_a_gemini(archivo_streamlit):
                        extension = archivo_streamlit.name.split('.')[-1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
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

                    # Prompt dinámico integrando a Mokkita
                    instrucciones = f"""
                    Eres Mokkita, un erizo intelectual que usa lentes y suéter. Eres un profesor universitario y revisor académico muy agudo. 
                    El usuario ha pedido que tu tono para esta revisión sea: {enfoque_feedback}. Adapta tu personalidad a este tono (si te piden ser crítico y directo, usa tu característico humor oscuro e irónico).
                    Tu tarea es comparar el trabajo del estudiante con el material del autor de referencia y emitir un informe.
                    
                    Niveles de exigencia (escala 1 a 5):
                    - Rigor Teórico: {nivel_teorico}/5
                    - Estructura y Coherencia: {nivel_estructura}/5
                    - Profundidad Crítica: {nivel_critica}/5
                    
                    Estructura estrictamente tu respuesta de la siguiente manera y háblale directamente al usuario como Mokkita:
                    1. 🎯 EL VEREDICTO DE MOKKITA: Breve apreciación general del trabajo.
                    2. ✅ PUNTOS FUERTES: Qué hizo bien el estudiante al articular la teoría.
                    3. 🛠️ ÁREAS DE MEJORA: Dónde falla el texto.
                    4. 💡 CONSEJO DEL ERIZO: Qué modificar específicamente antes de entregar la versión final.
                    """
                    
                    modelo = genai.GenerativeModel(
                        model_name="gemini-1.5-pro",
                        system_instruction=instrucciones
                    )
                    
                    prompt = "Analiza estos dos documentos. El primero es el material del autor/referencia. El segundo es el trabajo del estudiante."
                    
                    respuesta = modelo.generate_content([g_autor, g_trabajo, prompt])
                    
                    st.success("¡Mokkita ha terminado su análisis!")
                    
                    # Mostrar resultados en formato chat de Mokkita
                    st.markdown("---")
                    with st.chat_message("Mokkita", avatar="🦔"):
                        st.markdown(respuesta.text)
                        
                        # --- BOTÓN PARA GUARDAR/DESCARGAR DENTRO DEL CHAT ---
                        st.download_button(
                            label="📥 Descargar Reporte de Mokkita",
                            data=respuesta.text,
                            file_name=f"Revision_Mokkita_{st.session_state['usuario_actual']}.md",
                            mime="text/markdown"
                        )
                    st.markdown("---")

                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")
                
                finally:
                    # Limpieza
                    for f_g in archivos_gemini:
                        try:
                            genai.delete_file(f_g.name)
                        except:
                            pass
                    for f_tmp in archivos_temporales:
                        if os.path.exists(f_tmp):
                            os.remove(f_tmp)

# --- 4. CONTROLADOR DE VISTAS ---
if not st.session_state["autenticado"]:
    mostrar_login()
else:
    mostrar_aplicacion()
