import streamlit as st
import google.generativeai as genai
import docx  # Importación para Word
import PyPDF2  # Importación para PDF
import json
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Multi-Agente Literario", layout="wide")

# --- FUNCIONES DE PERSISTENCIA ---
def exportar_sesion():
    sesion = {
        "master_doc": st.session_state.master_doc,
        "chat_history": st.session_state.chat_history
    }
    return json.dumps(sesion, indent=4)

def importar_sesion(archivo_json):
    datos = json.load(archivo_json)
    st.session_state.master_doc = datos["master_doc"]
    st.session_state.chat_history = datos["chat_history"]
    st.success("¡Sesión restaurada correctamente!")

# Inicializar estados de sesión
if "master_doc" not in st.session_state:
    st.session_state.master_doc = "ESCRIBE AQUÍ EL RESUMEN O CAPÍTULOS DE TU LIBRO..."
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- BARRA LATERAL (Configuración y API) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    api_key = st.text_input("Google API Key:", type="password")

    # Modelos, esto se debe actualizar cuando se actualice streamlit
    modelo_nombre = st.selectbox(
        "Modelo:",
        ["gemini-2.5-flash", "gemini-2.5-pro"]
    )

    if api_key:
        genai.configure(api_key=api_key)

    st.divider()
    agente_activo = st.radio(
        "Seleccionar Agente:",
        ["Estratega Creativo", "Arquitecto de Estructura", "Editor de Estilo"]
    )

    if st.button("Limpiar Chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.divider()

    # SECCIÓN DE PERSISTENCIA
    with st.expander("💾 Guardar/Cargar Progreso"):
        # Botón para descargar la sesión actual
        st.download_button(
            label="Descargar Proyecto (.json)",
            data=exportar_sesion(),
            file_name="mi_novela_ia.json",
            mime="application/json"
        )

        # Subir sesión guardada anteriormente
        archivo_cargado = st.file_uploader("Importar Proyecto", type=["json"])
        if archivo_cargado:
            if st.button("Confirmar Importación"):
                importar_sesion(archivo_cargado)
                st.rerun()

    st.divider()

    # SECCIÓN DE CARGAR DOCUMENTO PDF O DOCX
    st.subheader("📁 Cargar Borrador")
    uploaded_file = st.file_uploader("Sube tu documento (PDF o DOCX)", type=["pdf", "docx"])

    if uploaded_file is not None:
        texto_extraido = ""
        try:
            if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                texto_extraido = "\n".join([para.text for para in doc.paragraphs])
            elif uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    texto_extraido += page.extract_text()

            if texto_extraido:
                st.session_state.master_doc = texto_extraido
                st.success("✅ ¡Documento cargado!")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    st.divider()


# --- DEFINICIÓN DE PROMPTS DE SISTEMA ---
PROMPTS = {
    "Estratega Creativo": "Eres un consultor creativo. Tu base de conocimiento es el 'DOCUMENTO MAESTRO' adjunto. Ayuda a expandir la trama y personajes basándote en lo escrito.",
    "Arquitecto de Estructura": "Eres experto en ritmo y estructura narrativa. Analiza el 'DOCUMENTO MAESTRO' para detectar baches o problemas de coherencia.",
    "Editor de Estilo": "Eres un editor de prosa profesional. Tu tarea es pulir el texto del 'DOCUMENTO MAESTRO' elevando la calidad literaria y manteniendo la voz del autor."
}

# --- CONFIGURACIÓN DE SEGURIDAD (Para evitar bloqueos de contenido literario) ---
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- DISEÑO DE DOS COLUMNAS ---
col_chat, col_doc = st.columns([1, 1])

# --- COLUMNA DERECHA: DOCUMENTO MAESTRO ---
with col_doc:
    st.subheader("📖 Documento Maestro (Memoria)")
    st.info("La IA lee este texto para mantener la coherencia.")
    st.session_state.master_doc = st.text_area(
        "Contenido actual:",
        value=st.session_state.master_doc,
        height=600
    )

# --- COLUMNA IZQUIERDA: INTERFAZ DE CHAT ---
with col_chat:
    st.subheader(f"💬 Chat con {agente_activo}")

    # Mostrar historial de mensajes
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
        if not api_key:
            st.error("Introduce la API Key en la barra lateral.")
        else:
            # 1. Mostrar mensaje del usuario
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. Generar respuesta
            with st.chat_message("assistant"):
                with st.spinner(f"El {agente_activo} está analizando con precisión..."):

                    # PROMPT DE INGENIERÍA PARA EVITAR ALUCINACIONES
                    contexto_blindado = f"""
                                ESTRICTAMENTE: Eres un asistente que solo utiliza la información del DOCUMENTO MAESTRO.
                                Si algo no está en el documento, di claramente 'No tengo esa información en el borrador'.

                                PASOS PARA TU RESPUESTA:
                                1. Extrae los hechos relevantes del DOCUMENTO MAESTRO.
                                2. Verifica que tu respuesta no contradiga lo escrito.
                                3. Si sugieres algo nuevo, márcalo como [SUGERENCIA].

                                DOCUMENTO MAESTRO:
                                {st.session_state.master_doc}

                                PETICIÓN: {prompt}
                                """

                    # Preparar contexto total
                    contexto_total = f"""
                    INSTRUCCIÓN DE ROL: {PROMPTS[agente_activo]}
                    ---
                    DOCUMENTO MAESTRO ACTUAL:
                    {st.session_state.master_doc}
                    ---
                    PETICIÓN DEL USUARIO:
                    {prompt}
                    """

                    try:
                        # Inicializar modelo con Safety Settings e Instrucción de Sistema
                        model = genai.GenerativeModel(
                            model_name=modelo_nombre,
                            safety_settings=safety_settings,
                            system_instruction=PROMPTS[agente_activo]
                        )

                        response = model.generate_content(contexto_total)

                        # Manejo de respuesta bloqueada o vacía
                        if response.candidates and len(response.candidates[0].content.parts) > 0:
                            respuesta_texto = response.text
                            st.markdown(respuesta_texto)
                            st.session_state.chat_history.append({"role": "assistant", "content": respuesta_texto})
                        else:
                            st.warning(
                                "⚠️ Google bloqueó esta respuesta por seguridad. Intenta cambiar el tono de la escena.")
                            if response.prompt_feedback:
                                st.caption(f"Motivo: {response.prompt_feedback.block_reason}")

                    except Exception as e:
                        st.error(f"Error técnico: {str(e)}")