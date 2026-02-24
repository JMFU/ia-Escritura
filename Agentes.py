import google.generativeai as genai
import os

# Configura tu API KEY
genai.configure(api_key="TU_API_KEY_AQUÍ")

# Define los filtros para permitir más libertad creativa
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class AgenteEscritura:
    def __init__(self, nombre, instrucciones_sistema):
        self.nombre = nombre
        # Configuramos el modelo con sus instrucciones específicas
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", # O gemini-1.5-pro para mayor calidad
            safety_settings=safety_settings,
            system_instruction=instrucciones_sistema
        )
        self.chat = self.model.start_chat(history=[])

    def responder(self, mensaje):
        response = self.chat.send_message(mensaje)
        return response.text

# --- DEFINICIÓN DE LOS AGENTES ---

# 1. El Estratega (Creatividad)
instrucciones_estratega = """
Eres un experto consultor literario. Tu función es ayudar a expandir ideas, 
crear giros argumentales sorprendentes y profundizar en la psicología de los personajes. 
Tu tono es inspirador y creativo.
"""

# 2. El Arquitecto (Estructura)
instrucciones_arquitecto = """
Eres un experto en estructura narrativa (Viaje del héroe, estructura en 3 actos, etc.). 
Tu trabajo es asegurar que el ritmo de la historia sea correcto y que no haya huecos en el guion.
"""

# 3. El Editor (Estilo)
instrucciones_editor = """
Eres un editor profesional con ojo clínico para la prosa. 
Te enfocas en mejorar el vocabulario, eliminar muletillas, ajustar el tono y asegurar 
que la lectura fluya perfectamente. Eres crítico y directo.
"""

try:
    response = model.generate_content(contexto_total)

    # Verificar si la respuesta tiene contenido antes de acceder a .text
    if response.candidates and response.candidates[0].content.parts:
        respuesta_texto = response.text
        st.markdown(respuesta_texto)
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta_texto})
    else:
        # Si no hay candidatos, es que fue bloqueado
        st.warning(
            "⚠️ La respuesta fue bloqueada por los filtros de seguridad de Google. Intenta reformular tu idea o suavizar el contenido.")
        if response.prompt_feedback:
            st.caption(f"Razón del bloqueo: {response.prompt_feedback.block_reason}")

except Exception as e:
    st.error(f"Ocurrió un error inesperado: {str(e)}")

# --- ORQUESTADOR DEL FLUJO ---

class SistemaEscritor:
    def __init__(self):
        self.estratega = AgenteEscritura("Estratega", instrucciones_estratega)
        self.arquitecto = AgenteEscritura("Arquitecto", instrucciones_arquitecto)
        self.editor = AgenteEscritura("Editor", instrucciones_editor)

    def proceso_creativo_completo(self, idea_inicial):
        print(f"--- 💡 Fase 1: Ideación (Estratega) ---")
        propuesta = self.estratega.responder(f"Tengo esta idea inicial: {idea_inicial}. Expándela y dime 2 giros interesantes.")
        print(propuesta)

        print(f"\n--- 🏗️ Fase 2: Estructura (Arquitecto) ---")
        estructura = self.arquitecto.responder(f"Basado en esta idea: {propuesta}, crea una escaleta de 3 actos.")
        print(estructura)

        print(f"\n--- ✍️ Fase 3: Refinamiento de Prosa (Editor) ---")
        # Supongamos que el usuario escribe un párrafo basado en lo anterior
        borrador = "El hombre caminaba por la calle oscura con miedo. Hacía frío."
        revision = self.editor.responder(f"Mejora este texto para que sea más evocador y literario: {borrador}")
        print(revision)

# --- EJECUCIÓN ---
escritorio_ia = SistemaEscritor()
escritorio_ia.proceso_creativo_completo("Una detective que descubre que el crimen que investiga ocurrió en un universo paralelo.")