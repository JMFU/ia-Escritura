import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Multi-Agente Literario", layout="wide")

# Inicializar estados de sesión
if "master_doc" not in st.session_state:
    st.session_state.master_doc = "ESCRIBE AQUÍ EL RESUMEN O CAPÍTULOS DE TU LIBRO..."
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- BARRA LATERAL (Configuración y API) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    api_key = st.text_input("Google API Key:", type="password")
    modelo_nombre = st.selectbox(
        "Modelo:",
        ["gemini-1.5-flash", "gemini-1.5-pro"]
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

# --- DEFINICIÓN DE PROMPTS DE SISTEMA ---
# Cada prompt ahora incluye una instrucción para mirar el "Documento Maestro"
PROMPTS = {
    "Estratega Creativo": "Eres un consultor creativo. Tu base de conocimiento es el 'DOCUMENTO MAESTRO' adjunto. Ayuda a expandir la trama y personajes basándote ÚNICAMENTE en lo que ya está escrito o sugiriendo adiciones coherentes.",

    "Arquitecto de Estructura": "Eres experto en ritmo y estructura. Analiza el 'DOCUMENTO MAESTRO' para detectar baches en la trama, problemas de ritmo o inconsistencias narrativas en los actos.",

    "Editor de Estilo": "Eres un editor de prosa. Tu tarea es pulir el texto del 'DOCUMENTO MAESTRO' o los fragmentos que el usuario te pase, manteniendo la voz del autor pero elevando la calidad literaria."
}

# --- DISEÑO DE DOS COLUMNAS ---
col_chat, col_doc = st.columns([1, 1])

# --- COLUMNA DERECHA: DOCUMENTO MAESTRO (Memoria Compartida) ---
with col_doc:
    st.subheader("📖 Documento Maestro (Memoria)")
    st.info("Todo lo que escribas aquí será leído por los agentes para darte respuestas con contexto.")
    # El usuario puede editar el libro/notas aquí
    st.session_state.master_doc = st.text_area(
        "Contenido del libro / Notas de mundo / Personajes",
        value=st.session_state.master_doc,
        height=600
    )

# --- COLUMNA IZQUIERDA: INTERFAZ DE CHAT ---
with col_chat:
    st.subheader(f"💬 Chat con {agente_activo}")

    # Mostrar historial
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte con el libro?"):
        if not api_key:
            st.error("Introduce la API Key en la barra lateral.")
        else:
            # Añadir mensaje del usuario al historial
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Preparar el contexto total para Gemini
            # Combinamos Instrucciones de Sistema + Memoria Compartida + Prompt
            contexto_total = f"""
            INSTRUCCIÓN DE ROL: {PROMPTS[agente_activo]}

            --- INICIO DEL DOCUMENTO MAESTRO ---
            {st.session_state.master_doc}
            --- FIN DEL DOCUMENTO MAESTRO ---

            PREGUNTA O PETICIÓN DEL USUARIO:
            {prompt}
            """

            with st.chat_message("assistant"):
                with st.spinner("Consultando memoria y generando respuesta..."):
                    try:
                        model = genai.GenerativeModel(model_name=modelo_nombre)
                        # Enviamos el contexto total
                        response = model.generate_content(contexto_total)
                        respuesta_texto = response.text
                        st.markdown(respuesta_texto)

                        # Guardar en historial
                        st.session_state.chat_history.append({"role": "assistant", "content": respuesta_texto})
                    except Exception as e:
                        st.error(f"Error: {e}")